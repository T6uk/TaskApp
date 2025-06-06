#!/usr/bin/env python3
"""
TickTick Clone - Desktop Version
Alternative desktop interface using tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import json
from datetime import datetime, date, timedelta
from pathlib import Path
import threading
import time
from utils import *


class TickTickDesktop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TickTick Clone - Desktop")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')

        # Load data
        self.load_data()

        # Setup UI
        self.setup_styles()
        self.create_widgets()
        self.refresh_task_list()

        # Setup auto-save
        self.setup_auto_save()

    def setup_styles(self):
        """Configure ttk styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure colors
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Priority.High.TLabel', foreground='#e74c3c')
        self.style.configure('Priority.Medium.TLabel', foreground='#f39c12')
        self.style.configure('Priority.Low.TLabel', foreground='#3498db')

    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(main_frame, text="📋 TickTick Clone", style='Title.TLabel')
        title_label.pack(pady=(0, 20))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.create_tasks_tab()
        self.create_habits_tab()
        self.create_pomodoro_tab()
        self.create_stats_tab()

    def create_tasks_tab(self):
        """Create tasks management tab"""
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text="📝 Tasks")

        # Top frame for controls
        top_frame = ttk.Frame(tasks_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Quick add frame
        add_frame = ttk.LabelFrame(top_frame, text="➕ Add Task")
        add_frame.pack(fill=tk.X, pady=(0, 10))

        # Task input
        input_frame = ttk.Frame(add_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(input_frame, text="Task:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.task_entry = ttk.Entry(input_frame, width=40)
        self.task_entry.grid(row=0, column=1, padx=(0, 10))
        self.task_entry.bind('<Return>', self.add_task_from_entry)

        ttk.Label(input_frame, text="Priority:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.priority_var = tk.StringVar(value="none")
        priority_combo = ttk.Combobox(input_frame, textvariable=self.priority_var,
                                      values=["none", "low", "medium", "high"], width=10)
        priority_combo.grid(row=0, column=3, padx=(0, 10))

        ttk.Label(input_frame, text="List:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.list_var = tk.StringVar(value="Inbox")
        list_combo = ttk.Combobox(input_frame, textvariable=self.list_var,
                                  values=getattr(self, 'lists', ["Inbox", "Personal", "Work"]), width=15)
        list_combo.grid(row=0, column=5, padx=(0, 10))

        add_button = ttk.Button(input_frame, text="Add Task", command=self.add_task)
        add_button.grid(row=0, column=6)

        # Filter frame
        filter_frame = ttk.LabelFrame(top_frame, text="🔍 Filters")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        filter_controls = ttk.Frame(filter_frame)
        filter_controls.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(filter_controls, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.status_filter = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_controls, textvariable=self.status_filter,
                                    values=["All", "Pending", "Completed"], width=12)
        status_combo.grid(row=0, column=1, padx=(0, 10))
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_task_list())

        ttk.Label(filter_controls, text="Priority:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.priority_filter = tk.StringVar(value="All")
        priority_filter_combo = ttk.Combobox(filter_controls, textvariable=self.priority_filter,
                                             values=["All", "High", "Medium", "Low", "None"], width=12)
        priority_filter_combo.grid(row=0, column=3, padx=(0, 10))
        priority_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_task_list())

        refresh_button = ttk.Button(filter_controls, text="🔄 Refresh", command=self.refresh_task_list)
        refresh_button.grid(row=0, column=4, padx=(10, 0))

        # Tasks list
        list_frame = ttk.LabelFrame(tasks_frame, text="📋 Tasks")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create treeview for tasks
        columns = ('Priority', 'Title', 'List', 'Due Date', 'Status')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)

        # Configure columns
        self.task_tree.heading('#0', text='☐')
        self.task_tree.column('#0', width=30, minwidth=30)

        for col in columns:
            self.task_tree.heading(col, text=col)
            if col == 'Title':
                self.task_tree.column(col, width=300)
            elif col == 'Priority':
                self.task_tree.column(col, width=80)
            else:
                self.task_tree.column(col, width=120)

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.task_tree.bind('<Double-1>', self.on_task_double_click)
        self.task_tree.bind('<Button-3>', self.show_task_context_menu)

        # Context menu
        self.task_context_menu = tk.Menu(self.root, tearoff=0)
        self.task_context_menu.add_command(label="✅ Complete", command=self.complete_selected_task)
        self.task_context_menu.add_command(label="✏️ Edit", command=self.edit_selected_task)
        self.task_context_menu.add_command(label="🗑️ Delete", command=self.delete_selected_task)

        # Status bar
        self.status_bar = ttk.Label(tasks_frame, text="Ready")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    def create_habits_tab(self):
        """Create habits tracking tab"""
        habits_frame = ttk.Frame(self.notebook)
        self.notebook.add(habits_frame, text="🎯 Habits")

        # Add habit frame
        add_habit_frame = ttk.LabelFrame(habits_frame, text="➕ Add Habit")
        add_habit_frame.pack(fill=tk.X, padx=10, pady=10)

        habit_input_frame = ttk.Frame(add_habit_frame)
        habit_input_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(habit_input_frame, text="Habit:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.habit_entry = ttk.Entry(habit_input_frame, width=30)
        self.habit_entry.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(habit_input_frame, text="Frequency:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.habit_frequency = tk.StringVar(value="daily")
        frequency_combo = ttk.Combobox(habit_input_frame, textvariable=self.habit_frequency,
                                       values=["daily", "weekly", "monthly"], width=12)
        frequency_combo.grid(row=0, column=3, padx=(0, 10))

        add_habit_button = ttk.Button(habit_input_frame, text="Add Habit", command=self.add_habit)
        add_habit_button.grid(row=0, column=4)

        # Habits list
        habits_list_frame = ttk.LabelFrame(habits_frame, text="🎯 My Habits")
        habits_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.habits_frame = ttk.Frame(habits_list_frame)
        self.habits_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.refresh_habits_list()

    def create_pomodoro_tab(self):
        """Create Pomodoro timer tab"""
        pomodoro_frame = ttk.Frame(self.notebook)
        self.notebook.add(pomodoro_frame, text="🍅 Pomodoro")

        # Timer display
        timer_display_frame = ttk.Frame(pomodoro_frame)
        timer_display_frame.pack(expand=True, fill=tk.BOTH)

        self.timer_label = ttk.Label(timer_display_frame, text="25:00",
                                     font=('Arial', 48, 'bold'))
        self.timer_label.pack(expand=True)

        # Timer controls
        controls_frame = ttk.Frame(pomodoro_frame)
        controls_frame.pack(pady=20)

        self.start_button = ttk.Button(controls_frame, text="▶️ Start Work", command=self.start_pomodoro)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = ttk.Button(controls_frame, text="⏸️ Pause", command=self.pause_pomodoro, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(controls_frame, text="⏹️ Stop", command=self.stop_pomodoro, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Settings
        settings_frame = ttk.LabelFrame(pomodoro_frame, text="⚙️ Settings")
        settings_frame.pack(fill=tk.X, padx=10, pady=10)

        settings_controls = ttk.Frame(settings_frame)
        settings_controls.pack(padx=10, pady=10)

        ttk.Label(settings_controls, text="Work (min):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.work_duration = tk.IntVar(value=25)
        work_spinbox = ttk.Spinbox(settings_controls, from_=1, to=60, textvariable=self.work_duration, width=10)
        work_spinbox.grid(row=0, column=1, padx=(0, 20))

        ttk.Label(settings_controls, text="Break (min):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.break_duration = tk.IntVar(value=5)
        break_spinbox = ttk.Spinbox(settings_controls, from_=1, to=30, textvariable=self.break_duration, width=10)
        break_spinbox.grid(row=0, column=3)

        # Initialize timer state
        self.timer_active = False
        self.timer_paused = False
        self.timer_start_time = None
        self.current_timer_duration = 25 * 60
        self.timer_type = "work"

    def create_stats_tab(self):
        """Create statistics tab"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Statistics")

        # Stats display
        self.stats_text = ScrolledText(stats_frame, height=20, width=80)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        refresh_stats_button = ttk.Button(stats_frame, text="🔄 Refresh Stats", command=self.refresh_stats)
        refresh_stats_button.pack(pady=10)

        self.refresh_stats()

    def load_data(self):
        """Load data from files"""
        data_dir = Path("data")

        # Load tasks
        tasks_file = data_dir / "tasks.json"
        if tasks_file.exists():
            with open(tasks_file, 'r') as f:
                self.tasks = json.load(f)
        else:
            self.tasks = []

        # Load habits
        habits_file = data_dir / "habits.json"
        if habits_file.exists():
            with open(habits_file, 'r') as f:
                self.habits = json.load(f)
        else:
            self.habits = []

        # Load lists
        self.lists = ["Inbox", "Personal", "Work", "Shopping", "Health"]

    def save_data(self):
        """Save data to files"""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # Save tasks
        with open(data_dir / "tasks.json", 'w') as f:
            json.dump(self.tasks, f, indent=2)

        # Save habits
        with open(data_dir / "habits.json", 'w') as f:
            json.dump(self.habits, f, indent=2)

    def add_task_from_entry(self, event):
        """Add task when Enter is pressed"""
        self.add_task()

    def add_task(self):
        """Add a new task"""
        title = self.task_entry.get().strip()
        if not title:
            messagebox.showwarning("Warning", "Please enter a task title")
            return

        task = {
            "id": datetime.now().isoformat() + "_" + str(hash(title)),
            "title": title,
            "description": "",
            "due_date": None,
            "priority": self.priority_var.get(),
            "list_name": self.list_var.get(),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "tags": [],
            "subtasks": []
        }

        self.tasks.append(task)
        self.save_data()
        self.refresh_task_list()
        self.task_entry.delete(0, tk.END)
        self.update_status("Task added successfully")

    def refresh_task_list(self):
        """Refresh the tasks list display"""
        # Clear existing items
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # Filter tasks
        filtered_tasks = self.tasks.copy()

        # Apply status filter
        status_filter = self.status_filter.get()
        if status_filter != "All":
            status_value = "pending" if status_filter == "Pending" else "completed"
            filtered_tasks = [t for t in filtered_tasks if t['status'] == status_value]

        # Apply priority filter
        priority_filter = self.priority_filter.get()
        if priority_filter != "All":
            priority_value = priority_filter.lower()
            filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority_value]

        # Sort tasks
        filtered_tasks.sort(key=lambda x: (x['status'] == 'completed', x['priority']))

        # Add tasks to tree
        for task in filtered_tasks:
            # Format display values
            priority_display = task['priority'].title()
            due_date_display = task['due_date'] if task['due_date'] else "No date"
            status_display = "✅" if task['status'] == 'completed' else "⭕"

            # Determine priority color
            priority_tag = f"priority_{task['priority']}"

            # Insert task
            item = self.task_tree.insert('', tk.END,
                                         text=status_display,
                                         values=(priority_display, task['title'],
                                                 task['list_name'], due_date_display,
                                                 task['status'].title()),
                                         tags=(priority_tag,))

            # Store task data with item
            self.task_tree.set(item, '#0', status_display)

        # Configure tags for priority colors
        self.task_tree.tag_configure('priority_high', foreground='#e74c3c')
        self.task_tree.tag_configure('priority_medium', foreground='#f39c12')
        self.task_tree.tag_configure('priority_low', foreground='#3498db')

        # Update status
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks if t['status'] == 'completed'])
        pending_tasks = total_tasks - completed_tasks

        self.update_status(f"Tasks: {total_tasks} total, {pending_tasks} pending, {completed_tasks} completed")

    def on_task_double_click(self, event):
        """Handle double-click on task"""
        self.complete_selected_task()

    def show_task_context_menu(self, event):
        """Show context menu for tasks"""
        item = self.task_tree.identify_row(event.y)
        if item:
            self.task_tree.selection_set(item)
            self.task_context_menu.post(event.x_root, event.y_root)

    def complete_selected_task(self):
        """Complete the selected task"""
        selection = self.task_tree.selection()
        if not selection:
            return

        item = selection[0]
        task_title = self.task_tree.item(item)['values'][1]

        # Find and update task
        for task in self.tasks:
            if task['title'] == task_title:
                if task['status'] == 'pending':
                    task['status'] = 'completed'
                    task['completed_at'] = datetime.now().isoformat()
                    self.update_status(f"Completed: {task['title']}")
                else:
                    task['status'] = 'pending'
                    task['completed_at'] = None
                    self.update_status(f"Reopened: {task['title']}")
                break

        self.save_data()
        self.refresh_task_list()

    def edit_selected_task(self):
        """Edit the selected task"""
        selection = self.task_tree.selection()
        if not selection:
            return

        item = selection[0]
        task_title = self.task_tree.item(item)['values'][1]

        # Find task
        task = next((t for t in self.tasks if t['title'] == task_title), None)
        if not task:
            return

        # Simple edit dialog
        new_title = simpledialog.askstring("Edit Task", "Task title:", initialvalue=task['title'])
        if new_title:
            task['title'] = new_title
            self.save_data()
            self.refresh_task_list()
            self.update_status(f"Updated: {new_title}")

    def delete_selected_task(self):
        """Delete the selected task"""
        selection = self.task_tree.selection()
        if not selection:
            return

        item = selection[0]
        task_title = self.task_tree.item(item)['values'][1]

        if messagebox.askyesno("Confirm Delete", f"Delete task '{task_title}'?"):
            self.tasks = [t for t in self.tasks if t['title'] != task_title]
            self.save_data()
            self.refresh_task_list()
            self.update_status(f"Deleted: {task_title}")

    def add_habit(self):
        """Add a new habit"""
        name = self.habit_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a habit name")
            return

        habit = {
            "id": datetime.now().isoformat() + "_" + str(hash(name)),
            "name": name,
            "frequency": self.habit_frequency.get(),
            "target": 1,
            "created_at": datetime.now().isoformat(),
            "completion_dates": [],
            "streak": 0,
            "best_streak": 0
        }

        self.habits.append(habit)
        self.save_data()
        self.refresh_habits_list()
        self.habit_entry.delete(0, tk.END)

    def refresh_habits_list(self):
        """Refresh the habits list display"""
        # Clear existing widgets
        for widget in self.habits_frame.winfo_children():
            widget.destroy()

        if not self.habits:
            ttk.Label(self.habits_frame, text="No habits yet. Add one above!").pack(pady=20)
            return

        for habit in self.habits:
            habit_frame = ttk.Frame(self.habits_frame)
            habit_frame.pack(fill=tk.X, pady=5)

            # Habit info
            info_frame = ttk.Frame(habit_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            ttk.Label(info_frame, text=habit['name'], font=('Arial', 11, 'bold')).pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Frequency: {habit['frequency'].title()}").pack(anchor=tk.W)

            # Completion status
            today = date.today().isoformat()
            completed_today = today in habit.get('completion_dates', [])

            # Action buttons
            button_frame = ttk.Frame(habit_frame)
            button_frame.pack(side=tk.RIGHT)

            if completed_today:
                ttk.Label(button_frame, text="✅ Done today", foreground='green').pack()
            else:
                complete_btn = ttk.Button(button_frame, text="Mark Complete",
                                          command=lambda h=habit: self.complete_habit(h))
                complete_btn.pack()

            ttk.Separator(self.habits_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

    def complete_habit(self, habit):
        """Mark habit as completed for today"""
        today = date.today().isoformat()
        if today not in habit['completion_dates']:
            habit['completion_dates'].append(today)
            habit['completion_dates'].sort()

            # Update streak
            self.update_habit_streak(habit)

            self.save_data()
            self.refresh_habits_list()
            messagebox.showinfo("Success", f"Marked '{habit['name']}' as complete!")

    def update_habit_streak(self, habit):
        """Update habit streak"""
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

    def start_pomodoro(self):
        """Start Pomodoro timer"""
        if not self.timer_active:
            self.timer_active = True
            self.timer_paused = False
            self.timer_start_time = time.time()
            self.current_timer_duration = self.work_duration.get() * 60
            self.timer_type = "work"

            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)

            self.update_timer()

    def pause_pomodoro(self):
        """Pause/resume Pomodoro timer"""
        if self.timer_active:
            if not self.timer_paused:
                self.timer_paused = True
                self.pause_button.config(text="▶️ Resume")
            else:
                self.timer_paused = False
                self.timer_start_time = time.time() - (self.work_duration.get() * 60 - self.current_timer_duration)
                self.pause_button.config(text="⏸️ Pause")

    def stop_pomodoro(self):
        """Stop Pomodoro timer"""
        self.timer_active = False
        self.timer_paused = False
        self.current_timer_duration = self.work_duration.get() * 60

        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="⏸️ Pause")
        self.stop_button.config(state=tk.DISABLED)

        self.timer_label.config(text=f"{self.work_duration.get()}:00")

    def update_timer(self):
        """Update timer display"""
        if self.timer_active and not self.timer_paused:
            elapsed = time.time() - self.timer_start_time
            remaining = max(0, self.current_timer_duration - elapsed)

            if remaining <= 0:
                # Timer finished
                self.timer_finished()
                return

            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")

        if self.timer_active:
            self.root.after(1000, self.update_timer)

    def timer_finished(self):
        """Handle timer completion"""
        if self.timer_type == "work":
            messagebox.showinfo("Pomodoro", "Work session complete! Time for a break.")
            self.timer_type = "break"
            self.current_timer_duration = self.break_duration.get() * 60
        else:
            messagebox.showinfo("Pomodoro", "Break time over! Ready for work?")
            self.timer_type = "work"
            self.current_timer_duration = self.work_duration.get() * 60

        self.stop_pomodoro()

    def refresh_stats(self):
        """Refresh statistics display"""
        self.stats_text.delete(1.0, tk.END)

        # Calculate stats
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks if t['status'] == 'completed'])
        pending_tasks = total_tasks - completed_tasks

        # Priority distribution
        priority_counts = {}
        for task in self.tasks:
            priority = task['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Habits stats
        total_habits = len(self.habits)
        today = date.today().isoformat()
        completed_habits_today = len([h for h in self.habits if today in h.get('completion_dates', [])])

        # Create stats text
        stats_text = f"""📊 TICKTICK CLONE STATISTICS
{'=' * 50}

📝 TASKS OVERVIEW
Total Tasks: {total_tasks}
Completed: {completed_tasks}
Pending: {pending_tasks}
Completion Rate: {(completed_tasks / total_tasks * 100):.1f}% if total_tasks > 0 else 0

📊 PRIORITY DISTRIBUTION
High Priority: {priority_counts.get('high', 0)}
Medium Priority: {priority_counts.get('medium', 0)}
Low Priority: {priority_counts.get('low', 0)}
No Priority: {priority_counts.get('none', 0)}

🎯 HABITS OVERVIEW
Total Habits: {total_habits}
Completed Today: {completed_habits_today}
Today's Rate: {(completed_habits_today / total_habits * 100):.1f}% if total_habits > 0 else 0

📋 LISTS BREAKDOWN
"""

        # List breakdown
        list_stats = {}
        for task in self.tasks:
            list_name = task['list_name']
            if list_name not in list_stats:
                list_stats[list_name] = {'total': 0, 'completed': 0}
            list_stats[list_name]['total'] += 1
            if task['status'] == 'completed':
                list_stats[list_name]['completed'] += 1

        for list_name, stats in list_stats.items():
            completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            stats_text += f"{list_name}: {stats['completed']}/{stats['total']} ({completion_rate:.1f}%)\n"

        # Recent activity
        stats_text += f"\n📈 RECENT ACTIVITY (Last 7 days)\n"
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent_completions = [t for t in self.tasks
                              if t.get('completed_at') and t['completed_at'] > week_ago]

        stats_text += f"Tasks completed: {len(recent_completions)}\n"

        for task in recent_completions[-5:]:  # Show last 5
            completed_date = datetime.fromisoformat(task['completed_at']).strftime('%m/%d %H:%M')
            stats_text += f"  • {task['title']} - {completed_date}\n"

        self.stats_text.insert(1.0, stats_text)

    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)
        self.root.after(3000, lambda: self.status_bar.config(text="Ready"))

    def setup_auto_save(self):
        """Setup automatic saving"""

        def auto_save():
            self.save_data()
            self.root.after(30000, auto_save)  # Save every 30 seconds

        self.root.after(30000, auto_save)

    def run(self):
        """Start the application"""
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")

        # Start main loop
        self.root.mainloop()

    def on_closing(self):
        """Handle application closing"""
        self.save_data()
        self.root.destroy()


def main():
    """Main function"""
    print("Starting TickTick Clone Desktop...")

    # Create and run app
    app = TickTickDesktop()
    app.run()


if __name__ == "__main__":
    main()