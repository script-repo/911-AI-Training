"""Run script for 911 Operator Training Simulator Backend"""

import uvicorn
import sys
import os

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings


if __name__ == "__main__":
    print("=" * 60)
    print("Starting 911 Operator Training Simulator Backend")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print(f"Host: {settings.backend_host}")
    print(f"Port: {settings.backend_port}")
    print(f"Workers: {settings.backend_workers}")
    print(f"Log Level: {settings.log_level}")
    print("=" * 60)
    print()

    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True
    )
