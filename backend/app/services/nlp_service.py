"""NLP service for entity extraction using spaCy"""

import logging
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)

# Lazy load spaCy model
_nlp = None


def get_nlp():
    """Lazy load spaCy model"""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            logger.info("Run: python -m spacy download en_core_web_sm")
            raise
    return _nlp


class NLPService:
    """Service for natural language processing and entity extraction"""

    # Entity types relevant for 911 calls
    EMERGENCY_ENTITY_TYPES = {
        "WEAPON": ["gun", "knife", "weapon", "rifle", "pistol", "firearm"],
        "INJURY": ["bleeding", "unconscious", "hurt", "injured", "pain", "wound", "broken"],
        "VEHICLE": ["car", "truck", "vehicle", "van", "motorcycle", "SUV"],
        "MEDICAL": ["heart attack", "stroke", "seizure", "breathing", "chest pain"],
        "TIME_REFERENCE": ["minutes ago", "just now", "earlier", "hour ago"],
    }

    async def extract_entities(
        self,
        text: str,
        session_id: str,
        timestamp_ms: int
    ) -> Dict[str, Any]:
        """
        Extract named entities and emergency-specific information from text.

        Args:
            text: Text to analyze
            session_id: Call session ID
            timestamp_ms: Timestamp of the text

        Returns:
            Dict containing extracted entities and processing metadata
        """
        start_time = time.time()

        try:
            nlp = get_nlp()
            doc = nlp(text)

            entities = []

            # Extract standard named entities
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "GPE", "LOC", "FAC", "ORG", "DATE", "TIME", "CARDINAL"]:
                    entities.append({
                        "entity_type": ent.label_,
                        "entity_value": ent.text,
                        "confidence_score": 0.85,  # spaCy doesn't provide confidence for entities
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                        "metadata": {
                            "label": ent.label_,
                            "is_builtin": True
                        }
                    })

            # Extract emergency-specific entities using keyword matching
            text_lower = text.lower()
            for entity_type, keywords in self.EMERGENCY_ENTITY_TYPES.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        start_pos = text_lower.index(keyword)
                        entities.append({
                            "entity_type": entity_type,
                            "entity_value": keyword,
                            "confidence_score": 0.90,
                            "start_char": start_pos,
                            "end_char": start_pos + len(keyword),
                            "metadata": {
                                "detection_method": "keyword_match",
                                "is_emergency_entity": True
                            }
                        })

            processing_time = (time.time() - start_time) * 1000

            return {
                "entities": entities,
                "text": text,
                "processing_time_ms": processing_time,
                "entity_count": len(entities)
            }

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {
                "entities": [],
                "text": text,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment/emotion in text.

        Args:
            text: Text to analyze

        Returns:
            Dict containing sentiment analysis results
        """
        try:
            # Simple rule-based sentiment analysis
            # In production, use a proper sentiment model
            text_lower = text.lower()

            panic_indicators = ["help", "emergency", "dying", "can't breathe", "hurry"]
            calm_indicators = ["okay", "fine", "stable", "calm", "better"]

            panic_score = sum(1 for word in panic_indicators if word in text_lower)
            calm_score = sum(1 for word in calm_indicators if word in text_lower)

            if panic_score > calm_score:
                emotion = "panicked" if panic_score > 2 else "anxious"
                confidence = min(0.7 + (panic_score * 0.1), 0.95)
            elif calm_score > 0:
                emotion = "calm"
                confidence = 0.8
            else:
                emotion = "neutral"
                confidence = 0.6

            return {
                "emotion": emotion,
                "confidence": confidence,
                "indicators": {
                    "panic_score": panic_score,
                    "calm_score": calm_score
                }
            }

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                "emotion": "neutral",
                "confidence": 0.5,
                "error": str(e)
            }

    def get_entity_summary(self, entities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Get a summary of extracted entities grouped by type.

        Args:
            entities: List of extracted entities

        Returns:
            Dict with entity types as keys and lists of values
        """
        summary = {}
        for entity in entities:
            entity_type = entity["entity_type"]
            entity_value = entity["entity_value"]

            if entity_type not in summary:
                summary[entity_type] = []

            if entity_value not in summary[entity_type]:
                summary[entity_type].append(entity_value)

        return summary


# Global service instance
nlp_service = NLPService()
