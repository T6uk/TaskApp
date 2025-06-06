#!/usr/bin/env python3
"""
TickTick Clone - Setup and Installation Script
Handles installation, configuration, and initial setup
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime


def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🎯 TickTick Clone - Setup & Installation")
    print("=" * 60)
    print("Setting up your personal productivity app...")
    print()


def check_system_requirements():
    """Check system requirements"""
    print("📋 Checking system requirements...")

    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")

    # Check pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                       capture_output=True, check=True)
        print("✅ pip is available")
    except:
        print("❌ pip not found")
        return False

    return True


def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")

    requirements = [
        "streamlit>=1.28.0",
        "pandas>=1.5.0",
        "plotly>=5.15.0",
        "openpyxl>=3.0.0",  # For Excel export
        "python-dateutil>=2.8.0"
    ]

    try:
        print("Installing packages...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True, capture_output=True)

        subprocess.run([
                           sys.executable, "-m", "pip", "install"
                       ] + requirements, check=True)

        print("✅ All dependencies installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_directory_structure():
    """Create necessary directories"""
    print("\n📁 Creating directory structure...")

    directories = [
        "data",
        "data/backups",
        "data/exports",
        "logs",
        "config"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")


def create_sample_data():
    """Create sample data for demonstration"""
    print("\n📄 Creating sample data...")

    sample_tasks = [
        {
            "id": "sample_1",
            "title": "Welcome to TickTick Clone!",
            "description": "Explore all the features of your new productivity app",
            "due_date": (datetime.now().date()).isoformat(),
            "priority": "high",
            "list_name": "Personal",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "tags": ["welcome", "getting-started"],
            "subtasks": [
                "Check out the calendar view",
                "Try the Pomodoro timer",
                "Create your first habit"
            ],
            "recurring": None,
            "reminder": None
        },
        {
            "id": "sample_2",
            "title": "Set up your workspace",
            "description": "Customize lists and organize your tasks",
            "due_date": None,
            "priority": "medium",
            "list_name": "Work",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "tags": ["setup", "organization"],
            "subtasks": [],
            "recurring": None,
            "reminder": None
        },
        {
            "id": "sample_3",
            "title": "Learn about advanced features",
            "description": "Explore Eisenhower Matrix, bulk operations, and analytics",
            "due_date": None,
            "priority": "low",
            "list_name": "Personal",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "tags": ["learning", "features"],
            "subtasks": [],
            "recurring": None,
            "reminder": None
        }
    ]

    sample_habits = [
        {
            "id": "habit_1",
            "name": "Daily Planning",
            "frequency": "daily",
            "target": 1,
            "reminder_time": "09:00",
            "created_at": datetime.now().isoformat(),
            "completion_dates": [],
            "streak": 0,
            "best_streak": 0
        },
        {
            "id": "habit_2",
            "name": "Exercise",
            "frequency": "daily",
            "target": 1,
            "reminder_time": "18:00",
            "created_at": datetime.now().isoformat(),
            "completion_dates": [],
            "streak": 0,
            "best_streak": 0
        }
    ]

    # Save sample data
    data_dir = Path("data")

    with open(data_dir / "tasks.json", "w") as f:
        json.dump(sample_tasks, f, indent=2)
    print("✅ Sample tasks created")

    with open(data_dir / "habits.json", "w") as f:
        json.dump(sample_habits, f, indent=2)
    print("✅ Sample habits created")


def create_config_files():
    """Create configuration files"""
    print("\n⚙️ Creating configuration files...")

    # App configuration
    app_config = {
        "app_name": "TickTick Clone",
        "version": "2.0.0",
        "theme": "default",
        "language": "en",
        "auto_save": True,
        "auto_save_interval": 30,
        "notifications_enabled": True,
        "data_storage": "file",
        "backup_retention_days": 30,
        "created_at": datetime.now().isoformat()
    }

    with open("config/app_config.json", "w") as f:
        json.dump(app_config, f, indent=2)
    print("✅ App configuration created")

    # User preferences
    user_preferences = {
        "default_list": "Inbox",
        "default_priority": "none",
        "pomodoro_work_duration": 25,
        "pomodoro_break_duration": 5,
        "pomodoro_long_break": 30,
        "habit_reminder_enabled": True,
        "achievement_notifications": True,
        "weekly_summary": True,
        "theme_preference": "default"
    }

    with open("config/user_preferences.json", "w") as f:
        json.dump(user_preferences, f, indent=2)
    print("✅ User preferences created")


def create_run_scripts():
    """Create platform-specific run scripts"""
    print("\n🚀 Creating run scripts...")

    # Windows batch file
    windows_script = """@echo off
title TickTick Clone
echo Starting TickTick Clone...
python run.py
pause
"""

    with open("run_ticktick.bat", "w") as f:
        f.write(windows_script)
    print("✅ Windows script: run_ticktick.bat")

    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting TickTick Clone..."
python3 run.py
"""

    with open("run_ticktick.sh", "w") as f:
        f.write(unix_script)

    # Make shell script executable
    try:
        os.chmod("run_ticktick.sh", 0o755)
        print("✅ Unix script: run_ticktick.sh")
    except:
        print("⚠️ Could not make shell script executable")


def create_desktop_shortcut():
    """Create desktop shortcut (Windows/Linux)"""
    print("\n🖥️ Creating desktop shortcut...")

    if sys.platform == "win32":
        # Windows shortcut creation would require pywin32
        print("ℹ️ Windows shortcut creation requires manual setup")
        print("   You can create a shortcut to run_ticktick.bat")

    elif sys.platform in ["linux", "darwin"]:
        # Linux desktop file
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=TickTick Clone
Comment=Personal Productivity App
Exec=python3 {Path.cwd() / 'run.py'}
Icon=productivity
Terminal=false
Categories=Office;Productivity;
"""

        desktop_file = Path.home() / "Desktop" / "TickTick-Clone.desktop"
        try:
            with open(desktop_file, "w") as f:
                f.write(desktop_content)
            os.chmod(desktop_file, 0o755)
            print("✅ Desktop shortcut created")
        except:
            print("⚠️ Could not create desktop shortcut")


def verify_installation():
    """Verify the installation is complete"""
    print("\n🔍 Verifying installation...")

    checks = [
        ("Python packages", lambda: __import__("streamlit") and __import__("pandas") and __import__("plotly")),
        ("Data directory", lambda: Path("data").exists()),
        ("Config files", lambda: Path("config/app_config.json").exists()),
        ("Sample data", lambda: Path("data/tasks.json").exists()),
        ("Run script", lambda: Path("run.py").exists())
    ]

    all_good = True
    for check_name, check_func in checks:
        try:
            check_func()
            print(f"✅ {check_name}")
        except:
            print(f"❌ {check_name}")
            all_good = False

    return all_good


def print_next_steps():
    """Print next steps for user"""
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run the app:")
    print("   • Windows: Double-click run_ticktick.bat")
    print("   • Mac/Linux: ./run_ticktick.sh")
    print("   • Or run: python run.py")
    print()
    print("2. Open your browser to: http://localhost:8501")
    print()
    print("3. Explore the features:")
    print("   • 📝 Tasks - Manage your to-do list")
    print("   • 📅 Calendar - Schedule and plan")
    print("   • 🎯 Habits - Track daily routines")
    print("   • 🍅 Pomodoro - Focus timer")
    print("   • 📊 Statistics - Track progress")
    print("   • 🧠 Advanced - Power user features")
    print()
    print("4. Check out the sample data to get started!")
    print()
    print("📚 Documentation: README.md")
    print("🐛 Issues: Check the troubleshooting section")
    print()
    print("Happy productivity! 🚀")


def main():
    """Main setup function"""
    print_header()

    # System requirements
    if not check_system_requirements():
        print("❌ System requirements not met")
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Create directories
    create_directory_structure()

    # Create configuration
    create_config_files()

    # Create sample data
    create_sample_data()

    # Create run scripts
    create_run_scripts()

    # Create desktop shortcut
    create_desktop_shortcut()

    # Verify installation
    if verify_installation():
        print_next_steps()
    else:
        print("❌ Installation verification failed")
        print("Please check the errors above and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()