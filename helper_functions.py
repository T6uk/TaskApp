import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import calendar
from typing import Dict, List, Optional, Tuple
from utils import *
from advanced_features import *


def render_advanced_search_interface():
    """Advanced search interface with multiple criteria"""
    st.markdown("### 🔍 Advanced Search")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Search query with syntax help
        search_query = st.text_input(
            "Search Query",
            placeholder="title:meeting priority:high #urgent list:work",
            help="Search syntax: title:text, priority:high/medium/low, #tag, list:name, status:pending/completed"
        )

        # Quick search templates
        search_templates = {
            "High Priority Due Today": "priority:high due:today",
            "Overdue Tasks": "status:pending overdue:true",
            "Work Tasks This Week": "list:work due:week",
            "Untagged Tasks": "tags:none",
            "Long Running Tasks": "created:>7days status:pending"
        }

        selected_template = st.selectbox("Quick Templates",
                                         ["Custom"] + list(search_templates.keys()))

        if selected_template != "Custom":
            search_query = search_templates[selected_template]

    with col2:
        # Search options
        st.markdown("**Search Options**")
        case_sensitive = st.checkbox("Case sensitive", value=False)
        include_description = st.checkbox("Search descriptions", value=True)
        include_completed = st.checkbox("Include completed", value=False)

        # Date range filter
        date_range = st.date_input("Date range", value=[], key="search_date_range")

    # Execute search
    if st.button("🔍 Search", type="primary") or search_query:
        # Build search filter
        search_filter = TaskFilter(
            search_query=search_query if search_query else None,
            due_date_range=tuple(date_range) if len(date_range) == 2 else None
        )

        if not include_completed:
            search_filter.status = TaskStatus.PENDING.value

        # Perform search
        results = get_tasks_by_filter(search_filter)

        st.markdown(f"### 📋 Search Results ({len(results)} found)")

        if results:
            # Results summary
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Results", len(results))
            col2.metric("High Priority", len([t for t in results if t['priority'] == 'high']))
            col3.metric("Due Soon", len([t for t in results if t.get('due_date') and
                                         datetime.fromisoformat(t['due_date']).date() <= date.today() + timedelta(
                days=3)]))
            col4.metric("Overdue", len([t for t in results if t.get('due_date') and
                                        datetime.fromisoformat(t['due_date']).date() < date.today()]))

            # Display results
            for task in results:
                render_enhanced_task_card(task)
        else:
            st.info("No tasks found matching your search criteria.")


def render_monthly_calendar_grid(current_date: date, show_completed: bool, color_by: str):
    """Render monthly calendar grid with tasks"""

    # Get month boundaries
    month_start = current_date.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

    # Get tasks for the month
    month_tasks = {}
    task_filter = TaskFilter()
    if not show_completed:
        task_filter.status = TaskStatus.PENDING.value

    for task in get_tasks_by_filter(task_filter):
        if task.get('due_date'):
            try:
                task_date = datetime.fromisoformat(task['due_date']).date()
                if month_start <= task_date <= month_end:
                    date_str = task_date.isoformat()
                    if date_str not in month_tasks:
                        month_tasks[date_str] = []
                    month_tasks[date_str].append(task)
            except (ValueError, TypeError):
                continue

    # Calendar header
    st.markdown(f"### {calendar.month_name[current_date.month]} {current_date.year}")

    # Days of week header
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Create calendar grid
    cal = calendar.monthcalendar(current_date.year, current_date.month)

    # Header row
    cols = st.columns(7)
    for i, day in enumerate(days_of_week):
        cols[i].markdown(f"**{day[:3]}**")

    # Calendar rows
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
                    # Day header with styling
                    if is_today:
                        st.markdown(f"**🔸 {day}**")
                    else:
                        st.markdown(f"**{day}**")

                    # Show tasks for this day
                    if date_str in month_tasks:
                        tasks_today = month_tasks[date_str][:3]  # Show max 3 tasks

                        for task in tasks_today:
                            # Color coding based on selection
                            if color_by == "Priority":
                                color = get_priority_color(task['priority'])
                            elif color_by == "List":
                                color = get_list_color(task['list_name'])
                            else:
                                color = get_status_color(task['status'])

                            status_icon = "✅" if task['status'] == TaskStatus.COMPLETED.value else "⭕"

                            st.markdown(f"""
                            <div style="background: {color}; color: white; padding: 2px 4px; 
                                      border-radius: 4px; margin: 2px 0; font-size: 10px;">
                                {status_icon} {task['title'][:15]}{'...' if len(task['title']) > 15 else ''}
                            </div>
                            """, unsafe_allow_html=True)

                        if len(month_tasks[date_str]) > 3:
                            st.markdown(f"<small>+{len(month_tasks[date_str]) - 3} more</small>",
                                        unsafe_allow_html=True)


def render_task_details_modal(task: Dict):
    """Render detailed task information in an expandable section"""

    with st.expander(f"📋 Task Details: {task['title']}", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📝 Basic Information")
            st.write(f"**Title:** {task['title']}")
            st.write(f"**Status:** {task['status'].title()}")
            st.write(f"**Priority:** {task['priority'].title()}")
            st.write(f"**List:** {task['list_name']}")

            if task.get('description'):
                st.write(f"**Description:** {task['description']}")

            if task.get('tags'):
                tags_display = ", ".join(task['tags'])
                st.write(f"**Tags:** {tags_display}")

        with col2:
            st.markdown("#### ⏰ Timing Information")
            st.write(f"**Created:** {format_date_display(task['created_at'])}")

            if task.get('updated_at'):
                st.write(f"**Updated:** {format_date_display(task['updated_at'])}")

            if task.get('due_date'):
                st.write(f"**Due Date:** {format_date_display(task['due_date'])}")

            if task.get('completed_at'):
                st.write(f"**Completed:** {format_date_display(task['completed_at'])}")

            # Time tracking
            if task.get('estimated_time'):
                est_hours = task['estimated_time'] / 60
                st.write(f"**Estimated Time:** {est_hours:.1f} hours")

            if task.get('actual_time'):
                act_hours = task['actual_time'] / 60
                st.write(f"**Actual Time:** {act_hours:.1f} hours")

        # Subtasks section
        if task.get('subtasks'):
            st.markdown("#### ✅ Subtasks")
            for i, subtask in enumerate(task['subtasks']):
                if isinstance(subtask, dict):
                    checked = subtask.get('completed', False)
                    if st.checkbox(subtask.get('text', f'Subtask {i + 1}'),
                                   value=checked,
                                   key=f"subtask_{task['id']}_{i}"):
                        if not checked:  # Just got checked
                            toggle_subtask(task['id'], subtask.get('id'))
                            st.rerun()
                    elif checked:  # Just got unchecked
                        toggle_subtask(task['id'], subtask.get('id'))
                        st.rerun()
                else:
                    st.write(f"• {subtask}")

        # Notes and history
        if task.get('notes'):
            st.markdown("#### 📝 Notes & History")
            for note in task['notes']:
                if isinstance(note, dict):
                    timestamp = datetime.fromisoformat(note['timestamp']).strftime('%m/%d %H:%M')
                    note_type = note.get('type', 'note').title()
                    st.write(f"**{timestamp} - {note_type}:** {note.get('note', note.get('changes', 'N/A'))}")


def render_current_task_focus():
    """Render current task focus section for Pomodoro"""

    st.markdown("### 🎯 Current Focus")

    current_task_id = st.session_state.pomodoro_state.get('current_task_id')

    if current_task_id:
        # Show current task details
        current_task = get_task_by_id(current_task_id)
        if current_task:
            st.markdown(f"**📋 {current_task['title']}**")
            if current_task.get('description'):
                st.markdown(f"*{current_task['description']}*")
            st.markdown(f"🎯 Priority: {current_task['priority'].title()}")
            st.markdown(f"📅 Due: {format_date_display(current_task['due_date'])}")

            if st.button("✅ Complete Task", use_container_width=True):
                complete_task(current_task_id)
                st.success("Task completed during focus session! 🎉")
                auto_save_data()
                st.rerun()
    else:
        # Select task to focus on
        pending_tasks = [t for t in st.session_state.tasks
                         if t['status'] == TaskStatus.PENDING.value]

        if pending_tasks:
            task_options = ["No specific task"] + [f"{t['title']} ({t['list_name']})" for t in pending_tasks]
            selected_task = st.selectbox("Select task to focus on", task_options)

            if selected_task != "No specific task":
                task_index = task_options.index(selected_task) - 1
                selected_task_obj = pending_tasks[task_index]

                if st.button("🎯 Set Focus Task", use_container_width=True):
                    st.session_state.pomodoro_state['current_task_id'] = selected_task_obj['id']
                    st.session_state.pomodoro_state['current_task'] = selected_task_obj['title']
                    st.rerun()
        else:
            st.info("No pending tasks. Create some tasks to focus on!")


def render_productivity_overview():
    """Render productivity overview dashboard"""

    # Time period selection
    col1, col2, col3 = st.columns(3)
    with col1:
        time_period = st.selectbox("Time Period", [7, 14, 30, 60, 90],
                                   format_func=lambda x: f"Last {x} days", index=2)
    with col2:
        comparison_enabled = st.checkbox("Compare with previous period", value=True)
    with col3:
        show_predictions = st.checkbox("Show trend predictions", value=True)

    # Calculate metrics
    tasks = st.session_state.tasks
    habits = st.session_state.habits

    end_date = date.today()
    start_date = end_date - timedelta(days=time_period)

    # Current period metrics
    current_metrics = ProductivityMetricsAnalyzer.calculate_comprehensive_metrics(
        tasks, habits, time_period
    )

    # Previous period metrics for comparison
    prev_metrics = None
    if comparison_enabled:
        prev_end_date = start_date
        prev_start_date = prev_end_date - timedelta(days=time_period)
        # Filter tasks for previous period
        prev_tasks = [t for t in tasks if ProductivityMetricsAnalyzer._is_in_period(t, prev_start_date, prev_end_date)]
        prev_metrics = ProductivityMetricsAnalyzer.calculate_comprehensive_metrics(
            prev_tasks, habits, time_period
        )

    # Main metrics display
    st.markdown("### 📊 Productivity Overview")

    # Key metrics cards
    col1, col2, col3, col4, col5 = st.columns(5)

    overall_score = current_metrics.get('overall_score', 0)
    task_metrics = current_metrics.get('task_metrics', {})

    with col1:
        delta = None
        if prev_metrics:
            prev_score = prev_metrics.get('overall_score', 0)
            delta = overall_score - prev_score
        st.metric("Overall Score", f"{overall_score:.1f}", delta=f"{delta:+.1f}" if delta else None)

    with col2:
        completion_rate = task_metrics.get('completion_rate', 0)
        delta = None
        if prev_metrics:
            prev_rate = prev_metrics.get('task_metrics', {}).get('completion_rate', 0)
            delta = completion_rate - prev_rate
        st.metric("Completion Rate", f"{completion_rate:.1f}%", delta=f"{delta:+.1f}%" if delta else None)

    with col3:
        completed_tasks = task_metrics.get('completed_tasks', 0)
        st.metric("Tasks Completed", completed_tasks)

    with col4:
        overdue_tasks = task_metrics.get('overdue_tasks', 0)
        st.metric("Overdue Tasks", overdue_tasks)

    with col5:
        habit_metrics = current_metrics.get('habit_metrics', {})
        avg_habit_rate = 0
        if habit_metrics.get('completion_rates'):
            avg_habit_rate = sum(habit_metrics['completion_rates'].values()) / len(habit_metrics['completion_rates'])
        st.metric("Habit Success", f"{avg_habit_rate:.1f}%")

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        # Task completion trend
        st.markdown("#### 📈 Task Completion Trend")

        # Generate daily completion data for the period
        daily_completions = {}
        for i in range(time_period):
            check_date = start_date + timedelta(days=i)
            daily_completions[check_date.isoformat()] = 0

        for task in tasks:
            if task['status'] == TaskStatus.COMPLETED.value and task.get('completed_at'):
                try:
                    completed_date = datetime.fromisoformat(task['completed_at']).date()
                    if start_date <= completed_date <= end_date:
                        daily_completions[completed_date.isoformat()] += 1
                except (ValueError, TypeError):
                    continue

        # Create trend chart
        dates = list(daily_completions.keys())
        completions = list(daily_completions.values())

        fig = px.line(x=dates, y=completions, title="Daily Task Completions",
                      labels={'x': 'Date', 'y': 'Tasks Completed'})

        # Add trend line
        if len(completions) > 1:
            z = np.polyfit(range(len(completions)), completions, 1)
            trend_line = np.poly1d(z)(range(len(completions)))
            fig.add_trace(go.Scatter(x=dates, y=trend_line, mode='lines',
                                     name='Trend', line=dict(dash='dash')))

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Priority distribution
        st.markdown("#### 🎯 Priority Distribution")

        priority_data = task_metrics.get('priority_breakdown', {})
        if priority_data:
            fig = px.pie(values=list(priority_data.values()),
                         names=[p.title() for p in priority_data.keys()],
                         title="Tasks by Priority",
                         color_discrete_map={
                             'High': '#FF6B6B',
                             'Medium': '#FFD93D',
                             'Low': '#4ECDC4',
                             'None': '#95A5A6'
                         })
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No priority data available")

    # Insights and recommendations
    st.markdown("### 💡 Insights & Recommendations")

    insights = []

    # Score-based insights
    if overall_score >= 85:
        insights.append("🌟 Excellent productivity! You're performing at a very high level.")
    elif overall_score >= 70:
        insights.append("👍 Good productivity levels. Look for specific areas to optimize.")
    elif overall_score >= 50:
        insights.append("📈 Room for improvement. Focus on task completion and consistency.")
    else:
        insights.append("⚠️ Low productivity score. Consider reviewing your task management approach.")

    # Trend insights
    if prev_metrics:
        score_change = overall_score - prev_metrics.get('overall_score', 0)
        if score_change > 5:
            insights.append(f"📈 Great improvement! Your score increased by {score_change:.1f} points.")
        elif score_change < -5:
            insights.append(f"📉 Score decreased by {abs(score_change):.1f} points. Consider what changed.")

    # Task-specific insights
    if overdue_tasks > 0:
        insights.append(f"⏰ You have {overdue_tasks} overdue tasks. Consider using Focus Mode to catch up.")

    if completion_rate > 80:
        insights.append("✅ Excellent completion rate! You're staying on top of your commitments.")

    for insight in insights:
        st.info(insight)


def render_goal_tracking_interface():
    """Render goal tracking and management interface"""

    st.markdown("### 🎯 Goal Tracking")

    # Initialize goals in session state
    if 'productivity_goals' not in st.session_state:
        st.session_state.productivity_goals = []

    # Add new goal
    with st.expander("➕ Add New Goal", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            goal_title = st.text_input("Goal title", placeholder="Complete 50 tasks this month")
        with col2:
            goal_type = st.selectbox("Goal type",
                                     ["tasks_completed", "habit_streaks", "focus_time", "completion_rate"])
        with col3:
            target_value = st.number_input("Target value", min_value=1, value=10)
        with col4:
            deadline = st.date_input("Deadline", value=date.today() + timedelta(days=30))

        goal_description = st.text_area("Description (optional)",
                                        placeholder="Describe your goal and why it's important...")

        if st.button("🎯 Create Goal", type="primary"):
            if goal_title:
                new_goal = ProductivityGoal(
                    id=str(uuid.uuid4()),
                    title=goal_title,
                    description=goal_description,
                    target_value=target_value,
                    current_value=0,
                    metric_type=goal_type,
                    deadline=deadline,
                    created_at=datetime.now()
                )
                st.session_state.productivity_goals.append(new_goal.__dict__)
                st.success("Goal created! 🎯")
                st.rerun()

    # Display existing goals
    if not st.session_state.productivity_goals:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #6b7280;">
            <div style="font-size: 48px; margin-bottom: 16px;">🎯</div>
            <div style="font-size: 18px; margin-bottom: 8px;">No goals set yet</div>
            <div style="font-size: 14px;">Create your first goal above to start tracking your progress!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for goal in st.session_state.productivity_goals:
            render_goal_card(goal)


def render_goal_card(goal: Dict):
    """Render individual goal card with progress tracking"""

    # Calculate current progress
    current_value = calculate_goal_progress(goal)
    progress_pct = min(100, (current_value / goal['target_value']) * 100)

    # Time progress
    created_date = datetime.fromisoformat(goal['created_at']).date()
    deadline_date = datetime.fromisoformat(goal['deadline']).date() if isinstance(goal['deadline'], str) else goal[
        'deadline']
    total_days = (deadline_date - created_date).days
    days_remaining = (deadline_date - date.today()).days
    time_progress = max(0, (total_days - days_remaining) / total_days * 100) if total_days > 0 else 100

    # Status determination
    if progress_pct >= 100:
        status = "completed"
        status_icon = "✅"
        status_color = "#10b981"
    elif days_remaining < 0:
        status = "overdue"
        status_icon = "⏰"
        status_color = "#ef4444"
    elif progress_pct >= time_progress:
        status = "on_track"
        status_icon = "📈"
        status_color = "#3b82f6"
    else:
        status = "behind"
        status_icon = "⚠️"
        status_color = "#f59e0b"

    with st.container():
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 16px 0; 
                  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 4px solid {status_color};">
            <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 16px;">
                <div style="flex: 1;">
                    <h3 style="margin: 0; color: #1f2937; display: flex; align-items: center;">
                        {status_icon} {goal['title']}
                    </h3>
                    <p style="margin: 4px 0; color: #6b7280; font-size: 14px;">
                        {goal.get('description', 'No description provided')}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Progress", f"{current_value}/{goal['target_value']}",
                      delta=f"{progress_pct:.1f}%")

        with col2:
            st.metric("Days Remaining", max(0, days_remaining))

        with col3:
            st.metric("Status", status.replace('_', ' ').title())

        with col4:
            if st.button("🗑️", key=f"delete_goal_{goal['id']}", help="Delete goal"):
                st.session_state.productivity_goals = [g for g in st.session_state.productivity_goals
                                                       if g['id'] != goal['id']]
                st.rerun()

        # Progress bars
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Goal Progress**")
            st.markdown(f"""
            <div style="background: #e5e7eb; border-radius: 10px; overflow: hidden; height: 8px;">
                <div style="height: 100%; background: {status_color}; width: {progress_pct}%; 
                          transition: width 0.5s ease; border-radius: 10px;"></div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("**Time Progress**")
            st.markdown(f"""
            <div style="background: #e5e7eb; border-radius: 10px; overflow: hidden; height: 8px;">
                <div style="height: 100%; background: #6b7280; width: {time_progress}%; 
                          transition: width 0.5s ease; border-radius: 10px;"></div>
            </div>
            """, unsafe_allow_html=True)


def calculate_goal_progress(goal: Dict) -> int:
    """Calculate current progress towards a goal"""

    metric_type = goal['metric_type']
    created_date = datetime.fromisoformat(goal['created_at']).date()

    if metric_type == "tasks_completed":
        # Count completed tasks since goal creation
        completed_count = 0
        for task in st.session_state.tasks:
            if task['status'] == TaskStatus.COMPLETED.value and task.get('completed_at'):
                try:
                    completed_date = datetime.fromisoformat(task['completed_at']).date()
                    if completed_date >= created_date:
                        completed_count += 1
                except (ValueError, TypeError):
                    continue
        return completed_count

    elif metric_type == "habit_streaks":
        # Find the longest current streak
        max_streak = 0
        for habit in st.session_state.habits:
            current_streak = habit.get('streak', 0)
            max_streak = max(max_streak, current_streak)
        return max_streak

    elif metric_type == "focus_time":
        # Calculate total Pomodoro sessions (as proxy for focus time)
        return st.session_state.pomodoro_state.get('sessions_completed', 0) * 25  # 25 min per session

    elif metric_type == "completion_rate":
        # Calculate current completion rate
        stats = get_task_stats()
        return int(stats.get('completion_rate', 0))

    return 0


def render_habit_achievements():
    """Render habit achievements and milestones"""

    st.markdown("### 🏆 Habit Achievements")

    if not st.session_state.habits:
        st.info("No habits to show achievements for. Create some habits first!")
        return

    # Achievement categories
    achievement_categories = {
        "Streak Milestones": calculate_streak_achievements(),
        "Consistency Awards": calculate_consistency_achievements(),
        "Total Completion": calculate_completion_achievements(),
        "Perfect Weeks": calculate_weekly_achievements()
    }

    for category, achievements in achievement_categories.items():
        if achievements:
            st.markdown(f"#### 🏆 {category}")

            for achievement in achievements:
                col1, col2, col3 = st.columns([1, 4, 1])

                with col1:
                    st.markdown(achievement['emoji'])

                with col2:
                    st.markdown(f"**{achievement['title']}**")
                    st.markdown(f"*{achievement['description']}*")

                with col3:
                    st.markdown(f"**{achievement['value']}**")


def calculate_streak_achievements() -> List[Dict]:
    """Calculate streak-based achievements"""
    achievements = []

    for habit in st.session_state.habits:
        current_streak = habit.get('streak', 0)
        best_streak = habit.get('best_streak', 0)

        # Milestone achievements
        milestones = [
            (7, "Week Warrior", "🔥"),
            (30, "Month Master", "🌟"),
            (100, "Century Champion", "💯"),
            (365, "Year Legend", "🏆")
        ]

        for days, title, emoji in milestones:
            if best_streak >= days:
                achievements.append({
                    'emoji': emoji,
                    'title': f"{title} - {habit['name']}",
                    'description': f"Achieved {days}+ day streak",
                    'value': f"{best_streak} days"
                })

    return achievements


def calculate_consistency_achievements() -> List[Dict]:
    """Calculate consistency-based achievements"""
    achievements = []

    for habit in st.session_state.habits:
        completion_dates = habit.get('completion_dates', [])

        if len(completion_dates) >= 30:  # Need at least 30 days of data
            # Calculate 30-day consistency
            last_30_days = date.today() - timedelta(days=30)
            recent_completions = [d for d in completion_dates
                                  if datetime.fromisoformat(d).date() >= last_30_days]

            consistency_rate = len(recent_completions) / 30 * 100

            if consistency_rate >= 90:
                achievements.append({
                    'emoji': '🎯',
                    'title': f"Consistency Master - {habit['name']}",
                    'description': "90%+ completion rate over 30 days",
                    'value': f"{consistency_rate:.1f}%"
                })
            elif consistency_rate >= 80:
                achievements.append({
                    'emoji': '📈',
                    'title': f"Steady Performer - {habit['name']}",
                    'description': "80%+ completion rate over 30 days",
                    'value': f"{consistency_rate:.1f}%"
                })

    return achievements


def calculate_completion_achievements() -> List[Dict]:
    """Calculate total completion achievements"""
    achievements = []

    for habit in st.session_state.habits:
        total_completions = len(habit.get('completion_dates', []))

        milestones = [
            (50, "Half Century", "⭐"),
            (100, "Centurion", "💯"),
            (365, "Annual Achiever", "📅"),
            (1000, "Millennium Master", "🌟")
        ]

        for count, title, emoji in milestones:
            if total_completions >= count:
                achievements.append({
                    'emoji': emoji,
                    'title': f"{title} - {habit['name']}",
                    'description': f"Completed {count}+ times",
                    'value': f"{total_completions} times"
                })

    return achievements


def calculate_weekly_achievements() -> List[Dict]:
    """Calculate weekly perfect completion achievements"""
    achievements = []

    for habit in st.session_state.habits:
        if habit['frequency'] != 'daily':
            continue

        completion_dates = habit.get('completion_dates', [])
        if not completion_dates:
            continue

        # Count perfect weeks (7 consecutive days)
        perfect_weeks = 0
        current_week_count = 0

        # Check each week in the last 12 weeks
        for week_offset in range(12):
            week_start = date.today() - timedelta(days=date.today().weekday() + (week_offset * 7))
            week_days = [week_start + timedelta(days=i) for i in range(7)]

            week_completions = sum(1 for day in week_days
                                   if day.isoformat() in completion_dates)

            if week_completions == 7:
                current_week_count += 1
            else:
                if current_week_count > 0:
                    perfect_weeks = max(perfect_weeks, current_week_count)
                current_week_count = 0

        # Check final streak
        perfect_weeks = max(perfect_weeks, current_week_count)

        if perfect_weeks >= 4:
            achievements.append({
                'emoji': '🗓️',
                'title': f"Perfect Month - {habit['name']}",
                'description': f"{perfect_weeks} consecutive perfect weeks",
                'value': f"{perfect_weeks} weeks"
            })
        elif perfect_weeks >= 1:
            achievements.append({
                'emoji': '📅',
                'title': f"Perfect Week - {habit['name']}",
                'description': f"{perfect_weeks} consecutive perfect weeks",
                'value': f"{perfect_weeks} weeks"
            })

    return achievements


def render_ai_insights_dashboard():
    """Render AI-powered insights dashboard"""

    st.markdown("### 🔮 AI-Powered Insights")
    st.markdown("*Intelligent analysis of your productivity patterns*")

    # Generate insights
    with st.spinner("Analyzing your productivity data..."):
        ai_insights = generate_comprehensive_insights()

    # Display insights in categories
    for category, insights in ai_insights.items():
        if insights:
            st.markdown(f"#### {category}")

            for insight in insights:
                # Color code based on insight type
                if insight['type'] == 'positive':
                    st.success(f"✅ {insight['message']}")
                elif insight['type'] == 'warning':
                    st.warning(f"⚠️ {insight['message']}")
                elif insight['type'] == 'info':
                    st.info(f"💡 {insight['message']}")
                else:
                    st.write(f"📊 {insight['message']}")

                # Show actionable recommendations
                if insight.get('actions'):
                    with st.expander("💡 Recommended Actions"):
                        for action in insight['actions']:
                            st.write(f"• {action}")


def generate_comprehensive_insights() -> Dict[str, List[Dict]]:
    """Generate comprehensive AI-like insights"""

    insights = {
        "🎯 Performance Insights": [],
        "📈 Trend Analysis": [],
        "⚡ Optimization Opportunities": [],
        "🔮 Predictions & Recommendations": []
    }

    tasks = st.session_state.tasks
    habits = st.session_state.habits

    # Performance insights
    if tasks:
        completion_rate = len([t for t in tasks if t['status'] == TaskStatus.COMPLETED.value]) / len(tasks) * 100

        if completion_rate > 80:
            insights["🎯 Performance Insights"].append({
                'type': 'positive',
                'message': f"Excellent completion rate of {completion_rate:.1f}%! You're highly effective at following through.",
                'actions': ["Consider taking on more challenging projects",
                            "Share your productivity methods with others"]
            })
        elif completion_rate < 50:
            insights["🎯 Performance Insights"].append({
                'type': 'warning',
                'message': f"Completion rate of {completion_rate:.1f}% suggests room for improvement.",
                'actions': ["Review task complexity - consider breaking large tasks down",
                            "Set more realistic deadlines"]
            })

    # Trend analysis
    patterns = AdvancedTaskAnalyzer.analyze_completion_patterns(tasks)
    if patterns and patterns.get('most_productive_periods'):
        most_productive_hour = patterns['most_productive_periods'].get('hour')
        if most_productive_hour:
            insights["📈 Trend Analysis"].append({
                'type': 'info',
                'message': f"You're most productive at {most_productive_hour}:00. This is your golden hour!",
                'actions': [f"Schedule your most important tasks around {most_productive_hour}:00",
                            "Protect this time from meetings and distractions"]
            })

    # Optimization opportunities
    overdue_count = len([t for t in tasks if t.get('due_date') and
                         datetime.fromisoformat(t['due_date']).date() < date.today() and
                         t['status'] == TaskStatus.PENDING.value])

    if overdue_count > 0:
        insights["⚡ Optimization Opportunities"].append({
            'type': 'warning',
            'message': f"You have {overdue_count} overdue tasks. This might indicate planning issues.",
            'actions': ["Use the Eisenhower Matrix to prioritize", "Consider time-blocking for better planning",
                        "Review your estimation accuracy"]
        })

    # Habit insights
    if habits:
        avg_streak = sum(h.get('streak', 0) for h in habits) / len(habits)
        if avg_streak > 14:
            insights["🎯 Performance Insights"].append({
                'type': 'positive',
                'message': f"Impressive habit consistency with average streak of {avg_streak:.1f} days!",
                'actions': ["Consider adding a new challenging habit", "Share your success strategies"]
            })

    # Predictions
    if len(tasks) > 10:  # Need sufficient data
        recent_completion_trend = analyze_recent_trends(tasks)
        if recent_completion_trend > 0:
            insights["🔮 Predictions & Recommendations"].append({
                'type': 'positive',
                'message': "Your productivity is trending upward! Keep up the momentum.",
                'actions': ["Maintain current strategies", "Consider setting more ambitious goals"]
            })
        elif recent_completion_trend < 0:
            insights["🔮 Predictions & Recommendations"].append({
                'type': 'warning',
                'message': "Productivity appears to be declining. Consider what might have changed.",
                'actions': ["Review recent changes in routine", "Consider if you're overcommitted"]
            })

    return insights


def analyze_recent_trends(tasks: List[Dict]) -> float:
    """Analyze recent productivity trends"""

    # Compare last 7 days vs previous 7 days
    today = date.today()
    week1_start = today - timedelta(days=7)
    week1_end = today
    week2_start = today - timedelta(days=14)
    week2_end = week1_start

    week1_completions = 0
    week2_completions = 0

    for task in tasks:
        if task['status'] == TaskStatus.COMPLETED.value and task.get('completed_at'):
            try:
                completed_date = datetime.fromisoformat(task['completed_at']).date()
                if week1_start <= completed_date <= week1_end:
                    week1_completions += 1
                elif week2_start <= completed_date <= week2_end:
                    week2_completions += 1
            except (ValueError, TypeError):
                continue

    if week2_completions == 0:
        return 0

    return (week1_completions - week2_completions) / week2_completions


# Utility functions for colors and styling
def get_list_color(list_name: str) -> str:
    """Get color for a specific list"""
    colors = {
        "Inbox": "#6B7280",
        "Personal": "#10B981",
        "Work": "#3B82F6",
        "Shopping": "#F59E0B",
        "Health": "#EF4444",
        "Learning": "#8B5CF6"
    }

    # Generate a color for unlisted items
    if list_name not in colors:
        hash_val = hash(list_name) % 360
        return f"hsl({hash_val}, 70%, 50%)"

    return colors[list_name]


def get_status_color(status: str) -> str:
    """Get color for task status"""
    colors = {
        "pending": "#F59E0B",
        "in_progress": "#3B82F6",
        "completed": "#10B981",
        "cancelled": "#6B7280"
    }
    return colors.get(status, "#6B7280")