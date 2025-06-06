import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import time, timedelta
import streamlit as st


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    type: str = "sqlite"  # sqlite, postgresql, mysql
    host: str = "localhost"
    port: int = 5432
    database: str = "ticktick_enhanced.db"
    username: str = ""
    password: str = ""
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False  # SQL logging


@dataclass
class NotificationConfig:
    """Notification system configuration"""
    enabled: bool = True
    sound_enabled: bool = True
    desktop_notifications: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    max_notifications_per_hour: int = 5
    smart_batching: bool = True
    auto_dismiss_after_hours: int = 24
    categories_enabled: Dict[str, bool] = None

    def __post_init__(self):
        if self.categories_enabled is None:
            self.categories_enabled = {
                "tasks": True,
                "habits": True,
                "productivity": True,
                "achievements": True,
                "reminders": True,
                "insights": True
            }


@dataclass
class BackupConfig:
    """Backup and data persistence configuration"""
    auto_backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_backups_to_keep: int = 30
    backup_location: str = "backups"
    compress_backups: bool = True
    backup_to_cloud: bool = False
    cloud_provider: str = ""  # dropbox, google_drive, onedrive
    encryption_enabled: bool = False
    retention_policy_days: int = 90


@dataclass
class UIConfig:
    """User interface configuration"""
    theme: str = "default"  # default, dark, light, custom
    language: str = "en"
    timezone: str = "UTC"
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"
    currency: str = "USD"
    first_day_of_week: int = 0  # 0=Monday, 6=Sunday
    tasks_per_page: int = 50
    sidebar_width: int = 300
    enable_animations: bool = True
    compact_mode: bool = False
    show_tutorial: bool = True


@dataclass
class ProductivityConfig:
    """Productivity features configuration"""
    pomodoro_work_duration: int = 25  # minutes
    pomodoro_short_break: int = 5
    pomodoro_long_break: int = 30
    sessions_until_long_break: int = 4
    auto_start_breaks: bool = False
    auto_start_pomodoros: bool = False
    daily_goal_sessions: int = 8
    focus_mode_enabled: bool = True
    smart_scheduling_enabled: bool = True
    time_tracking_enabled: bool = True


@dataclass
class SecurityConfig:
    """Security and privacy configuration"""
    password_protection: bool = False
    session_timeout_minutes: int = 480  # 8 hours
    auto_lock_enabled: bool = False
    data_encryption: bool = False
    audit_log_enabled: bool = True
    export_restrictions: bool = False
    sharing_enabled: bool = False
    anonymous_analytics: bool = True


@dataclass
class IntegrationConfig:
    """External integrations configuration"""
    google_calendar_enabled: bool = False
    google_calendar_api_key: str = ""
    outlook_enabled: bool = False
    outlook_api_key: str = ""
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    notion_enabled: bool = False
    notion_api_key: str = ""
    todoist_sync_enabled: bool = False
    todoist_api_key: str = ""


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    lazy_loading: bool = True
    batch_operations: bool = True
    compression_enabled: bool = True
    memory_limit_mb: int = 512
    max_concurrent_operations: int = 4
    debug_mode: bool = False
    profiling_enabled: bool = False


@dataclass
class AppConfig:
    """Main application configuration"""
    app_name: str = "TickTick Clone Enhanced"
    version: str = "2.0.0"
    debug: bool = False
    environment: str = "production"  # development, staging, production
    log_level: str = "INFO"
    data_directory: str = "data"

    # Sub-configurations
    database: DatabaseConfig = None
    notifications: NotificationConfig = None
    backup: BackupConfig = None
    ui: UIConfig = None
    productivity: ProductivityConfig = None
    security: SecurityConfig = None
    integrations: IntegrationConfig = None
    performance: PerformanceConfig = None

    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.notifications is None:
            self.notifications = NotificationConfig()
        if self.backup is None:
            self.backup = BackupConfig()
        if self.ui is None:
            self.ui = UIConfig()
        if self.productivity is None:
            self.productivity = ProductivityConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.integrations is None:
            self.integrations = IntegrationConfig()
        if self.performance is None:
            self.performance = PerformanceConfig()


class ConfigManager:
    """Enhanced configuration manager with file persistence and validation"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        self.config_file = self.config_dir / "app_config.json"
        self.user_config_file = self.config_dir / "user_config.json"
        self.secrets_file = self.config_dir / ".secrets.json"

        self._config: Optional[AppConfig] = None
        self._user_overrides: Dict[str, Any] = {}

    def load_config(self) -> AppConfig:
        """Load configuration from files and environment variables"""

        # Start with default configuration
        config_dict = asdict(AppConfig())

        # Load base configuration file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                config_dict = self._deep_merge(config_dict, file_config)
            except Exception as e:
                st.warning(f"Could not load config file: {e}")

        # Load user-specific overrides
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, 'r') as f:
                    user_config = json.load(f)
                config_dict = self._deep_merge(config_dict, user_config)
                self._user_overrides = user_config
            except Exception as e:
                st.warning(f"Could not load user config: {e}")

        # Load secrets separately
        secrets = self._load_secrets()
        if secrets:
            config_dict = self._deep_merge(config_dict, secrets)

        # Override with environment variables
        config_dict = self._apply_env_overrides(config_dict)

        # Convert back to AppConfig object
        self._config = self._dict_to_config(config_dict)

        return self._config

    def save_config(self, config: AppConfig, user_only: bool = False):
        """Save configuration to file"""

        config_dict = asdict(config)

        if user_only:
            # Save only user-specific settings
            self._save_user_config(config_dict)
        else:
            # Save full configuration
            self._save_base_config(config_dict)

        self._config = config

    def get_config(self) -> AppConfig:
        """Get current configuration (load if not already loaded)"""
        if self._config is None:
            return self.load_config()
        return self._config

    def update_setting(self, setting_path: str, value: Any, save: bool = True):
        """Update a specific setting using dot notation (e.g., 'ui.theme')"""

        if self._config is None:
            self._config = self.load_config()

        # Navigate to the setting using dot notation
        parts = setting_path.split('.')
        current = asdict(self._config)

        # Navigate to parent
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the value
        current[parts[-1]] = value

        # Update user overrides
        self._set_nested_dict(self._user_overrides, parts, value)

        # Convert back to config object
        self._config = self._dict_to_config(current if len(parts) == 1 else asdict(self._config))

        if save:
            self._save_user_config(self._user_overrides)

    def get_setting(self, setting_path: str, default: Any = None) -> Any:
        """Get a specific setting using dot notation"""

        if self._config is None:
            self._config = self.load_config()

        parts = setting_path.split('.')
        current = asdict(self._config)

        try:
            for part in parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default

    def reset_to_defaults(self, save: bool = True):
        """Reset configuration to defaults"""
        self._config = AppConfig()
        self._user_overrides = {}

        if save:
            # Remove user config file
            if self.user_config_file.exists():
                self.user_config_file.unlink()

    def export_config(self, include_secrets: bool = False) -> str:
        """Export configuration as JSON string"""
        if self._config is None:
            self._config = self.load_config()

        config_dict = asdict(self._config)

        if not include_secrets:
            # Remove sensitive information
            config_dict = self._remove_secrets(config_dict)

        return json.dumps(config_dict, indent=2, default=str)

    def import_config(self, config_json: str, merge: bool = True) -> bool:
        """Import configuration from JSON string"""
        try:
            imported_config = json.loads(config_json)

            if merge and self._config is not None:
                current_config = asdict(self._config)
                merged_config = self._deep_merge(current_config, imported_config)
                self._config = self._dict_to_config(merged_config)
            else:
                self._config = self._dict_to_config(imported_config)

            return True
        except Exception as e:
            st.error(f"Failed to import configuration: {e}")
            return False

    def validate_config(self, config: AppConfig = None) -> List[str]:
        """Validate configuration and return list of errors"""
        if config is None:
            config = self.get_config()

        errors = []

        # Validate paths
        if not Path(config.data_directory).exists():
            try:
                Path(config.data_directory).mkdir(parents=True, exist_ok=True)
            except Exception:
                errors.append(f"Cannot create data directory: {config.data_directory}")

        # Validate time formats
        try:
            time.fromisoformat(config.notifications.quiet_hours_start)
            time.fromisoformat(config.notifications.quiet_hours_end)
        except ValueError:
            errors.append("Invalid quiet hours time format")

        # Validate numeric ranges
        if config.productivity.pomodoro_work_duration < 1 or config.productivity.pomodoro_work_duration > 120:
            errors.append("Pomodoro work duration must be between 1 and 120 minutes")

        if config.backup.backup_interval_hours < 1:
            errors.append("Backup interval must be at least 1 hour")

        # Validate database config
        if config.database.type not in ["sqlite", "postgresql", "mysql"]:
            errors.append("Invalid database type")

        return errors

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _dict_to_config(self, config_dict: Dict) -> AppConfig:
        """Convert dictionary to AppConfig object"""
        try:
            # Handle nested configurations
            if 'database' in config_dict and isinstance(config_dict['database'], dict):
                config_dict['database'] = DatabaseConfig(**config_dict['database'])

            if 'notifications' in config_dict and isinstance(config_dict['notifications'], dict):
                config_dict['notifications'] = NotificationConfig(**config_dict['notifications'])

            if 'backup' in config_dict and isinstance(config_dict['backup'], dict):
                config_dict['backup'] = BackupConfig(**config_dict['backup'])

            if 'ui' in config_dict and isinstance(config_dict['ui'], dict):
                config_dict['ui'] = UIConfig(**config_dict['ui'])

            if 'productivity' in config_dict and isinstance(config_dict['productivity'], dict):
                config_dict['productivity'] = ProductivityConfig(**config_dict['productivity'])

            if 'security' in config_dict and isinstance(config_dict['security'], dict):
                config_dict['security'] = SecurityConfig(**config_dict['security'])

            if 'integrations' in config_dict and isinstance(config_dict['integrations'], dict):
                config_dict['integrations'] = IntegrationConfig(**config_dict['integrations'])

            if 'performance' in config_dict and isinstance(config_dict['performance'], dict):
                config_dict['performance'] = PerformanceConfig(**config_dict['performance'])

            return AppConfig(**config_dict)
        except Exception as e:
            st.warning(f"Error creating config object: {e}")
            return AppConfig()  # Return default config

    def _load_secrets(self) -> Dict:
        """Load secrets from separate file"""
        if not self.secrets_file.exists():
            return {}

        try:
            with open(self.secrets_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _apply_env_overrides(self, config_dict: Dict) -> Dict:
        """Apply environment variable overrides"""

        # Define environment variable mappings
        env_mappings = {
            'TICKTICK_DEBUG': 'debug',
            'TICKTICK_DATA_DIR': 'data_directory',
            'TICKTICK_DB_TYPE': 'database.type',
            'TICKTICK_DB_HOST': 'database.host',
            'TICKTICK_DB_PORT': 'database.port',
            'TICKTICK_THEME': 'ui.theme',
            'TICKTICK_LANG': 'ui.language',
            'TICKTICK_TIMEZONE': 'ui.timezone',
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert value to appropriate type
                if env_var.endswith('_PORT'):
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif env_var.endswith('_DEBUG'):
                    value = value.lower() in ('true', '1', 'yes', 'on')

                # Set nested value
                parts = config_path.split('.')
                current = config_dict
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value

        return config_dict

    def _save_base_config(self, config_dict: Dict):
        """Save base configuration file"""
        # Remove sensitive information before saving
        safe_config = self._remove_secrets(config_dict)

        with open(self.config_file, 'w') as f:
            json.dump(safe_config, f, indent=2, default=str)

    def _save_user_config(self, config_dict: Dict):
        """Save user-specific configuration"""
        with open(self.user_config_file, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

    def _remove_secrets(self, config_dict: Dict) -> Dict:
        """Remove sensitive information from config"""
        safe_config = config_dict.copy()

        # Remove sensitive fields
        sensitive_paths = [
            ['database', 'password'],
            ['integrations', 'google_calendar_api_key'],
            ['integrations', 'outlook_api_key'],
            ['integrations', 'slack_webhook_url'],
            ['integrations', 'notion_api_key'],
            ['integrations', 'todoist_api_key'],
        ]

        for path in sensitive_paths:
            current = safe_config
            for part in path[:-1]:
                if part in current and isinstance(current[part], dict):
                    current = current[part]
                else:
                    break
            else:
                if path[-1] in current:
                    current[path[-1]] = "***HIDDEN***"

        return safe_config

    def _set_nested_dict(self, dictionary: Dict, keys: List[str], value: Any):
        """Set value in nested dictionary"""
        current = dictionary
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value


# Global configuration instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get current application configuration"""
    return get_config_manager().get_config()


def update_config(setting_path: str, value: Any, save: bool = True):
    """Update a configuration setting"""
    get_config_manager().update_setting(setting_path, value, save)


def get_setting(setting_path: str, default: Any = None) -> Any:
    """Get a configuration setting"""
    return get_config_manager().get_setting(setting_path, default)


# Configuration UI helpers
def render_config_section(config: AppConfig, section: str):
    """Render configuration section in Streamlit UI"""

    if section == "ui":
        st.markdown("#### 🎨 User Interface")

        col1, col2 = st.columns(2)
        with col1:
            new_theme = st.selectbox("Theme",
                                     options=["default", "dark", "light"],
                                     value=config.ui.theme)
            new_language = st.selectbox("Language",
                                        options=["en", "es", "fr", "de"],
                                        value=config.ui.language)
            new_compact = st.checkbox("Compact mode", value=config.ui.compact_mode)

        with col2:
            new_animations = st.checkbox("Enable animations", value=config.ui.enable_animations)
            new_tasks_per_page = st.slider("Tasks per page", 10, 100, config.ui.tasks_per_page)
            new_tutorial = st.checkbox("Show tutorial", value=config.ui.show_tutorial)

        return {
            'theme': new_theme,
            'language': new_language,
            'compact_mode': new_compact,
            'enable_animations': new_animations,
            'tasks_per_page': new_tasks_per_page,
            'show_tutorial': new_tutorial
        }

    elif section == "productivity":
        st.markdown("#### 🍅 Productivity Features")

        col1, col2 = st.columns(2)
        with col1:
            new_work_duration = st.slider("Pomodoro work (minutes)", 15, 60, config.productivity.pomodoro_work_duration)
            new_short_break = st.slider("Short break (minutes)", 3, 15, config.productivity.pomodoro_short_break)
            new_long_break = st.slider("Long break (minutes)", 15, 45, config.productivity.pomodoro_long_break)

        with col2:
            new_sessions_until_long = st.slider("Sessions until long break", 2, 8,
                                                config.productivity.sessions_until_long_break)
            new_daily_goal = st.slider("Daily goal (sessions)", 1, 16, config.productivity.daily_goal_sessions)
            new_time_tracking = st.checkbox("Enable time tracking", value=config.productivity.time_tracking_enabled)

        return {
            'pomodoro_work_duration': new_work_duration,
            'pomodoro_short_break': new_short_break,
            'pomodoro_long_break': new_long_break,
            'sessions_until_long_break': new_sessions_until_long,
            'daily_goal_sessions': new_daily_goal,
            'time_tracking_enabled': new_time_tracking
        }

    elif section == "notifications":
        st.markdown("#### 🔔 Notifications")

        col1, col2 = st.columns(2)
        with col1:
            new_enabled = st.checkbox("Enable notifications", value=config.notifications.enabled)
            new_sound = st.checkbox("Sound notifications", value=config.notifications.sound_enabled)
            new_desktop = st.checkbox("Desktop notifications", value=config.notifications.desktop_notifications)

        with col2:
            new_max_per_hour = st.slider("Max per hour", 1, 20, config.notifications.max_notifications_per_hour)
            new_smart_batching = st.checkbox("Smart batching", value=config.notifications.smart_batching)
            new_auto_dismiss = st.slider("Auto dismiss (hours)", 1, 48, config.notifications.auto_dismiss_after_hours)

        # Quiet hours
        st.markdown("**Quiet Hours**")
        col1, col2 = st.columns(2)
        with col1:
            new_quiet_start = st.time_input("Start time",
                                            value=time.fromisoformat(config.notifications.quiet_hours_start))
        with col2:
            new_quiet_end = st.time_input("End time",
                                          value=time.fromisoformat(config.notifications.quiet_hours_end))

        return {
            'enabled': new_enabled,
            'sound_enabled': new_sound,
            'desktop_notifications': new_desktop,
            'max_notifications_per_hour': new_max_per_hour,
            'smart_batching': new_smart_batching,
            'auto_dismiss_after_hours': new_auto_dismiss,
            'quiet_hours_start': new_quiet_start.strftime('%H:%M'),
            'quiet_hours_end': new_quiet_end.strftime('%H:%M')
        }

    elif section == "backup":
        st.markdown("#### 💾 Backup & Data")

        col1, col2 = st.columns(2)
        with col1:
            new_auto_backup = st.checkbox("Auto backup", value=config.backup.auto_backup_enabled)
            new_interval = st.slider("Backup interval (hours)", 1, 168, config.backup.backup_interval_hours)
            new_max_backups = st.slider("Max backups to keep", 5, 100, config.backup.max_backups_to_keep)

        with col2:
            new_compress = st.checkbox("Compress backups", value=config.backup.compress_backups)
            new_cloud_backup = st.checkbox("Cloud backup", value=config.backup.backup_to_cloud)
            new_encryption = st.checkbox("Encrypt backups", value=config.backup.encryption_enabled)

        return {
            'auto_backup_enabled': new_auto_backup,
            'backup_interval_hours': new_interval,
            'max_backups_to_keep': new_max_backups,
            'compress_backups': new_compress,
            'backup_to_cloud': new_cloud_backup,
            'encryption_enabled': new_encryption
        }

    return {}