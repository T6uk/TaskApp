import streamlit as st
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import json
import uuid
from enum import Enum


class Priority(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class Task:
    def __init__(self, title: str, description: str = "", due_date: Optional[date] = None,
                 priority: Priority = Priority.NONE, list_name: str = "Inbox",
                 tags: List[str] = None, subtasks: List[str] = None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.due_date = due_date.isoformat() if due_date else None
        self.priority = priority.value
        self.list_name = list_name
        self.status = TaskStatus.PENDING.value
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.tags = tags or []
        self.subtasks = subtasks or []
        self.recurring = None
        self.reminder = None
        self.estimated_time = None
        self.actual_time = None


class Habit:
    def __init__(self, name: str, frequency: str = "daily", target: int = 1,
                 reminder_time: str = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.frequency = frequency
        self.target = target
        self.reminder_time = reminder_time
        self.created_at = datetime.now().isoformat()
        self.completion_dates = []
        self.streak = 0
        self.best_streak = 0


def init_session_state():
    """Initialize all session state variables"""
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []

    if 'lists' not in st.session_state:
        st.session_state.lists = ["Inbox", "Personal", "Work", "Shopping", "Health"]

    if 'habits' not in st.session_state:
        st.session_state.habits = []

    if 'current_view' not in st.session_state:
        st.session_state.current_view = "tasks"

    if 'current_filter' not in st.session_state:
        st.session_state.current_filter = "all"

    if 'pomodoro_state' not in st.session_state:
        st.session_state.pomodoro_state = {
            'active': False,
            'start_time': None,
            'duration': 25,
            'current_type': 'work',
            'sessions_completed': 0
        }

    if 'folders' not in st.session_state:
        st.session_state.folders = ["Personal", "Work", "Projects"]

    if 'app_settings' not in st.session_state:
        st.session_state.app_settings = {
            'theme': 'default',
            'language': 'en',
            'notifications': True,
            'auto_save': True
        }


def add_task(title: str, description: str = "", due_date: Optional[date] = None,
             priority: Priority = Priority.NONE, list_name: str = "Inbox",
             tags: List[str] = None, subtasks: List[str] = None) -> str:
    """Add a new task and return its ID"""
    task = Task(title, description, due_date, priority, list_name, tags, subtasks)
    st.session_state.tasks.append(task.__dict__)
    return task.id


def update_task(task_id: str, **kwargs) -> bool:
    """Update a task with given parameters"""
    for task in st.session_state.tasks:
        if task['id'] == task_id:
            for key, value in kwargs.items():
                if key in task:
                    task[key] = value
            return True
    return False


def complete_task(task_id: str) -> bool:
    """Mark a task as completed"""
    for task in st.session_state.tasks:
        if task['id'] == task_id:
            task['status'] = TaskStatus.COMPLETED.value
            task['completed_at'] = datetime.now().isoformat()
            return True
    return False


def uncomplete_task(task_id: str) -> bool:
    """Mark a completed task as pending"""
    for task in st.session_state.tasks:
        if task['id'] == task_id:
            task['status'] = TaskStatus.PENDING.value
            task['completed_at'] = None
            return True
    return False


def delete_task(task_id: str) -> bool:
    """Delete a task"""
    original_count = len(st.session_state.tasks)
    st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task_id]
    return len(st.session_state.tasks) < original_count


def get_task_by_id(task_id: str) -> Optional[Dict]:
    """Get a task by its ID"""
    for task in st.session_state.tasks:
        if task['id'] == task_id:
            return task
    return None


def get_tasks_by_filter(filter_type: str) -> List[Dict]:
    """Get tasks based on filter type"""
    tasks = st.session_state.tasks.copy()
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    week_end = (date.today() + timedelta(days=7)).isoformat()

    if filter_type == "all":
        return tasks
    elif filter_type == "today":
        return [t for t in tasks if t['due_date'] == today]
    elif filter_type == "tomorrow":
        return [t for t in tasks if t['due_date'] == tomorrow]
    elif filter_type == "this_week":
        return [t for t in tasks if t['due_date'] and t['due_date'] <= week_end]
    elif filter_type == "overdue":
        return [t for t in tasks if t['due_date'] and t['due_date'] < today
                and t['status'] == TaskStatus.PENDING.value]
    elif filter_type == "high_priority":
        return [t for t in tasks if t['priority'] == Priority.HIGH.value]
    elif filter_type == "completed":
        return [t for t in tasks if t['status'] == TaskStatus.COMPLETED.value]
    elif filter_type in st.session_state.lists:
        return [t for t in tasks if t['list_name'] == filter_type]
    else:
        return tasks


def get_task_stats() -> Dict:
    """Get comprehensive task statistics"""
    tasks = st.session_state.tasks
    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == TaskStatus.COMPLETED.value])
    pending = total - completed

    today = date.today().isoformat()
    overdue = len([t for t in tasks
                   if t['due_date'] and t['due_date'] < today
                   and t['status'] == TaskStatus.PENDING.value])

    due_today = len([t for t in tasks if t['due_date'] == today])

    # Priority distribution
    priority_stats = {}
    for priority in Priority:
        priority_stats[priority.value] = len([t for t in tasks if t['priority'] == priority.value])

    # List distribution
    list_stats = {}
    for list_name in st.session_state.lists:
        list_tasks = [t for t in tasks if t['list_name'] == list_name]
        list_stats[list_name] = {
            'total': len(list_tasks),
            'completed': len([t for t in list_tasks if t['status'] == TaskStatus.COMPLETED.value])
        }

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "overdue": overdue,
        "due_today": due_today,
        "completion_rate": (completed / total * 100) if total > 0 else 0,
        "priority_stats": priority_stats,
        "list_stats": list_stats
    }


def add_habit(name: str, frequency: str = "daily", target: int = 1,
              reminder_time: str = None) -> str:
    """Add a new habit and return its ID"""
    habit = Habit(name, frequency, target, reminder_time)
    st.session_state.habits.append(habit.__dict__)
    return habit.id


def complete_habit(habit_id: str, completion_date: date = None) -> bool:
    """Mark a habit as completed for a specific date"""
    if not completion_date:
        completion_date = date.today()

    date_str = completion_date.isoformat()

    for habit in st.session_state.habits:
        if habit['id'] == habit_id:
            if date_str not in habit['completion_dates']:
                habit['completion_dates'].append(date_str)
                habit['completion_dates'].sort()
                update_habit_streak(habit_id)
                return True
    return False


def uncomplete_habit(habit_id: str, completion_date: date = None) -> bool:
    """Remove habit completion for a specific date"""
    if not completion_date:
        completion_date = date.today()

    date_str = completion_date.isoformat()

    for habit in st.session_state.habits:
        if habit['id'] == habit_id:
            if date_str in habit['completion_dates']:
                habit['completion_dates'].remove(date_str)
                update_habit_streak(habit_id)
                return True
    return False


def update_habit_streak(habit_id: str):
    """Update the streak for a habit"""
    for habit in st.session_state.habits:
        if habit['id'] == habit_id:
            if not habit['completion_dates']:
                habit['streak'] = 0
                return

            # Calculate current streak
            today = date.today()
            current_streak = 0

            for i in range(100):  # Check last 100 days
                check_date = (today - timedelta(days=i)).isoformat()
                if check_date in habit['completion_dates']:
                    current_streak += 1
                else:
                    break

            habit['streak'] = current_streak
            habit['best_streak'] = max(habit.get('best_streak', 0), current_streak)


def delete_habit(habit_id: str) -> bool:
    """Delete a habit"""
    original_count = len(st.session_state.habits)
    st.session_state.habits = [h for h in st.session_state.habits if h['id'] != habit_id]
    return len(st.session_state.habits) < original_count


def get_habit_stats() -> Dict:
    """Get habit statistics"""
    habits = st.session_state.habits
    total_habits = len(habits)

    if total_habits == 0:
        return {"total": 0, "completed_today": 0, "completion_rate": 0, "average_streak": 0}

    today = date.today().isoformat()
    completed_today = len([h for h in habits if today in h['completion_dates']])

    total_streaks = sum(h.get('streak', 0) for h in habits)
    average_streak = total_streaks / total_habits if total_habits > 0 else 0

    return {
        "total": total_habits,
        "completed_today": completed_today,
        "completion_rate": (completed_today / total_habits * 100) if total_habits > 0 else 0,
        "average_streak": average_streak
    }


def parse_natural_language_date(text: str) -> Optional[date]:
    """Parse natural language date expressions"""
    text = text.lower().strip()
    today = date.today()

    if text in ["today", "now"]:
        return today
    elif text in ["tomorrow", "tmr"]:
        return today + timedelta(days=1)
    elif text in ["yesterday"]:
        return today - timedelta(days=1)
    elif text in ["next week"]:
        return today + timedelta(days=7)
    elif text in ["next month"]:
        return today + timedelta(days=30)
    elif "days" in text:
        try:
            days = int(text.split()[0])
            return today + timedelta(days=days)
        except:
            return None

    # Try to parse specific date formats
    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y"]
    for fmt in date_formats:
        try:
            return datetime.strptime(text, fmt).date()
        except:
            continue

    return None


def export_data(format_type: str = "json") -> str:
    """Export all data in specified format"""
    data = {
        "tasks": st.session_state.tasks,
        "habits": st.session_state.habits,
        "lists": st.session_state.lists,
        "folders": st.session_state.folders,
        "export_date": datetime.now().isoformat()
    }

    if format_type.lower() == "json":
        return json.dumps(data, indent=2)
    else:
        # Add CSV export logic here if needed
        return json.dumps(data, indent=2)


def import_data(data_str: str, format_type: str = "json") -> bool:
    """Import data from string"""
    try:
        if format_type.lower() == "json":
            data = json.loads(data_str)

            if "tasks" in data:
                st.session_state.tasks = data["tasks"]
            if "habits" in data:
                st.session_state.habits = data["habits"]
            if "lists" in data:
                st.session_state.lists = data["lists"]
            if "folders" in data:
                st.session_state.folders = data["folders"]

            return True
    except:
        return False

    return False


def search_tasks(query: str) -> List[Dict]:
    """Search tasks by title, description, or tags"""
    if not query:
        return st.session_state.tasks

    query = query.lower()
    results = []

    for task in st.session_state.tasks:
        # Search in title
        if query in task['title'].lower():
            results.append(task)
            continue

        # Search in description
        if task['description'] and query in task['description'].lower():
            results.append(task)
            continue

        # Search in tags
        if any(query in tag.lower() for tag in task['tags']):
            results.append(task)
            continue

    return results


def get_productivity_insights() -> Dict:
    """Generate productivity insights"""
    tasks = st.session_state.tasks
    habits = st.session_state.habits

    # Task insights
    completed_tasks = [t for t in tasks if t['status'] == TaskStatus.COMPLETED.value]

    # Completion times analysis
    completion_hours = []
    for task in completed_tasks:
        if task['completed_at']:
            completed_time = datetime.fromisoformat(task['completed_at'])
            completion_hours.append(completed_time.hour)

    most_productive_hour = max(set(completion_hours), key=completion_hours.count) if completion_hours else None

    # Weekly completion pattern
    weekly_completions = {}
    for task in completed_tasks:
        if task['completed_at']:
            completed_date = datetime.fromisoformat(task['completed_at'])
            day_name = completed_date.strftime('%A')
            weekly_completions[day_name] = weekly_completions.get(day_name, 0) + 1

    most_productive_day = max(weekly_completions, key=weekly_completions.get) if weekly_completions else None

    # Habit insights
    habit_completion_rates = []
    for habit in habits:
        total_days = max(1, (date.today() - datetime.fromisoformat(habit['created_at']).date()).days)
        completion_rate = len(habit['completion_dates']) / total_days * 100
        habit_completion_rates.append(completion_rate)

    average_habit_completion = sum(habit_completion_rates) / len(
        habit_completion_rates) if habit_completion_rates else 0

    return {
        "most_productive_hour": most_productive_hour,
        "most_productive_day": most_productive_day,
        "average_habit_completion": average_habit_completion,
        "total_tasks_completed": len(completed_tasks),
        "weekly_completions": weekly_completions
    }


def format_date_display(date_str: str) -> str:
    """Format date string for display"""
    if not date_str:
        return "No date"

    try:
        date_obj = datetime.fromisoformat(date_str).date()
        today = date.today()

        if date_obj == today:
            return "Today"
        elif date_obj == today + timedelta(days=1):
            return "Tomorrow"
        elif date_obj == today - timedelta(days=1):
            return "Yesterday"
        else:
            return date_obj.strftime("%b %d, %Y")
    except:
        return date_str


def get_priority_color(priority: str) -> str:
    """Get color for priority level"""
    colors = {
        "none": "#95a5a6",
        "low": "#3498db",
        "medium": "#f39c12",
        "high": "#e74c3c"
    }
    return colors.get(priority, "#95a5a6")


def validate_task_data(title: str, due_date: Optional[date] = None) -> List[str]:
    """Validate task data and return list of errors"""
    errors = []

    if not title or not title.strip():
        errors.append("Task title is required")
    elif len(title) > 100:
        errors.append("Task title must be less than 100 characters")

    if due_date and due_date < date.today():
        errors.append("Due date cannot be in the past")

    return errors