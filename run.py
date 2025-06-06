#!/usr/bin/env python3
"""
TickTick Clone - Application Launcher
Run this file to start the TickTick clone application
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'uuid'
    ]

    missing_packages = []

    for package in required_packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing_packages.append(package)
        else:
            print(f"✅ {package} is installed")

    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")

        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                *missing_packages
            ])
            print("✅ All packages installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages")
            print("Please run: pip install -r requirements.txt")
            return False

    print("✅ All required packages are installed")
    return True


def create_data_directory():
    """Create data directory if it doesn't exist"""
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir()
        print("✅ Created data directory")
    else:
        print("✅ Data directory exists")


def get_app_file():
    """Determine which app file to run"""
    # Check for enhanced version first
    if Path("app_enhanced.py").exists():
        return "app_enhanced.py"
    elif Path("app.py").exists():
        return "app.py"
    else:
        print("❌ No app.py or app_enhanced.py found")
        return None


def run_app():
    """Run the Streamlit application"""
    app_file = get_app_file()
    if not app_file:
        return False

    print(f"🚀 Starting TickTick Clone ({app_file})...")

    # Streamlit configuration
    config_args = [
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false",
        "--server.headless=false"
    ]

    try:
        # Run streamlit
        subprocess.run([
                           sys.executable, "-m", "streamlit", "run", app_file
                       ] + config_args)

    except KeyboardInterrupt:
        print("\n👋 TickTick Clone stopped")
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        return False

    return True


def main():
    """Main launcher function"""
    print("=" * 50)
    print("🎯 TickTick Clone Launcher")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check and install requirements
    if not check_requirements():
        sys.exit(1)

    # Create necessary directories
    create_data_directory()

    # Run the application
    if not run_app():
        sys.exit(1)


if __name__ == "__main__":
    main()