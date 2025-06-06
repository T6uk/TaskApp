import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import uuid
from utils import *
from advanced_features import *
from data_persistence import *
from notifications import *

# Page config
st.set_page_config(
    page_title="TickTick Clone - Enhanced Pro",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for modern UI
st.markdown("""
<style>
    /* Main theme variables */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --info-color: #3b82f6;
        --background-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        --border-radius: 12px;
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Header styling */
    .main-header {
        background: var(--background-gradient);
        color: white;
        padding: 20px;
        border-radius: var(--border-radius);
        margin-bottom: 24px;
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        box-shadow: var(--card-shadow);
    }

    /* Enhanced task cards */
    .task-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 16px;
        margin: 12px 0;
        box-shadow: var(--card-shadow);
        transition: var(--transition);
        border-left: 4px solid transparent;
        position: relative;
        overflow: hidden;
    }

    .task-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--background-gradient);
        opacity: 0;
        transition: var(--transition);
    }

    .task-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }

    .task-card:hover::before {
        opacity: 1;
    }

    .task-card.completed {
        background: #f8f9fa;
        opacity: 0.8;
    }

    .task-card.priority-high { border-left-color: var(--error-color); }
    .task-card.priority-medium { border-left-color: var(--warning-color); }
    .task-card.priority-low { border-left-color: var(--info-color); }
    .task-card.priority-none { border-left-color: #9ca3af; }

    /* Habit tracker styling */
    .habit-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 20px;
        margin: 16px 0;
        box-shadow: var(--card-shadow);
        transition: var(--transition);
        border: 2px solid transparent;
    }

    .habit-card:hover {
        border-color: var(--primary-color);
        transform: translateY(-1px);
    }

    .habit-tracker-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, 16px);
        gap: 2px;
        margin: 12px 0;
    }

    .habit-day {
        width: 16px;
        height: 16px;
        border-radius: 3px;
        transition: var(--transition);
        border: 1px solid #e5e7eb;
        cursor: pointer;
    }

    .habit-day.completed { 
        background: var(--success-color); 
        border-color: var(--success-color);
        transform: scale(1.1);
    }
    .habit-day.missed { background: var(--error-color); border-color: var(--error-color); }
    .habit-day.pending { background: #f3f4f6; }

    /* Sidebar enhancements */
    .sidebar-section {
        background: white;
        padding: 16px;
        border-radius: var(--border-radius);
        margin: 12px 0;
        box-shadow: var(--card-shadow);
        border: 1px solid #e5e7eb;
    }

    /* Metrics cards */
    .metric-card {
        background: var(--background-gradient);
        color: white;
        padding: 20px;
        border-radius: var(--border-radius);
        text-align: center;
        margin: 8px 0;
        box-shadow: var(--card-shadow);
        transition: var(--transition);
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }

    /* Pomodoro timer */
    .pomodoro-timer {
        background: white;
        border: 4px solid var(--primary-color);
        border-radius: 50%;
        width: 200px;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 20px auto;
        font-size: 32px;
        font-weight: bold;
        color: var(--primary-color);
        box-shadow: var(--card-shadow);
        transition: var(--transition);
        position: relative;
        overflow: hidden;
    }

    .pomodoro-timer.active {
        animation: pulse 2s infinite;
        border-color: var(--success-color);
        color: var(--success-color);
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(102, 126, 234, 0); }
        100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
    }

    /* Notification badges */
    .notification-badge {
        background: var(--error-color);
        color: white;
        border-radius: 50%;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 8px;
        animation: bounce 1s infinite;
    }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }

    /* Progress bars */
    .progress-container {
        background: #e5e7eb;
        border-radius: 10px;
        overflow: hidden;
        height: 8px;
        margin: 8px 0;
    }

    .progress-bar {
        height: 100%;
        background: var(--background-gradient);
        transition: width 0.5s ease;
        border-radius: 10px;
    }

    /* Focus mode styling */
    .focus-mode {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 24px;
        border-radius: var(--border-radius);
        margin: 20px 0;
        color: white;
        text-align: center;
        box-shadow: var(--card-shadow);
    }

    /* Achievement notifications */
    .achievement-card {
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        color: white;
        padding: 20px;
        border-radius: var(--border-radius);
        margin: 16px 0;
        text-align: center;
        box-shadow: var(--card-shadow);
        animation: slideInUp 0.5s ease;
    }

    @keyframes slideInUp {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    /* Calendar grid */
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 8px;
        margin: 16px 0;
    }

    .calendar-day {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 8px;
        min-height: 80px;
        transition: var(--transition);
        cursor: pointer;
    }

    .calendar-day:hover {
        border-color: var(--primary-color);
        transform: scale(1.02);
    }

    .calendar-day.today {
        border-color: var(--primary-color);
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    }

    /* Smart list styling */
    .smart-list-item {
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 8px;
        transition: var(--transition);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .smart-list-item:hover {
        background: rgba(102, 126, 234, 0.1);
        transform: translateX(4px);
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .calendar-grid {
            grid-template-columns: 1fr;
        }

        .pomodoro-timer {
            width: 150px;
            height: 150px;
            font-size: 24px;
        }
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: #1a1a1a;
            --text-color: #ffffff;
        }
    }

    /* Glassmorphism effects for premium feel */
    .glass-card {
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }

    /* Micro-interactions */
    .interactive-button {
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        transform-origin: center;
    }

    .interactive-button:hover {
        transform: scale(1.05);
    }

    .interactive-button:active {
        transform: scale(0.95);
    }

    /* Status indicators */
    .status-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }

    .status-pending { background: var(--warning-color); }
    .status-in-progress { background: var(--info-color); }
    .status-completed { background: var(--success-color); }
    .status-cancelled { background: #6b7280; }
</style>
""", unsafe_allow_html=True)

# Initialize enhanced systems
init_session_state()
init_smart_notification_system()

# Initialize smart data manager
if 'smart_data_manager' not in st.session_state:
    st.session_state.smart_data_manager = create_smart_data_manager("file", auto_backup=True)

# Load saved data on startup
if 'data_loaded' not in st.session_state:
    load_saved_data()
    st.session_state.data_loaded = True

# Auto-save with enhanced error handling
if 'last_auto_save' not in st.session_state:
    st.session_state.last_auto_save = datetime.now()

# Check if it's time to auto-save (every 30 seconds)
if (datetime.now() - st.session_state.last_auto_save).seconds > 30:
    auto_save_data()

# Enhanced sidebar with modern design
with st.sidebar:
    # App header with gradient
    st.markdown("""
    <div class="main-header">
        ✅ TickTick Pro
        <div style="font-size: 14px; font-weight: 400; margin-top: 8px;">
            Enhanced Productivity Suite
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats with modern cards
    stats = get_task_stats()
    habit_stats = get_habit_stats()

    # Modern metrics display
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 24px; font-weight: bold;">{stats['pending']}</div>
            <div style="font-size: 12px; opacity: 0.9;">Pending</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 24px; font-weight: bold;">{stats['overdue']}</div>
            <div style="font-size: 12px; opacity: 0.9;">Overdue</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 24px; font-weight: bold;">{stats['completed']}</div>
            <div style="font-size: 12px; opacity: 0.9;">Completed</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 24px; font-weight: bold;">{habit_stats['completed_today']}/{habit_stats['total']}</div>
            <div style="font-size: 12px; opacity: 0.9;">Habits</div>
        </div>
        """, unsafe_allow_html=True)

    # Enhanced progress visualization
    if stats['total'] > 0:
        progress = stats['completed'] / stats['total']
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress * 100}%"></div>
        </div>
        <div style="text-align: center; font-size: 14px; color: #6b7280; margin-top: 4px;">
            {progress:.1%} completion rate
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Smart search with advanced features
    search_query = st.text_input("🔍 Smart Search", placeholder="Search tasks, #tags, priority:high...")

    # Quick filters
    if st.checkbox("🎯 Smart Filters", value=False):
        quick_filters = st.multiselect(
            "Quick apply",
            ["High Priority", "Due Today", "Overdue", "No Due Date", "Work", "Personal"],
            default=[]
        )

    st.divider()

    # Enhanced navigation with notification badges
    notification_count = get_notification_badge_count()

    nav_options = {
        "📝 Tasks": "tasks",
        "📅 Calendar": "calendar",
        "🎯 Habits": "habits",
        "🍅 Pomodoro": "pomodoro",
        "📊 Analytics": "analytics",
        "🧠 Smart Features": "smart",
        "🔔 Notifications": "notifications",
        "⚙️ Settings": "settings"
    }

    for label, view in nav_options.items():
        # Add notification badge for notifications view
        display_label = label
        if view == "notifications" and notification_count > 0:
            display_label = f"{label} ({notification_count})"

        if st.button(display_label, use_container_width=True,
                     key=f"nav_{view}",
                     type="primary" if st.session_state.current_view == view else "secondary"):
            st.session_state.current_view = view
            st.rerun()

    st.divider()

    # Enhanced Smart Lists with modern styling
    st.markdown("### 🧠 Smart Lists")
    smart_filters = {
        "📋 All Tasks": "all",
        "📅 Today": "today",
        "📆 Tomorrow": "tomorrow",
        "📋 This Week": "this_week",
        "⚠️ Overdue": "overdue",
        "⭐ High Priority": "high_priority",
        "🔄 In Progress": "in_progress",
        "✅ Completed": "completed"
    }

    for label, filter_type in smart_filters.items():
        task_count = len(get_tasks_by_filter(filter_type))

        # Modern list item with hover effects
        if st.button(f"{label} ({task_count})",
                     use_container_width=True,
                     key=f"filter_{filter_type}",
                     help=f"Show {label.lower()}"):
            st.session_state.current_filter = filter_type
            st.session_state.current_view = "tasks"
            st.rerun()

    # Custom Lists with enhanced UI
    st.markdown("### 📁 My Lists")
    for list_name in st.session_state.lists:
        list_tasks = [t for t in st.session_state.tasks if t['list_name'] == list_name]
        total_count = len(list_tasks)
        pending_count = len([t for t in list_tasks if t['status'] == TaskStatus.PENDING.value])
        completed_count = len([t for t in list_tasks if t['status'] == TaskStatus.COMPLETED.value])

        if st.button(f"📋 {list_name} ({pending_count}/{total_count})",
                     use_container_width=True,
                     key=f"list_{list_name}",
                     help=f"{completed_count} completed, {pending_count} pending"):
            st.session_state.current_filter = list_name
            st.session_state.current_view = "tasks"
            st.rerun()

    # Quick add list with modern design
    with st.expander("➕ Manage Lists"):
        new_list = st.text_input("New list name", key="new_list_name")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Add", key="add_list_btn", use_container_width=True):
                if new_list and new_list not in st.session_state.lists:
                    st.session_state.lists.append(new_list)
                    st.success(f"Added: {new_list}")
                    auto_save_data()
                    st.rerun()

        with col2:
            # List management
            if st.button("Manage", key="manage_lists_btn", use_container_width=True):
                st.session_state.current_view = "settings"
                st.rerun()

    # Daily insights
    st.markdown("### 💡 Today's Insights")
    insights = generate_smart_insights(st.session_state.tasks, st.session_state.habits)

    if insights:
        for insight in insights[:3]:  # Show top 3 insights
            st.info(insight)
    else:
        st.success("🎉 All good! No urgent insights today.")

# Main content area with enhanced views
if st.session_state.current_view == "tasks":
    st.markdown('<div class="main-header">📝 Task Management</div>', unsafe_allow_html=True)

    # Enhanced task view with multiple tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📋 List View", "🎯 Focus Mode", "⚡ Bulk Actions", "📋 Templates", "🔍 Advanced Search"])

    with tab1:
        render_enhanced_task_list_view(search_query)

    with tab2:
        render_focus_mode()

    with tab3:
        render_bulk_operations()

    with tab4:
        render_task_templates()

    with tab5:
        render_advanced_search_interface()

elif st.session_state.current_view == "calendar":
    st.markdown('<div class="main-header">📅 Calendar & Planning</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📅 Month View", "📋 Week Planner", "📊 Timeline", "⏰ Time Blocking"])

    with tab1:
        render_enhanced_calendar_view()

    with tab2:
        render_weekly_planner()

    with tab3:
        render_gantt_chart()

    with tab4:
        render_time_blocking_interface()

elif st.session_state.current_view == "habits":
    st.markdown('<div class="main-header">🎯 Habit Tracking</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🎯 My Habits", "📊 Analytics", "🏆 Achievements"])

    with tab1:
        render_enhanced_habits_view()

    with tab2:
        render_habit_insights()

    with tab3:
        render_habit_achievements()

elif st.session_state.current_view == "pomodoro":
    st.markdown('<div class="main-header">🍅 Focus Sessions</div>', unsafe_allow_html=True)
    render_enhanced_pomodoro_timer()

elif st.session_state.current_view == "analytics":
    st.markdown('<div class="main-header">📊 Productivity Analytics</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🧠 Advanced Analytics", "🎯 Goal Tracking"])

    with tab1:
        render_productivity_overview()

    with tab2:
        render_comprehensive_analytics()

    with tab3:
        render_goal_tracking_interface()

elif st.session_state.current_view == "smart":
    st.markdown('<div class="main-header">🧠 Smart Features</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Eisenhower Matrix", "🚀 Smart Scheduling", "🔮 AI Insights"])

    with tab1:
        render_advanced_eisenhower_matrix()

    with tab2:
        render_smart_scheduling()

    with tab3:
        render_ai_insights_dashboard()

elif st.session_state.current_view == "notifications":
    render_enhanced_notification_center()

elif st.session_state.current_view == "settings":
    st.markdown('<div class="main-header">⚙️ Settings & Preferences</div>', unsafe_allow_html=True)
    render_enhanced_settings()


# Helper functions for enhanced views
def render_enhanced_task_list_view(search_query: str):
    """Enhanced task list view with modern UI"""

    # Quick add task with enhanced UI
    with st.container():
        st.markdown("### ➕ Quick Add Task")

        col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
        with col1:
            new_task_title = st.text_input("", placeholder="What do you want to accomplish?", key="quick_task_input")
        with col2:
            quick_due = st.date_input("Due date", value=None, key="quick_due")
        with col3:
            quick_priority = st.selectbox("Priority",
                                          options=[p.value for p in Priority],
                                          format_func=lambda x: x.title(),
                                          key="quick_priority")
        with col4:
            quick_list = st.selectbox("List", st.session_state.lists, key="quick_list")

        if st.button("✨ Add Task", type="primary", use_container_width=True):
            if new_task_title:
                errors = validate_task_data(new_task_title, quick_due)
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    task_id = add_task(new_task_title, due_date=quick_due,
                                       priority=Priority(quick_priority), list_name=quick_list)
                    if task_id:
                        st.success("Task added successfully! ✨")
                        create_task_completion_celebration("Task Created", {"task_id": task_id})
                        auto_save_data()
                        st.rerun()

    # Advanced filters with modern UI
    with st.expander("🔧 Advanced Filters & Sorting", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            filter_status = st.selectbox("Status",
                                         ["All", "Pending", "In Progress", "Completed", "Cancelled"],
                                         key="filter_status")
        with col2:
            filter_list = st.selectbox("List",
                                       ["All"] + st.session_state.lists,
                                       key="filter_list")
        with col3:
            filter_priority = st.selectbox("Priority",
                                           ["All"] + [p.value.title() for p in Priority],
                                           key="filter_priority")
        with col4:
            sort_by = st.selectbox("Sort by",
                                   ["Due Date", "Priority", "Created", "Updated", "Title", "Completion %"],
                                   key="sort_by")
        with col5:
            sort_reverse = st.checkbox("Reverse order", key="sort_reverse")

    # Get and filter tasks with enhanced logic
    if search_query:
        tasks = search_tasks_advanced(search_query)
    else:
        tasks = get_tasks_by_filter(getattr(st.session_state, 'current_filter', 'all'))

    # Apply additional filters
    if filter_status != "All":
        status_map = {
            "Pending": TaskStatus.PENDING.value,
            "In Progress": TaskStatus.IN_PROGRESS.value,
            "Completed": TaskStatus.COMPLETED.value,
            "Cancelled": TaskStatus.CANCELLED.value
        }
        tasks = [t for t in tasks if t['status'] == status_map[filter_status]]

    if filter_list != "All":
        tasks = [t for t in tasks if t['list_name'] == filter_list]

    if filter_priority != "All":
        tasks = [t for t in tasks if t['priority'] == filter_priority.lower()]

    # Enhanced sorting
    tasks = sort_tasks(tasks, sort_by.lower().replace(" ", "_"), sort_reverse)

    # Display enhanced task list
    st.markdown(f"### 📋 Found {len(tasks)} tasks")

    if not tasks:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #6b7280;">
            <div style="font-size: 48px; margin-bottom: 16px;">📝</div>
            <div style="font-size: 18px; margin-bottom: 8px;">No tasks found</div>
            <div style="font-size: 14px;">Create your first task above to get started!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for task in tasks:
            render_enhanced_task_card(task)


def render_enhanced_task_card(task: Dict):
    """Render enhanced task card with modern design"""

    # Determine card styling
    priority_class = f"priority-{task['priority']}"
    status_class = "completed" if task['status'] == TaskStatus.COMPLETED.value else ""

    # Build progress indicator for subtasks
    progress_html = ""
    if task.get('subtasks'):
        completed_subtasks = sum(1 for st in task['subtasks']
                                 if isinstance(st, dict) and st.get('completed', False))
        total_subtasks = len(task['subtasks'])
        progress_pct = (completed_subtasks / total_subtasks) * 100 if total_subtasks > 0 else 0

        progress_html = f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress_pct}%"></div>
        </div>
        <small style="color: #6b7280;">{completed_subtasks}/{total_subtasks} subtasks completed</small>
        """

    # Build tags display
    tags_html = ""
    if task.get('tags') and isinstance(task['tags'], list):
        tags_html = "<div style='margin-top: 8px;'>" + "".join([
            f'<span style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; '
            f'padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px;">{tag}</span>'
            for tag in task['tags']
        ]) + "</div>"

    # Time display
    due_date_display = format_date_display(task['due_date'])

    # Estimated vs actual time
    time_info = ""
    if task.get('estimated_time'):
        est_hours = task['estimated_time'] / 60
        time_info = f"⏱️ Est: {est_hours:.1f}h"

        if task.get('actual_time'):
            act_hours = task['actual_time'] / 60
            time_info += f" | Act: {act_hours:.1f}h"

    with st.container():
        col1, col2, col3, col4 = st.columns([0.5, 6, 1.5, 1])

        with col1:
            # Enhanced checkbox with status handling
            if task['status'] == TaskStatus.COMPLETED.value:
                checked = st.checkbox("", value=True, key=f"task_check_{task['id']}")
                if not checked:
                    uncomplete_task(task['id'])
                    st.success("Task marked as pending!")
                    auto_save_data()
                    st.rerun()
            else:
                checked = st.checkbox("", value=False, key=f"task_check_{task['id']}")
                if checked:
                    complete_task(task['id'])
                    create_task_completion_celebration(task['title'], {"task_id": task['id']})
                    st.balloons()
                    auto_save_data()
                    st.rerun()

        with col2:
            # Enhanced task display
            title_style = "text-decoration: line-through; opacity: 0.7;" if task[
                                                                                'status'] == TaskStatus.COMPLETED.value else ""

            st.markdown(f"""
            <div class="task-card {priority_class} {status_class}">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span class="status-indicator status-{task['status'].replace('_', '-')}"></span>
                    <h4 style="margin: 0; {title_style}">{task['title']}</h4>
                </div>

                {f'<p style="color: #6b7280; margin: 8px 0; {title_style}">{task["description"]}</p>' if task.get('description') else ''}

                <div style="display: flex; align-items: center; gap: 16px; font-size: 13px; color: #6b7280;">
                    <span>📋 {task['list_name']}</span>
                    <span>📅 {due_date_display}</span>
                    <span>🎯 {task['priority'].title()}</span>
                    {f'<span>{time_info}</span>' if time_info else ''}
                </div>

                {progress_html}
                {tags_html}
            </div>
            """, unsafe_allow_html=True)

        with col3:
            # Action buttons with modern styling
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                if st.button("✏️", key=f"edit_{task['id']}", help="Edit task"):
                    st.session_state.editing_task_id = task['id']
                    st.rerun()

            with col_b:
                if st.button("📊", key=f"details_{task['id']}", help="View details"):
                    render_task_details_modal(task)

            with col_c:
                if st.button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
                    if delete_task(task['id']):
                        st.success("Task deleted!")
                        auto_save_data()
                        st.rerun()

        with col4:
            # Priority indicator and quick actions
            priority_colors = {"high": "🔴", "medium": "🟡", "low": "🔵", "none": "⚪"}
            st.markdown(f"**{priority_colors.get(task['priority'], '⚪')}**")

            if task['status'] == TaskStatus.PENDING.value:
                if st.button("🍅", key=f"pomodoro_{task['id']}", help="Start focus session"):
                    start_pomodoro_for_task(task)


def render_enhanced_calendar_view():
    """Enhanced calendar view with modern design"""

    # Calendar controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        view_type = st.selectbox("View", ["Month", "Week", "Day"])
    with col2:
        current_date = st.date_input("Navigate to", value=date.today())
    with col3:
        show_completed = st.checkbox("Show completed", value=False)
    with col4:
        color_by = st.selectbox("Color by", ["Priority", "List", "Status"])

    if view_type == "Month":
        render_monthly_calendar_grid(current_date, show_completed, color_by)
    elif view_type == "Week":
        render_weekly_calendar_view(current_date, show_completed, color_by)
    else:
        render_daily_calendar_view(current_date, show_completed, color_by)


def render_enhanced_habits_view():
    """Enhanced habits view with modern design"""

    # Habit overview metrics
    habit_stats = get_habit_stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Habits", habit_stats['total'])
    col2.metric("Completed Today", habit_stats['completed_today'])
    col3.metric("Completion Rate", f"{habit_stats['completion_rate']:.1f}%")
    col4.metric("Active Habits", habit_stats['active_habits'])

    # Add new habit with enhanced UI
    with st.expander("➕ Add New Habit", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            habit_name = st.text_input("Habit name", placeholder="e.g., Drink 8 glasses of water")
        with col2:
            habit_frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly"])
        with col3:
            habit_target = st.number_input("Target", min_value=1, value=1)
        with col4:
            reminder_time = st.time_input("Reminder", value=None)
        with col5:
            habit_category = st.selectbox("Category",
                                          ["Health", "Fitness", "Learning", "Work", "Personal", "Social"])

        if st.button("✨ Create Habit", type="primary", use_container_width=True):
            if habit_name:
                reminder_str = reminder_time.strftime('%H:%M') if reminder_time else None
                habit_id = add_habit(habit_name, habit_frequency, habit_target, reminder_str, habit_category)
                if habit_id:
                    st.success("Habit created successfully! ✨")
                    auto_save_data()
                    st.rerun()

    # Display habits with enhanced cards
    if not st.session_state.habits:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #6b7280;">
            <div style="font-size: 48px; margin-bottom: 16px;">🎯</div>
            <div style="font-size: 18px; margin-bottom: 8px;">No habits yet</div>
            <div style="font-size: 14px;">Create your first habit above to start building positive routines!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for habit in st.session_state.habits:
            render_enhanced_habit_card(habit)


def render_enhanced_habit_card(habit: Dict):
    """Render enhanced habit card with modern design"""

    today = date.today().isoformat()
    completion_dates = habit.get('completion_dates', [])
    if isinstance(completion_dates, str):
        try:
            completion_dates = json.loads(completion_dates)
        except:
            completion_dates = []

    completed_today = today in completion_dates
    current_streak = habit.get('streak', 0)
    best_streak = habit.get('best_streak', 0)

    with st.container():
        st.markdown(f"""
        <div class="habit-card">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                <div>
                    <h3 style="margin: 0; color: #1f2937;">{habit['name']}</h3>
                    <p style="margin: 4px 0; color: #6b7280; font-size: 14px;">
                        📅 {habit['frequency'].title()} • 🎯 Target: {habit['target']} 
                        {f"• ⏰ {habit['reminder_time']}" if habit.get('reminder_time') else ""}
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 24px; font-weight: bold; color: #667eea;">{current_streak}</div>
                    <div style="font-size: 12px; color: #6b7280;">Current Streak</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            # Habit tracker visualization (last 30 days)
            render_habit_tracker_grid(completion_dates)

        with col2:
            # Today's status and action
            if completed_today:
                st.success("✅ Completed today!")
                if st.button("↩️ Undo", key=f"undo_habit_{habit['id']}"):
                    uncomplete_habit(habit['id'])
                    auto_save_data()
                    st.rerun()
            else:
                if st.button("✨ Mark Complete", key=f"habit_{habit['id']}", type="primary", use_container_width=True):
                    complete_habit(habit['id'])
                    st.balloons()
                    st.success("Great job! 🎉")
                    auto_save_data()
                    st.rerun()

        with col3:
            # Streak information with enhanced display
            st.metric("Best Streak", f"{best_streak} days",
                      delta=f"+{current_streak - best_streak}" if current_streak > best_streak else None)

            # Calculate completion rate for last 30 days
            thirty_days_ago = date.today() - timedelta(days=30)
            recent_completions = [d for d in completion_dates
                                  if datetime.fromisoformat(d).date() >= thirty_days_ago]
            completion_rate = len(recent_completions) / 30 * 100

            st.metric("30-Day Rate", f"{completion_rate:.0f}%")

        with col4:
            # Habit actions
            if st.button("🗑️", key=f"delete_habit_{habit['id']}", help="Delete habit"):
                if delete_habit(habit['id']):
                    st.success("Habit deleted!")
                    auto_save_data()
                    st.rerun()


def render_habit_tracker_grid(completion_dates: List[str]):
    """Render habit tracker grid for last 30 days"""

    # Generate last 30 days
    grid_html = '<div class="habit-tracker-grid">'

    for i in range(29, -1, -1):  # Last 30 days
        check_date = date.today() - timedelta(days=i)
        date_str = check_date.isoformat()

        if date_str in completion_dates:
            css_class = "completed"
            title = f"Completed on {check_date.strftime('%m/%d')}"
        elif check_date < date.today():
            css_class = "missed"
            title = f"Missed on {check_date.strftime('%m/%d')}"
        else:
            css_class = "pending"
            title = f"Today ({check_date.strftime('%m/%d')})"

        grid_html += f'<div class="habit-day {css_class}" title="{title}"></div>'

    grid_html += '</div>'

    st.markdown(grid_html, unsafe_allow_html=True)


def render_enhanced_pomodoro_timer():
    """Enhanced Pomodoro timer with modern design"""

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### ⚙️ Timer Configuration")

        # Enhanced settings
        work_duration = st.slider("Work duration (minutes)", 15, 60,
                                  st.session_state.pomodoro_state.get('duration', 25))
        break_duration = st.slider("Short break (minutes)", 5, 30,
                                   st.session_state.pomodoro_state.get('break_duration', 5))
        long_break = st.slider("Long break (minutes)", 15, 60,
                               st.session_state.pomodoro_state.get('long_break_duration', 30))
        daily_goal = st.slider("Daily goal (sessions)", 1, 16,
                               st.session_state.pomodoro_state.get('daily_goal', 8))

        # Session statistics
        sessions_completed = st.session_state.pomodoro_state.get('sessions_completed', 0)

        # Enhanced metrics display
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Today's Sessions", sessions_completed)
        col_b.metric("Daily Goal", daily_goal)
        col_c.metric("Progress", f"{min(100, sessions_completed / daily_goal * 100):.0f}%")

        # Progress bar for daily goal
        progress_pct = min(100, (sessions_completed / daily_goal) * 100)
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress_pct}%"></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🍅 Focus Timer")

        # Enhanced timer display
        if st.session_state.pomodoro_state.get('active', False):
            elapsed = time.time() - st.session_state.pomodoro_state['start_time']
            duration_seconds = st.session_state.pomodoro_state['duration'] * 60
            remaining = max(0, duration_seconds - elapsed)

            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            progress = 1 - (remaining / duration_seconds)

            # Enhanced timer display with animations
            timer_class = "active" if remaining > 0 else ""
            current_type = st.session_state.pomodoro_state['current_type']

            st.markdown(f"""
            <div class="pomodoro-timer {timer_class}">
                {minutes:02d}:{seconds:02d}
            </div>
            """, unsafe_allow_html=True)

            # Enhanced progress visualization
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=progress * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"{current_type.title()} Session"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#667eea"},
                    'steps': [{'range': [0, 100], 'color': "lightgray"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=200)
            st.plotly_chart(fig, use_container_width=True)

            if remaining <= 0:
                handle_pomodoro_completion(current_type, sessions_completed)

            # Enhanced controls
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
            # Timer ready state with enhanced UI
            st.markdown("""
            <div class="pomodoro-timer">
                Ready
            </div>
            """, unsafe_allow_html=True)

            # Enhanced start buttons
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                if st.button("▶️ Start Work", type="primary", use_container_width=True):
                    start_pomodoro_session('work', work_duration, sessions_completed)

            with col_b:
                if st.button("☕ Short Break", type="secondary", use_container_width=True):
                    start_pomodoro_session('short_break', break_duration, sessions_completed)

            with col_c:
                if st.button("🛌 Long Break", type="secondary", use_container_width=True):
                    start_pomodoro_session('long_break', long_break, sessions_completed)

        # Current task focus section
        render_current_task_focus()


def render_enhanced_settings():
    """Enhanced settings interface"""

    tab1, tab2, tab3, tab4 = st.tabs(["🎨 Appearance", "📋 Lists & Data", "🔔 Notifications", "📊 Analytics"])

    with tab1:
        render_appearance_settings()

    with tab2:
        render_data_management_settings()

    with tab3:
        render_notification_settings()

    with tab4:
        render_analytics_settings()


# Additional helper functions
def start_pomodoro_for_task(task: Dict):
    """Start a Pomodoro session for a specific task"""
    duration = min(25, task.get('estimated_time', 25) or 25)

    st.session_state.pomodoro_state = {
        'active': True,
        'start_time': time.time(),
        'duration': duration,
        'current_type': 'work',
        'current_task': task['title'],
        'current_task_id': task['id'],
        'sessions_completed': st.session_state.pomodoro_state.get('sessions_completed', 0)
    }
    st.session_state.current_view = "pomodoro"
    st.rerun()


def handle_pomodoro_completion(session_type: str, sessions_completed: int):
    """Handle Pomodoro session completion"""
    if session_type == 'work':
        st.session_state.pomodoro_state['sessions_completed'] = sessions_completed + 1
        create_pomodoro_notification("break", {"session_type": session_type})
        st.balloons()
        st.success("🎉 Work session completed! Time for a break.")
    else:
        create_pomodoro_notification("work", {"session_type": session_type})
        st.success("☕ Break time over! Ready for the next work session?")

    st.session_state.pomodoro_state['active'] = False
    auto_save_data()
    st.rerun()


def start_pomodoro_session(session_type: str, duration: int, sessions_completed: int):
    """Start a new Pomodoro session"""
    st.session_state.pomodoro_state = {
        'active': True,
        'start_time': time.time(),
        'duration': duration,
        'current_type': session_type,
        'sessions_completed': sessions_completed
    }
    st.rerun()


# Auto-refresh for active timer
if (st.session_state.current_view == "pomodoro" and
        st.session_state.pomodoro_state.get('active', False)):
    time.sleep(1)
    st.rerun()