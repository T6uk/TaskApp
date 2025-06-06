# Configuration file for TickTick Clone

# App Settings
APP_TITLE = "TickTick Clone"
APP_ICON = "✅"
APP_LAYOUT = "wide"

# Default Lists
DEFAULT_LISTS = ["Inbox", "Personal", "Work", "Shopping", "Health", "Learning"]

# Default Folders
DEFAULT_FOLDERS = ["Personal", "Work", "Projects"]

# Priority Colors (CSS classes)
PRIORITY_COLORS = {
    "none": "#95a5a6",    # Gray
    "low": "#3498db",     # Blue
    "medium": "#f39c12",  # Orange
    "high": "#e74c3c"     # Red
}

# Pomodoro Timer Settings
POMODORO_SETTINGS = {
    "work_duration": 25,      # minutes
    "short_break": 5,         # minutes
    "long_break": 30,         # minutes
    "sessions_until_long": 4  # number of work sessions
}

# Habit Frequencies
HABIT_FREQUENCIES = ["daily", "weekly", "monthly", "custom"]

# Theme Settings
THEMES = {
    "default": {
        "primary_color": "#2c3e50",
        "secondary_color": "#3498db",
        "background_color": "#ffffff",
        "sidebar_background": "#f8f9fa"
    },
    "dark": {
        "primary_color": "#ecf0f1",
        "secondary_color": "#3498db",
        "background_color": "#2c3e50",
        "sidebar_background": "#34495e"
    },
    "blue": {
        "primary_color": "#2980b9",
        "secondary_color": "#3498db",
        "background_color": "#ffffff",
        "sidebar_background": "#ebf3fd"
    }
}

# Date Formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DISPLAY_DATE_FORMAT = "%B %d, %Y"

# Task Settings
MAX_TASK_TITLE_LENGTH = 100
MAX_TASK_DESCRIPTION_LENGTH = 500
MAX_TAGS_PER_TASK = 10
MAX_SUBTASKS_PER_TASK = 20

# UI Settings
TASKS_PER_PAGE = 50
SIDEBAR_WIDTH = 300
MAIN_CONTENT_PADDING = 20

# Smart List Definitions
SMART_LISTS = {
    "today": {
        "name": "Today",
        "icon": "📅",
        "filter": "due_today"
    },
    "tomorrow": {
        "name": "Tomorrow",
        "icon": "📆",
        "filter": "due_tomorrow"
    },
    "this_week": {
        "name": "This Week",
        "icon": "📋",
        "filter": "due_this_week"
    },
    "overdue": {
        "name": "Overdue",
        "icon": "⚠️",
        "filter": "overdue"
    },
    "high_priority": {
        "name": "High Priority",
        "icon": "⭐",
        "filter": "high_priority"
    },
    "completed": {
        "name": "Completed",
        "icon": "✅",
        "filter": "completed"
    }
}

# Statistics Settings
STATS_CHART_HEIGHT = 400
STATS_CHART_WIDTH = 600
RECENT_ACTIVITY_DAYS = 7
MAX_RECENT_ACTIVITIES = 20

# Calendar Settings
CALENDAR_VIEWS = ["Month", "Week", "Day"]
DEFAULT_CALENDAR_VIEW = "Month"
TASKS_PER_CALENDAR_DAY = 3

# Export/Import Settings
EXPORT_FORMATS = ["JSON", "CSV", "TXT"]
IMPORT_FORMATS = ["JSON", "CSV"]

# Notification Settings (for future implementation)
NOTIFICATION_TYPES = {
    "task_due": "Task Due Reminder",
    "habit_reminder": "Habit Reminder",
    "pomodoro_break": "Pomodoro Break",
    "pomodoro_work": "Back to Work"
}

# Feature Flags
FEATURES = {
    "habits": True,
    "pomodoro": True,
    "statistics": True,
    "calendar": True,
    "collaboration": False,  # Not implemented
    "sync": False,          # Not implemented
    "notifications": False,  # Not implemented
    "themes": True,
    "export_import": False   # Not implemented
}

# Performance Settings
AUTO_SAVE_INTERVAL = 30  # seconds (for future implementation)
MAX_TASKS_IN_MEMORY = 1000
ENABLE_CACHING = True

# Validation Rules
VALIDATION = {
    "task_title_required": True,
    "due_date_format_check": True,
    "tag_format_check": True,
    "priority_validation": True
}

# UI Text/Labels
UI_TEXT = {
    "add_task_placeholder": "What do you want to do?",
    "no_tasks_message": "No tasks found. Create your first task above!",
    "no_habits_message": "No habits yet. Create your first habit above!",
    "task_completed_message": "Task completed successfully!",
    "habit_completed_message": "Habit marked as complete!",
    "pomodoro_finished_message": "Time's up! Take a break.",
    "confirm_delete": "Are you sure you want to delete this item?"
}

# Integration Settings (for future use)
INTEGRATIONS = {
    "google_calendar": {
        "enabled": False,
        "api_key": None
    },
    "outlook": {
        "enabled": False,
        "api_key": None
    },
    "slack": {
        "enabled": False,
        "webhook_url": None
    }
}