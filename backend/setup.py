"""Setup script for 911 Operator Training Simulator Backend"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n{description}...")
    try:
        subprocess.run(command, check=True, shell=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        return False


def main():
    """Main setup function"""
    print("=" * 60)
    print("911 Operator Training Simulator - Backend Setup")
    print("=" * 60)

    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("\n⚠️  Warning: You are not in a virtual environment!")
        print("It's recommended to use a virtual environment:")
        print("  python -m venv venv")
        print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return

    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        print("\n✗ Failed to install requirements. Please check your setup.")
        return

    # Download spaCy model
    print("\nDownloading spaCy language model...")
    if not run_command("python -m spacy download en_core_web_sm", "Downloading spaCy model"):
        print("⚠️  spaCy model download failed. You can try manually:")
        print("  python -m spacy download en_core_web_sm")

    # Check if .env file exists
    if not os.path.exists(".env"):
        print("\n⚠️  No .env file found!")
        print("Please create a .env file based on ../.env.example")
        print("  cp ../.env.example .env")
    else:
        print("\n✓ .env file found")

    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Ensure your .env file is properly configured")
    print("2. Start required services (PostgreSQL, Redis, MinIO, Coqui TTS)")
    print("3. Run database migrations: alembic upgrade head")
    print("4. Start the backend server: python -m uvicorn app.main:app --reload")
    print("\nFor health check: curl http://localhost:8000/health")
    print("For API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
