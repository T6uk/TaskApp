import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import uuid
import hashlib
from typing import Dict, List, Optional
import re
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="TickTick Pro - Ultimate Productivity Suite",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/ticktick-clone',
        'Report a bug': 'https://github.com/ticktick-clone/issues',
        'About': "TickTick Pro - The most advanced personal productivity app built with Streamlit"
    }
)

# Advanced CSS for modern UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .main {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 3px solid #e1e5f2;
    }

    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        margin: 8px 0;
        transition: transform 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-4px);
    }

    .task-card {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(0,0,0,0.1);
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .task-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--priority-color, #e0e0e0);
    }

    .task-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 40px rgba(0,0,0,0.12);
    }

    .task-card.completed {
        opacity: 0.7;
        background: rgba(248, 249, 250, 0.9);
    }

    .task-title {
        font-size: 16px;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 8px;
    }

    .task-title.completed {
        text-decoration: line-through;
        color: #a0aec0;
    }

    .task-meta {
        font-size: 12px;
        color: #718096;
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    }

    .task-tag {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .priority-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }

    .priority-high { background: #e53e3e; }
    .priority-medium { background: #ff8c00; }
    .priority-low { background: #38a169; }
    .priority-none { background: #cbd5e0; }

    .sidebar-section {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin: 16px 0;
        backdrop-filter: blur(10px);
    }

    .nav-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 8px;
        transition: all 0.2s ease;
        cursor: pointer;
        border: none;
        background: transparent;
        width: 100%;
        text-align: left;
    }

    .nav-item:hover {
        background: rgba(103, 126, 234, 0.1);
        transform: translateX(4px);
    }

    .nav-item.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .quick-add-container {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 8px 32px rgba(240, 147, 251, 0.3);
    }

    .habit-streak-indicator {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 12px;
    }

    .calendar-day {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        margin: 4px;
        min-height: 120px;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    .calendar-day:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }

    .calendar-today {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #667eea;
    }

    .pomodoro-timer {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        color: white;
        font-size: 64px;
        font-weight: 700;
        text-align: center;
        padding: 60px;
        border-radius: 50%;
        width: 280px;
        height: 280px;
        margin: 32px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 20px 60px rgba(255, 107, 107, 0.3);
        transition: all 0.3s ease;
    }

    .pomodoro-timer:hover {
        transform: scale(1.05);
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }

    .notification-badge {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        color: white;
        border-radius: 50%;
        padding: 4px 8px;
        font-size: 11px;
        font-weight: 600;
        position: absolute;
        top: -8px;
        right: -8px;
        min-width: 20px;
        text-align: center;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }

    .progress-ring {
        width: 120px;
        height: 120px;
        position: relative;
    }

    .progress-ring svg {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
    }

    .progress-ring circle {
        fill: none;
        stroke-width: 8;
        stroke-linecap: round;
    }

    .progress-background {
        stroke: #e2e8f0;
    }

    .progress-bar {
        stroke: url(#gradient);
        stroke-dasharray: 314;
        stroke-dashoffset: 314;
        transition: stroke-dashoffset 0.5s ease;
    }

    .floating-action-button {
        position: fixed;
        bottom: 32px;
        right: 32px;
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        font-size: 24px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        cursor: pointer;
        transition: all 0.3s ease;
        z-index: 1000;
    }

    .floating-action-button:hover {
        transform: scale(1.1) rotate(45deg);
    }

    .search-container {
        position: relative;
        margin: 16px 0;
    }

    .search-input {
        width: 100%;
        padding: 12px 16px 12px 44px;
        border: 2px solid #e2e8f0;
        border-radius: 24px;
        font-size: 14px;
        transition: all 0.2s ease;
        background: white;
    }

    .search-input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }

    .search-icon {
        position: absolute;
        left: 16px;
        top: 50%;
        transform: translateY(-50%);
        color: #a0aec0;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    .feature-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }

    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600;
    }

    .loading-spinner {
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .task-card {
            background: rgba(45, 55, 72, 0.95);
            color: white;
        }

        .calendar-day {
            background: #2d3748;
            color: white;
            border-color: #4a5568;
        }
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header {
            font-size: 24px;
        }

        .task-card {
            margin: 8px 0;
            padding: 12px;
        }

        .pomodoro-timer {
            width: 200px;
            height: 200px;
            font-size: 48px;
            padding: 40px;
        }

        .floating-action-button {
            width: 56px;
            height: 56px;
            bottom: 24px;
            right: 24px;
        }
    }

    /* Accessibility improvements */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    }
</style>
""", unsafe_allow_html=True)


# Enhanced data models
class Priority:
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task:
    def __init__(self, title: str, description: str = "", due_date: Optional[date] = None,
                 priority: str = Priority.NONE, list_name: str = "Inbox", tags: List[str] = None,
                 estimated_hours: float = 0, category: str = "General"):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.due_date = due_date.isoformat() if due_date else None
        self.priority = priority
        self.list_name = list_name
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.updated_at = datetime.now().isoformat()
        self.tags = tags or []
        self.subtasks = []
        self.attachments = []
        self.estimated_hours = estimated_hours
        self.actual_hours = 0
        self.category = category
        self.recurring = None
        self.reminder = None
        self.notes = ""
        self.progress = 0


class Habit:
    def __init__(self, name: str, frequency: str = "daily", target: int = 1, category: str = "Health"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.frequency = frequency
        self.target = target
        self.category = category
        self.created_at = datetime.now().isoformat()
        self.completion_dates = []
        self.streak = 0
        self.best_streak = 0
        self.color = "#667eea"
        self.icon = "🎯"
        self.reminder_time = None
        self.notes = ""


# Enhanced utility functions
def init_session_state():
    """Initialize comprehensive session state"""
    defaults = {
        'tasks': [],
        'habits': [],
        'lists': ["Inbox", "Personal", "Work", "Shopping", "Health", "Learning"],
        'categories': ["General", "Work", "Personal", "Health", "Finance", "Learning"],
        'current_view': "dashboard",
        'current_filter': "all",
        'selected_tasks': [],
        'search_query': "",
        'theme': "light",
        'pomodoro_state': {
            'active': False,
            'start_time': None,
            'duration': 25,
            'type': 'work',
            'sessions_today': 0,
            'total_sessions': 0
        },
        'notifications': [],
        'user_preferences': {
            'default_list': "Inbox",
            'default_priority': Priority.NONE,
            'auto_save': True,
            'show_completed': True,
            'sidebar_collapsed': False
        },
        'statistics': {
            'tasks_completed_today': 0,
            'tasks_completed_week': 0,
            'habits_completed_today': 0,
            'focus_time_today': 0
        },
        'ai_suggestions': [],
        'quick_notes': [],
        'time_tracking': {},
        'productivity_score': 0
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def calculate_productivity_score():
    """Calculate user's productivity score"""
    tasks = st.session_state.tasks
    habits = st.session_state.habits

    # Task completion rate (40%)
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t['status'] == TaskStatus.COMPLETED])
    task_score = (completed_tasks / max(total_tasks, 1)) * 40

    # Habit completion rate (30%)
    today = date.today().isoformat()
    total_habits = len(habits)
    completed_habits = len([h for h in habits if today in h.get('completion_dates', [])])
    habit_score = (completed_habits / max(total_habits, 1)) * 30

    # On-time completion (20%)
    on_time_tasks = 0
    total_due_tasks = 0
    for task in tasks:
        if task.get('due_date') and task.get('completed_at'):
            total_due_tasks += 1
            try:
                due = datetime.fromisoformat(task['due_date']).date()
                completed = datetime.fromisoformat(task['completed_at']).date()
                if completed <= due:
                    on_time_tasks += 1
            except:
                continue

    ontime_score = (on_time_tasks / max(total_due_tasks, 1)) * 20

    # Focus time (10%)
    focus_minutes = st.session_state.pomodoro_state.get('sessions_today', 0) * 25
    focus_score = min(focus_minutes / 120, 1) * 10  # Max score at 2 hours

    total_score = task_score + habit_score + ontime_score + focus_score
    st.session_state.productivity_score = round(total_score)
    return round(total_score)


def add_task(title: str, description: str = "", due_date: Optional[date] = None,
             priority: str = Priority.NONE, list_name: str = "Inbox",
             tags: List[str] = None, estimated_hours: float = 0, category: str = "General"):
    """Add a new task with enhanced features"""
    task = Task(title, description, due_date, priority, list_name, tags, estimated_hours, category)
    st.session_state.tasks.append(task.__dict__)

    # Add to recent activity
    add_activity(f"Created task: {title}", "task_created")

    # Check for AI suggestions
    generate_ai_suggestions(task.__dict__)

    return task.id


def add_habit(name: str, frequency: str = "daily", target: int = 1, category: str = "Health"):
    """Add a new habit"""
    habit = Habit(name, frequency, target, category)
    st.session_state.habits.append(habit.__dict__)
    add_activity(f"Created habit: {name}", "habit_created")
    return habit.id


def add_activity(description: str, activity_type: str):
    """Add activity to history"""
    if 'activities' not in st.session_state:
        st.session_state.activities = []

    activity = {
        'id': str(uuid.uuid4()),
        'description': description,
        'type': activity_type,
        'timestamp': datetime.now().isoformat()
    }

    st.session_state.activities.append(activity)

    # Keep only last 100 activities
    if len(st.session_state.activities) > 100:
        st.session_state.activities = st.session_state.activities[-100:]


def generate_ai_suggestions(task: Dict):
    """Generate AI-powered suggestions for task optimization"""
    suggestions = []

    # Analyze task patterns
    similar_tasks = [t for t in st.session_state.tasks
                     if any(tag in task.get('tags', []) for tag in t.get('tags', []))]

    if len(similar_tasks) > 3:
        avg_completion_time = sum(t.get('actual_hours', 0) for t in similar_tasks) / len(similar_tasks)
        if avg_completion_time > 0:
            suggestions.append({
                'type': 'time_estimate',
                'message': f"Similar tasks took an average of {avg_completion_time:.1f} hours",
                'icon': '⏱️'
            })

    # Priority suggestions
    if task['priority'] == Priority.NONE and task.get('due_date'):
        due_date = datetime.fromisoformat(task['due_date']).date()
        days_until_due = (due_date - date.today()).days
        if days_until_due <= 3:
            suggestions.append({
                'type': 'priority',
                'message': 'Consider setting this as high priority (due soon)',
                'icon': '🚨'
            })

    # Add suggestions to session state
    if 'ai_suggestions' not in st.session_state:
        st.session_state.ai_suggestions = []

    st.session_state.ai_suggestions.extend(suggestions)


def smart_search(query: str) -> List[Dict]:
    """Enhanced search with smart filtering"""
    if not query:
        return st.session_state.tasks

    query = query.lower()
    results = []

    for task in st.session_state.tasks:
        score = 0

        # Title match (highest weight)
        if query in task['title'].lower():
            score += 10

        # Description match
        if query in task.get('description', '').lower():
            score += 5

        # Tags match
        if any(query in tag.lower() for tag in task.get('tags', [])):
            score += 7

        # List name match
        if query in task['list_name'].lower():
            score += 3

        # Priority match
        if query in task['priority']:
            score += 2

        # Natural language queries
        if query in ['urgent', 'important'] and task['priority'] in [Priority.HIGH, Priority.URGENT]:
            score += 8
        elif query in ['today', 'due today'] and task.get('due_date') == date.today().isoformat():
            score += 10
        elif query in ['overdue', 'late'] and task.get('due_date'):
            due_date = datetime.fromisoformat(task['due_date']).date()
            if due_date < date.today() and task['status'] == TaskStatus.PENDING:
                score += 10

        if score > 0:
            task['search_score'] = score
            results.append(task)

    # Sort by score
    results.sort(key=lambda x: x.get('search_score', 0), reverse=True)
    return results


def get_task_analytics():
    """Generate comprehensive task analytics"""
    tasks = st.session_state.tasks

    # Basic stats
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t['status'] == TaskStatus.COMPLETED])
    pending_tasks = len([t for t in tasks if t['status'] == TaskStatus.PENDING])
    in_progress_tasks = len([t for t in tasks if t['status'] == TaskStatus.IN_PROGRESS])

    # Time-based analytics
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    tasks_due_today = len([t for t in tasks if t.get('due_date') == today.isoformat()])
    tasks_due_week = len([t for t in tasks if t.get('due_date') and
                          week_start.isoformat() <= t['due_date'] <= (week_start + timedelta(days=6)).isoformat()])

    overdue_tasks = len([t for t in tasks if t.get('due_date') and
                         datetime.fromisoformat(t['due_date']).date() < today and
                         t['status'] == TaskStatus.PENDING])

    # Productivity metrics
    completion_rate = (completed_tasks / max(total_tasks, 1)) * 100

    # Time tracking
    total_estimated = sum(t.get('estimated_hours', 0) for t in tasks)
    total_actual = sum(t.get('actual_hours', 0) for t in tasks if t['status'] == TaskStatus.COMPLETED)

    # Priority distribution
    priority_dist = {}
    for task in tasks:
        priority = task['priority']
        priority_dist[priority] = priority_dist.get(priority, 0) + 1

    # Category distribution
    category_dist = {}
    for task in tasks:
        category = task.get('category', 'General')
        category_dist[category] = category_dist.get(category, 0) + 1

    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'tasks_due_today': tasks_due_today,
        'tasks_due_week': tasks_due_week,
        'overdue_tasks': overdue_tasks,
        'completion_rate': completion_rate,
        'total_estimated_hours': total_estimated,
        'total_actual_hours': total_actual,
        'priority_distribution': priority_dist,
        'category_distribution': category_dist
    }


def render_task_card(task: Dict, show_actions: bool = True):
    """Render an enhanced task card"""
    priority_colors = {
        Priority.URGENT: "#dc2626",
        Priority.HIGH: "#ea580c",
        Priority.MEDIUM: "#ca8a04",
        Priority.LOW: "#16a34a",
        Priority.NONE: "#64748b"
    }

    priority_color = priority_colors.get(task['priority'], priority_colors[Priority.NONE])
    card_class = "completed" if task['status'] == TaskStatus.COMPLETED else ""

    # Due date formatting
    due_info = ""
    if task.get('due_date'):
        due_date = datetime.fromisoformat(task['due_date']).date()
        today = date.today()

        if due_date == today:
            due_info = "📅 Due today"
        elif due_date < today:
            days_overdue = (today - due_date).days
            due_info = f"⚠️ Overdue by {days_overdue} day{'s' if days_overdue > 1 else ''}"
        else:
            days_until = (due_date - today).days
            due_info = f"📅 Due in {days_until} day{'s' if days_until > 1 else ''}"

    # Progress bar
    progress = task.get('progress', 0)
    progress_bar = f"""
    <div style="width: 100%; background: #e5e7eb; border-radius: 8px; height: 6px; margin: 8px 0;">
        <div style="width: {progress}%; background: {priority_color}; height: 100%; border-radius: 8px; transition: width 0.3s ease;"></div>
    </div>
    """ if progress > 0 else ""

    # Tags
    tags_html = ""
    if task.get('tags'):
        tags_html = " ".join([f'<span class="task-tag">{tag}</span>' for tag in task['tags']])

    # Estimated vs actual time
    time_info = ""
    if task.get('estimated_hours') > 0:
        actual = task.get('actual_hours', 0)
        estimated = task['estimated_hours']
        time_info = f"⏱️ {actual:.1f}h / {estimated:.1f}h"

    card_html = f"""
    <div class="task-card {card_class}" style="--priority-color: {priority_color};">
        <div class="task-title {'completed' if task['status'] == TaskStatus.COMPLETED else ''}">{task['title']}</div>
        {f'<div style="color: #64748b; margin-bottom: 8px;">{task["description"]}</div>' if task.get('description') else ''}
        {progress_bar}
        <div class="task-meta">
            <span><span class="priority-indicator priority-{task['priority']}"></span>{task['priority'].title()}</span>
            <span>📋 {task['list_name']}</span>
            {f'<span>{due_info}</span>' if due_info else ''}
            {f'<span>{time_info}</span>' if time_info else ''}
            <span>📂 {task.get('category', 'General')}</span>
        </div>
        {f'<div style="margin-top: 8px;">{tags_html}</div>' if tags_html else ''}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


# Complete task functions
def complete_task(task_id: str) -> bool:
    """Mark a task as completed"""
    for task in st.session_state.tasks:
        if task['id'] == task_id:
            task['status'] = TaskStatus.COMPLETED
            task['completed_at'] = datetime.now().isoformat()
            return True
    return False


def uncomplete_task(task_id: str) -> bool:
    """Mark a completed task as pending"""
    for task in st.session_state.tasks:
        if task['id'] == task_id:
            task['status'] = TaskStatus.PENDING
            task['completed_at'] = None
            return True
    return False


def delete_task(task_id: str) -> bool:
    """Delete a task"""
    original_count = len(st.session_state.tasks)
    st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task_id]
    return len(st.session_state.tasks) < original_count


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
        "high": "#e74c3c",
        "urgent": "#8e44ad"
    }
    return colors.get(priority, "#95a5a6")


# Initialize session state
init_session_state()

# Sidebar navigation
with st.sidebar:
    st.markdown("### 🎯 TickTick Pro")

    # User productivity score
    score = calculate_productivity_score()
    score_color = "#16a34a" if score >= 80 else "#ca8a04" if score >= 60 else "#dc2626"

    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <div style="color: {score_color}; font-size: 32px; font-weight: bold;">{score}%</div>
        <div style="color: #64748b; font-size: 14px;">Productivity Score</div>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats
    analytics = get_task_analytics()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📋 Tasks", analytics['total_tasks'], delta=f"+{analytics['completed_tasks']} done")
        st.metric("🔥 Habits", len(st.session_state.habits))
    with col2:
        st.metric("⏰ Due Today", analytics['tasks_due_today'])
        st.metric("⚠️ Overdue", analytics['overdue_tasks'])

    st.divider()

    # Advanced search
    st.markdown("### 🔍 Smart Search")
    search_query = st.text_input("", placeholder="Search tasks, habits, or try 'urgent', 'today', 'overdue'...",
                                 key="main_search")

    if search_query:
        st.session_state.search_query = search_query

    st.divider()

    # Navigation
    nav_items = [
        ("🏠 Dashboard", "dashboard"),
        ("📝 Tasks", "tasks"),
        ("📅 Calendar", "calendar"),
        ("🎯 Habits", "habits"),
        ("🍅 Focus", "pomodoro"),
        ("📊 Analytics", "analytics"),
        ("🧠 AI Insights", "ai_insights"),
        ("⚡ Quick Actions", "quick_actions"),
        ("⚙️ Settings", "settings")
    ]

    for label, view in nav_items:
        if st.button(label, key=f"nav_{view}", use_container_width=True,
                     type="primary" if st.session_state.current_view == view else "secondary"):
            st.session_state.current_view = view

    st.divider()

    # Smart lists
    st.markdown("### 🧠 Smart Lists")
    smart_lists = [
        ("📋 All Tasks", "all", analytics['total_tasks']),
        ("📅 Today", "today", analytics['tasks_due_today']),
        ("📆 This Week", "week", analytics['tasks_due_week']),
        ("⚠️ Overdue", "overdue", analytics['overdue_tasks']),
        ("⭐ High Priority", "high_priority", analytics['priority_distribution'].get(Priority.HIGH, 0)),
        ("🔄 In Progress", "in_progress", analytics['in_progress_tasks']),
        ("✅ Completed", "completed", analytics['completed_tasks'])
    ]

    for label, filter_type, count in smart_lists:
        if st.button(f"{label} ({count})", key=f"filter_{filter_type}", use_container_width=True):
            st.session_state.current_filter = filter_type
            st.session_state.current_view = "tasks"

    # Custom lists
    st.markdown("### 📁 My Lists")
    for list_name in st.session_state.lists:
        list_count = len([t for t in st.session_state.tasks if t['list_name'] == list_name])
        if st.button(f"📋 {list_name} ({list_count})", key=f"list_{list_name}", use_container_width=True):
            st.session_state.current_filter = list_name
            st.session_state.current_view = "tasks"

# Main content area
if st.session_state.current_view == "dashboard":
    st.markdown('<h1 class="main-header">🏠 Dashboard</h1>', unsafe_allow_html=True)

    # Quick stats overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="font-size: 24px; font-weight: bold;">{analytics['total_tasks']}</div>
            <div>Total Tasks</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        completion_rate = analytics['completion_rate']
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div style="font-size: 24px; font-weight: bold;">{completion_rate:.1f}%</div>
            <div>Completion Rate</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <div style="font-size: 24px; font-weight: bold;">{len(st.session_state.habits)}</div>
            <div>Active Habits</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        focus_time = st.session_state.pomodoro_state.get('sessions_today', 0) * 25
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
            <div style="font-size: 24px; font-weight: bold;">{focus_time}m</div>
            <div>Focus Time Today</div>
        </div>
        """, unsafe_allow_html=True)

    # Quick add task
    st.markdown("### ➕ Quick Add")
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            quick_task = st.text_input("", placeholder="What needs to be done?", key="quick_add_task")
        with col2:
            if st.button("Add Task", type="primary", use_container_width=True):
                if quick_task:
                    add_task(quick_task)
                    st.success("Task added!")
                    st.rerun()

    # Today's agenda
    st.markdown("### 📅 Today's Agenda")

    today_tasks = [t for t in st.session_state.tasks
                   if t.get('due_date') == date.today().isoformat() and t['status'] != TaskStatus.COMPLETED]

    if today_tasks:
        for task in today_tasks[:5]:  # Show top 5
            render_task_card(task, show_actions=False)
    else:
        st.info("No tasks due today. Great job staying on top of things! 🎉")

    # Habit progress
    st.markdown("### 🎯 Today's Habits")

    today = date.today().isoformat()
    habit_progress = 0
    total_habits = len(st.session_state.habits)

    if total_habits > 0:
        for habit in st.session_state.habits:
            completed = today in habit.get('completion_dates', [])
            if completed:
                habit_progress += 1

            status_icon = "✅" if completed else "⭕"
            streak = habit.get('streak', 0)

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{status_icon} {habit['name']}")
            with col2:
                st.write(f"🔥 {streak} days")
            with col3:
                if not completed:
                    if st.button("✓", key=f"complete_habit_{habit['id']}", help="Mark complete"):
                        complete_habit(habit['id'])
                        st.rerun()

        # Habit completion rate
        habit_rate = (habit_progress / total_habits) * 100
        st.progress(habit_rate / 100)
        st.write(f"Daily Progress: {habit_progress}/{total_habits} habits ({habit_rate:.1f}%)")
    else:
        st.info("No habits set up yet. Create some habits to track your daily routines!")

    # Recent activity
    st.markdown("### 📈 Recent Activity")

    if 'activities' in st.session_state and st.session_state.activities:
        recent_activities = sorted(st.session_state.activities,
                                   key=lambda x: x['timestamp'], reverse=True)[:5]

        for activity in recent_activities:
            timestamp = datetime.fromisoformat(activity['timestamp'])
            time_ago = datetime.now() - timestamp

            if time_ago.days > 0:
                time_str = f"{time_ago.days}d ago"
            elif time_ago.seconds > 3600:
                hours = time_ago.seconds // 3600
                time_str = f"{hours}h ago"
            else:
                minutes = time_ago.seconds // 60
                time_str = f"{minutes}m ago"

            st.write(f"• {activity['description']} - {time_str}")
    else:
        st.info("No recent activity to show.")

elif st.session_state.current_view == "quick_actions":
    st.markdown('<h1 class="main-header">⚡ Quick Actions</h1>', unsafe_allow_html=True)

    # Quick action cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📝 Tasks")
        if st.button("➕ Quick Add Task", use_container_width=True):
            st.session_state.current_view = "tasks"
            st.rerun()

        if st.button("🔍 Search Tasks", use_container_width=True):
            st.session_state.current_view = "tasks"
            st.rerun()

        if st.button("✅ Complete All Due", use_container_width=True):
            due_today = [t for t in st.session_state.tasks
                         if t.get('due_date') == date.today().isoformat()
                         and t['status'] == TaskStatus.PENDING]
            for task in due_today:
                complete_task(task['id'])
            st.success(f"Completed {len(due_today)} tasks!")
            st.rerun()

    with col2:
        st.markdown("### 🎯 Habits")
        if st.button("🎯 Add Habit", use_container_width=True):
            st.session_state.current_view = "habits"
            st.rerun()

        if st.button("✅ Mark All Habits", use_container_width=True):
            today = date.today().isoformat()
            completed_count = 0
            for habit in st.session_state.habits:
                if today not in habit.get('completion_dates', []):
                    complete_habit(habit['id'])
                    completed_count += 1
            st.success(f"Completed {completed_count} habits!")
            st.rerun()

    with col3:
        st.markdown("### 🍅 Focus")
        if st.button("🍅 Start Pomodoro", use_container_width=True):
            st.session_state.pomodoro_state = {
                'active': True,
                'start_time': time.time(),
                'duration': 25,
                'type': 'work',
                'sessions_today': st.session_state.pomodoro_state.get('sessions_today', 0)
            }
            st.session_state.current_view = "pomodoro"
            st.rerun()

        if st.button("📊 View Stats", use_container_width=True):
            st.session_state.current_view = "analytics"
            st.rerun()

    # Bulk operations
    st.markdown("### ⚡ Bulk Operations")

    pending_tasks = [t for t in st.session_state.tasks if t['status'] == TaskStatus.PENDING]

    if pending_tasks:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🗑️ Clear Completed", use_container_width=True):
                completed_tasks = [t for t in st.session_state.tasks if t['status'] == TaskStatus.COMPLETED]
                st.session_state.tasks = [t for t in st.session_state.tasks if t['status'] != TaskStatus.COMPLETED]
                st.success(f"Removed {len(completed_tasks)} completed tasks!")
                st.rerun()

        with col2:
            if st.button("📅 Reschedule Overdue", use_container_width=True):
                today = date.today()
                overdue_count = 0
                for task in st.session_state.tasks:
                    if (task.get('due_date') and
                            datetime.fromisoformat(task['due_date']).date() < today and
                            task['status'] == TaskStatus.PENDING):
                        task['due_date'] = today.isoformat()
                        overdue_count += 1
                st.success(f"Rescheduled {overdue_count} overdue tasks to today!")
                st.rerun()

        with col3:
            if st.button("⭐ Set All High Priority", use_container_width=True):
                for task in pending_tasks[:10]:  # Limit to first 10
                    task['priority'] = Priority.HIGH
                st.success("Set high priority for pending tasks!")
                st.rerun()

        with col4:
            if st.button("📋 Move to Inbox", use_container_width=True):
                moved_count = 0
                for task in pending_tasks:
                    if task['list_name'] != "Inbox":
                        task['list_name'] = "Inbox"
                        moved_count += 1
                st.success(f"Moved {moved_count} tasks to Inbox!")
                st.rerun()

# Continue with other views...
elif st.session_state.current_view == "tasks":
    st.markdown('<h1 class="main-header">📝 Tasks</h1>', unsafe_allow_html=True)
    st.info("Task management view - implement full task functionality here")

elif st.session_state.current_view == "calendar":
    st.markdown('<h1 class="main-header">📅 Calendar</h1>', unsafe_allow_html=True)
    st.info("Calendar view - implement calendar functionality here")

elif st.session_state.current_view == "habits":
    st.markdown('<h1 class="main-header">🎯 Habits</h1>', unsafe_allow_html=True)
    st.info("Habits tracking view - implement habit functionality here")

elif st.session_state.current_view == "pomodoro":
    st.markdown('<h1 class="main-header">🍅 Pomodoro Timer</h1>', unsafe_allow_html=True)
    st.info("Pomodoro timer view - implement timer functionality here")

elif st.session_state.current_view == "analytics":
    st.markdown('<h1 class="main-header">📊 Analytics</h1>', unsafe_allow_html=True)
    st.info("Analytics and statistics view - implement analytics here")

elif st.session_state.current_view == "ai_insights":
    st.markdown('<h1 class="main-header">🧠 AI Insights</h1>', unsafe_allow_html=True)
    st.info("AI-powered insights view - implement AI features here")

elif st.session_state.current_view == "settings":
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    st.info("Application settings view - implement settings here")

# Auto-refresh for timer
if (st.session_state.current_view == "pomodoro" and
        st.session_state.pomodoro_state.get('active', False)):
    time.sleep(1)
    st.rerun()