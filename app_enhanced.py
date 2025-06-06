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
    page_title="TickTick Clone - Enhanced",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for TickTick-like styling
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 20px;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }

    .task-item {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .task-item:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }

    .task-completed {
        background: #f8f9fa;
        opacity: 0.7;
    }

    .task-title-completed {
        text-decoration: line-through;
        color: #7f8c8d;
    }

    .priority-high { border-left: 4px solid #e74c3c; }
    .priority-medium { border-left: 4px solid #f39c12; }
    .priority-low { border-left: 4px solid #3498db; }
    .priority-none { border-left: 4px solid #95a5a6; }

    .sidebar-section {
        margin: 15px 0;
        padding: 12px;
        border-radius: 8px;
        background: #f8f9fa;
        border: 1px solid #e9ecef;
    }

    .notification-badge {
        background: #e74c3c;
        color: white;
        border-radius: 50%;
        padding: 2px 6px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 5px;
    }

    .achievement-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
    }

    .focus-mode {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
    }

    .pomodoro-timer {
        text-align: center;
        font-size: 48px;
        font-weight: bold;
        color: #e74c3c;
        margin: 20px 0;
        padding: 30px;
        border-radius: 50%;
        background: #f8f9fa;
        border: 4px solid #e74c3c;
        width: 200px;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 20px auto;
    }

    .habit-tracker {
        display: flex;
        flex-wrap: wrap;
        gap: 3px;
        margin: 10px 0;
    }

    .habit-day {
        width: 20px;
        height: 20px;
        border-radius: 3px;
        display: inline-block;
        border: 1px solid #ddd;
    }

    .habit-completed { background: #27ae60; border-color: #27ae60; }
    .habit-missed { background: #e74c3c; border-color: #e74c3c; }
    .habit-pending { background: #ecf0f1; }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state and systems
init_session_state()
init_notification_system()

# Load saved data on startup
if 'data_loaded' not in st.session_state:
    load_saved_data()
    st.session_state.data_loaded = True

# Auto-save data
if 'last_auto_save' not in st.session_state:
    st.session_state.last_auto_save = datetime.now()

# Check if it's time to auto-save
if (datetime.now() - st.session_state.last_auto_save).seconds > 30:
    auto_save_data()

# Sidebar navigation
with st.sidebar:
    st.markdown("### 📋 TickTick Clone Enhanced")

    # Notification badge
    notification_count = get_notification_badge_count()
    if notification_count > 0:
        st.markdown(f"🔔 Notifications <span class='notification-badge'>{notification_count}</span>",
                    unsafe_allow_html=True)

    # Quick stats
    stats = get_task_stats()
    habit_stats = get_habit_stats()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📋 Pending", stats['pending'])
        st.metric("⚠️ Overdue", stats['overdue'])
    with col2:
        st.metric("✅ Completed", stats['completed'])
        st.metric("🔥 Habits", f"{habit_stats['completed_today']}/{habit_stats['total']}")

    # Progress bar
    if stats['total'] > 0:
        progress = stats['completed'] / stats['total']
        st.progress(progress)
        st.write(f"**{progress:.1%}** completion rate")

    st.divider()

    # Search box
    search_query = st.text_input("🔍 Search tasks", placeholder="Search...")

    st.divider()

    # Navigation with notification badges
    nav_options = {
        "📝 Tasks": "tasks",
        "📅 Calendar": "calendar",
        "🎯 Habits": "habits",
        "🍅 Pomodoro": "pomodoro",
        "📊 Statistics": "statistics",
        "🧠 Advanced": "advanced",
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

    st.divider()

    # Smart Lists
    st.markdown("### 🧠 Smart Lists")
    smart_filters = {
        "📋 All Tasks": "all",
        "📅 Today": "today",
        "📆 Tomorrow": "tomorrow",
        "📋 This Week": "this_week",
        "⚠️ Overdue": "overdue",
        "⭐ High Priority": "high_priority",
        "✅ Completed": "completed"
    }

    for label, filter_type in smart_filters.items():
        task_count = len(get_tasks_by_filter(filter_type))
        if st.button(f"{label} ({task_count})", use_container_width=True, key=f"filter_{filter_type}"):
            st.session_state.current_filter = filter_type
            st.session_state.current_view = "tasks"

    # Custom Lists
    st.markdown("### 📁 My Lists")
    for list_name in st.session_state.lists:
        list_tasks = [t for t in st.session_state.tasks if t['list_name'] == list_name]
        task_count = len(list_tasks)
        pending_count = len([t for t in list_tasks if t['status'] == TaskStatus.PENDING.value])

        if st.button(f"📋 {list_name} ({pending_count}/{task_count})",
                     use_container_width=True, key=f"list_{list_name}"):
            st.session_state.current_filter = list_name
            st.session_state.current_view = "tasks"

    # Quick add list
    with st.expander("➕ Add List"):
        new_list = st.text_input("List name", key="new_list_name")
        if st.button("Add", key="add_list_btn"):
            if new_list and new_list not in st.session_state.lists:
                st.session_state.lists.append(new_list)
                st.success(f"Added list: {new_list}")
                auto_save_data()
                st.rerun()

# Main content area
if st.session_state.current_view == "tasks":
    st.markdown('<h1 class="main-header">📝 Tasks</h1>', unsafe_allow_html=True)

    # Quick action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 List View", "🎯 Focus Mode", "⚡ Bulk Operations", "📋 Templates"])

    with tab1:
        # Quick add task
        with st.container():
            st.markdown("### ➕ Quick Add Task")

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                new_task_title = st.text_input("", placeholder="What do you want to do?", key="quick_task_input")
            with col2:
                quick_due = st.date_input("Due date", value=None, key="quick_due")
            with col3:
                quick_priority = st.selectbox("Priority",
                                              options=[p.value for p in Priority],
                                              format_func=lambda x: x.title(),
                                              key="quick_priority")
            with col4:
                quick_list = st.selectbox("List", st.session_state.lists, key="quick_list")

            if st.button("Add Task", type="primary", use_container_width=True):
                if new_task_title:
                    errors = validate_task_data(new_task_title, quick_due)
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        add_task(new_task_title, due_date=quick_due,
                                 priority=Priority(quick_priority), list_name=quick_list)
                        st.success("Task added!")
                        auto_save_data()
                        st.rerun()

        # Advanced task creation
        with st.expander("🔧 Advanced Task Creation"):
            col1, col2 = st.columns(2)

            with col1:
                adv_title = st.text_input("Title", key="adv_title")
                adv_description = st.text_area("Description", key="adv_desc")
                adv_due_date = st.date_input("Due date", value=None, key="adv_due")

            with col2:
                adv_priority = st.selectbox("Priority",
                                            options=[p.value for p in Priority],
                                            format_func=lambda x: x.title(),
                                            key="adv_priority")
                adv_list = st.selectbox("List", st.session_state.lists, key="adv_list")
                adv_tags = st.text_input("Tags (comma separated)", key="adv_tags")
                adv_subtasks = st.text_area("Subtasks (one per line)", key="adv_subtasks")

            if st.button("Create Advanced Task", type="primary"):
                if adv_title:
                    errors = validate_task_data(adv_title, adv_due_date)
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        tags = [tag.strip() for tag in adv_tags.split(",")] if adv_tags else []
                        subtasks = [s.strip() for s in adv_subtasks.split("\n")] if adv_subtasks else []
                        add_task(adv_title, adv_description, adv_due_date,
                                 Priority(adv_priority), adv_list, tags, subtasks)
                        st.success("Advanced task created!")
                        auto_save_data()
                        st.rerun()

        # Task filters and sorting
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filter_status = st.selectbox("Status",
                                         ["All", "Pending", "Completed"],
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
                                   ["Due Date", "Priority", "Created", "Title"],
                                   key="sort_by")

        # Get and filter tasks
        if search_query:
            tasks = search_tasks(search_query)
        else:
            tasks = get_tasks_by_filter(getattr(st.session_state, 'current_filter', 'all'))

        # Apply additional filters
        if filter_status != "All":
            status_val = TaskStatus.PENDING.value if filter_status == "Pending" else TaskStatus.COMPLETED.value
            tasks = [t for t in tasks if t['status'] == status_val]

        if filter_list != "All":
            tasks = [t for t in tasks if t['list_name'] == filter_list]

        if filter_priority != "All":
            tasks = [t for t in tasks if t['priority'] == filter_priority.lower()]

        # Sort tasks
        if sort_by == "Due Date":
            tasks.sort(key=lambda x: (x['due_date'] is None, x['due_date'] or '9999-12-31'))
        elif sort_by == "Priority":
            priority_order = {p.value: i for i, p in enumerate(Priority)}
            tasks.sort(key=lambda x: priority_order.get(x['priority'], 999))
        elif sort_by == "Created":
            tasks.sort(key=lambda x: x['created_at'], reverse=True)
        elif sort_by == "Title":
            tasks.sort(key=lambda x: x['title'].lower())

        # Display tasks
        st.markdown(f"### Found {len(tasks)} tasks")

        if not tasks:
            st.info("No tasks found. Create your first task above!")
        else:
            for task in tasks:
                priority_class = f"priority-{task['priority']}"
                status_class = "task-completed" if task['status'] == TaskStatus.COMPLETED.value else ""
                title_class = "task-title-completed" if task['status'] == TaskStatus.COMPLETED.value else ""

                with st.container():
                    col1, col2, col3, col4 = st.columns([0.5, 4, 1, 1])

                    with col1:
                        if task['status'] == TaskStatus.PENDING.value:
                            if st.checkbox("", key=f"complete_{task['id']}"):
                                complete_task(task['id'])
                                st.success("Task completed!")
                                auto_save_data()
                                st.rerun()
                        else:
                            if st.checkbox("", value=True, key=f"uncomplete_{task['id']}"):
                                pass
                            else:
                                uncomplete_task(task['id'])
                                st.success("Task marked as pending!")
                                auto_save_data()
                                st.rerun()

                    with col2:
                        # Build task display
                        tags_html = ""
                        if task.get('tags') and isinstance(task['tags'], list):
                            tags_html = "<br>" + " ".join(
                                [
                                    f'<span style="background:#667eea;color:white;padding:2px 6px;border-radius:8px;font-size:10px;">{tag}</span>'
                                    for tag in task['tags']])

                        # Format due date
                        due_date_display = format_date_display(task['due_date'])

                        # Subtasks count
                        subtask_info = ""
                        if task.get('subtasks') and isinstance(task['subtasks'], list):
                            subtask_info = f" | 📝 {len(task['subtasks'])} subtasks"

                        st.markdown(f"""
                        <div class="task-item {priority_class} {status_class}">
                            <strong class="{title_class}">{task['title']}</strong><br>
                            <small style="color: #6c757d;">{task.get('description', '')}</small><br>
                            <small style="color: #6c757d;">📋 {task['list_name']} | 📅 {due_date_display} | 
                            🎯 {task['priority'].title()}{subtask_info}</small>
                            {tags_html}
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        if st.button("✏️", key=f"edit_{task['id']}", help="Edit task"):
                            # Simple edit functionality
                            with st.form(key=f"edit_form_{task['id']}"):
                                new_title = st.text_input("Title", value=task['title'])
                                new_desc = st.text_area("Description", value=task.get('description', ''))
                                if st.form_submit_button("Update"):
                                    if new_title:
                                        task['title'] = new_title
                                        task['description'] = new_desc
                                        st.success("Task updated!")
                                        auto_save_data()
                                        st.rerun()

                    with col4:
                        if st.button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
                            delete_task(task['id'])
                            st.success("Task deleted!")
                            auto_save_data()
                            st.rerun()

    with tab2:
        render_focus_mode()

    with tab3:
        render_bulk_operations()

    with tab4:
        render_task_templates()

elif st.session_state.current_view == "calendar":
    st.markdown('<h1 class="main-header">📅 Calendar</h1>', unsafe_allow_html=True)

    # Calendar view tabs
    tab1, tab2, tab3 = st.tabs(["📅 Month View", "📋 Week Planner", "📊 Timeline"])

    with tab1:
        # Monthly calendar view
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            view_type = st.selectbox("View", ["Month", "Week", "Day"])
        with col2:
            current_date = st.date_input("Navigate to", value=date.today())
        with col3:
            st.metric("Tasks Today", len(get_tasks_by_filter("today")))

        if view_type == "Month":
            # Monthly calendar implementation
            import calendar

            month_start = current_date.replace(day=1)

            # Get tasks for the month
            month_tasks = {}
            for task in st.session_state.tasks:
                if task['due_date']:
                    try:
                        task_date = datetime.fromisoformat(task['due_date']).date()
                        if task_date.month == current_date.month and task_date.year == current_date.year:
                            date_str = task_date.isoformat()
                            if date_str not in month_tasks:
                                month_tasks[date_str] = []
                            month_tasks[date_str].append(task)
                    except:
                        continue

            # Create calendar grid
            cal = calendar.monthcalendar(current_date.year, current_date.month)

            st.markdown(f"### {calendar.month_name[current_date.month]} {current_date.year}")

            # Days of week header
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            cols = st.columns(7)
            for i, day in enumerate(days):
                cols[i].markdown(f"**{day}**")

            # Calendar days
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day == 0:
                        cols[i].write("")
                    else:
                        day_date = date(current_date.year, current_date.month, day)
                        date_str = day_date.isoformat()
                        is_today = day_date == date.today()

                        with cols[i]:
                            # Day number with today highlighting
                            if is_today:
                                st.markdown(f"**🔸 {day}**")
                            else:
                                st.markdown(f"**{day}**")

                            # Show tasks for this day
                            if date_str in month_tasks:
                                tasks_today = month_tasks[date_str]
                                for idx, task in enumerate(tasks_today[:3]):  # Show max 3 tasks
                                    status_icon = "✅" if task['status'] == TaskStatus.COMPLETED.value else "⭕"
                                    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🔵", "none": "⚪"}.get(
                                        task['priority'], "⚪")
                                    st.markdown(f"{status_icon}{priority_emoji} {task['title'][:12]}...")

                                if len(tasks_today) > 3:
                                    st.markdown(f"<small>...+{len(tasks_today) - 3} more</small>",
                                                unsafe_allow_html=True)

    with tab2:
        render_weekly_planner()

    with tab3:
        render_gantt_chart()

elif st.session_state.current_view == "habits":
    st.markdown('<h1 class="main-header">🎯 Habits</h1>', unsafe_allow_html=True)

    # Habit tabs
    tab1, tab2 = st.tabs(["🎯 My Habits", "📊 Habit Analytics"])

    with tab1:
        # Habit stats overview
        habit_stats = get_habit_stats()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Habits", habit_stats['total'])
        col2.metric("Completed Today", habit_stats['completed_today'])
        col3.metric("Completion Rate", f"{habit_stats['completion_rate']:.1f}%")
        col4.metric("Avg Streak", f"{habit_stats['average_streak']:.1f}")

        # Add new habit
        with st.expander("➕ Add New Habit", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                habit_name = st.text_input("Habit name", placeholder="e.g., Drink 8 glasses of water")
            with col2:
                habit_frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly"])
            with col3:
                habit_target = st.number_input("Target", min_value=1, value=1)
            with col4:
                reminder_time = st.time_input("Reminder time", value=None)

            if st.button("Add Habit", type="primary"):
                if habit_name:
                    reminder_str = reminder_time.strftime('%H:%M') if reminder_time else None
                    add_habit(habit_name, habit_frequency, habit_target, reminder_str)
                    st.success("Habit added!")
                    auto_save_data()
                    st.rerun()

        # Display habits
        if not st.session_state.habits:
            st.info("No habits yet. Create your first habit above!")
        else:
            for habit in st.session_state.habits:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                    with col1:
                        st.markdown(f"**{habit['name']}**")
                        st.markdown(f"📅 {habit['frequency'].title()} | 🎯 Target: {habit['target']}")

                        if habit.get('reminder_time'):
                            st.markdown(f"⏰ Reminder: {habit['reminder_time']}")

                    with col2:
                        # Today's status
                        today = date.today().isoformat()
                        completion_dates = habit.get('completion_dates', [])
                        if isinstance(completion_dates, str):
                            try:
                                completion_dates = json.loads(completion_dates)
                            except:
                                completion_dates = []

                        completed_today = today in completion_dates

                        if completed_today:
                            st.success("✅ Completed today")
                            if st.button("Undo", key=f"undo_habit_{habit['id']}"):
                                uncomplete_habit(habit['id'])
                                auto_save_data()
                                st.rerun()
                        else:
                            if st.button("Mark Complete", key=f"habit_{habit['id']}", type="primary"):
                                complete_habit(habit['id'])
                                st.success("Habit completed!")
                                auto_save_data()
                                st.rerun()

                    with col3:
                        # Streak information
                        current_streak = habit.get('streak', 0)
                        best_streak = habit.get('best_streak', 0)

                        st.metric("Current Streak", f"{current_streak} days")
                        st.metric("Best Streak", f"{best_streak} days")

                    with col4:
                        if st.button("🗑️", key=f"delete_habit_{habit['id']}", help="Delete habit"):
                            delete_habit(habit['id'])
                            st.success("Habit deleted!")
                            auto_save_data()
                            st.rerun()

                    # Habit tracker visualization (last 30 days)
                    st.markdown("**Last 30 days:**")
                    habit_html = '<div class="habit-tracker">'

                    for i in range(29, -1, -1):  # Last 30 days
                        check_date = (date.today() - timedelta(days=i))
                        date_str = check_date.isoformat()

                        if date_str in completion_dates:
                            css_class = "habit-completed"
                            title = f"Completed on {check_date.strftime('%m/%d')}"
                        else:
                            css_class = "habit-missed" if check_date < date.today() else "habit-pending"
                            title = f"Missed on {check_date.strftime('%m/%d')}" if check_date < date.today() else f"Pending for {check_date.strftime('%m/%d')}"

                        habit_html += f'<div class="habit-day {css_class}" title="{title}"></div>'

                    habit_html += '</div>'
                    st.markdown(habit_html, unsafe_allow_html=True)

                    st.divider()

    with tab2:
        render_habit_insights()

elif st.session_state.current_view == "pomodoro":
    st.markdown('<h1 class="main-header">🍅 Pomodoro Timer</h1>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Timer Settings")
        work_duration = st.slider("Work duration (minutes)", 15, 60,
                                  st.session_state.pomodoro_state.get('duration', 25))
        break_duration = st.slider("Break duration (minutes)", 5, 30, 5)
        long_break = st.slider("Long break duration (minutes)", 15, 60, 30)

        # Sessions counter
        sessions_completed = st.session_state.pomodoro_state.get('sessions_completed', 0)
        st.metric("Sessions Completed Today", sessions_completed)

        # Timer display and controls
        if st.session_state.pomodoro_state.get('active', False):
            elapsed = time.time() - st.session_state.pomodoro_state['start_time']
            duration_seconds = st.session_state.pomodoro_state['duration'] * 60
            remaining = max(0, duration_seconds - elapsed)

            minutes = int(remaining // 60)
            seconds = int(remaining % 60)

            # Progress calculation
            progress = 1 - (remaining / duration_seconds)

            # Timer display
            timer_color = "#e74c3c" if st.session_state.pomodoro_state['current_type'] == 'work' else "#27ae60"

            st.markdown(f"""
            <div class="pomodoro-timer" style="border-color: {timer_color}; color: {timer_color};">
                {minutes:02d}:{seconds:02d}
            </div>
            """, unsafe_allow_html=True)

            # Progress bar
            st.progress(progress)

            current_type = st.session_state.pomodoro_state['current_type']
            st.markdown(f"**Current: {current_type.title()} Session**")

            if remaining <= 0:
                if current_type == 'work':
                    st.session_state.pomodoro_state['sessions_completed'] = sessions_completed + 1
                    create_pomodoro_notification("break")
                    st.balloons()
                    st.success("🎉 Work session completed! Time for a break.")
                else:
                    create_pomodoro_notification("work")
                    st.success("☕ Break time over! Ready for the next work session?")

                st.session_state.pomodoro_state['active'] = False
                auto_save_data()
                st.rerun()

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
            st.markdown(f"""
            <div class="pomodoro-timer" style="border-color: #95a5a6; color: #95a5a6;">
                Ready
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("▶️ Start Work", type="primary", use_container_width=True):
                    st.session_state.pomodoro_state = {
                        'active': True,
                        'start_time': time.time(),
                        'duration': work_duration,
                        'current_type': 'work',
                        'sessions_completed': sessions_completed
                    }
                    st.rerun()

            with col_b:
                if st.button("☕ Short Break", type="secondary", use_container_width=True):
                    st.session_state.pomodoro_state = {
                        'active': True,
                        'start_time': time.time(),
                        'duration': break_duration,
                        'current_type': 'break',
                        'sessions_completed': sessions_completed
                    }
                    st.rerun()

            with col_c:
                if st.button("🛌 Long Break", type="secondary", use_container_width=True):
                    st.session_state.pomodoro_state = {
                        'active': True,
                        'start_time': time.time(),
                        'duration': long_break,
                        'current_type': 'long_break',
                        'sessions_completed': sessions_completed
                    }
                    st.rerun()

    with col2:
        st.markdown("### Current Task Focus")

        pending_tasks = [t for t in st.session_state.tasks
                         if t['status'] == TaskStatus.PENDING.value]

        if pending_tasks:
            current_task = st.selectbox("Select task to focus on",
                                        ["No task selected"] + [t['title'] for t in pending_tasks])

            if current_task != "No task selected":
                task = next((t for t in pending_tasks if t['title'] == current_task), None)
                if task:
                    st.markdown(f"**{task['title']}**")
                    if task.get('description'):
                        st.markdown(task['description'])
                    st.markdown(f"📅 Due: {format_date_display(task['due_date'])}")
                    st.markdown(f"🎯 Priority: {task['priority'].title()}")

                    # Task actions during focus
                    if st.button("✅ Complete Task", use_container_width=True):
                        complete_task(task['id'])
                        st.success("Task completed during focus session!")
                        auto_save_data()
                        st.rerun()
        else:
            st.info("No pending tasks. Create some tasks to focus on!")

        # Pomodoro statistics
        st.markdown("### Today's Focus Stats")
        st.metric("Work Sessions", sessions_completed)

        if sessions_completed > 0:
            total_focus_time = sessions_completed * work_duration
            st.metric("Total Focus Time", f"{total_focus_time} minutes")

            # Recommended break time
            if sessions_completed % 4 == 0:
                st.info("🎯 Consider taking a long break!")
            else:
                st.info("☕ Take a short break after this session")

elif st.session_state.current_view == "statistics":
    st.markdown('<h1 class="main-header">📊 Statistics & Analytics</h1>', unsafe_allow_html=True)

    # Statistics tabs
    tab1, tab2 = st.tabs(["📊 Overview", "🧠 Advanced Analytics"])

    with tab1:
        # Overview metrics
        stats = get_task_stats()
        habit_stats = get_habit_stats()
        insights = get_productivity_insights()

        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Tasks", stats['total'])
        col2.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")
        col3.metric("Tasks Due Today", stats['due_today'])
        col4.metric("Habits Tracked", habit_stats['total'])
        col5.metric("Focus Sessions", st.session_state.pomodoro_state.get('sessions_completed', 0))

        # Charts
        if stats['total'] > 0:
            # Priority distribution
            priority_data = stats['priority_stats']
            if any(priority_data.values()):
                fig = px.pie(
                    values=list(priority_data.values()),
                    names=list(priority_data.keys()),
                    title="Tasks by Priority"
                )
                st.plotly_chart(fig, use_container_width=True)

            # List distribution
            list_data = stats['list_stats']
            if list_data:
                list_names = list(list_data.keys())
                list_totals = [list_data[name]['total'] for name in list_names]

                fig = px.bar(
                    x=list_names,
                    y=list_totals,
                    title="Tasks by List"
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        render_advanced_statistics()

elif st.session_state.current_view == "advanced":
    st.markdown('<h1 class="main-header">🧠 Advanced Features</h1>', unsafe_allow_html=True)

    # Advanced features tabs
    tab1, tab2 = st.tabs(["📋 Eisenhower Matrix", "📊 Data Management"])

    with tab1:
        render_eisenhower_matrix()

    with tab2:
        st.markdown("### 💾 Data Management")

        # Data export/import
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📤 Export Data")

            if st.button("Export as JSON", use_container_width=True):
                export_data_str = export_data("json")
                st.download_button(
                    label="📥 Download Export File",
                    data=export_data_str,
                    file_name=f"ticktick_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

        with col2:
            st.markdown("#### 📥 Import Data")

            uploaded_file = st.file_uploader("Choose backup file", type=['json'])
            if uploaded_file:
                try:
                    import_data_str = uploaded_file.read().decode('utf-8')
                    if st.button("📥 Import Data", use_container_width=True):
                        if import_data(import_data_str, "json"):
                            st.success("Data imported successfully!")
                            auto_save_data()
                            st.rerun()
                        else:
                            st.error("Failed to import data. Please check file format.")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")

elif st.session_state.current_view == "notifications":
    st.markdown('<h1 class="main-header">🔔 Notifications</h1>', unsafe_allow_html=True)
    render_notification_center()

elif st.session_state.current_view == "settings":
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)

    # Settings tabs
    tab1, tab2, tab3 = st.tabs(["🎨 Appearance", "📋 Lists", "🔄 Data"])

    with tab1:
        # App preferences
        st.markdown("### 🎨 Appearance")
        col1, col2 = st.columns(2)
        with col1:
            theme = st.selectbox("Theme", ["Default", "Dark", "Blue"],
                                 index=0, key="theme_select")
        with col2:
            language = st.selectbox("Language", ["English", "Spanish", "French"],
                                    index=0, key="language_select")

        st.markdown("### 🔔 Notifications")
        enable_notifications = st.checkbox("Enable notifications", value=True)
        enable_achievements = st.checkbox("Achievement notifications", value=True)
        enable_reminders = st.checkbox("Habit reminders", value=True)

    with tab2:
        # List management
        st.markdown("### 📁 List Management")

        # Display current lists
        st.write("**Current Lists:**")
        for i, list_name in enumerate(st.session_state.lists):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📋 {list_name}")
            with col2:
                if st.button("Delete", key=f"delete_list_{i}"):
                    # Don't delete if it has tasks
                    list_tasks = [t for t in st.session_state.tasks if t['list_name'] == list_name]
                    if list_tasks:
                        st.error(f"Cannot delete '{list_name}' - it contains {len(list_tasks)} tasks")
                    else:
                        st.session_state.lists.remove(list_name)
                        st.success(f"Deleted list: {list_name}")
                        auto_save_data()
                        st.rerun()

    with tab3:
        # Data management
        st.markdown("### 💾 Data Management")

        # Auto-save settings
        st.markdown("#### ⚙️ Auto-Save")
        auto_save_enabled = st.checkbox("Enable auto-save", value=True)
        if auto_save_enabled:
            auto_save_interval = st.slider("Auto-save interval (seconds)", 10, 300, 30)

        # Reset data
        st.markdown("#### 🔄 Reset Data")
        st.warning("⚠️ This will delete all your tasks, habits, and custom lists!")

        if st.button("🗑️ Reset All Data", type="secondary"):
            if st.checkbox("I understand this will delete all my data", key="confirm_reset"):
                st.session_state.tasks = []
                st.session_state.habits = []
                st.session_state.lists = ["Inbox", "Personal", "Work", "Shopping"]
                st.session_state.pomodoro_state = {
                    'active': False,
                    'start_time': None,
                    'duration': 25,
                    'current_type': 'work',
                    'sessions_completed': 0
                }
                if 'notifications_data' in st.session_state:
                    st.session_state.notifications_data = []
                st.success("All data has been reset!")
                auto_save_data()
                st.rerun()

        # App information
        st.markdown("### ℹ️ About")
        st.info("""
        **TickTick Clone Enhanced v2.0**

        A comprehensive task management application with advanced features.

        ✨ **Features:**
        - ✅ Task management with priorities and due dates
        - 📅 Calendar views and scheduling
        - 🎯 Habit tracking with streaks
        - 🍅 Pomodoro timer for focus sessions
        - 📊 Statistics and productivity insights
        - 🔔 Smart notifications system
        - 🧠 Eisenhower Matrix view
        - 📈 Advanced analytics
        - ⚡ Bulk operations
        - 📋 Task templates
        - 💾 Data persistence and backup

        Created for personal productivity and task organization.
        """)

# Auto-refresh for timer (only when timer is active)
if (st.session_state.current_view == "pomodoro" and
        st.session_state.pomodoro_state.get('active', False)):
    time.sleep(1)
    st.rerun()