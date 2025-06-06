#!/usr/bin/env python3
"""
TickTick Clone Enhanced - Setup and Installation Script
Automated setup for the enhanced productivity application
"""

import os
import sys
import subprocess
import json
import shutil
import platform
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import tempfile
import urllib.request
import zipfile


class Colors:
    """Terminal color codes for enhanced output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SetupManager:
    """Enhanced setup manager for TickTick Clone"""

    def __init__(self):
        self.app_name = "TickTick Clone Enhanced"
        self.version = "2.0.0"
        self.python_min_version = (3, 8)
        self.app_dir = Path.cwd()
        self.requirements_file = self.app_dir / "requirements.txt"

        # Setup directories
        self.directories = [
            "data",
            "backups",
            "cache",
            "config",
            "logs",
            "exports",
            "templates"
        ]

        # Configuration files to create
        self.config_files = {
            "config/app_config.json": self._get_default_app_config(),
            "config/user_preferences.json": self._get_default_user_preferences(),
            ".env": self._get_default_env_config(),
            ".gitignore": self._get_default_gitignore()
        }

    def run_setup(self, options: Dict[str, bool] = None):
        """Run complete setup process"""

        if options is None:
            options = {
                "check_system": True,
                "install_dependencies": True,
                "create_directories": True,
                "create_configs": True,
                "initialize_database": True,
                "run_tests": False,
                "create_shortcuts": True
            }

        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("=" * 60)
        print(f"  {self.app_name} v{self.version}")
        print("  Enhanced Setup & Installation")
        print("=" * 60)
        print(f"{Colors.ENDC}")

        try:
            # Step 1: System checks
            if options["check_system"]:
                self._print_step("🔍 Checking system requirements")
                self._check_system_requirements()
                self._check_dependencies()

            # Step 2: Install dependencies
            if options["install_dependencies"]:
                self._print_step("📦 Installing dependencies")
                self._install_python_dependencies()
                self._install_optional_dependencies()

            # Step 3: Create directory structure
            if options["create_directories"]:
                self._print_step("📁 Creating directory structure")
                self._create_directories()

            # Step 4: Create configuration files
            if options["create_configs"]:
                self._print_step("⚙️ Creating configuration files")
                self._create_configuration_files()

            # Step 5: Initialize database
            if options["initialize_database"]:
                self._print_step("🗄️ Initializing database")
                self._initialize_database()

            # Step 6: Run tests (optional)
            if options["run_tests"]:
                self._print_step("🧪 Running tests")
                self._run_tests()

            # Step 7: Create shortcuts (optional)
            if options["create_shortcuts"]:
                self._print_step("🔗 Creating shortcuts")
                self._create_shortcuts()

            # Setup complete
            self._print_success()

        except Exception as e:
            self._print_error(f"Setup failed: {str(e)}")
            sys.exit(1)

    def _check_system_requirements(self):
        """Check system requirements"""

        # Check Python version
        current_version = sys.version_info[:2]
        if current_version < self.python_min_version:
            raise Exception(f"Python {self.python_min_version[0]}.{self.python_min_version[1]}+ required, "
                            f"but {current_version[0]}.{current_version[1]} found")

        print(f"  ✅ Python {current_version[0]}.{current_version[1]} - OK")

        # Check operating system
        os_name = platform.system()
        print(f"  ✅ Operating System: {os_name} - OK")

        # Check available disk space
        disk_usage = shutil.disk_usage(self.app_dir)
        free_gb = disk_usage.free / (1024 ** 3)
        if free_gb < 1:
            print(f"  ⚠️ Low disk space: {free_gb:.1f}GB available")
        else:
            print(f"  ✅ Disk space: {free_gb:.1f}GB available - OK")

        # Check write permissions
        test_file = self.app_dir / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print(f"  ✅ Write permissions - OK")
        except Exception:
            raise Exception("No write permission in application directory")

    def _check_dependencies(self):
        """Check for existing dependencies"""

        critical_packages = [
            "streamlit",
            "pandas",
            "plotly",
            "numpy"
        ]

        missing_packages = []

        for package in critical_packages:
            try:
                __import__(package)
                print(f"  ✅ {package} - Already installed")
            except ImportError:
                missing_packages.append(package)
                print(f"  ⚠️ {package} - Missing")

        if missing_packages:
            print(f"  📦 {len(missing_packages)} packages need to be installed")
        else:
            print(f"  ✅ All critical packages available")

    def _install_python_dependencies(self):
        """Install Python dependencies from requirements.txt"""

        if not self.requirements_file.exists():
            print(f"  ⚠️ Requirements file not found, creating basic one")
            self._create_basic_requirements()

        print(f"  📦 Installing packages from {self.requirements_file}")

        try:
            # Upgrade pip first
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True)

            # Install requirements
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)
            ], check=True, capture_output=True, text=True)

            print(f"  ✅ Dependencies installed successfully")

        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install dependencies")
            print(f"     Error: {e.stderr}")

            # Try installing critical packages individually
            critical_packages = ["streamlit", "pandas", "plotly", "numpy"]

            print(f"  🔄 Attempting to install critical packages individually...")

            for package in critical_packages:
                try:
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", package
                    ], check=True, capture_output=True)
                    print(f"     ✅ {package} installed")
                except subprocess.CalledProcessError:
                    print(f"     ❌ Failed to install {package}")

    def _install_optional_dependencies(self):
        """Install optional dependencies for enhanced features"""

        optional_packages = {
            "scikit-learn": "Advanced analytics",
            "openpyxl": "Excel export support",
            "fuzzywuzzy": "Fuzzy text matching",
            "python-levenshtein": "Fast text similarity"
        }

        print(f"  🔧 Installing optional packages...")

        for package, description in optional_packages.items():
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], check=True, capture_output=True)
                print(f"     ✅ {package} - {description}")
            except subprocess.CalledProcessError:
                print(f"     ⚠️ {package} - Failed (feature may be limited)")

    def _create_directories(self):
        """Create necessary directory structure"""

        for directory in self.directories:
            dir_path = self.app_dir / directory
            dir_path.mkdir(exist_ok=True)
            print(f"  ✅ Created: {directory}/")

            # Create subdirectories for specific folders
            if directory == "data":
                (dir_path / "exports").mkdir(exist_ok=True)
                (dir_path / "imports").mkdir(exist_ok=True)
                print(f"     ✅ Created: {directory}/exports/")
                print(f"     ✅ Created: {directory}/imports/")

            elif directory == "logs":
                (dir_path / "app").mkdir(exist_ok=True)
                (dir_path / "error").mkdir(exist_ok=True)
                print(f"     ✅ Created: {directory}/app/")
                print(f"     ✅ Created: {directory}/error/")

    def _create_configuration_files(self):
        """Create default configuration files"""

        for file_path, content in self.config_files.items():
            full_path = self.app_dir / file_path

            # Create parent directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Don't overwrite existing files
            if full_path.exists():
                print(f"  ✅ {file_path} - Already exists")
                continue

            # Write content based on type
            if isinstance(content, dict):
                with open(full_path, 'w') as f:
                    json.dump(content, f, indent=2)
            else:
                full_path.write_text(content)

            print(f"  ✅ Created: {file_path}")

    def _initialize_database(self):
        """Initialize the application database"""

        try:
            # Import after dependencies are installed
            from data_persistence import SmartDataManager

            print(f"  🗄️ Initializing SQLite database...")

            data_manager = SmartDataManager("sqlite")
            print(f"     ✅ Database schema created")

            # Create sample data if requested
            response = input(f"  📋 Create sample data? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                self._create_sample_data(data_manager)

        except ImportError as e:
            print(f"  ⚠️ Could not initialize database: {e}")
            print(f"     Database will be created on first run")

    def _create_sample_data(self, data_manager):
        """Create sample tasks and habits"""

        from datetime import datetime, date, timedelta
        import uuid

        # Sample tasks
        sample_tasks = [
            {
                "id": str(uuid.uuid4()),
                "title": "Welcome to TickTick Clone Enhanced!",
                "description": "Explore the features of your new productivity app",
                "due_date": (date.today() + timedelta(days=1)).isoformat(),
                "priority": "high",
                "list_name": "Personal",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "tags": ["welcome", "tutorial"],
                "subtasks": []
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Set up your first habit",
                "description": "Create a daily habit to track your progress",
                "due_date": date.today().isoformat(),
                "priority": "medium",
                "list_name": "Personal",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "tags": ["habits", "setup"],
                "subtasks": []
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Try the Pomodoro timer",
                "description": "Use the focus mode to complete a task",
                "priority": "low",
                "list_name": "Personal",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "tags": ["pomodoro", "focus"],
                "subtasks": []
            }
        ]

        # Sample habits
        sample_habits = [
            {
                "id": str(uuid.uuid4()),
                "name": "Daily Planning",
                "frequency": "daily",
                "target": 1,
                "reminder_time": "09:00",
                "category": "Productivity",
                "created_at": datetime.now().isoformat(),
                "completion_dates": [],
                "streak": 0,
                "best_streak": 0,
                "active": True
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Exercise",
                "frequency": "daily",
                "target": 1,
                "reminder_time": "18:00",
                "category": "Health",
                "created_at": datetime.now().isoformat(),
                "completion_dates": [],
                "streak": 0,
                "best_streak": 0,
                "active": True
            }
        ]

        try:
            data_manager.save_data("tasks", sample_tasks)
            data_manager.save_data("habits", sample_habits)
            print(f"     ✅ Sample data created")
        except Exception as e:
            print(f"     ⚠️ Could not create sample data: {e}")

    def _run_tests(self):
        """Run basic tests to verify installation"""

        print(f"  🧪 Running system tests...")

        tests = [
            ("Import streamlit", lambda: __import__("streamlit")),
            ("Import pandas", lambda: __import__("pandas")),
            ("Import plotly", lambda: __import__("plotly")),
            ("Check data directory", lambda: (self.app_dir / "data").exists()),
            ("Check config directory", lambda: (self.app_dir / "config").exists()),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                result = test_func()
                if result is not False:
                    print(f"     ✅ {test_name}")
                    passed += 1
                else:
                    print(f"     ❌ {test_name}")
            except Exception as e:
                print(f"     ❌ {test_name}: {e}")

        print(f"  📊 Tests passed: {passed}/{total}")

        if passed < total:
            print(f"  ⚠️ Some tests failed - application may have limited functionality")

    def _create_shortcuts(self):
        """Create desktop shortcuts and launch scripts"""

        # Create launch script
        if platform.system() == "Windows":
            self._create_windows_shortcuts()
        else:
            self._create_unix_shortcuts()

    def _create_windows_shortcuts(self):
        """Create Windows batch files and shortcuts"""

        # Create batch file to launch the app
        batch_content = f"""@echo off
cd /d "{self.app_dir}"
python -m streamlit run app_enhanced.py --server.port=8501 --browser.gatherUsageStats=false
pause
"""

        batch_file = self.app_dir / "run_ticktick.bat"
        batch_file.write_text(batch_content)
        print(f"  ✅ Created: run_ticktick.bat")

        # Make batch file executable
        os.chmod(batch_file, 0o755)

    def _create_unix_shortcuts(self):
        """Create Unix shell scripts"""

        # Create shell script to launch the app
        script_content = f"""#!/bin/bash
cd "{self.app_dir}"
python3 -m streamlit run app_enhanced.py --server.port=8501 --browser.gatherUsageStats=false
"""

        script_file = self.app_dir / "run_ticktick.sh"
        script_file.write_text(script_content)
        print(f"  ✅ Created: run_ticktick.sh")

        # Make script executable
        os.chmod(script_file, 0o755)

    def _create_basic_requirements(self):
        """Create a basic requirements.txt if it doesn't exist"""

        basic_requirements = """# TickTick Clone Enhanced - Basic Requirements
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.15.0
numpy>=1.24.0
python-dateutil>=2.8.2
openpyxl>=3.1.0
"""

        self.requirements_file.write_text(basic_requirements)
        print(f"  ✅ Created basic requirements.txt")

    def _get_default_app_config(self) -> Dict:
        """Get default application configuration"""

        return {
            "app_name": self.app_name,
            "version": self.version,
            "debug": False,
            "environment": "production",
            "data_directory": "data",
            "database": {
                "type": "sqlite",
                "database": "data/ticktick_enhanced.db"
            },
            "ui": {
                "theme": "default",
                "language": "en",
                "timezone": "UTC",
                "enable_animations": True,
                "compact_mode": False,
                "show_tutorial": True
            },
            "productivity": {
                "pomodoro_work_duration": 25,
                "pomodoro_short_break": 5,
                "pomodoro_long_break": 30,
                "sessions_until_long_break": 4,
                "daily_goal_sessions": 8
            },
            "backup": {
                "auto_backup_enabled": True,
                "backup_interval_hours": 24,
                "max_backups_to_keep": 30
            },
            "created_at": datetime.now().isoformat()
        }

    def _get_default_user_preferences(self) -> Dict:
        """Get default user preferences"""

        return {
            "default_list": "Inbox",
            "default_priority": "none",
            "pomodoro_auto_start": False,
            "notification_sound": True,
            "theme_preference": "default",
            "show_completed_tasks": False,
            "task_sorting": "due_date",
            "habit_reminder_enabled": True,
            "achievement_notifications": True,
            "weekly_summary": True
        }

    def _get_default_env_config(self) -> str:
        """Get default environment configuration"""

        return """# TickTick Clone Enhanced - Environment Configuration
# Copy this file to .env and customize as needed

# Application Settings
TICKTICK_DEBUG=false
TICKTICK_DATA_DIR=data
TICKTICK_LOG_LEVEL=INFO

# UI Settings  
TICKTICK_THEME=default
TICKTICK_LANG=en
TICKTICK_TIMEZONE=UTC

# Database Settings
TICKTICK_DB_TYPE=sqlite
# TICKTICK_DB_HOST=localhost
# TICKTICK_DB_PORT=5432
# TICKTICK_DB_NAME=ticktick_enhanced
# TICKTICK_DB_USER=
# TICKTICK_DB_PASS=

# External Integrations (optional)
# TICKTICK_GOOGLE_CALENDAR_API_KEY=
# TICKTICK_SLACK_WEBHOOK_URL=
# TICKTICK_NOTION_API_KEY=

# Security (optional)
# TICKTICK_SECRET_KEY=
# TICKTICK_ENCRYPT_DATA=false
"""

    def _get_default_gitignore(self) -> str:
        """Get default .gitignore content"""

        return """# TickTick Clone Enhanced - Git Ignore File

# Data files
data/
backups/
logs/
exports/
cache/

# Configuration files with secrets
.env
config/.secrets.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Streamlit
.streamlit/

# Temporary files
*.tmp
*.temp
.cache/
"""

    def _print_step(self, message: str):
        """Print a setup step"""
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}{message}{Colors.ENDC}")

    def _print_success(self):
        """Print setup success message"""

        print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
        print("=" * 60)
        print("  🎉 Setup completed successfully!")
        print("=" * 60)
        print(f"{Colors.ENDC}")

        print(f"{Colors.OKGREEN}")
        print("Next steps:")
        print("1. Run the application:")

        if platform.system() == "Windows":
            print("   • Double-click 'run_ticktick.bat', or")
            print("   • Run: python -m streamlit run app_enhanced.py")
        else:
            print("   • Run: ./run_ticktick.sh, or")
            print("   • Run: python3 -m streamlit run app_enhanced.py")

        print("\n2. Open your browser to: http://localhost:8501")
        print("3. Follow the welcome tutorial to get started")
        print("4. Customize settings in the Settings tab")
        print(f"{Colors.ENDC}")

        print(f"{Colors.OKCYAN}")
        print("📚 Documentation: Check the README.md file")
        print("🐛 Issues: Report bugs in the issue tracker")
        print("💡 Features: Suggest improvements")
        print(f"{Colors.ENDC}")

    def _print_error(self, message: str):
        """Print error message"""
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ {message}{Colors.ENDC}")


def main():
    """Main setup function"""

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="TickTick Clone Enhanced Setup")
    parser.add_argument("--minimal", action="store_true",
                        help="Minimal setup (dependencies only)")
    parser.add_argument("--no-deps", action="store_true",
                        help="Skip dependency installation")
    parser.add_argument("--dev", action="store_true",
                        help="Development setup with tests")
    parser.add_argument("--reset", action="store_true",
                        help="Reset configuration to defaults")

    args = parser.parse_args()

    # Configure setup options
    options = {
        "check_system": True,
        "install_dependencies": not args.no_deps,
        "create_directories": True,
        "create_configs": not args.reset,
        "initialize_database": not args.minimal,
        "run_tests": args.dev,
        "create_shortcuts": not args.minimal
    }

    # Run setup
    setup_manager = SetupManager()

    if args.reset:
        # Reset configuration
        print(f"{Colors.WARNING}Resetting configuration to defaults...{Colors.ENDC}")

        config_dir = Path("config")
        if config_dir.exists():
            shutil.rmtree(config_dir)

        env_file = Path(".env")
        if env_file.exists():
            env_file.unlink()

        print(f"{Colors.OKGREEN}Configuration reset complete. Run setup again.{Colors.ENDC}")
        return

    setup_manager.run_setup(options)


if __name__ == "__main__":
    main()