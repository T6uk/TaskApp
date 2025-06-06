import streamlit as st
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import json
from enum import Enum


class NotificationType(Enum):
    TASK_DUE = "task_due"
    TASK_OVERDUE = "task_overdue"
    HABIT_REMINDER = "habit_reminder"
    POMODORO_BREAK = "pomodoro_break"
    POMODORO_WORK = "pomodoro_work"
    ACHIEVEMENT = "achievement"
    WEEKLY_SUMMARY = "weekly_summary"


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification:
    def __init__(self, title: str, message: str, notification_type: NotificationType,
                 priority: NotificationPriority = NotificationPriority.MEDIUM,
                 action_url: str = None, data: Dict = None):
        self.id = datetime.now().isoformat() + "_" + str(hash(title + message))
        self.title = title
        self.message = message
        self.type = notification_type
        self.priority = priority
        self.action_url = action_url
        self.data = data or {}
        self.created_at = datetime.now()
        self.read = False
        self.dismissed = False


class NotificationManager:
    def __init__(self):
        self.notifications = []
        self.load_notifications()

    def create_notification(self, title: str, message: str,
                            notification_type: NotificationType,
                            priority: NotificationPriority = NotificationPriority.MEDIUM,
                            action_url: str = None, data: Dict = None) -> Notification:
        """Create a new notification"""
        notification = Notification(title, message, notification_type, priority, action_url, data)
        self.notifications.append(notification)
        self.save_notifications()
        return notification

    def get_unread_notifications(self) -> List[Notification]:
        """Get all unread notifications"""
        return [n for n in self.notifications if not n.read and not n.dismissed]

    def get_notifications_by_type(self, notification_type: NotificationType) -> List[Notification]:
        """Get notifications by type"""
        return [n for n in self.notifications if n.type == notification_type]

    def mark_as_read(self, notification_id: str):
        """Mark a notification as read"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                break
        self.save_notifications()

    def dismiss_notification(self, notification_id: str):
        """Dismiss a notification"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.dismissed = True
                break
        self.save_notifications()

    def clear_old_notifications(self, days: int = 30):
        """Clear notifications older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        self.notifications = [n for n in self.notifications if n.created_at > cutoff_date]
        self.save_notifications()

    def save_notifications(self):
        """Save notifications to session state"""
        notification_data = []
        for n in self.notifications:
            notification_data.append({
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.type.value,
                'priority': n.priority.value,
                'action_url': n.action_url,
                'data': n.data,
                'created_at': n.created_at.isoformat(),
                'read': n.read,
                'dismissed': n.dismissed
            })
        st.session_state.notifications_data = notification_data

    def load_notifications(self):
        """Load notifications from session state"""
        if 'notifications_data' not in st.session_state:
            st.session_state.notifications_data = []

        self.notifications = []
        for data in st.session_state.notifications_data:
            notification = Notification(
                data['title'], data['message'],
                NotificationType(data['type']),
                NotificationPriority(data['priority']),
                data.get('action_url'), data.get('data', {})
            )
            notification.id = data['id']
            notification.created_at = datetime.fromisoformat(data['created_at'])
            notification.read = data['read']
            notification.dismissed = data['dismissed']
            self.notifications.append(notification)


def check_task_notifications():
    """Check for task-related notifications"""
    if 'notification_manager' not in st.session_state:
        st.session_state.notification_manager = NotificationManager()

    manager = st.session_state.notification_manager
    today = date.today()

    # Check for due tasks
    for task in st.session_state.get('tasks', []):
        if task['status'] == 'completed' or not task.get('due_date'):
            continue

        due_date = datetime.fromisoformat(task['due_date']).date()

        # Task due today
        if due_date == today:
            existing = manager.get_notifications_by_type(NotificationType.TASK_DUE)
            if not any(n.data.get('task_id') == task['id'] for n in existing):
                manager.create_notification(
                    "Task Due Today",
                    f"'{task['title']}' is due today",
                    NotificationType.TASK_DUE,
                    NotificationPriority.HIGH,
                    data={'task_id': task['id']}
                )

        # Overdue tasks
        elif due_date < today:
            existing = manager.get_notifications_by_type(NotificationType.TASK_OVERDUE)
            if not any(n.data.get('task_id') == task['id'] for n in existing):
                days_overdue = (today - due_date).days
                manager.create_notification(
                    "Task Overdue",
                    f"'{task['title']}' is {days_overdue} day(s) overdue",
                    NotificationType.TASK_OVERDUE,
                    NotificationPriority.URGENT,
                    data={'task_id': task['id'], 'days_overdue': days_overdue}
                )


def check_habit_notifications():
    """Check for habit reminder notifications"""
    if 'notification_manager' not in st.session_state:
        st.session_state.notification_manager = NotificationManager()

    manager = st.session_state.notification_manager
    today = date.today().isoformat()

    for habit in st.session_state.get('habits', []):
        # Check if habit wasn't completed today
        if today not in habit.get('completion_dates', []):
            # Check if we already sent a reminder today
            existing = manager.get_notifications_by_type(NotificationType.HABIT_REMINDER)
            today_reminders = [n for n in existing
                               if n.data.get('habit_id') == habit['id']
                               and n.created_at.date() == date.today()]

            if not today_reminders:
                manager.create_notification(
                    "Habit Reminder",
                    f"Don't forget: {habit['name']}",
                    NotificationType.HABIT_REMINDER,
                    NotificationPriority.MEDIUM,
                    data={'habit_id': habit['id']}
                )


def check_achievement_notifications():
    """Check for achievement notifications"""
    if 'notification_manager' not in st.session_state:
        st.session_state.notification_manager = NotificationManager()

    manager = st.session_state.notification_manager

    # Check for task completion milestones
    completed_tasks = [t for t in st.session_state.get('tasks', [])
                       if t['status'] == 'completed']

    milestones = [10, 25, 50, 100, 250, 500, 1000]
    task_count = len(completed_tasks)

    for milestone in milestones:
        if task_count >= milestone:
            # Check if we already celebrated this milestone
            existing = [n for n in manager.notifications
                        if n.type == NotificationType.ACHIEVEMENT
                        and n.data.get('milestone_type') == 'tasks_completed'
                        and n.data.get('milestone_value') == milestone]

            if not existing:
                manager.create_notification(
                    "Achievement Unlocked! 🎉",
                    f"You've completed {milestone} tasks!",
                    NotificationType.ACHIEVEMENT,
                    NotificationPriority.MEDIUM,
                    data={'milestone_type': 'tasks_completed', 'milestone_value': milestone}
                )

    # Check for habit streaks
    for habit in st.session_state.get('habits', []):
        streak = habit.get('streak', 0)
        streak_milestones = [7, 30, 60, 100, 365]

        for milestone in streak_milestones:
            if streak >= milestone:
                existing = [n for n in manager.notifications
                            if n.type == NotificationType.ACHIEVEMENT
                            and n.data.get('milestone_type') == 'habit_streak'
                            and n.data.get('habit_id') == habit['id']
                            and n.data.get('milestone_value') == milestone]

                if not existing:
                    manager.create_notification(
                        "Streak Achievement! 🔥",
                        f"{streak} day streak for '{habit['name']}'!",
                        NotificationType.ACHIEVEMENT,
                        NotificationPriority.MEDIUM,
                        data={
                            'milestone_type': 'habit_streak',
                            'habit_id': habit['id'],
                            'milestone_value': milestone
                        }
                    )


def create_pomodoro_notification(notification_type: str, session_type: str = "work"):
    """Create Pomodoro timer notifications"""
    if 'notification_manager' not in st.session_state:
        st.session_state.notification_manager = NotificationManager()

    manager = st.session_state.notification_manager

    if notification_type == "break":
        manager.create_notification(
            "Time for a Break! ☕",
            "Your work session is complete. Take a well-deserved break!",
            NotificationType.POMODORO_BREAK,
            NotificationPriority.HIGH
        )

    elif notification_type == "work":
        manager.create_notification(
            "Back to Work! 💪",
            "Break time is over. Ready to focus on your next task?",
            NotificationType.POMODORO_WORK,
            NotificationPriority.HIGH
        )


def generate_weekly_summary():
    """Generate weekly summary notification"""
    if 'notification_manager' not in st.session_state:
        st.session_state.notification_manager = NotificationManager()

    manager = st.session_state.notification_manager

    # Calculate weekly stats
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_end = week_start + timedelta(days=6)

    # Tasks completed this week
    weekly_tasks = []
    for task in st.session_state.get('tasks', []):
        if task['completed_at']:
            try:
                completed_date = datetime.fromisoformat(task['completed_at']).date()
                if week_start <= completed_date <= week_end:
                    weekly_tasks.append(task)
            except:
                continue

    # Habits completed this week
    weekly_habit_completions = 0
    for habit in st.session_state.get('habits', []):
        for completion_date_str in habit.get('completion_dates', []):
            try:
                completion_date = datetime.fromisoformat(completion_date_str).date()
                if week_start <= completion_date <= week_end:
                    weekly_habit_completions += 1
            except:
                continue

    # Pomodoro sessions
    weekly_pomodoros = st.session_state.get('pomodoro_state', {}).get('sessions_completed', 0)

    # Create summary message
    summary = f"""Weekly Summary:
    ✅ {len(weekly_tasks)} tasks completed
    🎯 {weekly_habit_completions} habits completed
    🍅 {weekly_pomodoros} focus sessions

    Keep up the great work!"""

    manager.create_notification(
        "Weekly Summary 📊",
        summary,
        NotificationType.WEEKLY_SUMMARY,
        NotificationPriority.LOW,
        data={
            'week_start': week_start.isoformat(),
            'tasks_completed': len(weekly_tasks),
            'habits_completed': weekly_habit_completions,
            'pomodoro_sessions': weekly_pomodoros
        }
    )


def render_notification_center():
    """Render the notification center UI"""
    if 'notification_manager' not in st.session_state:
        st.session_state.notification_manager = NotificationManager()

    manager = st.session_state.notification_manager

    st.markdown("### 🔔 Notifications")

    # Notification summary
    unread_count = len(manager.get_unread_notifications())
    total_count = len([n for n in manager.notifications if not n.dismissed])

    col1, col2, col3 = st.columns(3)
    col1.metric("Unread", unread_count)
    col2.metric("Total", total_count)

    with col3:
        if st.button("🧹 Clear All", help="Mark all as read"):
            for notification in manager.notifications:
                notification.read = True
            manager.save_notifications()
            st.rerun()

    # Check for new notifications
    check_task_notifications()
    check_habit_notifications()
    check_achievement_notifications()

    # Display notifications
    unread_notifications = manager.get_unread_notifications()

    if not unread_notifications:
        st.info("No new notifications 🎉")
    else:
        for notification in sorted(unread_notifications,
                                   key=lambda x: x.created_at, reverse=True):

            # Priority indicator
            priority_colors = {
                NotificationPriority.LOW: "🟢",
                NotificationPriority.MEDIUM: "🟡",
                NotificationPriority.HIGH: "🟠",
                NotificationPriority.URGENT: "🔴"
            }
            priority_icon = priority_colors.get(notification.priority, "⚪")

            # Type icon
            type_icons = {
                NotificationType.TASK_DUE: "📅",
                NotificationType.TASK_OVERDUE: "⚠️",
                NotificationType.HABIT_REMINDER: "🎯",
                NotificationType.POMODORO_BREAK: "☕",
                NotificationType.POMODORO_WORK: "💪",
                NotificationType.ACHIEVEMENT: "🎉",
                NotificationType.WEEKLY_SUMMARY: "📊"
            }
            type_icon = type_icons.get(notification.type, "📋")

            with st.container():
                col1, col2, col3, col4 = st.columns([0.5, 0.5, 4, 1])

                with col1:
                    st.write(priority_icon)

                with col2:
                    st.write(type_icon)

                with col3:
                    st.markdown(f"**{notification.title}**")
                    st.markdown(notification.message)
                    st.markdown(f"<small>{notification.created_at.strftime('%m/%d %H:%M')}</small>",
                                unsafe_allow_html=True)

                with col4:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("👁️", key=f"read_{notification.id}", help="Mark as read"):
                            manager.mark_as_read(notification.id)
                            st.rerun()
                    with col_b:
                        if st.button("❌", key=f"dismiss_{notification.id}", help="Dismiss"):
                            manager.dismiss_notification(notification.id)
                            st.rerun()

                st.divider()


def get_notification_badge_count() -> int:
    """Get the count for notification badge"""
    if 'notification_manager' not in st.session_state:
        return 0

    manager = st.session_state.notification_manager
    return len(manager.get_unread_notifications())


def init_notification_system():
    """Initialize the notification system"""
    if 'notification_manager' not in st.session_state:
        st.session_state.notification_manager = NotificationManager()

    # Clean up old notifications on startup
    st.session_state.notification_manager.clear_old_notifications()

    # Check for initial notifications
    check_task_notifications()
    check_habit_notifications()
    check_achievement_notifications()