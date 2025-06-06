import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta, time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time as time_module
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re
from collections import defaultdict, Counter
from utils import *


@dataclass
class ProductivityGoal:
    """Represents a productivity goal"""
    id: str
    title: str
    description: str
    target_value: int
    current_value: int
    metric_type: str  # 'tasks_completed', 'habit_streaks', 'focus_time'
    deadline: date
    created_at: datetime
    completed: bool = False


@dataclass
class TimeBlock:
    """Represents a time block for time blocking"""
    id: str
    title: str
    start_time: time
    end_time: time
    date: date
    task_ids: List[str]
    category: str
    color: str


class AdvancedTaskAnalyzer:
    """Advanced task analysis and insights"""

    @staticmethod
    def analyze_completion_patterns(tasks: List[Dict]) -> Dict:
        """Analyze task completion patterns"""
        completed_tasks = [t for t in tasks if t['status'] == 'completed' and t.get('completed_at')]

        if not completed_tasks:
            return {}

        patterns = {
            'hourly_distribution': defaultdict(int),
            'daily_distribution': defaultdict(int),
            'monthly_distribution': defaultdict(int),
            'priority_completion_times': defaultdict(list),
            'list_completion_times': defaultdict(list),
            'completion_streaks': [],
            'most_productive_periods': {}
        }

        for task in completed_tasks:
            try:
                completed_dt = datetime.fromisoformat(task['completed_at'])
                created_dt = datetime.fromisoformat(task['created_at'])

                # Time distributions
                patterns['hourly_distribution'][completed_dt.hour] += 1
                patterns['daily_distribution'][completed_dt.strftime('%A')] += 1
                patterns['monthly_distribution'][completed_dt.strftime('%B')] += 1

                # Completion time by priority and list
                completion_time_hours = (completed_dt - created_dt).total_seconds() / 3600
                patterns['priority_completion_times'][task['priority']].append(completion_time_hours)
                patterns['list_completion_times'][task['list_name']].append(completion_time_hours)

            except (ValueError, TypeError):
                continue

        # Calculate averages
        for priority, times in patterns['priority_completion_times'].items():
            patterns['priority_completion_times'][priority] = {
                'average': np.mean(times),
                'median': np.median(times),
                'count': len(times)
            }

        for list_name, times in patterns['list_completion_times'].items():
            patterns['list_completion_times'][list_name] = {
                'average': np.mean(times),
                'median': np.median(times),
                'count': len(times)
            }

        # Find most productive periods
        if patterns['hourly_distribution']:
            patterns['most_productive_periods']['hour'] = max(
                patterns['hourly_distribution'],
                key=patterns['hourly_distribution'].get
            )

        if patterns['daily_distribution']:
            patterns['most_productive_periods']['day'] = max(
                patterns['daily_distribution'],
                key=patterns['daily_distribution'].get
            )

        return patterns

    @staticmethod
    def predict_task_completion_time(task: Dict, historical_data: List[Dict]) -> float:
        """Predict task completion time based on historical data"""
        if not historical_data:
            return 2.0  # Default 2 hours

        # Filter similar tasks
        similar_tasks = []
        for hist_task in historical_data:
            if (hist_task['status'] == 'completed' and
                    hist_task.get('completed_at') and
                    hist_task.get('created_at')):

                similarity_score = 0

                # Same priority
                if hist_task['priority'] == task['priority']:
                    similarity_score += 0.3

                # Same list
                if hist_task['list_name'] == task['list_name']:
                    similarity_score += 0.2

                # Similar title (simple word matching)
                task_words = set(task['title'].lower().split())
                hist_words = set(hist_task['title'].lower().split())
                if task_words & hist_words:  # Common words
                    similarity_score += 0.2

                # Similar tags
                task_tags = set(task.get('tags', []))
                hist_tags = set(hist_task.get('tags', []))
                if task_tags & hist_tags:
                    similarity_score += 0.1

                if similarity_score > 0.3:  # Threshold for similarity
                    try:
                        completed_dt = datetime.fromisoformat(hist_task['completed_at'])
                        created_dt = datetime.fromisoformat(hist_task['created_at'])
                        completion_time = (completed_dt - created_dt).total_seconds() / 3600
                        similar_tasks.append((completion_time, similarity_score))
                    except (ValueError, TypeError):
                        continue

        if similar_tasks:
            # Weighted average based on similarity
            total_weight = sum(weight for _, weight in similar_tasks)
            weighted_sum = sum(time * weight for time, weight in similar_tasks)
            return weighted_sum / total_weight

        # Fallback to priority-based estimation
        priority_estimates = {
            'high': 3.0,
            'medium': 2.0,
            'low': 1.0,
            'none': 1.5
        }

        return priority_estimates.get(task['priority'], 2.0)

    @staticmethod
    def detect_procrastination_patterns(tasks: List[Dict]) -> Dict:
        """Detect procrastination patterns in task behavior"""
        patterns = {
            'overdue_by_priority': defaultdict(int),
            'delayed_start_pattern': [],
            'last_minute_completions': 0,
            'chronic_postponement': [],
            'avoidance_categories': defaultdict(int)
        }

        today = date.today()

        for task in tasks:
            # Overdue analysis
            if (task.get('due_date') and task['status'] != 'completed' and
                    datetime.fromisoformat(task['due_date']).date() < today):
                patterns['overdue_by_priority'][task['priority']] += 1
                patterns['avoidance_categories'][task['list_name']] += 1

            # Last minute completion analysis
            if (task['status'] == 'completed' and task.get('due_date') and
                    task.get('completed_at')):
                try:
                    due_date = datetime.fromisoformat(task['due_date']).date()
                    completed_date = datetime.fromisoformat(task['completed_at']).date()

                    if due_date == completed_date:
                        patterns['last_minute_completions'] += 1
                except (ValueError, TypeError):
                    continue

        return patterns


class SmartScheduler:
    """Intelligent task scheduling system"""

    @staticmethod
    def suggest_optimal_schedule(tasks: List[Dict], available_hours: int = 8,
                                 user_preferences: Dict = None) -> List[Dict]:
        """Suggest optimal task schedule based on various factors"""
        if not tasks:
            return []

        # Default preferences
        preferences = {
            'prefer_morning_for_high_priority': True,
            'batch_similar_tasks': True,
            'respect_deadlines': True,
            'energy_curve': 'morning_person',  # 'morning_person', 'night_owl', 'steady'
            'break_frequency': 2  # hours between breaks
        }

        if user_preferences:
            preferences.update(user_preferences)

        # Score tasks for scheduling
        scored_tasks = []
        for task in tasks:
            if task['status'] != 'pending':
                continue

            score = SmartScheduler._calculate_task_priority_score(task, preferences)
            scored_tasks.append((task, score))

        # Sort by score (highest first)
        scored_tasks.sort(key=lambda x: x[1], reverse=True)

        # Create schedule
        schedule = []
        current_time = 9  # Start at 9 AM
        remaining_hours = available_hours

        for task, score in scored_tasks:
            if remaining_hours <= 0:
                break

            # Estimate time needed
            estimated_time = task.get('estimated_time', 120) / 60  # Convert to hours
            if estimated_time == 0:
                estimated_time = 1  # Default 1 hour

            if estimated_time <= remaining_hours:
                schedule_item = {
                    'task': task,
                    'scheduled_time': current_time,
                    'duration': estimated_time,
                    'priority_score': score,
                    'suggested_focus_level': SmartScheduler._suggest_focus_level(task, current_time, preferences)
                }

                schedule.append(schedule_item)
                current_time += estimated_time
                remaining_hours -= estimated_time

                # Add break if needed
                if (len(schedule) % preferences['break_frequency'] == 0 and
                        remaining_hours > 0.25):
                    current_time += 0.25  # 15-minute break
                    remaining_hours -= 0.25

        return schedule

    @staticmethod
    def _calculate_task_priority_score(task: Dict, preferences: Dict) -> float:
        """Calculate priority score for task scheduling"""
        score = 0

        # Priority weight
        priority_weights = {'high': 10, 'medium': 6, 'low': 3, 'none': 1}
        score += priority_weights.get(task['priority'], 1)

        # Deadline urgency
        if task.get('due_date'):
            try:
                due_date = datetime.fromisoformat(task['due_date']).date()
                days_until_due = (due_date - date.today()).days

                if days_until_due <= 0:
                    score += 20  # Overdue
                elif days_until_due == 1:
                    score += 15  # Due tomorrow
                elif days_until_due <= 3:
                    score += 10  # Due soon
                elif days_until_due <= 7:
                    score += 5  # Due this week
            except (ValueError, TypeError):
                pass

        # List-based priority
        important_lists = ['Work', 'Health', 'Personal']
        if task['list_name'] in important_lists:
            score += 3

        # Task age (older tasks get slight priority)
        try:
            created_date = datetime.fromisoformat(task['created_at']).date()
            days_old = (date.today() - created_date).days
            score += min(days_old * 0.1, 2)  # Max 2 points for age
        except (ValueError, TypeError):
            pass

        return score

    @staticmethod
    def _suggest_focus_level(task: Dict, scheduled_time: float, preferences: Dict) -> str:
        """Suggest focus level needed for task"""
        priority = task['priority']

        # High priority tasks need high focus
        if priority == 'high':
            return 'high'

        # Consider time of day based on user preferences
        if preferences['energy_curve'] == 'morning_person':
            if 9 <= scheduled_time <= 12:
                return 'high'
            elif 13 <= scheduled_time <= 15:
                return 'medium'
            else:
                return 'low'
        elif preferences['energy_curve'] == 'night_owl':
            if 15 <= scheduled_time <= 18:
                return 'high'
            elif 9 <= scheduled_time <= 12:
                return 'low'
            else:
                return 'medium'

        return 'medium'  # Default


class TimeBlockingManager:
    """Advanced time blocking functionality"""

    @staticmethod
    def create_time_blocks(date_selected: date, tasks: List[Dict]) -> List[TimeBlock]:
        """Create time blocks for a specific date"""
        if 'time_blocks' not in st.session_state:
            st.session_state.time_blocks = []

        existing_blocks = [tb for tb in st.session_state.time_blocks
                           if datetime.fromisoformat(tb['date']).date() == date_selected]

        return existing_blocks

    @staticmethod
    def suggest_time_blocks(date_selected: date, tasks: List[Dict],
                            work_start: time = time(9, 0),
                            work_end: time = time(17, 0)) -> List[Dict]:
        """Suggest optimal time blocks for tasks"""
        # Filter tasks for the selected date
        date_str = date_selected.isoformat()
        relevant_tasks = [t for t in tasks
                          if (t.get('due_date') == date_str or
                              t['status'] == 'pending') and
                          t.get('estimated_time')]

        if not relevant_tasks:
            return []

        # Sort by priority and deadline
        relevant_tasks.sort(key=lambda t: (
            {'high': 0, 'medium': 1, 'low': 2, 'none': 3}.get(t['priority'], 3),
            t.get('due_date', '9999-12-31')
        ))

        suggestions = []
        current_time = datetime.combine(date_selected, work_start)
        end_time = datetime.combine(date_selected, work_end)

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        color_index = 0

        for task in relevant_tasks:
            if current_time >= end_time:
                break

            duration_minutes = task.get('estimated_time', 60)
            duration = timedelta(minutes=duration_minutes)

            if current_time + duration <= end_time:
                suggestion = {
                    'id': f"block_{len(suggestions)}",
                    'title': task['title'],
                    'start_time': current_time.time().isoformat(),
                    'end_time': (current_time + duration).time().isoformat(),
                    'date': date_selected.isoformat(),
                    'task_ids': [task['id']],
                    'category': task['list_name'],
                    'color': colors[color_index % len(colors)],
                    'estimated_duration': duration_minutes,
                    'priority': task['priority']
                }

                suggestions.append(suggestion)
                current_time += duration

                # Add buffer time between tasks
                current_time += timedelta(minutes=15)
                color_index += 1

        return suggestions


class ProductivityMetricsAnalyzer:
    """Advanced productivity metrics and analysis"""

    @staticmethod
    def calculate_comprehensive_metrics(tasks: List[Dict], habits: List[Dict],
                                        time_period: int = 30) -> Dict:
        """Calculate comprehensive productivity metrics"""
        end_date = date.today()
        start_date = end_date - timedelta(days=time_period)

        metrics = {
            'task_metrics': ProductivityMetricsAnalyzer._analyze_task_metrics(tasks, start_date, end_date),
            'habit_metrics': ProductivityMetricsAnalyzer._analyze_habit_metrics(habits, start_date, end_date),
            'efficiency_metrics': ProductivityMetricsAnalyzer._analyze_efficiency_metrics(tasks, start_date, end_date),
            'consistency_metrics': ProductivityMetricsAnalyzer._analyze_consistency_metrics(tasks, habits, start_date,
                                                                                            end_date),
            'growth_metrics': ProductivityMetricsAnalyzer._analyze_growth_metrics(tasks, habits, start_date, end_date)
        }

        # Calculate overall productivity score
        metrics['overall_score'] = ProductivityMetricsAnalyzer._calculate_overall_score(metrics)

        return metrics

    @staticmethod
    def _analyze_task_metrics(tasks: List[Dict], start_date: date, end_date: date) -> Dict:
        """Analyze task-specific metrics"""
        period_tasks = [t for t in tasks if ProductivityMetricsAnalyzer._is_in_period(t, start_date, end_date)]
        completed_tasks = [t for t in period_tasks if t['status'] == 'completed']

        metrics = {
            'total_tasks': len(period_tasks),
            'completed_tasks': len(completed_tasks),
            'completion_rate': len(completed_tasks) / max(1, len(period_tasks)) * 100,
            'priority_breakdown': defaultdict(int),
            'list_breakdown': defaultdict(int),
            'overdue_tasks': 0,
            'average_completion_time': 0
        }

        completion_times = []

        for task in period_tasks:
            metrics['priority_breakdown'][task['priority']] += 1
            metrics['list_breakdown'][task['list_name']] += 1

            # Check for overdue
            if (task.get('due_date') and task['status'] != 'completed' and
                    datetime.fromisoformat(task['due_date']).date() < end_date):
                metrics['overdue_tasks'] += 1

        for task in completed_tasks:
            if task.get('completed_at') and task.get('created_at'):
                try:
                    completed_dt = datetime.fromisoformat(task['completed_at'])
                    created_dt = datetime.fromisoformat(task['created_at'])
                    completion_time = (completed_dt - created_dt).total_seconds() / 3600
                    completion_times.append(completion_time)
                except (ValueError, TypeError):
                    continue

        if completion_times:
            metrics['average_completion_time'] = np.mean(completion_times)

        return metrics

    @staticmethod
    def _analyze_habit_metrics(habits: List[Dict], start_date: date, end_date: date) -> Dict:
        """Analyze habit-specific metrics"""
        metrics = {
            'total_habits': len(habits),
            'active_habits': len([h for h in habits if h.get('active', True)]),
            'completion_rates': {},
            'streak_analysis': {},
            'consistency_scores': {}
        }

        for habit in habits:
            if not habit.get('active', True):
                continue

            completion_dates = habit.get('completion_dates', [])
            period_completions = []

            for date_str in completion_dates:
                try:
                    completion_date = datetime.fromisoformat(date_str).date()
                    if start_date <= completion_date <= end_date:
                        period_completions.append(completion_date)
                except (ValueError, TypeError):
                    continue

            # Calculate completion rate for period
            total_days = (end_date - start_date).days + 1
            completion_rate = len(period_completions) / total_days * 100
            metrics['completion_rates'][habit['name']] = completion_rate

            # Analyze streaks
            current_streak = habit.get('streak', 0)
            best_streak = habit.get('best_streak', 0)
            metrics['streak_analysis'][habit['name']] = {
                'current': current_streak,
                'best': best_streak,
                'streak_ratio': current_streak / max(1, best_streak)
            }

            # Calculate consistency score
            if len(period_completions) > 1:
                # Calculate gaps between completions
                sorted_completions = sorted(period_completions)
                gaps = []
                for i in range(1, len(sorted_completions)):
                    gap = (sorted_completions[i] - sorted_completions[i - 1]).days
                    gaps.append(gap)

                if gaps:
                    avg_gap = np.mean(gaps)
                    gap_variance = np.var(gaps)
                    consistency_score = max(0, 100 - gap_variance * 10)  # Higher variance = lower consistency
                    metrics['consistency_scores'][habit['name']] = consistency_score

        return metrics

    @staticmethod
    def _analyze_efficiency_metrics(tasks: List[Dict], start_date: date, end_date: date) -> Dict:
        """Analyze efficiency-related metrics"""
        completed_tasks = [t for t in tasks
                           if t['status'] == 'completed' and
                           ProductivityMetricsAnalyzer._is_in_period(t, start_date, end_date)]

        metrics = {
            'time_estimation_accuracy': 0,
            'priority_efficiency': {},
            'focus_effectiveness': 0,
            'task_switching_frequency': 0
        }

        # Time estimation accuracy
        estimation_accuracies = []
        for task in completed_tasks:
            estimated = task.get('estimated_time')
            actual = task.get('actual_time')

            if estimated and actual and estimated > 0:
                accuracy = 1 - abs(estimated - actual) / estimated
                estimation_accuracies.append(max(0, accuracy))

        if estimation_accuracies:
            metrics['time_estimation_accuracy'] = np.mean(estimation_accuracies) * 100

        # Priority efficiency (how well high-priority tasks are completed)
        priority_counts = defaultdict(lambda: {'total': 0, 'completed': 0})

        for task in tasks:
            if ProductivityMetricsAnalyzer._is_in_period(task, start_date, end_date):
                priority_counts[task['priority']]['total'] += 1
                if task['status'] == 'completed':
                    priority_counts[task['priority']]['completed'] += 1

        for priority, counts in priority_counts.items():
            if counts['total'] > 0:
                efficiency = counts['completed'] / counts['total'] * 100
                metrics['priority_efficiency'][priority] = efficiency

        return metrics

    @staticmethod
    def _analyze_consistency_metrics(tasks: List[Dict], habits: List[Dict],
                                     start_date: date, end_date: date) -> Dict:
        """Analyze consistency patterns"""
        # Daily task completion consistency
        daily_completions = defaultdict(int)

        for task in tasks:
            if task['status'] == 'completed' and task.get('completed_at'):
                try:
                    completed_date = datetime.fromisoformat(task['completed_at']).date()
                    if start_date <= completed_date <= end_date:
                        daily_completions[completed_date] += 1
                except (ValueError, TypeError):
                    continue

        completion_counts = list(daily_completions.values())
        consistency_score = 0

        if len(completion_counts) > 1:
            mean_completions = np.mean(completion_counts)
            std_completions = np.std(completion_counts)

            if mean_completions > 0:
                coefficient_of_variation = std_completions / mean_completions
                consistency_score = max(0, 100 - coefficient_of_variation * 100)

        return {
            'daily_task_consistency': consistency_score,
            'average_daily_completions': np.mean(completion_counts) if completion_counts else 0,
            'most_productive_day': max(daily_completions, key=daily_completions.get) if daily_completions else None
        }

    @staticmethod
    def _analyze_growth_metrics(tasks: List[Dict], habits: List[Dict],
                                start_date: date, end_date: date) -> Dict:
        """Analyze growth and improvement trends"""
        # Split period in half to compare
        mid_date = start_date + (end_date - start_date) / 2

        first_half_tasks = [t for t in tasks if ProductivityMetricsAnalyzer._is_in_period(t, start_date, mid_date)]
        second_half_tasks = [t for t in tasks if ProductivityMetricsAnalyzer._is_in_period(t, mid_date, end_date)]

        first_half_completed = len([t for t in first_half_tasks if t['status'] == 'completed'])
        second_half_completed = len([t for t in second_half_tasks if t['status'] == 'completed'])

        # Calculate growth rate
        task_completion_growth = 0
        if first_half_completed > 0:
            task_completion_growth = ((second_half_completed - first_half_completed) / first_half_completed) * 100

        return {
            'task_completion_growth': task_completion_growth,
            'trend_direction': 'improving' if task_completion_growth > 5 else 'stable' if task_completion_growth > -5 else 'declining'
        }

    @staticmethod
    def _calculate_overall_score(metrics: Dict) -> float:
        """Calculate overall productivity score"""
        score_components = []

        # Task completion rate (30% weight)
        task_completion = metrics['task_metrics'].get('completion_rate', 0)
        score_components.append(task_completion * 0.3)

        # Habit consistency (25% weight)
        habit_rates = metrics['habit_metrics'].get('completion_rates', {})
        if habit_rates:
            avg_habit_rate = np.mean(list(habit_rates.values()))
            score_components.append(avg_habit_rate * 0.25)

        # Efficiency (25% weight)
        time_accuracy = metrics['efficiency_metrics'].get('time_estimation_accuracy', 0)
        score_components.append(time_accuracy * 0.25)

        # Consistency (20% weight)
        consistency = metrics['consistency_metrics'].get('daily_task_consistency', 0)
        score_components.append(consistency * 0.2)

        return sum(score_components)

    @staticmethod
    def _is_in_period(task_or_habit: Dict, start_date: date, end_date: date) -> bool:
        """Check if task/habit is within the specified period"""
        created_at = task_or_habit.get('created_at')
        if not created_at:
            return False

        try:
            created_date = datetime.fromisoformat(created_at).date()
            return start_date <= created_date <= end_date
        except (ValueError, TypeError):
            return False


def render_advanced_eisenhower_matrix():
    """Enhanced Eisenhower Matrix with advanced filtering and actions"""
    st.markdown("### 📋 Advanced Eisenhower Matrix")
    st.markdown("*Organize tasks by urgency and importance with smart insights*")

    # Advanced filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        show_completed = st.checkbox("Include completed tasks", value=False)
    with col2:
        time_horizon = st.selectbox("Time horizon",
                                    options=[1, 3, 7, 14, 30],
                                    format_func=lambda x: f"{x} days",
                                    index=2)  # Default 7 days
    with col3:
        list_filter = st.multiselect("Filter by lists",
                                     options=st.session_state.get('lists', []),
                                     default=st.session_state.get('lists', []))
    with col4:
        priority_weights = st.checkbox("Use AI priority weights", value=True)

    tasks = st.session_state.tasks

    # Apply filters
    if not show_completed:
        tasks = [t for t in tasks if t['status'] != 'completed']

    if list_filter:
        tasks = [t for t in tasks if t['list_name'] in list_filter]

    today = date.today()
    cutoff_date = today + timedelta(days=time_horizon)

    # Enhanced categorization with AI-like priority weighting
    quadrants = {
        'urgent_important': [],  # Do First (Q1)
        'not_urgent_important': [],  # Schedule (Q2)
        'urgent_not_important': [],  # Delegate (Q3)
        'not_urgent_not_important': []  # Eliminate (Q4)
    }

    for task in tasks:
        # Determine urgency
        is_urgent = False
        urgency_score = 0

        if task.get('due_date'):
            try:
                due_date = datetime.fromisoformat(task['due_date']).date()
                days_until_due = (due_date - today).days

                if days_until_due <= 0:
                    urgency_score = 1.0  # Overdue
                elif days_until_due <= 1:
                    urgency_score = 0.9  # Due tomorrow
                elif days_until_due <= 3:
                    urgency_score = 0.7  # Due soon
                elif days_until_due <= 7:
                    urgency_score = 0.4  # Due this week
                else:
                    urgency_score = 0.1  # Due later

                is_urgent = urgency_score > 0.5
            except (ValueError, TypeError):
                pass

        # Determine importance
        importance_score = 0

        # Base importance on priority
        priority_scores = {'high': 1.0, 'medium': 0.6, 'low': 0.3, 'none': 0.1}
        importance_score += priority_scores.get(task['priority'], 0.1)

        # Add AI-like weighting if enabled
        if priority_weights:
            # Tags influence importance
            important_tags = ['urgent', 'important', 'critical', 'key', 'milestone']
            task_tags = [tag.lower() for tag in task.get('tags', [])]
            if any(tag in important_tags for tag in task_tags):
                importance_score += 0.2

            # List-based importance
            important_lists = ['Work', 'Health', 'Finance']
            if task['list_name'] in important_lists:
                importance_score += 0.1

            # Title keywords
            important_keywords = ['meeting', 'deadline', 'review', 'presentation', 'doctor']
            title_lower = task['title'].lower()
            if any(keyword in title_lower for keyword in important_keywords):
                importance_score += 0.1

        is_important = importance_score > 0.5

        # Categorize with scores for sorting
        task_with_scores = task.copy()
        task_with_scores['urgency_score'] = urgency_score
        task_with_scores['importance_score'] = importance_score

        if is_urgent and is_important:
            quadrants['urgent_important'].append(task_with_scores)
        elif not is_urgent and is_important:
            quadrants['not_urgent_important'].append(task_with_scores)
        elif is_urgent and not is_important:
            quadrants['urgent_not_important'].append(task_with_scores)
        else:
            quadrants['not_urgent_not_important'].append(task_with_scores)

    # Sort quadrants by scores
    for quadrant in quadrants.values():
        quadrant.sort(key=lambda x: (x['urgency_score'] + x['importance_score']), reverse=True)

    # Render matrix
    col1, col2 = st.columns(2)

    with col1:
        render_matrix_quadrant("🔴 Q1: Do First", "Urgent & Important",
                               quadrants['urgent_important'], "danger")

    with col2:
        render_matrix_quadrant("🟡 Q2: Schedule", "Not Urgent & Important",
                               quadrants['not_urgent_important'], "warning")

    col3, col4 = st.columns(2)

    with col3:
        render_matrix_quadrant("🟠 Q3: Delegate", "Urgent & Not Important",
                               quadrants['urgent_not_important'], "info")

    with col4:
        render_matrix_quadrant("🟢 Q4: Eliminate", "Not Urgent & Not Important",
                               quadrants['not_urgent_not_important'], "success")

    # Action recommendations
    render_matrix_insights(quadrants)


def render_matrix_quadrant(title: str, description: str, tasks: List[Dict], color_type: str):
    """Render individual matrix quadrant with enhanced features"""
    with st.container():
        st.markdown(f"#### {title}")
        st.markdown(f"*{description}*")

        if not tasks:
            st.info("No tasks in this quadrant")
            return

        st.markdown(f"**{len(tasks)} tasks**")

        # Show top tasks with action buttons
        for i, task in enumerate(tasks[:5]):  # Show first 5
            with st.expander(f"{task['title'][:40]}{'...' if len(task['title']) > 40 else ''}",
                             expanded=i == 0):

                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"**Priority:** {task['priority'].title()}")
                    if task.get('due_date'):
                        st.write(f"**Due:** {format_date_display(task['due_date'])}")
                    st.write(f"**List:** {task['list_name']}")

                    if task.get('description'):
                        st.write(f"**Description:** {task['description'][:100]}...")

                    # Show AI scores
                    st.write(f"**Urgency Score:** {task['urgency_score']:.1f}")
                    st.write(f"**Importance Score:** {task['importance_score']:.1f}")

                with col2:
                    if st.button("✅ Complete", key=f"complete_matrix_{task['id']}"):
                        complete_task(task['id'])
                        st.success("Task completed!")
                        st.rerun()

                with col3:
                    if st.button("📝 Edit", key=f"edit_matrix_{task['id']}"):
                        st.session_state.editing_task = task['id']
                        st.rerun()

        if len(tasks) > 5:
            st.markdown(f"... and {len(tasks) - 5} more tasks")


def render_matrix_insights(quadrants: Dict):
    """Render insights and recommendations based on matrix analysis"""
    st.markdown("### 🧠 Matrix Insights & Recommendations")

    total_tasks = sum(len(quadrant) for quadrant in quadrants.values())
    if total_tasks == 0:
        return

    # Calculate distribution
    q1_pct = len(quadrants['urgent_important']) / total_tasks * 100
    q2_pct = len(quadrants['not_urgent_important']) / total_tasks * 100
    q3_pct = len(quadrants['urgent_not_important']) / total_tasks * 100
    q4_pct = len(quadrants['not_urgent_not_important']) / total_tasks * 100

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Task Distribution")

        # Create pie chart
        fig = px.pie(
            values=[q1_pct, q2_pct, q3_pct, q4_pct],
            names=['Q1: Do First', 'Q2: Schedule', 'Q3: Delegate', 'Q4: Eliminate'],
            color_discrete_sequence=['#FF6B6B', '#FFD93D', '#6BCF7F', '#4D96FF']
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🎯 Recommendations")

        recommendations = []

        if q1_pct > 40:
            recommendations.append("🚨 Too many urgent tasks! Focus on prevention and planning.")

        if q2_pct < 20:
            recommendations.append("📅 Invest more time in important, non-urgent activities for long-term success.")

        if q3_pct > 30:
            recommendations.append("🤝 Consider delegating or automating urgent but less important tasks.")

        if q4_pct > 25:
            recommendations.append("🗑️ Review and eliminate low-value activities to free up time.")

        if not recommendations:
            recommendations.append("✅ Great balance! Your task distribution looks healthy.")

        for rec in recommendations:
            st.write(f"• {rec}")

        # Action buttons
        if q1_pct > 30:
            if st.button("🎯 Start Focus Session", type="primary"):
                st.session_state.current_view = "pomodoro"
                st.rerun()


def render_smart_scheduling():
    """Render intelligent task scheduling interface"""
    st.markdown("### 🧠 Smart Task Scheduler")
    st.markdown("*AI-powered scheduling based on your productivity patterns*")

    # Configuration
    col1, col2, col3 = st.columns(3)

    with col1:
        available_hours = st.slider("Available hours today", 1, 12, 8)
        energy_curve = st.selectbox("Energy pattern",
                                    ['morning_person', 'night_owl', 'steady'])

    with col2:
        prefer_morning_priority = st.checkbox("High priority in morning", value=True)
        batch_similar = st.checkbox("Batch similar tasks", value=True)

    with col3:
        break_frequency = st.slider("Break frequency (hours)", 1, 4, 2)
        include_completed = st.checkbox("Include completed tasks in analysis", value=False)

    # Get pending tasks
    pending_tasks = [t for t in st.session_state.tasks
                     if t['status'] == 'pending']

    if not pending_tasks:
        st.info("No pending tasks to schedule!")
        return

    # User preferences
    preferences = {
        'prefer_morning_for_high_priority': prefer_morning_priority,
        'batch_similar_tasks': batch_similar,
        'energy_curve': energy_curve,
        'break_frequency': break_frequency
    }

    # Generate schedule
    if st.button("🚀 Generate Smart Schedule", type="primary"):
        with st.spinner("Analyzing your tasks and generating optimal schedule..."):
            schedule = SmartScheduler.suggest_optimal_schedule(
                pending_tasks, available_hours, preferences
            )

        if schedule:
            st.success(f"Generated schedule for {len(schedule)} tasks!")
            render_schedule_visualization(schedule)
            render_schedule_timeline(schedule)
        else:
            st.warning("Could not generate schedule. Try adjusting your parameters.")


def render_schedule_visualization(schedule: List[Dict]):
    """Render schedule as visual timeline"""
    st.markdown("#### 📅 Your Optimized Schedule")

    # Create Gantt-like chart
    fig = go.Figure()

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']

    for i, item in enumerate(schedule):
        task = item['task']
        start_time = item['scheduled_time']
        duration = item['duration']

        # Create time labels
        start_str = f"{int(start_time):02d}:{int((start_time % 1) * 60):02d}"
        end_str = f"{int(start_time + duration):02d}:{int(((start_time + duration) % 1) * 60):02d}"

        fig.add_trace(go.Bar(
            name=task['title'][:30],
            x=[duration],
            y=[i],
            orientation='h',
            marker_color=colors[i % len(colors)],
            text=f"{start_str}-{end_str}",
            textposition='middle center',
            hovertemplate=f"<b>{task['title']}</b><br>" +
                          f"Time: {start_str} - {end_str}<br>" +
                          f"Duration: {duration:.1f}h<br>" +
                          f"Priority: {task['priority'].title()}<br>" +
                          f"Focus Level: {item['suggested_focus_level'].title()}<extra></extra>"
        ))

    fig.update_layout(
        title="Daily Schedule Timeline",
        xaxis_title="Duration (hours)",
        yaxis_title="Tasks",
        height=max(400, len(schedule) * 50),
        showlegend=False,
        yaxis=dict(tickmode='array',
                   tickvals=list(range(len(schedule))),
                   ticktext=[item['task']['title'][:30] for item in schedule])
    )

    st.plotly_chart(fig, use_container_width=True)


def render_schedule_timeline(schedule: List[Dict]):
    """Render detailed schedule timeline"""
    st.markdown("#### ⏰ Detailed Timeline")

    for i, item in enumerate(schedule):
        task = item['task']
        start_time = item['scheduled_time']
        duration = item['duration']
        focus_level = item['suggested_focus_level']

        # Time formatting
        start_str = f"{int(start_time):02d}:{int((start_time % 1) * 60):02d}"
        end_str = f"{int(start_time + duration):02d}:{int(((start_time + duration) % 1) * 60):02d}"

        # Focus level styling
        focus_colors = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }

        with st.container():
            col1, col2, col3, col4 = st.columns([2, 3, 2, 1])

            with col1:
                st.markdown(f"**⏰ {start_str} - {end_str}**")
                st.markdown(f"*{duration:.1f}h duration*")

            with col2:
                st.markdown(f"**📋 {task['title']}**")
                st.markdown(f"📁 {task['list_name']} | 🎯 {task['priority'].title()}")

            with col3:
                st.markdown(f"**Focus Level**")
                st.markdown(f"{focus_colors.get(focus_level, '⚪')} {focus_level.title()}")

            with col4:
                if st.button("▶️ Start", key=f"start_scheduled_{i}"):
                    # Start Pomodoro for this task
                    st.session_state.pomodoro_state = {
                        'active': True,
                        'start_time': time_module.time(),
                        'duration': min(25, int(duration * 60)),  # Max 25 min Pomodoro
                        'current_type': 'work',
                        'current_task': task['title']
                    }
                    st.session_state.current_view = "pomodoro"
                    st.rerun()

            st.divider()


def render_time_blocking_interface():
    """Render advanced time blocking interface"""
    st.markdown("### 📅 Time Blocking Planner")
    st.markdown("*Plan your day with focused time blocks*")

    # Date selection
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_date = st.date_input("Select date", value=date.today())

    with col2:
        work_start = st.time_input("Work start time", value=time(9, 0))

    with col3:
        work_end = st.time_input("Work end time", value=time(17, 0))

    # Get tasks for selected date
    date_str = selected_date.isoformat()
    relevant_tasks = [t for t in st.session_state.tasks
                      if (t.get('due_date') == date_str or t['status'] == 'pending')]

    if not relevant_tasks:
        st.info(f"No tasks found for {selected_date.strftime('%B %d, %Y')}")
        return

    # Generate suggestions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🚀 Generate Time Blocks", type="primary"):
            suggestions = TimeBlockingManager.suggest_time_blocks(
                selected_date, relevant_tasks, work_start, work_end
            )

            if suggestions:
                st.session_state.current_time_block_suggestions = suggestions
                st.success(f"Generated {len(suggestions)} time blocks!")
            else:
                st.warning("Could not generate time blocks. Try adding estimated times to your tasks.")

    with col2:
        if st.button("📋 View Existing Blocks"):
            existing_blocks = TimeBlockingManager.create_time_blocks(selected_date, relevant_tasks)
            st.session_state.current_time_blocks = existing_blocks

    # Display suggestions or existing blocks
    if hasattr(st.session_state, 'current_time_block_suggestions'):
        render_time_block_suggestions(st.session_state.current_time_block_suggestions)

    if hasattr(st.session_state, 'current_time_blocks'):
        render_existing_time_blocks(st.session_state.current_time_blocks)


def render_time_block_suggestions(suggestions: List[Dict]):
    """Render time block suggestions"""
    st.markdown("#### 💡 Suggested Time Blocks")

    for i, block in enumerate(suggestions):
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 3, 2, 1])

            with col1:
                start_time = datetime.strptime(block['start_time'], '%H:%M:%S').time()
                end_time = datetime.strptime(block['end_time'], '%H:%M:%S').time()
                st.markdown(f"**⏰ {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}**")

            with col2:
                st.markdown(f"**📋 {block['title']}**")
                st.markdown(f"📁 {block['category']} | 🎯 {block['priority'].title()}")

            with col3:
                duration_min = block['estimated_duration']
                st.markdown(f"**Duration:** {duration_min} min")

                # Color indicator
                st.markdown(
                    f"<div style='width:20px;height:20px;background-color:{block['color']};border-radius:3px;display:inline-block;'></div>",
                    unsafe_allow_html=True)

            with col4:
                if st.button("✅ Accept", key=f"accept_block_{i}"):
                    # Add to time blocks
                    if 'time_blocks' not in st.session_state:
                        st.session_state.time_blocks = []

                    st.session_state.time_blocks.append(block)
                    st.success("Time block added!")
                    st.rerun()

            st.divider()


def render_existing_time_blocks(blocks: List[Dict]):
    """Render existing time blocks"""
    if not blocks:
        st.info("No existing time blocks for this date.")
        return

    st.markdown("#### 📅 Existing Time Blocks")

    for i, block in enumerate(blocks):
        with st.container():
            col1, col2, col3 = st.columns([2, 4, 1])

            with col1:
                start_time = datetime.strptime(block['start_time'], '%H:%M:%S').time()
                end_time = datetime.strptime(block['end_time'], '%H:%M:%S').time()
                st.markdown(f"**⏰ {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}**")

            with col2:
                st.markdown(f"**📋 {block['title']}**")
                st.markdown(f"📁 {block['category']}")

            with col3:
                if st.button("🗑️", key=f"delete_block_{i}", help="Delete block"):
                    st.session_state.time_blocks.remove(block)
                    st.rerun()

            st.divider()


def render_comprehensive_analytics():
    """Render comprehensive productivity analytics"""
    st.markdown("### 📊 Comprehensive Productivity Analytics")

    # Time period selection
    col1, col2, col3 = st.columns(3)

    with col1:
        time_period = st.selectbox("Analysis period",
                                   options=[7, 14, 30, 60, 90],
                                   format_func=lambda x: f"Last {x} days",
                                   index=2)  # Default 30 days

    with col2:
        include_weekends = st.checkbox("Include weekends", value=True)

    with col3:
        show_predictions = st.checkbox("Show predictions", value=True)

    # Calculate comprehensive metrics
    tasks = st.session_state.tasks
    habits = st.session_state.habits

    with st.spinner("Analyzing your productivity data..."):
        metrics = ProductivityMetricsAnalyzer.calculate_comprehensive_metrics(
            tasks, habits, time_period
        )

    # Overall score
    overall_score = metrics.get('overall_score', 0)
    score_color = "success" if overall_score >= 80 else "warning" if overall_score >= 60 else "error"

    st.markdown(f"### 🎯 Overall Productivity Score")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Score", f"{overall_score:.1f}/100",
                delta=f"{overall_score - 70:.1f}" if overall_score > 70 else None)

    task_metrics = metrics.get('task_metrics', {})
    col2.metric("Task Completion", f"{task_metrics.get('completion_rate', 0):.1f}%")
    col3.metric("Completed Tasks", task_metrics.get('completed_tasks', 0))
    col4.metric("Avg. Completion Time", f"{task_metrics.get('average_completion_time', 0):.1f}h")

    # Detailed metrics tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Task Analysis", "🎯 Habit Analysis", "⚡ Efficiency", "📈 Growth"])

    with tab1:
        render_task_analytics(task_metrics)

    with tab2:
        render_habit_analytics(metrics.get('habit_metrics', {}))

    with tab3:
        render_efficiency_analytics(metrics.get('efficiency_metrics', {}))

    with tab4:
        render_growth_analytics(metrics.get('growth_metrics', {}))


def render_task_analytics(task_metrics: Dict):
    """Render detailed task analytics"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎯 Priority Breakdown")
        priority_data = task_metrics.get('priority_breakdown', {})

        if priority_data:
            fig = px.bar(
                x=list(priority_data.keys()),
                y=list(priority_data.values()),
                title="Tasks by Priority",
                color=list(priority_data.keys()),
                color_discrete_map={
                    'high': '#FF6B6B',
                    'medium': '#FFD93D',
                    'low': '#4ECDC4',
                    'none': '#95A5A6'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No priority data available")

    with col2:
        st.markdown("#### 📁 List Distribution")
        list_data = task_metrics.get('list_breakdown', {})

        if list_data:
            fig = px.pie(
                values=list(list_data.values()),
                names=list(list_data.keys()),
                title="Tasks by List"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No list data available")

    # Key insights
    st.markdown("#### 💡 Key Insights")

    insights = []
    completion_rate = task_metrics.get('completion_rate', 0)
    overdue_tasks = task_metrics.get('overdue_tasks', 0)

    if completion_rate >= 80:
        insights.append("🌟 Excellent completion rate! You're staying on top of your tasks.")
    elif completion_rate >= 60:
        insights.append("👍 Good completion rate, but there's room for improvement.")
    else:
        insights.append("⚠️ Low completion rate. Consider reviewing your task management strategy.")

    if overdue_tasks > 0:
        insights.append(f"📅 You have {overdue_tasks} overdue tasks. Consider prioritizing these.")
    else:
        insights.append("✅ No overdue tasks! Great job staying current.")

    for insight in insights:
        st.write(f"• {insight}")


def render_habit_analytics(habit_metrics: Dict):
    """Render detailed habit analytics"""
    completion_rates = habit_metrics.get('completion_rates', {})
    streak_analysis = habit_metrics.get('streak_analysis', {})

    if not completion_rates:
        st.info("No habit data available for analysis")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Completion Rates")

        if completion_rates:
            fig = px.bar(
                x=list(completion_rates.keys()),
                y=list(completion_rates.values()),
                title="Habit Completion Rates (%)",
                color=list(completion_rates.values()),
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🔥 Streak Analysis")

        if streak_analysis:
            streak_data = []
            for habit, data in streak_analysis.items():
                streak_data.append({
                    'Habit': habit,
                    'Current Streak': data['current'],
                    'Best Streak': data['best']
                })

            df = pd.DataFrame(streak_data)
            st.dataframe(df, use_container_width=True)

    # Habit recommendations
    st.markdown("#### 🎯 Habit Recommendations")

    recommendations = []
    avg_completion = np.mean(list(completion_rates.values())) if completion_rates else 0

    if avg_completion >= 80:
        recommendations.append("🌟 Outstanding habit consistency! Consider adding new challenging habits.")
    elif avg_completion >= 60:
        recommendations.append("👍 Good habit performance. Focus on the habits with lower completion rates.")
    else:
        recommendations.append("📈 Habit completion could be improved. Consider reducing targets or habit count.")

    # Find lowest performing habit
    if completion_rates:
        lowest_habit = min(completion_rates, key=completion_rates.get)
        lowest_rate = completion_rates[lowest_habit]
        if lowest_rate < 50:
            recommendations.append(
                f"🎯 Focus on '{lowest_habit}' - it has the lowest completion rate ({lowest_rate:.1f}%).")

    for rec in recommendations:
        st.write(f"• {rec}")


def render_efficiency_analytics(efficiency_metrics: Dict):
    """Render efficiency analytics"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ⏱️ Time Estimation Accuracy")
        accuracy = efficiency_metrics.get('time_estimation_accuracy', 0)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=accuracy,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Estimation Accuracy (%)"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🎯 Priority Efficiency")
        priority_efficiency = efficiency_metrics.get('priority_efficiency', {})

        if priority_efficiency:
            fig = px.bar(
                x=list(priority_efficiency.keys()),
                y=list(priority_efficiency.values()),
                title="Completion Rate by Priority (%)",
                color=list(priority_efficiency.values()),
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No priority efficiency data available")

    # Efficiency insights
    st.markdown("#### 💡 Efficiency Insights")

    insights = []

    if accuracy >= 80:
        insights.append("🎯 Excellent time estimation! You know your work patterns well.")
    elif accuracy >= 60:
        insights.append("👍 Good time estimation. Small adjustments could improve accuracy.")
    else:
        insights.append("⏱️ Time estimation needs work. Track actual vs. estimated time more carefully.")

    if priority_efficiency:
        high_priority_eff = priority_efficiency.get('high', 0)
        if high_priority_eff < 70:
            insights.append("🚨 High-priority task completion is low. Focus on these first.")
        else:
            insights.append("✅ Good high-priority task completion rate.")

    for insight in insights:
        st.write(f"• {insight}")


def render_growth_analytics(growth_metrics: Dict):
    """Render growth and trend analytics"""
    growth_rate = growth_metrics.get('task_completion_growth', 0)
    trend = growth_metrics.get('trend_direction', 'stable')

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📈 Growth Trend")

        # Growth indicator
        color = "success" if growth_rate > 5 else "warning" if growth_rate > -5 else "error"
        st.metric("Task Completion Growth", f"{growth_rate:+.1f}%",
                  delta=f"{trend.title()}")

        # Trend visualization
        if growth_rate != 0:
            trend_data = [0, growth_rate]
            fig = px.line(
                x=['Start', 'Current'],
                y=trend_data,
                title="Growth Trajectory",
                markers=True
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🎯 Future Projections")

        if growth_rate > 0:
            projected_improvement = growth_rate * 2  # Simple projection
            st.success(f"📈 If current trend continues, expect {projected_improvement:.1f}% improvement next period")
        elif growth_rate < -5:
            st.warning("📉 Declining trend detected. Consider reviewing your productivity strategies.")
        else:
            st.info("📊 Stable performance. Look for opportunities to optimize.")

        # Recommendations based on trend
        st.markdown("**Recommendations:**")

        if trend == 'improving':
            st.write("• 🚀 Keep up the great work! Consider what's working and do more of it.")
            st.write("• 📈 This is a good time to take on new challenges.")
        elif trend == 'declining':
            st.write("• 🔍 Analyze what changed and identify obstacles.")
            st.write("• 🎯 Focus on completing smaller, achievable tasks to rebuild momentum.")
        else:
            st.write("• 💡 Look for new strategies to break out of the plateau.")
            st.write("• 🔄 Consider changing your approach or trying new productivity techniques.")


# Additional utility functions for the enhanced features
def calculate_task_similarity(task1: Dict, task2: Dict) -> float:
    """Calculate similarity score between two tasks"""
    score = 0

    # Title similarity (simple word overlap)
    words1 = set(task1['title'].lower().split())
    words2 = set(task2['title'].lower().split())
    word_overlap = len(words1 & words2) / max(len(words1 | words2), 1)
    score += word_overlap * 0.4

    # Same priority
    if task1['priority'] == task2['priority']:
        score += 0.2

    # Same list
    if task1['list_name'] == task2['list_name']:
        score += 0.2

    # Tag overlap
    tags1 = set(task1.get('tags', []))
    tags2 = set(task2.get('tags', []))
    if tags1 or tags2:
        tag_overlap = len(tags1 & tags2) / max(len(tags1 | tags2), 1)
        score += tag_overlap * 0.2

    return score


def generate_smart_insights(tasks: List[Dict], habits: List[Dict]) -> List[str]:
    """Generate smart insights based on user data"""
    insights = []

    # Task insights
    if tasks:
        overdue_count = len([t for t in tasks
                             if t.get('due_date') and t['status'] != 'completed' and
                             datetime.fromisoformat(t['due_date']).date() < date.today()])

        if overdue_count > 0:
            insights.append(f"🚨 You have {overdue_count} overdue tasks. Consider using the Focus Mode to catch up.")

        # Priority distribution
        high_priority = len([t for t in tasks if t['priority'] == 'high' and t['status'] == 'pending'])
        if high_priority > 5:
            insights.append(
                f"⚡ You have {high_priority} high-priority tasks. Consider breaking some into smaller tasks.")

    # Habit insights
    if habits:
        today_str = date.today().isoformat()
        completed_today = len([h for h in habits if today_str in h.get('completion_dates', [])])
        total_active = len([h for h in habits if h.get('active', True)])

        if total_active > 0:
            completion_rate = completed_today / total_active * 100
            if completion_rate < 50:
                insights.append(f"🎯 Only {completion_rate:.0f}% of habits completed today. Small steps count!")

    # Time-based insights
    current_hour = datetime.now().hour
    if 9 <= current_hour <= 11:
        insights.append("🌅 Morning energy is high! Perfect time for important tasks.")
    elif 14 <= current_hour <= 16:
        insights.append("☕ Post-lunch dip period. Consider easier tasks or a short break.")

    return insights
