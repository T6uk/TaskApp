import time

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from typing import Dict, List, Optional
from utils import *


def render_eisenhower_matrix():
    """Render the Eisenhower Matrix view for task prioritization"""
    st.markdown("### 📋 Eisenhower Matrix")
    st.markdown("*Organize tasks by urgency and importance*")

    tasks = st.session_state.tasks
    today = date.today().isoformat()

    # Categorize tasks
    urgent_important = []  # High priority + due soon
    not_urgent_important = []  # High/Medium priority + not due soon
    urgent_not_important = []  # Low priority + due soon
    not_urgent_not_important = []  # Low priority + not due soon

    for task in tasks:
        if task['status'] == TaskStatus.COMPLETED.value:
            continue

        is_urgent = (task['due_date'] and
                     task['due_date'] <= (date.today() + timedelta(days=2)).isoformat())
        is_important = task['priority'] in ['high', 'medium']

        if is_urgent and is_important:
            urgent_important.append(task)
        elif not is_urgent and is_important:
            not_urgent_important.append(task)
        elif is_urgent and not is_important:
            urgent_not_important.append(task)
        else:
            not_urgent_not_important.append(task)

    # Create 2x2 matrix
    col1, col2 = st.columns(2)

    with col1:
        # Urgent & Important (Do First)
        st.markdown("#### 🔴 Do First")
        st.markdown("*Urgent & Important*")

        with st.container():
            st.markdown(f"**{len(urgent_important)} tasks**")
            for task in urgent_important[:5]:  # Show first 5
                st.markdown(f"• {task['title']}")
                if task['due_date']:
                    st.markdown(f"  📅 {format_date_display(task['due_date'])}")

            if len(urgent_important) > 5:
                st.markdown(f"... and {len(urgent_important) - 5} more")

    with col2:
        # Not Urgent but Important (Schedule)
        st.markdown("#### 🟡 Schedule")
        st.markdown("*Not Urgent & Important*")

        with st.container():
            st.markdown(f"**{len(not_urgent_important)} tasks**")
            for task in not_urgent_important[:5]:
                st.markdown(f"• {task['title']}")
                if task['due_date']:
                    st.markdown(f"  📅 {format_date_display(task['due_date'])}")

            if len(not_urgent_important) > 5:
                st.markdown(f"... and {len(not_urgent_important) - 5} more")

    col3, col4 = st.columns(2)

    with col3:
        # Urgent but Not Important (Delegate)
        st.markdown("#### 🟠 Delegate")
        st.markdown("*Urgent & Not Important*")

        with st.container():
            st.markdown(f"**{len(urgent_not_important)} tasks**")
            for task in urgent_not_important[:5]:
                st.markdown(f"• {task['title']}")
                if task['due_date']:
                    st.markdown(f"  📅 {format_date_display(task['due_date'])}")

            if len(urgent_not_important) > 5:
                st.markdown(f"... and {len(urgent_not_important) - 5} more")

    with col4:
        # Neither Urgent nor Important (Eliminate)
        st.markdown("#### 🟢 Eliminate")
        st.markdown("*Not Urgent & Not Important*")

        with st.container():
            st.markdown(f"**{len(not_urgent_not_important)} tasks**")
            for task in not_urgent_not_important[:5]:
                st.markdown(f"• {task['title']}")
                if task['due_date']:
                    st.markdown(f"  📅 {format_date_display(task['due_date'])}")

            if len(not_urgent_not_important) > 5:
                st.markdown(f"... and {len(not_urgent_not_important) - 5} more")


def render_gantt_chart():
    """Render a Gantt chart view of tasks with due dates"""
    st.markdown("### 📊 Project Timeline")

    # Get tasks with due dates
    tasks_with_dates = [t for t in st.session_state.tasks
                        if t['due_date'] and t['status'] == TaskStatus.PENDING.value]

    if not tasks_with_dates:
        st.info("No tasks with due dates found. Add due dates to see the timeline.")
        return

    # Prepare data for Gantt chart
    df_data = []
    for task in tasks_with_dates:
        start_date = datetime.fromisoformat(task['created_at']).date()
        end_date = datetime.fromisoformat(task['due_date']).date()

        df_data.append({
            'Task': task['title'][:30] + "..." if len(task['title']) > 30 else task['title'],
            'Start': start_date,
            'Finish': end_date,
            'Priority': task['priority'].title(),
            'List': task['list_name']
        })

    if df_data:
        df = pd.DataFrame(df_data)

        # Create Gantt chart
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task",
                          color="Priority", title="Task Timeline",
                          color_discrete_map={
                              'High': '#e74c3c',
                              'Medium': '#f39c12',
                              'Low': '#3498db',
                              'None': '#95a5a6'
                          })

        fig.update_yaxes(categoryorder="total ascending")
        fig.update_layout(height=max(400, len(df_data) * 30))
        st.plotly_chart(fig, use_container_width=True)


def render_weekly_planner():
    """Render a weekly planner view"""
    st.markdown("### 📅 Weekly Planner")

    # Week navigation
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Previous Week"):
            if 'current_week_offset' not in st.session_state:
                st.session_state.current_week_offset = 0
            st.session_state.current_week_offset -= 1
            st.rerun()

    with col2:
        week_offset = getattr(st.session_state, 'current_week_offset', 0)
        current_week_start = date.today() - timedelta(days=date.today().weekday()) + timedelta(weeks=week_offset)
        st.markdown(f"**Week of {current_week_start.strftime('%B %d, %Y')}**")

    with col3:
        if st.button("Next Week →"):
            if 'current_week_offset' not in st.session_state:
                st.session_state.current_week_offset = 0
            st.session_state.current_week_offset += 1
            st.rerun()

    # Create weekly grid
    week_days = [current_week_start + timedelta(days=i) for i in range(7)]

    cols = st.columns(7)

    for i, day in enumerate(week_days):
        with cols[i]:
            is_today = day == date.today()
            day_name = day.strftime('%A')

            # Header
            if is_today:
                st.markdown(f"**🔸 {day_name[:3]}**")
                st.markdown(f"**{day.strftime('%m/%d')}**")
            else:
                st.markdown(f"**{day_name[:3]}**")
                st.markdown(f"{day.strftime('%m/%d')}")

            # Tasks for this day
            day_tasks = [t for t in st.session_state.tasks
                         if t['due_date'] == day.isoformat()]

            # Show existing tasks
            for task in day_tasks:
                priority_emoji = {
                    "high": "🔴", "medium": "🟡",
                    "low": "🔵", "none": "⚪"
                }.get(task['priority'], "⚪")

                status_emoji = "✅" if task['status'] == TaskStatus.COMPLETED.value else "⭕"

                st.markdown(f"{status_emoji}{priority_emoji}")
                st.markdown(f"**{task['title'][:20]}...**" if len(task['title']) > 20 else f"**{task['title']}**")
                st.markdown(f"<small>{task['list_name']}</small>", unsafe_allow_html=True)

            # Quick add task for this day
            with st.expander(f"➕ Add task"):
                task_title = st.text_input("Task", key=f"quick_task_{day.isoformat()}")
                if st.button("Add", key=f"add_task_{day.isoformat()}"):
                    if task_title:
                        add_task(task_title, due_date=day)
                        st.success("Task added!")
                        st.rerun()


def render_focus_mode():
    """Render a distraction-free focus mode"""
    st.markdown("### 🎯 Focus Mode")
    st.markdown("*Minimize distractions and focus on what matters*")

    # Get high priority tasks due today or overdue
    today = date.today().isoformat()
    focus_tasks = []

    for task in st.session_state.tasks:
        if task['status'] == TaskStatus.COMPLETED.value:
            continue

        # High priority tasks
        if task['priority'] == 'high':
            focus_tasks.append(task)
        # Tasks due today
        elif task['due_date'] == today:
            focus_tasks.append(task)
        # Overdue tasks
        elif task['due_date'] and task['due_date'] < today:
            focus_tasks.append(task)

    # Remove duplicates
    seen_ids = set()
    unique_focus_tasks = []
    for task in focus_tasks:
        if task['id'] not in seen_ids:
            unique_focus_tasks.append(task)
            seen_ids.add(task['id'])

    if not unique_focus_tasks:
        st.info("🎉 Great! No urgent tasks found. You can focus on long-term goals.")
        return

    st.markdown(f"### 🚨 {len(unique_focus_tasks)} tasks need your attention")

    # Focus task display
    for i, task in enumerate(unique_focus_tasks[:5]):  # Show max 5 tasks
        priority_color = get_priority_color(task['priority'])

        with st.container():
            col1, col2, col3 = st.columns([0.5, 4, 1])

            with col1:
                if st.checkbox("", key=f"focus_complete_{task['id']}"):
                    complete_task(task['id'])
                    st.balloons()
                    st.success("Task completed! 🎉")
                    st.rerun()

            with col2:
                st.markdown(f"### {i + 1}. {task['title']}")
                if task['description']:
                    st.markdown(task['description'])

                # Task metadata
                col_a, col_b, col_c = st.columns(3)
                col_a.markdown(f"📋 {task['list_name']}")
                col_b.markdown(f"📅 {format_date_display(task['due_date'])}")
                col_c.markdown(f"🎯 {task['priority'].title()}")

            with col3:
                # Start Pomodoro for this task
                if st.button("🍅 Focus", key=f"focus_pomodoro_{task['id']}"):
                    st.session_state.pomodoro_state = {
                        'active': True,
                        'start_time': time.time(),
                        'duration': 25,
                        'current_type': 'work',
                        'current_task': task['title']
                    }
                    st.session_state.current_view = "pomodoro"
                    st.rerun()

        st.divider()


def render_habit_insights():
    """Render detailed habit analytics"""
    st.markdown("### 📈 Habit Analytics")

    if not st.session_state.habits:
        st.info("No habits to analyze. Create some habits first!")
        return

    # Overall habit statistics
    total_habits = len(st.session_state.habits)
    today = date.today().isoformat()
    completed_today = sum(1 for h in st.session_state.habits if today in h['completion_dates'])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Habits", total_habits)
    col2.metric("Completed Today", completed_today)
    col3.metric("Completion Rate", f"{(completed_today / total_habits * 100):.1f}%" if total_habits > 0 else "0%")

    # Habit performance over time
    st.markdown("#### 📊 30-Day Habit Performance")

    # Create heatmap data
    habits_data = []
    dates = []

    # Last 30 days
    for i in range(29, -1, -1):
        check_date = date.today() - timedelta(days=i)
        dates.append(check_date.strftime('%m/%d'))

        day_completions = []
        for habit in st.session_state.habits:
            date_str = check_date.isoformat()
            completed = 1 if date_str in habit['completion_dates'] else 0
            day_completions.append(completed)

        habits_data.append(day_completions)

    if habits_data:
        # Create heatmap
        habit_names = [h['name'][:20] + "..." if len(h['name']) > 20 else h['name']
                       for h in st.session_state.habits]

        fig = go.Figure(data=go.Heatmap(
            z=list(zip(*habits_data)),  # Transpose for correct orientation
            x=dates,
            y=habit_names,
            colorscale='RdYlGn',
            showscale=True,
            hovertemplate='Date: %{x}<br>Habit: %{y}<br>Completed: %{z}<extra></extra>'
        ))

        fig.update_layout(
            title="Habit Completion Heatmap (Last 30 Days)",
            height=max(300, len(habit_names) * 40),
            xaxis_title="Date",
            yaxis_title="Habits"
        )

        st.plotly_chart(fig, use_container_width=True)

    # Individual habit statistics
    st.markdown("#### 📋 Individual Habit Performance")

    for habit in st.session_state.habits:
        with st.expander(f"📊 {habit['name']} Analytics"):
            col1, col2, col3, col4 = st.columns(4)

            # Calculate statistics
            total_days = (date.today() - datetime.fromisoformat(habit['created_at']).date()).days + 1
            completed_days = len(habit['completion_dates'])
            completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
            current_streak = habit.get('streak', 0)
            best_streak = habit.get('best_streak', 0)

            col1.metric("Completion Rate", f"{completion_rate:.1f}%")
            col2.metric("Total Completions", completed_days)
            col3.metric("Current Streak", f"{current_streak} days")
            col4.metric("Best Streak", f"{best_streak} days")

            # Weekly completion pattern
            weekly_pattern = {day: 0 for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}

            for date_str in habit['completion_dates']:
                try:
                    habit_date = datetime.fromisoformat(date_str)
                    day_name = habit_date.strftime('%a')
                    weekly_pattern[day_name] += 1
                except:
                    continue

            if sum(weekly_pattern.values()) > 0:
                fig = px.bar(
                    x=list(weekly_pattern.keys()),
                    y=list(weekly_pattern.values()),
                    title=f"Weekly Pattern for {habit['name']}",
                    labels={'x': 'Day of Week', 'y': 'Completions'}
                )
                st.plotly_chart(fig, use_container_width=True)


def render_advanced_statistics():
    """Render advanced analytics and insights"""
    st.markdown("### 🧠 Advanced Analytics")

    tasks = st.session_state.tasks

    if not tasks:
        st.info("No data available for analysis. Create some tasks first!")
        return

    # Task completion velocity
    st.markdown("#### 📈 Productivity Trends")

    # Daily completion counts for last 30 days
    daily_completions = {}
    for i in range(30):
        check_date = (date.today() - timedelta(days=i)).isoformat()
        daily_completions[check_date] = 0

    for task in tasks:
        if task['completed_at']:
            try:
                completed_date = datetime.fromisoformat(task['completed_at']).date().isoformat()
                if completed_date in daily_completions:
                    daily_completions[completed_date] += 1
            except:
                continue

    # Create trend chart
    dates = sorted(daily_completions.keys())
    completions = [daily_completions[d] for d in dates]
    formatted_dates = [datetime.fromisoformat(d).strftime('%m/%d') for d in dates]

    fig = px.line(
        x=formatted_dates,
        y=completions,
        title="Daily Task Completions (Last 30 Days)",
        labels={'x': 'Date', 'y': 'Tasks Completed'}
    )
    fig.add_hline(y=sum(completions) / len(completions), line_dash="dash",
                  annotation_text="Average", annotation_position="bottom right")

    st.plotly_chart(fig, use_container_width=True)

    # Task creation vs completion analysis
    col1, col2 = st.columns(2)

    with col1:
        # Tasks created by hour
        creation_hours = []
        for task in tasks:
            try:
                created_time = datetime.fromisoformat(task['created_at'])
                creation_hours.append(created_time.hour)
            except:
                continue

        if creation_hours:
            hour_counts = {h: creation_hours.count(h) for h in range(24)}

            fig = px.bar(
                x=list(hour_counts.keys()),
                y=list(hour_counts.values()),
                title="Tasks Created by Hour of Day",
                labels={'x': 'Hour', 'y': 'Tasks Created'}
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Task completion time analysis
        completion_times = []
        for task in tasks:
            if task['completed_at'] and task['created_at']:
                try:
                    created = datetime.fromisoformat(task['created_at'])
                    completed = datetime.fromisoformat(task['completed_at'])
                    completion_time = (completed - created).days
                    completion_times.append(completion_time)
                except:
                    continue

        if completion_times:
            avg_completion = sum(completion_times) / len(completion_times)

            fig = px.histogram(
                x=completion_times,
                title="Task Completion Time Distribution",
                labels={'x': 'Days to Complete', 'y': 'Number of Tasks'},
                nbins=20
            )
            fig.add_vline(x=avg_completion, line_dash="dash",
                          annotation_text=f"Avg: {avg_completion:.1f} days")

            st.plotly_chart(fig, use_container_width=True)

    # Productivity score calculation
    st.markdown("#### 🏆 Productivity Score")

    # Calculate various metrics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t['status'] == TaskStatus.COMPLETED.value])
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # On-time completion rate
    on_time_completions = 0
    total_with_due_dates = 0

    for task in tasks:
        if task['due_date'] and task['completed_at']:
            total_with_due_dates += 1
            try:
                due_date = datetime.fromisoformat(task['due_date']).date()
                completed_date = datetime.fromisoformat(task['completed_at']).date()
                if completed_date <= due_date:
                    on_time_completions += 1
            except:
                continue

    on_time_rate = (on_time_completions / total_with_due_dates * 100) if total_with_due_dates > 0 else 0

    # High priority completion rate
    high_priority_tasks = [t for t in tasks if t['priority'] == 'high']
    high_priority_completed = [t for t in high_priority_tasks if t['status'] == TaskStatus.COMPLETED.value]
    high_priority_rate = (len(high_priority_completed) / len(high_priority_tasks) * 100) if high_priority_tasks else 0

    # Overall productivity score (weighted average)
    productivity_score = (completion_rate * 0.4 + on_time_rate * 0.4 + high_priority_rate * 0.2)

    # Display score with color coding
    if productivity_score >= 80:
        score_color = "🟢"
        score_text = "Excellent"
    elif productivity_score >= 60:
        score_color = "🟡"
        score_text = "Good"
    else:
        score_color = "🔴"
        score_text = "Needs Improvement"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Productivity Score", f"{productivity_score:.1f}", f"{score_color} {score_text}")
    col2.metric("Completion Rate", f"{completion_rate:.1f}%")
    col3.metric("On-Time Rate", f"{on_time_rate:.1f}%")
    col4.metric("High Priority Rate", f"{high_priority_rate:.1f}%")


def render_bulk_operations():
    """Render bulk operations interface"""
    st.markdown("### ⚡ Bulk Operations")
    st.markdown("*Manage multiple tasks at once*")

    # Select tasks for bulk operations
    tasks = [t for t in st.session_state.tasks if t['status'] == TaskStatus.PENDING.value]

    if not tasks:
        st.info("No pending tasks available for bulk operations.")
        return

    # Task selection
    st.markdown("#### Select Tasks")
    selected_tasks = []

    # Select all checkbox
    select_all = st.checkbox("Select All Tasks")

    if select_all:
        selected_tasks = [t['id'] for t in tasks]
    else:
        # Individual task selection
        for task in tasks[:20]:  # Show first 20 tasks
            if st.checkbox(f"{task['title']} - {task['list_name']}", key=f"bulk_select_{task['id']}"):
                selected_tasks.append(task['id'])

    if selected_tasks:
        st.markdown(f"**{len(selected_tasks)} tasks selected**")

        # Bulk operations
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Bulk complete
            if st.button("✅ Complete Selected", type="primary"):
                for task_id in selected_tasks:
                    complete_task(task_id)
                st.success(f"Completed {len(selected_tasks)} tasks!")
                st.rerun()

        with col2:
            # Bulk delete
            if st.button("🗑️ Delete Selected", type="secondary"):
                for task_id in selected_tasks:
                    delete_task(task_id)
                st.success(f"Deleted {len(selected_tasks)} tasks!")
                st.rerun()

        with col3:
            # Bulk move to list
            target_list = st.selectbox("Move to List", st.session_state.lists, key="bulk_move_list")
            if st.button("📋 Move Selected"):
                for task_id in selected_tasks:
                    update_task(task_id, list_name=target_list)
                st.success(f"Moved {len(selected_tasks)} tasks to {target_list}!")
                st.rerun()

        with col4:
            # Bulk set priority
            target_priority = st.selectbox("Set Priority",
                                           [p.value for p in Priority],
                                           format_func=lambda x: x.title(),
                                           key="bulk_priority")
            if st.button("🎯 Set Priority"):
                for task_id in selected_tasks:
                    update_task(task_id, priority=target_priority)
                st.success(f"Updated priority for {len(selected_tasks)} tasks!")
                st.rerun()


def render_task_templates():
    """Render task templates functionality"""
    st.markdown("### 📋 Task Templates")
    st.markdown("*Create reusable task templates for common workflows*")

    # Initialize templates in session state
    if 'task_templates' not in st.session_state:
        st.session_state.task_templates = [
            {
                'name': 'Daily Review',
                'tasks': [
                    {'title': 'Check emails', 'priority': 'medium'},
                    {'title': 'Review calendar for tomorrow', 'priority': 'low'},
                    {'title': 'Update task priorities', 'priority': 'low'}
                ]
            },
            {
                'name': 'Weekly Planning',
                'tasks': [
                    {'title': 'Review weekly goals', 'priority': 'high'},
                    {'title': 'Plan next week schedule', 'priority': 'medium'},
                    {'title': 'Clear completed tasks', 'priority': 'low'}
                ]
            }
        ]

    # Display existing templates
    st.markdown("#### 📚 Available Templates")

    for i, template in enumerate(st.session_state.task_templates):
        with st.expander(f"📋 {template['name']} ({len(template['tasks'])} tasks)"):
            # Show template tasks
            for task in template['tasks']:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🔵", "none": "⚪"}.get(task['priority'], "⚪")
                st.markdown(f"{priority_emoji} {task['title']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✨ Use Template", key=f"use_template_{i}"):
                    # Create tasks from template
                    target_list = st.selectbox("Add to list", st.session_state.lists,
                                               key=f"template_list_{i}")

                    for task in template['tasks']:
                        add_task(task['title'], priority=Priority(task['priority']),
                                 list_name=target_list)

                    st.success(f"Created {len(template['tasks'])} tasks from template!")
                    st.rerun()

            with col2:
                if st.button(f"🗑️ Delete Template", key=f"delete_template_{i}"):
                    st.session_state.task_templates.pop(i)
                    st.success("Template deleted!")
                    st.rerun()

    # Create new template
    st.markdown("#### ➕ Create New Template")

    with st.form("new_template_form"):
        template_name = st.text_input("Template Name")

        st.markdown("**Tasks in Template:**")
        num_tasks = st.number_input("Number of tasks", min_value=1, max_value=10, value=3)

        template_tasks = []
        for i in range(num_tasks):
            col1, col2 = st.columns([3, 1])
            with col1:
                task_title = st.text_input(f"Task {i + 1}", key=f"template_task_{i}")
            with col2:
                task_priority = st.selectbox(f"Priority",
                                             [p.value for p in Priority],
                                             format_func=lambda x: x.title(),
                                             key=f"template_priority_{i}")

            if task_title:
                template_tasks.append({'title': task_title, 'priority': task_priority})

        if st.form_submit_button("Create Template"):
            if template_name and template_tasks:
                st.session_state.task_templates.append({
                    'name': template_name,
                    'tasks': template_tasks
                })
                st.success("Template created!")
                st.rerun()