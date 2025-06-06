import json
import os
import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional
import streamlit as st
from pathlib import Path


class DataManager:
    """Handles data persistence for the TickTick clone"""

    def __init__(self, storage_type="file"):
        self.storage_type = storage_type
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "ticktick.db"

        if storage_type == "sqlite":
            self.init_database()

    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority TEXT,
                list_name TEXT,
                status TEXT,
                created_at TEXT,
                completed_at TEXT,
                tags TEXT,
                subtasks TEXT,
                recurring TEXT,
                reminder TEXT,
                estimated_time INTEGER,
                actual_time INTEGER
            )
        """)

        # Habits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                frequency TEXT,
                target INTEGER,
                reminder_time TEXT,
                created_at TEXT,
                completion_dates TEXT,
                streak INTEGER,
                best_streak INTEGER
            )
        """)

        # Lists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                name TEXT PRIMARY KEY,
                created_at TEXT,
                color TEXT,
                folder TEXT
            )
        """)

        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tasks TEXT,
                created_at TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_data(self, data_type: str, data: List[Dict]):
        """Save data based on storage type"""
        if self.storage_type == "file":
            self._save_to_file(data_type, data)
        elif self.storage_type == "sqlite":
            self._save_to_sqlite(data_type, data)

    def load_data(self, data_type: str) -> List[Dict]:
        """Load data based on storage type"""
        if self.storage_type == "file":
            return self._load_from_file(data_type)
        elif self.storage_type == "sqlite":
            return self._load_from_sqlite(data_type)
        return []

    def _save_to_file(self, data_type: str, data: List[Dict]):
        """Save data to JSON file"""
        file_path = self.data_dir / f"{data_type}.json"

        # Convert date objects to strings for JSON serialization
        serializable_data = []
        for item in data:
            serializable_item = item.copy()
            for key, value in serializable_item.items():
                if isinstance(value, (date, datetime)):
                    serializable_item[key] = value.isoformat()
                elif isinstance(value, list):
                    serializable_item[key] = json.dumps(value)
            serializable_data.append(serializable_item)

        with open(file_path, 'w') as f:
            json.dump(serializable_data, f, indent=2, default=str)

    def _load_from_file(self, data_type: str) -> List[Dict]:
        """Load data from JSON file"""
        file_path = self.data_dir / f"{data_type}.json"

        if not file_path.exists():
            return []

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Convert JSON strings back to lists for certain fields
            processed_data = []
            for item in data:
                processed_item = item.copy()

                # Handle list fields that were stored as JSON strings
                list_fields = ['tags', 'subtasks', 'completion_dates']
                for field in list_fields:
                    if field in processed_item and isinstance(processed_item[field], str):
                        try:
                            processed_item[field] = json.loads(processed_item[field])
                        except:
                            processed_item[field] = []

                processed_data.append(processed_item)

            return processed_data
        except Exception as e:
            st.error(f"Error loading {data_type}: {str(e)}")
            return []

    def _save_to_sqlite(self, data_type: str, data: List[Dict]):
        """Save data to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if data_type == "tasks":
            # Clear existing tasks
            cursor.execute("DELETE FROM tasks")

            # Insert tasks
            for task in data:
                cursor.execute("""
                    INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task['id'], task['title'], task.get('description', ''),
                    task.get('due_date'), task['priority'], task['list_name'],
                    task['status'], task['created_at'], task.get('completed_at'),
                    json.dumps(task.get('tags', [])), json.dumps(task.get('subtasks', [])),
                    task.get('recurring'), task.get('reminder'),
                    task.get('estimated_time'), task.get('actual_time')
                ))

        elif data_type == "habits":
            cursor.execute("DELETE FROM habits")

            for habit in data:
                cursor.execute("""
                    INSERT INTO habits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    habit['id'], habit['name'], habit['frequency'],
                    habit['target'], habit.get('reminder_time'),
                    habit['created_at'], json.dumps(habit.get('completion_dates', [])),
                    habit.get('streak', 0), habit.get('best_streak', 0)
                ))

        elif data_type == "lists":
            cursor.execute("DELETE FROM lists")

            for list_item in data:
                cursor.execute("""
                    INSERT INTO lists VALUES (?, ?, ?, ?)
                """, (
                    list_item['name'], list_item.get('created_at', datetime.now().isoformat()),
                    list_item.get('color'), list_item.get('folder')
                ))

        conn.commit()
        conn.close()

    def _load_from_sqlite(self, data_type: str) -> List[Dict]:
        """Load data from SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if data_type == "tasks":
                cursor.execute("SELECT * FROM tasks")
                rows = cursor.fetchall()

                columns = ['id', 'title', 'description', 'due_date', 'priority',
                           'list_name', 'status', 'created_at', 'completed_at',
                           'tags', 'subtasks', 'recurring', 'reminder',
                           'estimated_time', 'actual_time']

                tasks = []
                for row in rows:
                    task = dict(zip(columns, row))
                    # Parse JSON fields
                    task['tags'] = json.loads(task['tags']) if task['tags'] else []
                    task['subtasks'] = json.loads(task['subtasks']) if task['subtasks'] else []
                    tasks.append(task)

                return tasks

            elif data_type == "habits":
                cursor.execute("SELECT * FROM habits")
                rows = cursor.fetchall()

                columns = ['id', 'name', 'frequency', 'target', 'reminder_time',
                           'created_at', 'completion_dates', 'streak', 'best_streak']

                habits = []
                for row in rows:
                    habit = dict(zip(columns, row))
                    habit['completion_dates'] = json.loads(habit['completion_dates']) if habit[
                        'completion_dates'] else []
                    habits.append(habit)

                return habits

            elif data_type == "lists":
                cursor.execute("SELECT * FROM lists")
                rows = cursor.fetchall()

                columns = ['name', 'created_at', 'color', 'folder']

                return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            st.error(f"Error loading {data_type} from database: {str(e)}")
            return []
        finally:
            conn.close()

    def backup_data(self, backup_path: str = None) -> str:
        """Create a complete backup of all data"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.data_dir / f"backup_{timestamp}.json"

        backup_data = {
            'tasks': self.load_data('tasks'),
            'habits': self.load_data('habits'),
            'lists': st.session_state.get('lists', []),
            'folders': st.session_state.get('folders', []),
            'templates': st.session_state.get('task_templates', []),
            'settings': st.session_state.get('app_settings', {}),
            'backup_date': datetime.now().isoformat(),
            'version': '1.0'
        }

        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)

        return str(backup_path)

    def restore_data(self, backup_path: str) -> bool:
        """Restore data from backup"""
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            # Restore to session state
            if 'tasks' in backup_data:
                st.session_state.tasks = backup_data['tasks']
                self.save_data('tasks', backup_data['tasks'])

            if 'habits' in backup_data:
                st.session_state.habits = backup_data['habits']
                self.save_data('habits', backup_data['habits'])

            if 'lists' in backup_data:
                st.session_state.lists = backup_data['lists']

            if 'folders' in backup_data:
                st.session_state.folders = backup_data['folders']

            if 'templates' in backup_data:
                st.session_state.task_templates = backup_data['templates']

            if 'settings' in backup_data:
                st.session_state.app_settings = backup_data['settings']

            return True
        except Exception as e:
            st.error(f"Error restoring backup: {str(e)}")
            return False

    def export_to_csv(self) -> Dict[str, str]:
        """Export data to CSV format"""
        csv_files = {}

        # Export tasks
        tasks = self.load_data('tasks')
        if tasks:
            df_tasks = pd.DataFrame(tasks)
            tasks_csv = df_tasks.to_csv(index=False)
            csv_files['tasks'] = tasks_csv

        # Export habits
        habits = self.load_data('habits')
        if habits:
            # Flatten habit data for CSV
            habit_rows = []
            for habit in habits:
                base_row = {
                    'id': habit['id'],
                    'name': habit['name'],
                    'frequency': habit['frequency'],
                    'target': habit['target'],
                    'created_at': habit['created_at'],
                    'streak': habit.get('streak', 0),
                    'best_streak': habit.get('best_streak', 0)
                }

                # Add completion dates as separate rows
                for completion_date in habit.get('completion_dates', []):
                    row = base_row.copy()
                    row['completion_date'] = completion_date
                    habit_rows.append(row)

                # Add at least one row even if no completions
                if not habit.get('completion_dates'):
                    habit_rows.append(base_row)

            df_habits = pd.DataFrame(habit_rows)
            habits_csv = df_habits.to_csv(index=False)
            csv_files['habits'] = habits_csv

        return csv_files

    def get_storage_stats(self) -> Dict:
        """Get storage usage statistics"""
        stats = {
            'storage_type': self.storage_type,
            'data_directory': str(self.data_dir),
            'files': {}
        }

        if self.storage_type == "file":
            for file_path in self.data_dir.glob("*.json"):
                stats['files'][file_path.name] = {
                    'size_bytes': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }

        elif self.storage_type == "sqlite":
            if self.db_path.exists():
                stats['database'] = {
                    'path': str(self.db_path),
                    'size_bytes': self.db_path.stat().st_size,
                    'modified': datetime.fromtimestamp(self.db_path.stat().st_mtime).isoformat()
                }

                # Get table statistics
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                tables = ['tasks', 'habits', 'lists', 'settings', 'templates']
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        stats['files'][f"{table}_count"] = count
                    except:
                        stats['files'][f"{table}_count"] = 0

                conn.close()

        return stats

    def cleanup_old_backups(self, keep_count: int = 10):
        """Clean up old backup files, keeping only the most recent ones"""
        backup_files = list(self.data_dir.glob("backup_*.json"))

        if len(backup_files) <= keep_count:
            return

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Delete old backups
        for old_backup in backup_files[keep_count:]:
            try:
                old_backup.unlink()
            except Exception as e:
                st.warning(f"Could not delete old backup {old_backup.name}: {str(e)}")


def auto_save_data():
    """Auto-save function to be called periodically"""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager("file")

    data_manager = st.session_state.data_manager

    try:
        # Save tasks and habits
        if 'tasks' in st.session_state:
            data_manager.save_data('tasks', st.session_state.tasks)

        if 'habits' in st.session_state:
            data_manager.save_data('habits', st.session_state.habits)

        # Update last save time
        st.session_state.last_auto_save = datetime.now()

    except Exception as e:
        st.error(f"Auto-save failed: {str(e)}")


def load_saved_data():
    """Load saved data when the app starts"""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager("file")

    data_manager = st.session_state.data_manager

    try:
        # Load tasks
        saved_tasks = data_manager.load_data('tasks')
        if saved_tasks:
            st.session_state.tasks = saved_tasks

        # Load habits
        saved_habits = data_manager.load_data('habits')
        if saved_habits:
            st.session_state.habits = saved_habits

        return True
    except Exception as e:
        st.error(f"Failed to load saved data: {str(e)}")
        return False


def create_data_manager(storage_type: str = "file") -> DataManager:
    """Factory function to create data manager"""
    return DataManager(storage_type)