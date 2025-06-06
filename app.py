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
                        habit['completion_dates'].append(today)
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

elif st.session_state.current_view == "tasks":
    st.markdown('<h1 class="main-header">📝 Tasks</h1>', unsafe_allow_html=True)

    # Advanced task creation
    with st.expander("➕ Create New Task", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            task_title = st.text_input("Task Title", placeholder="What needs to be done?")
            task_description = st.text_area("Description", placeholder="Add details...")
            task_due_date = st.date_input("Due Date", value=None)

        with col2:
            task_priority = st.selectbox("Priority",
                                         [Priority.NONE, Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.URGENT])
            task_list = st.selectbox("List", st.session_state.lists)
            task_category = st.selectbox("Category", st.session_state.categories)
            task_estimated_hours = st.number_input("Estimated Hours", min_value=0.0, step=0.5)

        task_tags = st.text_input("Tags (comma-separated)", placeholder="work, urgent, meeting")

        if st.button("Create Task", type="primary", use_container_width=True):
            if task_title:
                tags = [tag.strip() for tag in task_tags.split(",")] if task_tags else []
                task_id = add_task(task_title, task_description, task_due_date,
                                   task_priority, task_list, tags, task_estimated_hours, task_category)
                st.success(f"Task '{task_title}' created successfully!")
                st.rerun()
            else:
                st.error("Please enter a task title")

    # Filters and sorting
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "In Progress", "Completed"])
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "Urgent", "High", "Medium", "Low", "None"])
    with col3:
        list_filter = st.selectbox("List", ["All"] + st.session_state.lists)
    with col4:
        sort_by = st.selectbox("Sort by", ["Created Date", "Due Date", "Priority", "Title", "Progress"])

    # Apply filters
    filtered_tasks = st.session_state.tasks.copy()

    # Search filter
    if st.session_state.search_query:
        filtered_tasks = smart_search(st.session_state.search_query)

    # Status filter
    if status_filter != "All":
        status_map = {
            "Pending": TaskStatus.PENDING,
            "In Progress": TaskStatus.IN_PROGRESS,
            "Completed": TaskStatus.COMPLETED
        }
        filtered_tasks = [t for t in filtered_tasks if t['status'] == status_map[status_filter]]

    # Priority filter
    if priority_filter != "All":
        priority_value = priority_filter.lower()
        filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority_value]

    # List filter
    if list_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t['list_name'] == list_filter]

    # Sorting
    sort_key_map = {
        "Created Date": lambda x: x['created_at'],
        "Due Date": lambda x: x.get('due_date') or '9999-12-31',
        "Priority": lambda x: {Priority.URGENT: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3,
                               Priority.NONE: 4}.get(x['priority'], 5),
        "Title": lambda x: x['title'].lower(),
        "Progress": lambda x: x.get('progress', 0)
    }

    if sort_by in sort_key_map:
        filtered_tasks.sort(key=sort_key_map[sort_by], reverse=(sort_by in ["Created Date", "Priority", "Progress"]))

    # Task display
    st.markdown(f"### Found {len(filtered_tasks)} tasks")

    if not filtered_tasks:
        st.info("No tasks found. Try adjusting your filters or create a new task!")
    else:
        # Bulk actions
        if len(filtered_tasks) > 1:
            with st.expander("⚡ Bulk Actions"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("✅ Mark All Complete"):
                        for task in filtered_tasks:
                            if task['status'] == TaskStatus.PENDING:
                                task['status'] = TaskStatus.COMPLETED
                                task['completed_at'] = datetime.now().isoformat()
                        st.success(f"Marked {len(filtered_tasks)} tasks as complete!")
                        st.rerun()

                with col2:
                    bulk_priority = st.selectbox("Set Priority",
                                                 [Priority.URGENT, Priority.HIGH, Priority.MEDIUM, Priority.LOW,
                                                  Priority.NONE], key="bulk_priority")
                    if st.button("🎯 Update Priority"):
                        for task in filtered_tasks:
                            task['priority'] = bulk_priority
                        st.success(f"Updated priority for {len(filtered_tasks)} tasks!")
                        st.rerun()

                with col3:
                    bulk_list = st.selectbox("Move to List", st.session_state.lists, key="bulk_list")
                    if st.button("📋 Move Tasks"):
                        for task in filtered_tasks:
                            task['list_name'] = bulk_list
                        st.success(f"Moved {len(filtered_tasks)} tasks to {bulk_list}!")
                        st.rerun()

        # Task cards
        for i, task in enumerate(filtered_tasks):
            col1, col2, col3, col4 = st.columns([0.5, 6, 1, 1])

            with col1:
                # Checkbox for completion
                completed = task['status'] == TaskStatus.COMPLETED
                if st.checkbox("", value=completed, key=f"task_check_{task['id']}"):
                    if not completed:
                        task['status'] = TaskStatus.COMPLETED
                        task['completed_at'] = datetime.now().isoformat()
                        add_activity(f"Completed task: {task['title']}", "task_completed")
                        st.rerun()
                elif completed:
                    task['status'] = TaskStatus.PENDING
                    task['completed_at'] = None
                    st.rerun()

            with col2:
                render_task_card(task, show_actions=False)

            with col3:
                # Progress slider
                if task['status'] != TaskStatus.COMPLETED:
                    progress = st.slider("", 0, 100, task.get('progress', 0),
                                         key=f"progress_{task['id']}",
                                         help="Task progress")
                    if progress != task.get('progress', 0):
                        task['progress'] = progress
                        task['updated_at'] = datetime.now().isoformat()
                        if progress == 100:
                            task['status'] = TaskStatus.COMPLETED
                            task['completed_at'] = datetime.now().isoformat()
                        st.rerun()

            with col4:
                # Action buttons
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✏️", key=f"edit_{task['id']}", help="Edit task"):
                        st.session_state[f"edit_task_{task['id']}"] = True
                with col_b:
                    if st.button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
                        st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task['id']]
                        add_activity(f"Deleted task: {task['title']}", "task_deleted")
                        st.rerun()

elif st.session_state.current_view == "calendar":
    st.markdown('<h1 class="main-header">📅 Calendar</h1>', unsafe_allow_html=True)

    # Calendar view options
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Month View", "📋 Week Planning", "📊 Timeline", "📈 Schedule Analytics"])

    with tab1:
        # Month view implementation
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            selected_date = st.date_input("Navigate to", value=date.today())

        with col2:
            st.markdown(f"### {selected_date.strftime('%B %Y')}")

        with col3:
            view_density = st.selectbox("Density", ["Compact", "Comfortable", "Spacious"])

        # Generate calendar
        import calendar

        cal = calendar.monthcalendar(selected_date.year, selected_date.month)

        # Days header
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cols = st.columns(7)
        for i, day in enumerate(days):
            cols[i].markdown(f"**{day}**")

        # Calendar grid
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    day_date = date(selected_date.year, selected_date.month, day)
                    is_today = day_date == date.today()

                    # Get tasks for this day
                    day_tasks = [t for t in st.session_state.tasks
                                 if t.get('due_date') == day_date.isoformat()]

                    with cols[i]:
                        # Day header
                        day_class = "calendar-today" if is_today else "calendar-day"
                        day_html = f"""
                        <div class="{day_class}">
                            <div style="font-weight: bold; margin-bottom: 8px;">
                                {'🔸' if is_today else ''} {day}
                            </div>
                        """

                        # Show tasks
                        for task in day_tasks[:3]:  # Show max 3 tasks
                            priority_colors = {
                                Priority.URGENT: "#dc2626",
                                Priority.HIGH: "#ea580c",
                                Priority.MEDIUM: "#ca8a04",
                                Priority.LOW: "#16a34a",
                                Priority.NONE: "#64748b"
                            }

                            color = priority_colors.get(task['priority'], "#64748b")
                            status = "✅" if task['status'] == TaskStatus.COMPLETED else "⭕"

                            day_html += f"""
                            <div style="font-size: 11px; margin: 2px 0; padding: 2px 4px; 
                                       background: {color}; color: white; border-radius: 4px;">
                                {status} {task['title'][:15]}{'...' if len(task['title']) > 15 else ''}
                            </div>
                            """

                        if len(day_tasks) > 3:
                            day_html += f"<div style='font-size: 10px; color: #64748b;'>+{len(day_tasks) - 3} more</div>"

                        day_html += "</div>"
                        st.markdown(day_html, unsafe_allow_html=True)

    with tab2:
        # Weekly planning view
        st.markdown("### 📋 Weekly Planning")

        # Week selector
        week_offset = st.slider("Week", -4, 4, 0, help="Navigate weeks")
        today = date.today()
        week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        week_days = [week_start + timedelta(days=i) for i in range(7)]

        st.markdown(f"**Week of {week_start.strftime('%B %d, %Y')}**")

        # Weekly goals
        week_key = week_start.isoformat()
        if f"week_goals_{week_key}" not in st.session_state:
            st.session_state[f"week_goals_{week_key}"] = []

        with st.expander("🎯 Weekly Goals"):
            weekly_goal = st.text_input("Add weekly goal", key=f"weekly_goal_input_{week_key}")
            if st.button("Add Goal", key=f"add_goal_{week_key}"):
                if weekly_goal:
                    st.session_state[f"week_goals_{week_key}"].append(weekly_goal)
                    st.rerun()

            # Display goals
            for i, goal in enumerate(st.session_state[f"week_goals_{week_key}"]):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"• {goal}")
                with col2:
                    if st.button("❌", key=f"remove_goal_{week_key}_{i}"):
                        st.session_state[f"week_goals_{week_key}"].pop(i)
                        st.rerun()

        # Weekly task distribution
        cols = st.columns(7)
        for i, day in enumerate(week_days):
            with cols[i]:
                is_today = day == date.today()
                day_name = day.strftime('%A')

                st.markdown(f"**{'🔸 ' if is_today else ''}{day_name}**")
                st.markdown(f"*{day.strftime('%m/%d')}*")

                # Tasks for this day
                day_tasks = [t for t in st.session_state.tasks
                             if t.get('due_date') == day.isoformat()]

                # Add task for this day
                with st.expander(f"➕"):
                    new_task = st.text_input("Task", key=f"day_task_{day.isoformat()}")
                    if st.button("Add", key=f"add_day_task_{day.isoformat()}"):
                        if new_task:
                            add_task(new_task, due_date=day)
                            st.rerun()

                # Show tasks
                for task in day_tasks:
                    priority_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "none": "⚪"}
                    status_emoji = "✅" if task['status'] == TaskStatus.COMPLETED else "⭕"

                    st.markdown(f"{status_emoji}{priority_emoji.get(task['priority'], '⚪')} {task['title'][:20]}...")

elif st.session_state.current_view == "habits":
    st.markdown('<h1 class="main-header">🎯 Habits</h1>', unsafe_allow_html=True)

    # Habit overview
    total_habits = len(st.session_state.habits)
    today = date.today().isoformat()
    completed_today = len([h for h in st.session_state.habits if today in h.get('completion_dates', [])])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Habits", total_habits)
    with col2:
        st.metric("Completed Today", completed_today)
    with col3:
        completion_rate = (completed_today / max(total_habits, 1)) * 100
        st.metric("Today's Rate", f"{completion_rate:.1f}%")
    with col4:
        avg_streak = sum(h.get('streak', 0) for h in st.session_state.habits) / max(total_habits, 1)
        st.metric("Avg Streak", f"{avg_streak:.1f} days")

    # Add new habit
    with st.expander("➕ Create New Habit", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            habit_name = st.text_input("Habit Name", placeholder="e.g., Morning meditation")
            habit_frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly"])
            habit_target = st.number_input("Daily Target", min_value=1, value=1)

        with col2:
            habit_category = st.selectbox("Category",
                                          ["Health", "Productivity", "Learning", "Fitness", "Mindfulness", "Social"])
            habit_reminder = st.time_input("Reminder Time", value=None)
            habit_icon = st.text_input("Icon", value="🎯", help="Choose an emoji")

        habit_notes = st.text_area("Notes", placeholder="Why is this habit important to you?")

        if st.button("Create Habit", type="primary", use_container_width=True):
            if habit_name:
                habit_id = add_habit(habit_name, habit_frequency, habit_target, habit_category)
                # Update with additional details
                for habit in st.session_state.habits:
                    if habit['id'] == habit_id:
                        habit['reminder_time'] = habit_reminder.strftime('%H:%M') if habit_reminder else None
                        habit['icon'] = habit_icon
                        habit['notes'] = habit_notes
                        break
                st.success(f"Habit '{habit_name}' created!")
                st.rerun()

    # Habit tracking
    if st.session_state.habits:
        st.markdown("### 📊 Habit Tracking")

        for habit in st.session_state.habits:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    icon = habit.get('icon', '🎯')
                    st.markdown(f"### {icon} {habit['name']}")
                    st.markdown(f"**Category:** {habit.get('category', 'General')}")
                    if habit.get('notes'):
                        st.markdown(f"*{habit['notes']}*")

                with col2:
                    # Today's completion
                    completed_today = today in habit.get('completion_dates', [])

                    if completed_today:
                        st.success("✅ Completed Today!")
                        if st.button("Undo", key=f"undo_{habit['id']}"):
                            habit['completion_dates'].remove(today)
                            # Recalculate streak
                            update_habit_streak(habit)
                            st.rerun()
                    else:
                        if st.button("✓ Mark Complete", key=f"complete_{habit['id']}", type="primary"):
                            habit['completion_dates'].append(today)
                            habit['completion_dates'].sort()
                            update_habit_streak(habit)
                            add_activity(f"Completed habit: {habit['name']}", "habit_completed")
                            st.rerun()

                with col3:
                    # Streak info
                    current_streak = habit.get('streak', 0)
                    best_streak = habit.get('best_streak', 0)

                    st.metric("Current Streak", f"{current_streak} days")
                    st.metric("Best Streak", f"{best_streak} days")

                with col4:
                    # Actions
                    if st.button("📊", key=f"analytics_{habit['id']}", help="View analytics"):
                        st.session_state[f"show_habit_analytics_{habit['id']}"] = True

                    if st.button("🗑️", key=f"delete_habit_{habit['id']}", help="Delete habit"):
                        st.session_state.habits = [h for h in st.session_state.habits if h['id'] != habit['id']]
                        st.rerun()

                # 30-day visualization
                st.markdown("**Last 30 days:**")

                habit_viz_html = '<div style="display: flex; gap: 2px; margin: 8px 0;">'
                for i in range(29, -1, -1):
                    check_date = (date.today() - timedelta(days=i)).isoformat()

                    if check_date in habit.get('completion_dates', []):
                        color = "#16a34a"  # Green for completed
                        title = f"Completed on {check_date}"
                    elif datetime.fromisoformat(check_date).date() < date.today():
                        color = "#dc2626"  # Red for missed
                        title = f"Missed on {check_date}"
                    else:
                        color = "#e5e7eb"  # Gray for future
                        title = f"Upcoming: {check_date}"

                    habit_viz_html += f'''
                    <div style="width: 12px; height: 12px; background: {color}; 
                                border-radius: 2px; title="{title}"></div>
                    '''

                habit_viz_html += '</div>'
                st.markdown(habit_viz_html, unsafe_allow_html=True)

                st.divider()

                # Show detailed analytics if requested
                if st.session_state.get(f"show_habit_analytics_{habit['id']}", False):
                    with st.expander(f"📊 Analytics for {habit['name']}", expanded=True):
                        # Completion rate over time
                        completion_dates = habit.get('completion_dates', [])
                        if completion_dates:
                            # Weekly completion rate
                            weeks_data = {}
                            for date_str in completion_dates:
                                week_start = datetime.fromisoformat(date_str).date() - timedelta(
                                    days=datetime.fromisoformat(date_str).weekday())
                                week_key = week_start.isoformat()
                                weeks_data[week_key] = weeks_data.get(week_key, 0) + 1

                            if weeks_data:
                                fig = px.bar(
                                    x=list(weeks_data.keys()),
                                    y=list(weeks_data.values()),
                                    title=f"Weekly Completion for {habit['name']}",
                                    labels={'x': 'Week', 'y': 'Completions'}
                                )
                                st.plotly_chart(fig, use_container_width=True)

                        if st.button("Close Analytics", key=f"close_analytics_{habit['id']}"):
                            st.session_state[f"show_habit_analytics_{habit['id']}"] = False
                            st.rerun()
    else:
        st.info("No habits created yet. Start building better habits today!")


def update_habit_streak(habit):
    """Update habit streak calculation"""
    completion_dates = habit.get('completion_dates', [])
    if not completion_dates:
        habit['streak'] = 0
        return

    # Sort dates
    dates = sorted([datetime.fromisoformat(d).date() for d in completion_dates])

    # Calculate current streak
    today = date.today()
    streak = 0

    # Check if completed today or yesterday (for daily habits)
    check_date = today
    while check_date in dates:
        streak += 1
        check_date -= timedelta(days=1)

    # If not completed today, check if yesterday was the last completion
    if today not in dates and (today - timedelta(days=1)) in dates:
        streak = 1
        check_date = today - timedelta(days=2)
        while check_date in dates:
            streak += 1
            check_date -= timedelta(days=1)

    habit['streak'] = streak
    habit['best_streak'] = max(habit.get('best_streak', 0), streak)

elif st.session_state.current_view == "pomodoro":
st.markdown('<h1 class="main-header">🍅 Pomodoro Focus</h1>', unsafe_allow_html=True)

# Pomodoro settings
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### ⚙️ Timer Settings")

    work_duration = st.slider("Work Session (minutes)", 15, 60,
                              st.session_state.pomodoro_state.get('work_duration', 25))
    short_break = st.slider("Short Break (minutes)", 5, 20, 5)
    long_break = st.slider("Long Break (minutes)", 15, 45, 30)
    auto_start_breaks = st.checkbox("Auto-start breaks", value=True)

    # Session statistics
    st.markdown("### 📊 Today's Sessions")
    sessions_today = st.session_state.pomodoro_state.get('sessions_today', 0)
    total_focus_time = sessions_today * work_duration

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Sessions", sessions_today)
    with col_b:
        st.metric("Focus Time", f"{total_focus_time}m")

    # Productivity tips
    st.markdown("### 💡 Productivity Tips")
    tips = [
        "🎯 Choose one specific task before starting",
        "📱 Put your phone in another room",
        "💧 Keep water nearby to stay hydrated",
        "🎵 Try instrumental music or nature sounds",
        "🧘 Use breaks for light stretching or breathing"
    ]

    for tip in tips:
        st.write(tip)

with col2:
    # Timer display
    if st.session_state.pomodoro_state['active']:
        elapsed = time.time() - st.session_state.pomodoro_state['start_time']
        duration_seconds = st.session_state.pomodoro_state['duration'] * 60
        remaining = max(0, duration_seconds - elapsed)

        minutes = int(remaining // 60)
        seconds = int(remaining % 60)

        # Progress
        progress = 1 - (remaining / duration_seconds)

        # Timer display
        timer_color = "#ff6b6b" if st.session_state.pomodoro_state['type'] == 'work' else "#4ecdc4"

        st.markdown(f"""
            <div class="pomodoro-timer" style="background: linear-gradient(135deg, {timer_color} 0%, {timer_color}dd 100%);">
                {minutes:02d}:{seconds:02d}
            </div>
            """, unsafe_allow_html=True)

        # Progress bar
        st.progress(progress)

        session_type = st.session_state.pomodoro_state['type']
        st.markdown(f"**Current: {session_type.title()} Session**")

        # Timer completion
        if remaining <= 0:
            if session_type == 'work':
                st.session_state.pomodoro_state['sessions_today'] += 1
                st.balloons()
                st.success("🎉 Work session complete! Time for a break.")

                # Auto-start break if enabled
                if auto_start_breaks:
                    break_duration = long_break if st.session_state.pomodoro_state[
                                                       'sessions_today'] % 4 == 0 else short_break
                    st.session_state.pomodoro_state.update({
                        'start_time': time.time(),
                        'duration': break_duration,
                        'type': 'break'
                    })
                else:
                    st.session_state.pomodoro_state['active'] = False
            else:
                st.success("☕ Break complete! Ready for another work session?")
                if auto_start_breaks:
                    st.session_state.pomodoro_state.update({
                        'start_time': time.time(),
                        'duration': work_duration,
                        'type': 'work'
                    })
                else:
                    st.session_state.pomodoro_state['active'] = False

            if not auto_start_breaks:
                st.rerun()

        # Timer controls
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("⏸️ Pause", type="secondary", use_container_width=True):
                st.session_state.pomodoro_state['active'] = False
                st.rerun()
        with col_b:
            if st.button("⏹️ Stop", type="secondary", use_container_width=True):
                st.session_state.pomodoro_state['active'] = False
                st.session_state.pomodoro_state['start_time'] = None
                st.rerun()

    else:
        # Timer ready state
        st.markdown(f"""
            <div class="pomodoro-timer" style="background: linear-gradient(135deg, #64748b 0%, #64748bdd 100%);">
                Ready
            </div>
            """, unsafe_allow_html=True)

        # Start buttons
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if st.button("▶️ Work", type="primary", use_container_width=True):
                st.session_state.pomodoro_state.update({
                    'active': True,
                    'start_time': time.time(),
                    'duration': work_duration,
                    'type': 'work'
                })
                st.rerun()

        with col_b:
            if st.button("☕ Short Break", type="secondary", use_container_width=True):
                st.session_state.pomodoro_state.update({
                    'active': True,
                    'start_time': time.time(),
                    'duration': short_break,
                    'type': 'break'
                })
                st.rerun()

        with col_c:
            if st.button("🛌 Long Break", type="secondary", use_container_width=True):
                st.session_state.pomodoro_state.update({
                    'active': True,
                    'start_time': time.time(),
                    'duration': long_break,
                    'type': 'break'
                })
                st.rerun()

    # Current task focus
    st.markdown("### 🎯 Current Task")

    pending_tasks = [t for t in st.session_state.tasks if t['status'] == TaskStatus.PENDING]

    if pending_tasks:
        focus_task = st.selectbox(
            "Select task to focus on:",
            ["No task selected"] + [f"{t['title']} ({t['priority'].title()})" for t in pending_tasks]
        )

        if focus_task != "No task selected":
            # Find selected task
            task_title = focus_task.split(" (")[0]
            selected_task = next((t for t in pending_tasks if t['title'] == task_title), None)

            if selected_task:
                st.markdown(f"**{selected_task['title']}**")
                if selected_task.get('description'):
                    st.markdown(selected_task['description'])

                # Task actions during focus
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Complete Task", use_container_width=True):
                        selected_task['status'] = TaskStatus.COMPLETED
                        selected_task['completed_at'] = datetime.now().isoformat()
                        add_activity(f"Completed task during focus: {selected_task['title']}", "task_completed")
                        st.success("Task completed! 🎉")
                        st.rerun()

                with col_b:
                    # Track time spent
                    if st.button("⏱️ Log Time", use_container_width=True):
                        time_spent = st.number_input("Hours spent", min_value=0.1, step=0.1, value=0.5)
                        if time_spent:
                            selected_task['actual_hours'] = selected_task.get('actual_hours', 0) + time_spent
                            st.success(f"Logged {time_spent} hours!")
                            st.rerun()
    else:
        st.info("No pending tasks. Create some tasks to focus on!")

elif st.session_state.current_view == "analytics":
st.markdown('<h1 class="main-header">📊 Analytics & Insights</h1>', unsafe_allow_html=True)

# Time period selector
time_period = st.selectbox("Time Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"])

# Calculate date range
end_date = date.today()
if time_period == "Last 7 days":
    start_date = end_date - timedelta(days=7)
elif time_period == "Last 30 days":
    start_date = end_date - timedelta(days=30)
elif time_period == "Last 90 days":
    start_date = end_date - timedelta(days=90)
else:
    start_date = date(2020, 1, 1)  # All time

# Overview metrics
analytics = get_task_analytics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Productivity Score", f"{st.session_state.productivity_score}%")
with col2:
    st.metric("Task Completion Rate", f"{analytics['completion_rate']:.1f}%")
with col3:
    efficiency = (analytics['total_actual_hours'] / max(analytics['total_estimated_hours'], 1)) * 100
    st.metric("Time Efficiency", f"{efficiency:.1f}%")
with col4:
    focus_time_total = st.session_state.pomodoro_state.get('total_sessions', 0) * 25
    st.metric("Total Focus Time", f"{focus_time_total}h")

# Charts
col1, col2 = st.columns(2)

with col1:
    # Task completion trend
    st.markdown("#### 📈 Task Completion Trend")

    # Generate daily completion data
    daily_data = {}
    for i in range((end_date - start_date).days + 1):
        check_date = start_date + timedelta(days=i)
        daily_data[check_date.isoformat()] = 0

    for task in st.session_state.tasks:
        if task.get('completed_at'):
            completed_date = datetime.fromisoformat(task['completed_at']).date()
            if start_date <= completed_date <= end_date:
                daily_data[completed_date.isoformat()] += 1

    if daily_data:
        df = pd.DataFrame(list(daily_data.items()), columns=['Date', 'Completed'])
        df['Date'] = pd.to_datetime(df['Date'])

        fig = px.line(df, x='Date', y='Completed', title='Daily Task Completions')
        fig.update_traces(line_color='#667eea')
        st.plotly_chart(fig, use_container_width=True)

with col2:
    # Priority distribution
    st.markdown("#### 🎯 Priority Distribution")

    priority_data = analytics['priority_distribution']
    if priority_data:
        fig = px.pie(
            values=list(priority_data.values()),
            names=[p.title() for p in priority_data.keys()],
            title="Tasks by Priority",
            color_discrete_map={
                'Urgent': '#dc2626',
                'High': '#ea580c',
                'Medium': '#ca8a04',
                'Low': '#16a34a',
                'None': '#64748b'
            }
        )
        st.plotly_chart(fig, use_container_width=True)

# Detailed analytics
col1, col2 = st.columns(2)

with col1:
    # Category performance
    st.markdown("#### 📂 Category Performance")

    category_stats = {}
    for task in st.session_state.tasks:
        category = task.get('category', 'General')
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'completed': 0}

        category_stats[category]['total'] += 1
        if task['status'] == TaskStatus.COMPLETED:
            category_stats[category]['completed'] += 1

    category_df = pd.DataFrame([
        {
            'Category': cat,
            'Completion Rate': (stats['completed'] / max(stats['total'], 1)) * 100,
            'Total Tasks': stats['total']
        }
        for cat, stats in category_stats.items()
    ])

    if not category_df.empty:
        fig = px.bar(category_df, x='Category', y='Completion Rate',
                     title='Completion Rate by Category',
                     color='Completion Rate',
                     color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

with col2:
    # Time tracking analysis
    st.markdown("#### ⏱️ Time Tracking")

    estimated_vs_actual = []
    for task in st.session_state.tasks:
        if task.get('estimated_hours', 0) > 0 and task.get('actual_hours', 0) > 0:
            estimated_vs_actual.append({
                'Task': task['title'][:20] + '...' if len(task['title']) > 20 else task['title'],
                'Estimated': task['estimated_hours'],
                'Actual': task['actual_hours']
            })

    if estimated_vs_actual:
        df = pd.DataFrame(estimated_vs_actual)

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Estimated', x=df['Task'], y=df['Estimated'], marker_color='#93c5fd'))
        fig.add_trace(go.Bar(name='Actual', x=df['Task'], y=df['Actual'], marker_color='#3b82f6'))

        fig.update_layout(
            title='Estimated vs Actual Time',
            xaxis_title='Tasks',
            yaxis_title='Hours',
            barmode='group'
        )

        st.plotly_chart(fig, use_container_width=True)

# Habit analytics
st.markdown("#### 🎯 Habit Analytics")

if st.session_state.habits:
    habit_performance = []

    for habit in st.session_state.habits:
        # Calculate completion rate for the selected period
        completion_dates = [datetime.fromisoformat(d).date() for d in habit.get('completion_dates', [])]
        period_completions = [d for d in completion_dates if start_date <= d <= end_date]

        total_days = (end_date - start_date).days + 1
        completion_rate = (len(period_completions) / total_days) * 100

        habit_performance.append({
            'Habit': habit['name'],
            'Completion Rate': completion_rate,
            'Current Streak': habit.get('streak', 0),
            'Best Streak': habit.get('best_streak', 0)
        })

    habit_df = pd.DataFrame(habit_performance)

    # Habit completion rates
    fig = px.bar(habit_df, x='Habit', y='Completion Rate',
                 title=f'Habit Completion Rates ({time_period})',
                 color='Completion Rate',
                 color_continuous_scale='RdYlGn')
    st.plotly_chart(fig, use_container_width=True)

    # Habit streaks
    fig = px.scatter(habit_df, x='Current Streak', y='Best Streak',
                     size='Completion Rate', hover_name='Habit',
                     title='Habit Streak Analysis',
                     color='Completion Rate',
                     color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)

# Productivity insights
st.markdown("#### 💡 Productivity Insights")

insights = []

# Task completion insights
if analytics['completion_rate'] > 80:
    insights.append("🎉 Excellent! You're completing over 80% of your tasks.")
elif analytics['completion_rate'] > 60:
    insights.append("👍 Good job! You're on track with a 60%+ completion rate.")
else:
    insights.append("📈 Consider breaking down large tasks into smaller, manageable pieces.")

# Time estimation insights
if analytics['total_estimated_hours'] > 0 and analytics['total_actual_hours'] > 0:
    ratio = analytics['total_actual_hours'] / analytics['total_estimated_hours']
    if ratio < 0.8:
        insights.append("⏰ You're completing tasks faster than estimated. Great efficiency!")
    elif ratio > 1.2:
        insights.append("🤔 Tasks are taking longer than estimated. Consider more realistic time planning.")
    else:
        insights.append("🎯 Your time estimation is quite accurate!")

# Habit insights
if st.session_state.habits:
    avg_habit_completion = sum(len([d for d in h.get('completion_dates', [])
                                    if datetime.fromisoformat(d).date() >= start_date])
                               for h in st.session_state.habits) / len(st.session_state.habits)

    if avg_habit_completion > 20:  # For 30-day period
        insights.append("🌟 Outstanding habit consistency! You're building strong routines.")
    elif avg_habit_completion > 10:
        insights.append("💪 Good habit progress! Keep building those daily routines.")
    else:
        insights.append("🎯 Focus on consistency. Start with just one habit at a time.")

for insight in insights:
    st.info(insight)

elif st.session_state.current_view == "ai_insights":
st.markdown('<h1 class="main-header">🧠 AI Insights</h1>', unsafe_allow_html=True)

st.markdown("### 🤖 Personalized Recommendations")

# Generate AI-powered insights
tasks = st.session_state.tasks
habits = st.session_state.habits

# Task pattern analysis
st.markdown("#### 📊 Task Pattern Analysis")

if tasks:
    # Most productive days
    completion_by_day = {}
    for task in tasks:
        if task.get('completed_at'):
            day = datetime.fromisoformat(task['completed_at']).strftime('%A')
            completion_by_day[day] = completion_by_day.get(day, 0) + 1

    if completion_by_day:
        best_day = max(completion_by_day, key=completion_by_day.get)
        st.success(f"🎯 Your most productive day is {best_day}! Consider scheduling important tasks on {best_day}s.")

    # Overdue pattern analysis
    overdue_tasks = [t for t in tasks if t.get('due_date') and
                     datetime.fromisoformat(t['due_date']).date() < date.today() and
                     t['status'] == TaskStatus.PENDING]

    if overdue_tasks:
        overdue_categories = {}
        for task in overdue_tasks:
            category = task.get('category', 'General')
            overdue_categories[category] = overdue_categories.get(category, 0) + 1

        if overdue_categories:
            problem_category = max(overdue_categories, key=overdue_categories.get)
            st.warning(
                f"⚠️ You have the most overdue tasks in '{problem_category}'. Consider dedicating more time to this area.")

    # Time estimation accuracy
    time_tracking_tasks = [t for t in tasks if t.get('estimated_hours', 0) > 0 and t.get('actual_hours', 0) > 0]
    if time_tracking_tasks:
        total_estimated = sum(t['estimated_hours'] for t in time_tracking_tasks)
        total_actual = sum(t['actual_hours'] for t in time_tracking_tasks)

        ratio = total_actual / total_estimated
        if ratio > 1.2:
            st.info("🤔 You tend to underestimate task duration. Try adding 20% buffer time to your estimates.")
        elif ratio < 0.8:
            st.info(
                "⚡ You often finish tasks faster than expected! You might be overestimating or working very efficiently.")

# Habit insights
st.markdown("#### 🎯 Habit Optimization")

if habits:
    # Best performing habits
    habit_scores = []
    for habit in habits:
        completion_rate = len(habit.get('completion_dates', [])) / max(
            (date.today() - datetime.fromisoformat(habit['created_at']).date()).days, 1)
        habit_scores.append((habit['name'], completion_rate, habit.get('streak', 0)))

    if habit_scores:
        best_habit = max(habit_scores, key=lambda x: x[1])
        worst_habit = min(habit_scores, key=lambda x: x[1])

        st.success(
            f"🌟 Your most successful habit is '{best_habit[0]}'. Consider applying the same approach to other habits.")

        if worst_habit[1] < 0.3:  # Less than 30% completion rate
            st.warning(
                f"📉 '{worst_habit[0]}' needs attention. Try making it easier or linking it to an existing habit.")

    # Habit scheduling suggestions
    st.info(
        "💡 **Habit Stacking Tip**: Link new habits to existing ones. For example: 'After I pour my morning coffee, I will write in my journal.'")

# Productivity recommendations
st.markdown("#### 🚀 Productivity Boost Recommendations")

recommendations = [
    "🎯 **Time Blocking**: Schedule specific time slots for different types of tasks",
    "🍅 **Pomodoro Technique**: Use 25-minute focused work sessions with 5-minute breaks",
    "📱 **Digital Minimalism**: Turn off non-essential notifications during work hours",
    "🧘 **Mindfulness**: Take 2-minute breathing breaks between tasks",
    "📊 **Weekly Review**: Spend 15 minutes every Sunday planning the upcoming week"
]

for rec in recommendations:
    st.markdown(rec)

# Smart suggestions based on current state
st.markdown("#### 💡 Smart Suggestions")

current_hour = datetime.now().hour

if 9 <= current_hour <= 11:
    st.info("🌅 **Morning Power**: This is typically a high-energy time. Tackle your most challenging tasks now!")
elif 14 <= current_hour <= 16:
    st.info("📉 **Afternoon Dip**: Energy often drops after lunch. Consider easier tasks or take a short walk.")
elif 19 <= current_hour <= 21:
    st.info("🌙 **Evening Planning**: Great time to plan tomorrow and review today's accomplishments.")

# Personalized goal suggestions
st.markdown("#### 🎯 Suggested Goals")

current_completion_rate = analytics['completion_rate']

if current_completion_rate < 50:
    goal = "Reach 60% task completion rate this month"
elif current_completion_rate < 75:
    goal = "Achieve 80% task completion rate"
else:
    goal = "Maintain your excellent completion rate and focus on time estimation accuracy"

st.markdown(f"**This Month's Goal**: {goal}")

# Habit goal
if not habits:
    habit_goal = "Start your first habit! Begin with just 2 minutes daily."
elif len(habits) < 3:
    habit_goal = "Add one more keystone habit to your routine"
else:
    habit_goal = "Focus on consistency - complete all habits for 7 days straight"

st.markdown(f"**Habit Goal**: {habit_goal}")

elif st.session_state.current_view == "quick_actions":
st.markdown('<h1 class="main-header">⚡ Quick Actions</h1>', unsafe_allow_html=True)

# Quick action cards
col1, col2, col3 = st.columns(3)
