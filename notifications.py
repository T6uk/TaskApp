import streamlit as st
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Set, Callable
import json
from enum import Enum
from dataclasses import dataclass, asdict
import uuid


class NotificationType(Enum):
    TASK_DUE = "task_due"
    TASK_OVERDUE = "task_overdue"
    TASK_COMPLETED = "task_completed"
    HABIT_REMINDER = "habit_reminder"
    HABIT_STREAK = "habit_streak"
    POMODORO_BREAK = "pomodoro_break"
    POMODORO_WORK = "pomodoro_work"
    ACHIEVEMENT = "achievement"
    WEEKLY_SUMMARY = "weekly_summary"
    PRODUCTIVITY_INSIGHT = "productivity_insight"
    GOAL_REMINDER = "goal_reminder"
    DEADLINE_WARNING = "deadline_warning"
    FOCUS_SUGGESTION = "focus_suggestion"


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationCategory(Enum):
    TASKS = "tasks"
    HABITS = "habits"
    PRODUCTIVITY = "productivity"
    ACHIEVEMENTS = "achievements"
    REMINDERS = "reminders"
    INSIGHTS = "insights"


@dataclass
class NotificationRule:
    """Defines when and how notifications should be triggered"""
    id: str
    name: str
    condition: Callable[[], bool]
    notification_type: NotificationType
    priority: NotificationPriority
    category: NotificationCategory
    cooldown_hours: int = 24  # Minimum hours between same type notifications
    enabled: bool = True
    custom_message: Optional[str] = None


class Notification:
    def __init__(self, title: str, message: str, notification_type: NotificationType,
                 priority: NotificationPriority = NotificationPriority.MEDIUM,
                 category: NotificationCategory = NotificationCategory.TASKS,
                 action_url: str = None, data: Dict = None,
                 expires_at: datetime = None, auto_dismiss: bool = False):
        self.id = str(uuid.uuid4())
        self.title = title
        self.message = message
        self.type = notification_type
        self.priority = priority
        self.category = category
        self.action_url = action_url
        self.data = data or {}
        self.created_at = datetime.now()
        self.expires_at = expires_at or (datetime.now() + timedelta(days=7))
        self.read = False
        self.dismissed = False
        self.auto_dismiss = auto_dismiss
        self.interaction_count = 0
        self.last_interaction = None


class SmartNotificationManager:
    def __init__(self):
        self.notifications = []
        self.notification_rules = []
        self.notification_history = []
        self.user_preferences = self._load_preferences()
        self.load_notifications()
        self._register_default_rules()

    def _load_preferences(self) -> Dict:
        """Load user notification preferences"""
        default_prefs = {
            'enabled': True,
            'quiet_hours_start': '22:00',
            'quiet_hours_end': '08:00',
            'max_notifications_per_hour': 5,
            'categories': {
                cat.value: True for cat in NotificationCategory
            },
            'priorities': {
                prio.value: True for prio in NotificationPriority
            },
            'smart_batching': True,
            'sound_enabled': True,
            'desktop_notifications': False
        }

        return st.session_state.get('notification_preferences', default_prefs)

    def _register_default_rules(self):
        """Register default notification rules"""
        self.notification_rules = [
            # Task-related rules
            NotificationRule(
                id="task_due_today",
                name="Tasks Due Today",
                condition=self._check_tasks_due_today,
                notification_type=NotificationType.TASK_DUE,
                priority=NotificationPriority.HIGH,
                category=NotificationCategory.TASKS,
                cooldown_hours=8
            ),

            NotificationRule(
                id="task_overdue",
                name="Overdue Tasks",
                condition=self._check_overdue_tasks,
                notification_type=NotificationType.TASK_OVERDUE,
                priority=NotificationPriority.URGENT,
                category=NotificationCategory.TASKS,
                cooldown_hours=12
            ),

            NotificationRule(
                id="deadline_warning",
                name="Upcoming Deadlines",
                condition=self._check_upcoming_deadlines,
                notification_type=NotificationType.DEADLINE_WARNING,
                priority=NotificationPriority.MEDIUM,
                category=NotificationCategory.REMINDERS,
                cooldown_hours=24
            ),

            # Habit-related rules
            NotificationRule(
                id="habit_reminder",
                name="Habit Reminders",
                condition=self._check_habit_reminders,
                notification_type=NotificationType.HABIT_REMINDER,
                priority=NotificationPriority.MEDIUM,
                category=NotificationCategory.HABITS,
                cooldown_hours=24
            ),

            NotificationRule(
                id="habit_streak_milestone",
                name="Habit Streak Milestones",
                condition=self._check_habit_streaks,
                notification_type=NotificationType.HABIT_STREAK,
                priority=NotificationPriority.HIGH,
                category=NotificationCategory.ACHIEVEMENTS,
                cooldown_hours=0
            ),

            # Productivity rules
            NotificationRule(
                id="productivity_insight",
                name="Daily Productivity Insights",
                condition=self._check_productivity_insights,
                notification_type=NotificationType.PRODUCTIVITY_INSIGHT,
                priority=NotificationPriority.LOW,
                category=NotificationCategory.INSIGHTS,
                cooldown_hours=24
            ),

            NotificationRule(
                id="focus_suggestion",
                name="Focus Time Suggestions",
                condition=self._check_focus_suggestions,
                notification_type=NotificationType.FOCUS_SUGGESTION,
                priority=NotificationPriority.MEDIUM,
                category=NotificationCategory.PRODUCTIVITY,
                cooldown_hours=4
            )
        ]

    def create_notification(self, title: str, message: str,
                            notification_type: NotificationType,
                            priority: NotificationPriority = NotificationPriority.MEDIUM,
                            category: NotificationCategory = NotificationCategory.TASKS,
                            action_url: str = None, data: Dict = None,
                            expires_at: datetime = None,
                            auto_dismiss: bool = False) -> Optional[Notification]:
        """Create a new notification with smart filtering"""

        # Check if notifications are enabled
        if not self.user_preferences.get('enabled', True):
            return None

        # Check category preferences
        if not self.user_preferences.get('categories', {}).get(category.value, True):
            return None

        # Check priority preferences
        if not self.user_preferences.get('priorities', {}).get(priority.value, True):
            return None

        # Check quiet hours
        if self._is_quiet_hours():
            if priority not in [NotificationPriority.URGENT, NotificationPriority.CRITICAL]:
                return None

        # Check rate limiting
        if not self._check_rate_limit():
            return None

        # Check for duplicates
        if self._is_duplicate_notification(title, notification_type, data):
            return None

        notification = Notification(
            title, message, notification_type, priority, category,
            action_url, data, expires_at, auto_dismiss
        )

        self.notifications.append(notification)
        self._add_to_history(notification)
        self.save_notifications()

        return notification

    def process_smart_notifications(self):
        """Process all notification rules and create smart notifications"""
        current_time = datetime.now()

        for rule in self.notification_rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if self._is_in_cooldown(rule):
                continue

            try:
                # Execute the rule condition
                if rule.condition():
                    self._execute_notification_rule(rule)
            except Exception as e:
                st.error(f"Error processing notification rule {rule.name}: {str(e)}")

    def _execute_notification_rule(self, rule: NotificationRule):
        """Execute a notification rule and create appropriate notifications"""
        if rule.notification_type == NotificationType.TASK_DUE:
            self._create_task_due_notifications()
        elif rule.notification_type == NotificationType.TASK_OVERDUE:
            self._create_overdue_notifications()
        elif rule.notification_type == NotificationType.DEADLINE_WARNING:
            self._create_deadline_warnings()
        elif rule.notification_type == NotificationType.HABIT_REMINDER:
            self._create_habit_reminders()
        elif rule.notification_type == NotificationType.HABIT_STREAK:
            self._create_streak_notifications()
        elif rule.notification_type == NotificationType.PRODUCTIVITY_INSIGHT:
            self._create_productivity_insights()
        elif rule.notification_type == NotificationType.FOCUS_SUGGESTION:
            self._create_focus_suggestions()

    def _create_task_due_notifications(self):
        """Create notifications for tasks due today"""
        today = date.today().isoformat()
        tasks_due = [t for t in st.session_state.get('tasks', [])
                     if t.get('due_date') == today and t.get('status') == 'pending']

        if len(tasks_due) == 1:
            task = tasks_due[0]
            self.create_notification(
                "Task Due Today! 📅",
                f"'{task['title']}' is due today",
                NotificationType.TASK_DUE,
                NotificationPriority.HIGH,
                NotificationCategory.TASKS,
                data={'task_id': task['id'], 'task_count': 1}
            )
        elif len(tasks_due) > 1:
            high_priority_count = len([t for t in tasks_due if t.get('priority') == 'high'])
            message = f"You have {len(tasks_due)} tasks due today"
            if high_priority_count > 0:
                message += f" ({high_priority_count} high priority)"

            self.create_notification(
                f"🎯 {len(tasks_due)} Tasks Due Today!",
                message,
                NotificationType.TASK_DUE,
                NotificationPriority.HIGH,
                NotificationCategory.TASKS,
                data={'task_ids': [t['id'] for t in tasks_due], 'task_count': len(tasks_due)}
            )

    def _create_overdue_notifications(self):
        """Create notifications for overdue tasks"""
        today = date.today().isoformat()
        overdue_tasks = [t for t in st.session_state.get('tasks', [])
                         if t.get('due_date') and t.get('due_date') < today
                         and t.get('status') == 'pending']

        if not overdue_tasks:
            return

        # Group by how overdue they are
        critical_overdue = [t for t in overdue_tasks
                            if (date.today() - datetime.fromisoformat(t['due_date']).date()).days > 7]

        if critical_overdue:
            self.create_notification(
                "⚠️ Critical: Tasks Seriously Overdue",
                f"{len(critical_overdue)} tasks are more than a week overdue",
                NotificationType.TASK_OVERDUE,
                NotificationPriority.CRITICAL,
                NotificationCategory.TASKS,
                data={'task_ids': [t['id'] for t in critical_overdue]}
            )
        elif overdue_tasks:
            self.create_notification(
                "⏰ Overdue Tasks Need Attention",
                f"{len(overdue_tasks)} tasks are past their due date",
                NotificationType.TASK_OVERDUE,
                NotificationPriority.URGENT,
                NotificationCategory.TASKS,
                data={'task_ids': [t['id'] for t in overdue_tasks]}
            )

    def _create_deadline_warnings(self):
        """Create warnings for upcoming deadlines"""
        upcoming_tasks = []
        for days_ahead in [1, 3, 7]:  # Tomorrow, 3 days, 1 week
            target_date = (date.today() + timedelta(days=days_ahead)).isoformat()
            tasks = [t for t in st.session_state.get('tasks', [])
                     if t.get('due_date') == target_date
                     and t.get('status') == 'pending'
                     and t.get('priority') in ['high', 'medium']]

            if tasks:
                time_frame = "tomorrow" if days_ahead == 1 else f"in {days_ahead} days"
                self.create_notification(
                    f"📅 Deadline Approaching",
                    f"{len(tasks)} important tasks due {time_frame}",
                    NotificationType.DEADLINE_WARNING,
                    NotificationPriority.MEDIUM,
                    NotificationCategory.REMINDERS,
                    data={'task_ids': [t['id'] for t in tasks], 'days_ahead': days_ahead}
                )

    def _create_habit_reminders(self):
        """Create smart habit reminders"""
        today = date.today().isoformat()
        current_time = datetime.now().time()

        for habit in st.session_state.get('habits', []):
            if not habit.get('active', True):
                continue

            # Skip if already completed today
            if today in habit.get('completion_dates', []):
                continue

            # Check if it's time for reminder
            reminder_time = habit.get('reminder_time')
            if reminder_time:
                try:
                    reminder_time_obj = datetime.strptime(reminder_time, '%H:%M').time()
                    if current_time >= reminder_time_obj:
                        # Create contextual reminder based on streak
                        streak = habit.get('streak', 0)
                        if streak >= 7:
                            message = f"Keep your {streak}-day streak alive! Time for: {habit['name']}"
                            priority = NotificationPriority.HIGH
                        elif streak >= 3:
                            message = f"Don't break your {streak}-day streak: {habit['name']}"
                            priority = NotificationPriority.MEDIUM
                        else:
                            message = f"Gentle reminder: {habit['name']}"
                            priority = NotificationPriority.LOW

                        self.create_notification(
                            "🎯 Habit Reminder",
                            message,
                            NotificationType.HABIT_REMINDER,
                            priority,
                            NotificationCategory.HABITS,
                            data={'habit_id': habit['id'], 'streak': streak}
                        )
                except:
                    continue

    def _create_streak_notifications(self):
        """Create notifications for habit streak milestones"""
        milestones = [7, 14, 30, 60, 100, 365]

        for habit in st.session_state.get('habits', []):
            current_streak = habit.get('streak', 0)

            # Check if we just hit a milestone
            if current_streak in milestones:
                # Ensure we haven't already celebrated this milestone
                existing = [n for n in self.notifications
                            if n.type == NotificationType.HABIT_STREAK
                            and n.data.get('habit_id') == habit['id']
                            and n.data.get('streak') == current_streak]

                if not existing:
                    emoji = "🔥" if current_streak >= 30 else "⭐"
                    celebration = ""
                    if current_streak == 7:
                        celebration = "One week strong!"
                    elif current_streak == 30:
                        celebration = "A full month! Amazing!"
                    elif current_streak == 100:
                        celebration = "100 days! You're unstoppable!"
                    elif current_streak == 365:
                        celebration = "ONE YEAR! Legendary achievement!"

                    self.create_notification(
                        f"{emoji} {current_streak}-Day Streak!",
                        f"{celebration} Keep up '{habit['name']}'",
                        NotificationType.HABIT_STREAK,
                        NotificationPriority.HIGH,
                        NotificationCategory.ACHIEVEMENTS,
                        data={'habit_id': habit['id'], 'streak': current_streak}
                    )

    def _create_productivity_insights(self):
        """Create daily productivity insights"""
        try:
            from utils import get_productivity_insights
            insights = get_productivity_insights()

            if insights:
                # Create insight based on patterns
                recommendations = insights.get('recommendations', [])
                if recommendations:
                    insight = recommendations[0]  # Take the first recommendation

                    self.create_notification(
                        "💡 Productivity Insight",
                        insight,
                        NotificationType.PRODUCTIVITY_INSIGHT,
                        NotificationPriority.LOW,
                        NotificationCategory.INSIGHTS,
                        data={'insights': insights}
                    )
        except:
            pass

    def _create_focus_suggestions(self):
        """Create smart focus time suggestions"""
        # Check if user has many pending high-priority tasks
        high_priority_tasks = [t for t in st.session_state.get('tasks', [])
                               if t.get('priority') == 'high'
                               and t.get('status') == 'pending']

        if len(high_priority_tasks) >= 3:
            # Check if user hasn't used Pomodoro recently
            pomodoro_state = st.session_state.get('pomodoro_state', {})
            last_session = pomodoro_state.get('sessions_completed', 0)

            if last_session < 2:  # Less than 2 sessions today
                self.create_notification(
                    "🍅 Focus Time Suggestion",
                    f"You have {len(high_priority_tasks)} high-priority tasks. Consider a focus session!",
                    NotificationType.FOCUS_SUGGESTION,
                    NotificationPriority.MEDIUM,
                    NotificationCategory.PRODUCTIVITY,
                    data={'high_priority_count': len(high_priority_tasks)}
                )

    # Condition checking methods
    def _check_tasks_due_today(self) -> bool:
        """Check if there are tasks due today"""
        today = date.today().isoformat()
        return any(t.get('due_date') == today and t.get('status') == 'pending'
                   for t in st.session_state.get('tasks', []))

    def _check_overdue_tasks(self) -> bool:
        """Check if there are overdue tasks"""
        today = date.today().isoformat()
        return any(t.get('due_date') and t.get('due_date') < today and t.get('status') == 'pending'
                   for t in st.session_state.get('tasks', []))

    def _check_upcoming_deadlines(self) -> bool:
        """Check for upcoming deadlines in next 7 days"""
        week_ahead = (date.today() + timedelta(days=7)).isoformat()
        return any(t.get('due_date') and t.get('due_date') <= week_ahead
                   and t.get('status') == 'pending' and t.get('priority') in ['high', 'medium']
                   for t in st.session_state.get('tasks', []))

    def _check_habit_reminders(self) -> bool:
        """Check if any habits need reminders"""
        today = date.today().isoformat()
        current_time = datetime.now().time()

        for habit in st.session_state.get('habits', []):
            if (habit.get('active', True) and
                    today not in habit.get('completion_dates', []) and
                    habit.get('reminder_time')):
                try:
                    reminder_time = datetime.strptime(habit['reminder_time'], '%H:%M').time()
                    if current_time >= reminder_time:
                        return True
                except:
                    continue
        return False

    def _check_habit_streaks(self) -> bool:
        """Check for habit streak milestones"""
        milestones = [7, 14, 30, 60, 100, 365]
        for habit in st.session_state.get('habits', []):
            if habit.get('streak', 0) in milestones:
                return True
        return False

    def _check_productivity_insights(self) -> bool:
        """Check if it's time for productivity insights"""
        last_insight = self._get_last_notification_time(NotificationType.PRODUCTIVITY_INSIGHT)
        if not last_insight:
            return True

        # Send insights once per day
        return (datetime.now() - last_insight).days >= 1

    def _check_focus_suggestions(self) -> bool:
        """Check if focus suggestions should be shown"""
        high_priority_count = len([t for t in st.session_state.get('tasks', [])
                                   if t.get('priority') == 'high' and t.get('status') == 'pending'])

        pomodoro_sessions = st.session_state.get('pomodoro_state', {}).get('sessions_completed', 0)

        return high_priority_count >= 3 and pomodoro_sessions < 2

    # Helper methods
    def _is_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours"""
        current_time = datetime.now().time()

        try:
            start_time = datetime.strptime(self.user_preferences.get('quiet_hours_start', '22:00'), '%H:%M').time()
            end_time = datetime.strptime(self.user_preferences.get('quiet_hours_end', '08:00'), '%H:%M').time()

            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:  # Quiet hours span midnight
                return current_time >= start_time or current_time <= end_time
        except:
            return False

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        max_per_hour = self.user_preferences.get('max_notifications_per_hour', 5)

        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_notifications = [n for n in self.notifications
                                if n.created_at >= one_hour_ago and not n.dismissed]

        return len(recent_notifications) < max_per_hour

    def _is_duplicate_notification(self, title: str, notification_type: NotificationType, data: Dict) -> bool:
        """Check for duplicate notifications"""
        similar_notifications = [n for n in self.notifications
                                 if n.type == notification_type
                                 and n.title == title
                                 and not n.dismissed
                                 and (datetime.now() - n.created_at).hours < 24]

        return len(similar_notifications) > 0

    def _is_in_cooldown(self, rule: NotificationRule) -> bool:
        """Check if a rule is in cooldown period"""
        last_notification = self._get_last_notification_time(rule.notification_type)
        if not last_notification:
            return False

        hours_since = (datetime.now() - last_notification).total_seconds() / 3600
        return hours_since < rule.cooldown_hours

    def _get_last_notification_time(self, notification_type: NotificationType) -> Optional[datetime]:
        """Get the time of the last notification of a specific type"""
        matching_notifications = [n for n in self.notifications if n.type == notification_type]
        if not matching_notifications:
            return None

        return max(n.created_at for n in matching_notifications)

    def _add_to_history(self, notification: Notification):
        """Add notification to history for analytics"""
        self.notification_history.append({
            'id': notification.id,
            'type': notification.type.value,
            'priority': notification.priority.value,
            'category': notification.category.value,
            'created_at': notification.created_at.isoformat(),
            'title': notification.title
        })

        # Keep only last 1000 history entries
        if len(self.notification_history) > 1000:
            self.notification_history = self.notification_history[-1000:]

    def get_unread_notifications(self) -> List[Notification]:
        """Get all unread notifications, sorted by priority and time"""
        unread = [n for n in self.notifications if not n.read and not n.dismissed]

        # Remove expired notifications
        current_time = datetime.now()
        unread = [n for n in unread if n.expires_at > current_time]

        # Sort by priority (higher priority first) then by creation time (newer first)
        priority_order = {
            NotificationPriority.CRITICAL: 0,
            NotificationPriority.URGENT: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.MEDIUM: 3,
            NotificationPriority.LOW: 4
        }

        return sorted(unread, key=lambda n: (priority_order.get(n.priority, 999), -n.created_at.timestamp()))

    def get_notifications_by_category(self, category: NotificationCategory) -> List[Notification]:
        """Get notifications by category"""
        return [n for n in self.notifications if n.category == category and not n.dismissed]

    def mark_as_read(self, notification_id: str):
        """Mark a notification as read"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                notification.interaction_count += 1
                notification.last_interaction = datetime.now()
                break
        self.save_notifications()

    def dismiss_notification(self, notification_id: str):
        """Dismiss a notification"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.dismissed = True
                notification.interaction_count += 1
                notification.last_interaction = datetime.now()
                break
        self.save_notifications()

    def snooze_notification(self, notification_id: str, minutes: int = 60):
        """Snooze a notification for specified minutes"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.dismissed = True
                notification.interaction_count += 1
                notification.last_interaction = datetime.now()

                # Create a new notification for later
                snooze_time = datetime.now() + timedelta(minutes=minutes)
                snoozed_notification = Notification(
                    f"⏰ {notification.title}",
                    f"Snoozed reminder: {notification.message}",
                    notification.type,
                    notification.priority,
                    notification.category,
                    notification.action_url,
                    notification.data,
                    auto_dismiss=True
                )
                snoozed_notification.created_at = snooze_time
                self.notifications.append(snoozed_notification)
                break
        self.save_notifications()

    def clear_old_notifications(self, days: int = 30):
        """Clear notifications older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        self.notifications = [n for n in self.notifications
                              if n.created_at > cutoff_date or not n.dismissed]
        self.save_notifications()

    def get_notification_analytics(self) -> Dict:
        """Get analytics about notification patterns"""
        if not self.notification_history:
            return {}

        total_notifications = len(self.notification_history)

        # Type distribution
        type_counts = {}
        for entry in self.notification_history:
            type_counts[entry['type']] = type_counts.get(entry['type'], 0) + 1

        # Daily pattern
        daily_counts = {}
        for entry in self.notification_history:
            try:
                created_date = datetime.fromisoformat(entry['created_at']).date()
                daily_counts[created_date.isoformat()] = daily_counts.get(created_date.isoformat(), 0) + 1
            except:
                continue

        # Interaction rates
        total_notifications_obj = len(self.notifications)
        interacted_notifications = len([n for n in self.notifications if n.interaction_count > 0])
        interaction_rate = (
                interacted_notifications / total_notifications_obj * 100) if total_notifications_obj > 0 else 0

        return {
            'total_notifications': total_notifications,
            'type_distribution': type_counts,
            'daily_pattern': daily_counts,
            'interaction_rate': interaction_rate,
            'average_per_day': total_notifications / max(1, len(set(daily_counts.keys())))
        }

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
                'category': n.category.value,
                'action_url': n.action_url,
                'data': n.data,
                'created_at': n.created_at.isoformat(),
                'expires_at': n.expires_at.isoformat(),
                'read': n.read,
                'dismissed': n.dismissed,
                'auto_dismiss': n.auto_dismiss,
                'interaction_count': n.interaction_count,
                'last_interaction': n.last_interaction.isoformat() if n.last_interaction else None
            })

        st.session_state.notifications_data = notification_data
        st.session_state.notification_history = self.notification_history

    def load_notifications(self):
        """Load notifications from session state"""
        if 'notifications_data' not in st.session_state:
            st.session_state.notifications_data = []

        self.notifications = []
        for data in st.session_state.notifications_data:
            try:
                notification = Notification(
                    data['title'], data['message'],
                    NotificationType(data['type']),
                    NotificationPriority(data['priority']),
                    NotificationCategory(data.get('category', 'tasks')),
                    data.get('action_url'), data.get('data', {})
                )
                notification.id = data['id']
                notification.created_at = datetime.fromisoformat(data['created_at'])
                notification.expires_at = datetime.fromisoformat(data['expires_at'])
                notification.read = data['read']
                notification.dismissed = data['dismissed']
                notification.auto_dismiss = data.get('auto_dismiss', False)
                notification.interaction_count = data.get('interaction_count', 0)
                notification.last_interaction = (
                    datetime.fromisoformat(data['last_interaction'])
                    if data.get('last_interaction') else None
                )
                self.notifications.append(notification)
            except Exception as e:
                continue  # Skip malformed notifications

        # Load history
        self.notification_history = st.session_state.get('notification_history', [])


def render_enhanced_notification_center():
    """Render the enhanced notification center UI"""
    if 'smart_notification_manager' not in st.session_state:
        st.session_state.smart_notification_manager = SmartNotificationManager()

    manager = st.session_state.smart_notification_manager

    # Process smart notifications
    manager.process_smart_notifications()

    st.markdown("### 🔔 Smart Notifications")

    # Notification summary with categories
    unread_notifications = manager.get_unread_notifications()
    total_count = len([n for n in manager.notifications if not n.dismissed])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Unread", len(unread_notifications))
    col2.metric("Total Active", total_count)

    # Category breakdown
    category_counts = {}
    for notification in unread_notifications:
        cat = notification.category.value
        category_counts[cat] = category_counts.get(cat, 0) + 1

    col3.metric("Categories", len(category_counts))

    # Show highest priority
    if unread_notifications:
        highest_priority = max(unread_notifications, key=lambda n: {
            NotificationPriority.CRITICAL: 5,
            NotificationPriority.URGENT: 4,
            NotificationPriority.HIGH: 3,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.LOW: 1
        }.get(n.priority, 0))
        col4.metric("Highest Priority", highest_priority.priority.value.title())

    # Quick actions
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🧹 Mark All Read", help="Mark all notifications as read"):
            for notification in manager.notifications:
                if not notification.dismissed:
                    notification.read = True
            manager.save_notifications()
            st.rerun()

    with col2:
        if st.button("🗑️ Clear Read", help="Clear all read notifications"):
            manager.notifications = [n for n in manager.notifications if not n.read or not n.dismissed]
            manager.save_notifications()
            st.rerun()

    with col3:
        if st.button("🔄 Refresh", help="Check for new notifications"):
            manager.process_smart_notifications()
            st.rerun()

    with col4:
        show_analytics = st.checkbox("📊 Analytics", value=False)

    # Show analytics if requested
    if show_analytics:
        with st.expander("📊 Notification Analytics", expanded=True):
            analytics = manager.get_notification_analytics()
            if analytics:
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Sent", analytics.get('total_notifications', 0))
                col2.metric("Interaction Rate", f"{analytics.get('interaction_rate', 0):.1f}%")
                col3.metric("Daily Average", f"{analytics.get('average_per_day', 0):.1f}")

                # Type distribution
                if analytics.get('type_distribution'):
                    st.markdown("**Notification Types:**")
                    for ntype, count in analytics['type_distribution'].items():
                        st.write(f"• {ntype.replace('_', ' ').title()}: {count}")

    # Category filters
    if category_counts:
        st.markdown("#### Filter by Category")
        selected_categories = st.multiselect(
            "Categories",
            options=list(NotificationCategory),
            default=list(NotificationCategory),
            format_func=lambda x: f"{x.value.title()} ({category_counts.get(x.value, 0)})"
        )
    else:
        selected_categories = list(NotificationCategory)

    # Display notifications
    if not unread_notifications:
        st.success("🎉 All caught up! No new notifications.")
    else:
        filtered_notifications = [n for n in unread_notifications
                                  if n.category in selected_categories]

        if not filtered_notifications:
            st.info("No notifications in selected categories.")
        else:
            st.markdown(f"#### {len(filtered_notifications)} Notifications")

            for notification in filtered_notifications:
                render_notification_card(notification, manager)

    # Notification preferences
    with st.expander("⚙️ Notification Settings"):
        render_notification_preferences(manager)


def render_notification_card(notification: Notification, manager: SmartNotificationManager):
    """Render an individual notification card"""
    # Priority and type indicators
    priority_colors = {
        NotificationPriority.CRITICAL: "🔴",
        NotificationPriority.URGENT: "🟠",
        NotificationPriority.HIGH: "🟡",
        NotificationPriority.MEDIUM: "🔵",
        NotificationPriority.LOW: "⚪"
    }

    type_icons = {
        NotificationType.TASK_DUE: "📅",
        NotificationType.TASK_OVERDUE: "⚠️",
        NotificationType.TASK_COMPLETED: "✅",
        NotificationType.HABIT_REMINDER: "🎯",
        NotificationType.HABIT_STREAK: "🔥",
        NotificationType.POMODORO_BREAK: "☕",
        NotificationType.POMODORO_WORK: "💪",
        NotificationType.ACHIEVEMENT: "🏆",
        NotificationType.WEEKLY_SUMMARY: "📊",
        NotificationType.PRODUCTIVITY_INSIGHT: "💡",
        NotificationType.GOAL_REMINDER: "🎪",
        NotificationType.DEADLINE_WARNING: "⏰",
        NotificationType.FOCUS_SUGGESTION: "🍅"
    }

    priority_icon = priority_colors.get(notification.priority, "⚪")
    type_icon = type_icons.get(notification.type, "📋")

    with st.container():
        col1, col2, col3, col4, col5 = st.columns([0.3, 0.3, 4, 1, 1])

        with col1:
            st.write(priority_icon)

        with col2:
            st.write(type_icon)

        with col3:
            st.markdown(f"**{notification.title}**")
            st.markdown(notification.message)

            # Show metadata
            time_ago = get_time_ago(notification.created_at)
            category = notification.category.value.title()
            st.markdown(f"<small>{category} • {time_ago}</small>", unsafe_allow_html=True)

            # Show action data if available
            if notification.data:
                if notification.type == NotificationType.TASK_DUE:
                    task_count = notification.data.get('task_count', 1)
                    if task_count > 1:
                        st.markdown(f"<small>📋 {task_count} tasks involved</small>", unsafe_allow_html=True)

        with col4:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("👁️", key=f"read_{notification.id}", help="Mark as read"):
                    manager.mark_as_read(notification.id)
                    st.rerun()

            with col_b:
                if st.button("💤", key=f"snooze_{notification.id}", help="Snooze for 1 hour"):
                    manager.snooze_notification(notification.id, 60)
                    st.rerun()

            with col_c:
                if st.button("❌", key=f"dismiss_{notification.id}", help="Dismiss"):
                    manager.dismiss_notification(notification.id)
                    st.rerun()

        with col5:
            # Action button based on notification type
            if notification.type in [NotificationType.TASK_DUE, NotificationType.TASK_OVERDUE]:
                if st.button("📋 View Tasks", key=f"action_{notification.id}"):
                    st.session_state.current_view = "tasks"
                    if notification.data.get('task_ids'):
                        st.session_state.highlighted_tasks = notification.data['task_ids']
                    st.rerun()

            elif notification.type == NotificationType.HABIT_REMINDER:
                if st.button("🎯 View Habits", key=f"action_{notification.id}"):
                    st.session_state.current_view = "habits"
                    st.rerun()

            elif notification.type == NotificationType.FOCUS_SUGGESTION:
                if st.button("🍅 Start Focus", key=f"action_{notification.id}"):
                    st.session_state.current_view = "pomodoro"
                    st.rerun()

        st.divider()


def render_notification_preferences(manager: SmartNotificationManager):
    """Render notification preferences UI"""
    prefs = manager.user_preferences

    # General settings
    st.markdown("**General Settings**")
    col1, col2 = st.columns(2)

    with col1:
        enabled = st.checkbox("Enable notifications", value=prefs.get('enabled', True))
        sound_enabled = st.checkbox("Sound notifications", value=prefs.get('sound_enabled', True))
        smart_batching = st.checkbox("Smart batching", value=prefs.get('smart_batching', True),
                                     help="Group similar notifications together")

    with col2:
        max_per_hour = st.slider("Max notifications per hour", 1, 20, prefs.get('max_notifications_per_hour', 5))
        desktop_notifications = st.checkbox("Desktop notifications", value=prefs.get('desktop_notifications', False))

    # Quiet hours
    st.markdown("**Quiet Hours**")
    col1, col2 = st.columns(2)
    with col1:
        quiet_start = st.time_input("Start time",
                                    value=datetime.strptime(prefs.get('quiet_hours_start', '22:00'), '%H:%M').time())
    with col2:
        quiet_end = st.time_input("End time",
                                  value=datetime.strptime(prefs.get('quiet_hours_end', '08:00'), '%H:%M').time())

    # Category preferences
    st.markdown("**Categories**")
    category_prefs = {}
    cols = st.columns(3)
    for i, category in enumerate(NotificationCategory):
        with cols[i % 3]:
            category_prefs[category.value] = st.checkbox(
                category.value.title(),
                value=prefs.get('categories', {}).get(category.value, True),
                key=f"cat_{category.value}"
            )

    # Priority preferences
    st.markdown("**Priorities**")
    priority_prefs = {}
    cols = st.columns(5)
    for i, priority in enumerate(NotificationPriority):
        with cols[i]:
            priority_prefs[priority.value] = st.checkbox(
                priority.value.title(),
                value=prefs.get('priorities', {}).get(priority.value, True),
                key=f"prio_{priority.value}"
            )

    # Save preferences
    if st.button("💾 Save Preferences"):
        new_prefs = {
            'enabled': enabled,
            'sound_enabled': sound_enabled,
            'smart_batching': smart_batching,
            'max_notifications_per_hour': max_per_hour,
            'desktop_notifications': desktop_notifications,
            'quiet_hours_start': quiet_start.strftime('%H:%M'),
            'quiet_hours_end': quiet_end.strftime('%H:%M'),
            'categories': category_prefs,
            'priorities': priority_prefs
        }

        st.session_state.notification_preferences = new_prefs
        manager.user_preferences = new_prefs
        st.success("Preferences saved!")
        st.rerun()


def get_time_ago(timestamp: datetime) -> str:
    """Get human-readable time ago string"""
    now = datetime.now()
    diff = now - timestamp

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


def get_notification_badge_count() -> int:
    """Get the count for notification badge"""
    if 'smart_notification_manager' not in st.session_state:
        return 0

    manager = st.session_state.smart_notification_manager
    unread = manager.get_unread_notifications()

    # Count only high-priority unread notifications for badge
    high_priority_unread = [n for n in unread
                            if n.priority in [NotificationPriority.HIGH, NotificationPriority.URGENT,
                                              NotificationPriority.CRITICAL]]

    return len(high_priority_unread)


def init_smart_notification_system():
    """Initialize the smart notification system"""
    if 'smart_notification_manager' not in st.session_state:
        st.session_state.smart_notification_manager = SmartNotificationManager()

    # Clean up old notifications on startup
    manager = st.session_state.smart_notification_manager
    manager.clear_old_notifications()

    # Process initial notifications
    manager.process_smart_notifications()


# Convenience functions for creating specific notification types
def create_task_completion_celebration(task_title: str, task_data: Dict = None):
    """Create a celebration notification for task completion"""
    if 'smart_notification_manager' not in st.session_state:
        init_smart_notification_system()

    manager = st.session_state.smart_notification_manager
    manager.create_notification(
        "🎉 Task Completed!",
        f"Great job completing '{task_title}'!",
        NotificationType.TASK_COMPLETED,
        NotificationPriority.LOW,
        NotificationCategory.ACHIEVEMENTS,
        data=task_data,
        auto_dismiss=True
    )


def create_pomodoro_notification(notification_type: str, session_data: Dict = None):
    """Create Pomodoro timer notifications"""
    if 'smart_notification_manager' not in st.session_state:
        init_smart_notification_system()

    manager = st.session_state.smart_notification_manager

    if notification_type == "break":
        manager.create_notification(
            "Time for a Break! ☕",
            "Your focus session is complete. Take a well-deserved break!",
            NotificationType.POMODORO_BREAK,
            NotificationPriority.HIGH,
            NotificationCategory.PRODUCTIVITY,
            data=session_data,
            auto_dismiss=True
        )

    elif notification_type == "work":
        manager.create_notification(
            "Back to Work! 💪",
            "Break time is over. Ready to focus on your next task?",
            NotificationType.POMODORO_WORK,
            NotificationPriority.HIGH,
            NotificationCategory.PRODUCTIVITY,
            data=session_data,
            auto_dismiss=True
        )


def generate_weekly_summary():
    """Generate comprehensive weekly summary notification"""
    if 'smart_notification_manager' not in st.session_state:
        init_smart_notification_system()

    manager = st.session_state.smart_notification_manager

    # Calculate comprehensive weekly stats
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_end = week_start + timedelta(days=6)

    # Tasks completed this week
    weekly_tasks = []
    for task in st.session_state.get('tasks', []):
        if task.get('completed_at'):
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

    # Performance insights
    performance_emoji = "🌟" if len(weekly_tasks) > 5 else "👍" if len(weekly_tasks) > 2 else "💪"

    summary = f"""{performance_emoji} Weekly Achievement Summary:

✅ {len(weekly_tasks)} tasks completed
🎯 {weekly_habit_completions} habit completions  
🍅 {weekly_pomodoros} focus sessions

{get_weekly_encouragement(len(weekly_tasks), weekly_habit_completions)}"""

    manager.create_notification(
        "📊 Weekly Summary",
        summary,
        NotificationType.WEEKLY_SUMMARY,
        NotificationPriority.LOW,
        NotificationCategory.INSIGHTS,
        data={
            'week_start': week_start.isoformat(),
            'tasks_completed': len(weekly_tasks),
            'habits_completed': weekly_habit_completions,
            'pomodoro_sessions': weekly_pomodoros
        }
    )


def get_weekly_encouragement(tasks_completed: int, habits_completed: int) -> str:
    """Get encouraging message based on weekly performance"""
    total_score = tasks_completed + (habits_completed * 0.5)

    if total_score >= 10:
        return "Outstanding week! You're crushing your goals! 🚀"
    elif total_score >= 7:
        return "Great progress this week! Keep up the momentum! 💪"
    elif total_score >= 4:
        return "Solid week! Every step forward counts! 👍"
    elif total_score >= 2:
        return "Nice start! Next week, let's aim even higher! 📈"
    else:
        return "New week, fresh start! You've got this! 🌱"
