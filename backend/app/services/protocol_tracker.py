"""Real-time protocol event detection from call transcripts"""
import logging
import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.protocol_event import ProtocolEventType

logger = logging.getLogger(__name__)

# Patterns that indicate protocol questions/actions by the dispatcher
PROTOCOL_PATTERNS: Dict[ProtocolEventType, List[str]] = {
    ProtocolEventType.LOCATION_OBTAINED: [
        r"(?:what(?:'s| is) (?:the |your )?address)",
        r"(?:where (?:are you|is (?:this|the|that)))",
        r"(?:(?:what|which) (?:street|road|intersection|location))",
        r"(?:can you (?:give|tell) me (?:the |your )?(?:address|location))",
    ],
    ProtocolEventType.CALLBACK_NUMBER_OBTAINED: [
        r"(?:what(?:'s| is) (?:the |your )?(?:phone|callback|call.?back) ?(?:number)?)",
        r"(?:(?:phone|number) (?:you(?:'re| are) calling from))",
        r"(?:what number (?:can|should) (?:we|I) (?:call|reach))",
    ],
    ProtocolEventType.CONSCIOUSNESS_VERIFIED: [
        r"(?:is (?:he|she|the (?:person|patient|victim)) (?:conscious|awake|alert|responsive))",
        r"(?:(?:are|is) (?:they|he|she) (?:conscious|awake|responding))",
        r"(?:can (?:they|he|she) (?:hear|talk|speak|respond))",
    ],
    ProtocolEventType.BREATHING_VERIFIED: [
        r"(?:is (?:he|she|the (?:person|patient|victim)) breathing)",
        r"(?:(?:are|is) (?:they|he|she) breathing)",
        r"(?:can (?:they|he|she) breathe)",
        r"(?:(?:check|verify|confirm) (?:their |his |her )?breathing)",
    ],
    ProtocolEventType.WEAPON_INQUIRY: [
        r"(?:(?:any|are there) (?:weapons?|guns?|knives?|firearms?))",
        r"(?:(?:does|do) (?:he|she|they|anyone) have a weapon)",
        r"(?:is (?:he|she|anyone) armed)",
        r"(?:what (?:kind|type) of weapon)",
    ],
    ProtocolEventType.SUSPECT_DESCRIPTION: [
        r"(?:(?:can you )?describe (?:the |what )?(?:suspect|person|shooter|attacker|intruder))",
        r"(?:what (?:does|do) (?:he|she|they) look like)",
        r"(?:what (?:is|are) (?:he|she|they) wearing)",
    ],
    ProtocolEventType.CALLER_SAFETY_VERIFIED: [
        r"(?:are you (?:safe|okay|in (?:a )?safe (?:place|location)))",
        r"(?:(?:is|are) (?:you|everyone) (?:safe|okay|hurt|injured))",
        r"(?:(?:can you |are you able to )?get to (?:a )?safe)",
    ],
    ProtocolEventType.VICTIM_COUNT_CONFIRMED: [
        r"(?:how many (?:people|victims?|patients?|persons?) (?:are )?(?:hurt|injured|involved))",
        r"(?:(?:is it|are there) (?:just )?(?:one|1) (?:person|victim))",
        r"(?:(?:anyone|anybody) else (?:hurt|injured))",
    ],
    ProtocolEventType.CALLER_NAME_OBTAINED: [
        r"(?:what(?:'s| is) your name)",
        r"(?:(?:can|may) I (?:get|have) your name)",
        r"(?:who am I speaking (?:with|to))",
    ],
    ProtocolEventType.CPR_INSTRUCTIONS_GIVEN: [
        r"(?:(?:start|begin|do) (?:cpr|chest compressions|mouth.to.mouth))",
        r"(?:push (?:hard|down) (?:on|in the center of) (?:the |his |her )?chest)",
        r"(?:30 compressions)",
    ],
}

# Patterns that indicate the caller has provided key information
CALLER_RESPONSE_PATTERNS: Dict[ProtocolEventType, List[str]] = {
    ProtocolEventType.LOCATION_OBTAINED: [
        r"\d+\s+\w+\s+(?:street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd|lane|ln|way|court|ct)",
        r"(?:apartment|apt|unit|suite|ste)\s*#?\s*\w+",
    ],
    ProtocolEventType.CALLBACK_NUMBER_OBTAINED: [
        r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    ],
}


class ProtocolTracker:
    """Detects protocol adherence events in real-time from call transcripts."""

    def __init__(self):
        self._compiled_patterns: Dict[ProtocolEventType, List[re.Pattern]] = {}
        self._compiled_caller_patterns: Dict[ProtocolEventType, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        for event_type, patterns in PROTOCOL_PATTERNS.items():
            self._compiled_patterns[event_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        for event_type, patterns in CALLER_RESPONSE_PATTERNS.items():
            self._compiled_caller_patterns[event_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def detect_events(
        self,
        text: str,
        speaker: str,
        timestamp_ms: int,
        already_detected: Optional[set] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect protocol events in a transcript utterance.

        Args:
            text: The utterance text
            speaker: "operator" or "caller"
            timestamp_ms: Milliseconds from call start
            already_detected: Set of event types already detected (to avoid duplicates)

        Returns:
            List of detected events with type, timestamp, and details
        """
        detected = []
        already = already_detected or set()

        if speaker == "operator":
            patterns = self._compiled_patterns
        else:
            patterns = self._compiled_caller_patterns

        for event_type, compiled_list in patterns.items():
            if event_type.value in already:
                continue
            for pattern in compiled_list:
                match = pattern.search(text)
                if match:
                    detected.append({
                        "event_type": event_type,
                        "timestamp_ms": timestamp_ms,
                        "details": {
                            "matched_text": match.group(),
                            "speaker": speaker,
                            "full_text": text,
                        },
                    })
                    break  # Only detect each event type once per utterance

        return detected


protocol_tracker = ProtocolTracker()
