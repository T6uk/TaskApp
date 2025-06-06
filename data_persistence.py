import json
import os
import sqlite3
import pandas as pd
import shutil
import zipfile
import hashlib
import threading
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import streamlit as st


@dataclass
class BackupMetadata:
    """Metadata for backup files"""
    timestamp: str
    version: str
    file_count: int
    total_size: int
    checksum: str
    backup_type: str  # 'manual', 'auto', 'scheduled'
    description: Optional[str] = None


@dataclass
class SyncStatus:
    """Status of data synchronization"""
    last_sync: Optional[str]
    pending_changes: int
    sync_errors: List[str]
    is_syncing: bool = False


class DataValidator:
    """Validates data integrity and structure"""

    @staticmethod
    def validate_task(task: Dict) -> Tuple[bool, List[str]]:
        """Validate task data structure"""
        errors = []
        required_fields = ['id', 'title', 'status', 'created_at']

        for field in required_fields:
            if field not in task:
                errors.append(f"Missing required field: {field}")

        # Validate data types
        if 'created_at' in task:
            try:
                datetime.fromisoformat(task['created_at'])
            except ValueError:
                errors.append("Invalid created_at format")

        if 'due_date' in task and task['due_date']:
            try:
                datetime.fromisoformat(task['due_date'])
            except ValueError:
                errors.append("Invalid due_date format")

        # Validate enums
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if task.get('status') not in valid_statuses:
            errors.append(f"Invalid status: {task.get('status')}")

        valid_priorities = ['none', 'low', 'medium', 'high']
        if task.get('priority') not in valid_priorities:
            errors.append(f"Invalid priority: {task.get('priority')}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_habit(habit: Dict) -> Tuple[bool, List[str]]:
        """Validate habit data structure"""
        errors = []
        required_fields = ['id', 'name', 'frequency', 'created_at']

        for field in required_fields:
            if field not in habit:
                errors.append(f"Missing required field: {field}")

        # Validate frequency
        valid_frequencies = ['daily', 'weekly', 'monthly', 'custom']
        if habit.get('frequency') not in valid_frequencies:
            errors.append(f"Invalid frequency: {habit.get('frequency')}")

        # Validate completion dates
        if 'completion_dates' in habit:
            for date_str in habit['completion_dates']:
                try:
                    datetime.fromisoformat(date_str)
                except ValueError:
                    errors.append(f"Invalid completion date: {date_str}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_full_dataset(data: Dict) -> Tuple[bool, List[str]]:
        """Validate complete dataset"""
        errors = []

        # Validate structure
        required_sections = ['tasks', 'habits']
        for section in required_sections:
            if section not in data:
                errors.append(f"Missing required section: {section}")

        # Validate individual items
        if 'tasks' in data:
            for i, task in enumerate(data['tasks']):
                valid, task_errors = DataValidator.validate_task(task)
                if not valid:
                    errors.extend([f"Task {i}: {error}" for error in task_errors])

        if 'habits' in data:
            for i, habit in enumerate(data['habits']):
                valid, habit_errors = DataValidator.validate_habit(habit)
                if not valid:
                    errors.extend([f"Habit {i}: {error}" for error in habit_errors])

        return len(errors) == 0, errors


class SmartDataManager:
    """Enhanced data manager with smart features, backup, and sync capabilities"""

    def __init__(self, storage_type: str = "file", auto_backup: bool = True):
        self.storage_type = storage_type
        self.auto_backup = auto_backup
        self.data_dir = Path("data")
        self.backup_dir = Path("backups")
        self.cache_dir = Path("cache")

        # Create directories
        for directory in [self.data_dir, self.backup_dir, self.cache_dir]:
            directory.mkdir(exist_ok=True)

        self.db_path = self.data_dir / "ticktick_enhanced.db"
        self.lock_file = self.data_dir / ".lock"

        # Initialize storage
        if storage_type == "sqlite":
            self.init_database()

        # Background backup thread
        self._backup_thread = None
        self._stop_backup = threading.Event()

        # Data change tracking
        self.change_log = []
        self.last_save_time = datetime.now()

        # Performance metrics
        self.performance_metrics = {
            'save_times': [],
            'load_times': [],
            'backup_times': [],
            'data_sizes': []
        }

    def init_database(self):
        """Initialize SQLite database with enhanced schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enhanced tasks table
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
                updated_at TEXT,
                completed_at TEXT,
                tags TEXT,
                subtasks TEXT,
                recurring TEXT,
                reminder TEXT,
                estimated_time INTEGER,
                actual_time INTEGER,
                completion_percentage INTEGER DEFAULT 0,
                parent_task_id TEXT,
                dependencies TEXT,
                notes TEXT,
                version INTEGER DEFAULT 1,
                checksum TEXT
            )
        """)

        # Enhanced habits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                frequency TEXT,
                target INTEGER,
                reminder_time TEXT,
                category TEXT,
                created_at TEXT,
                updated_at TEXT,
                completion_dates TEXT,
                streak INTEGER,
                best_streak INTEGER,
                total_completions INTEGER,
                active BOOLEAN DEFAULT 1,
                notes TEXT,
                version INTEGER DEFAULT 1,
                checksum TEXT
            )
        """)

        # Lists table with metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                name TEXT PRIMARY KEY,
                created_at TEXT,
                updated_at TEXT,
                color TEXT,
                folder TEXT,
                description TEXT,
                task_count INTEGER DEFAULT 0,
                completed_count INTEGER DEFAULT 0,
                archived BOOLEAN DEFAULT 0
            )
        """)

        # Settings table with versioning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                data_type TEXT,
                updated_at TEXT,
                version INTEGER DEFAULT 1
            )
        """)

        # Templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                tasks TEXT,
                created_at TEXT,
                updated_at TEXT,
                usage_count INTEGER DEFAULT 0
            )
        """)

        # Change log table for audit trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,
                entity_id TEXT,
                action TEXT,
                changes TEXT,
                timestamp TEXT,
                user_info TEXT
            )
        """)

        # Backup metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backup_metadata (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                version TEXT,
                file_count INTEGER,
                total_size INTEGER,
                checksum TEXT,
                backup_type TEXT,
                description TEXT,
                status TEXT
            )
        """)

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_list ON tasks(list_name)",
            "CREATE INDEX IF NOT EXISTS idx_habits_active ON habits(active)",
            "CREATE INDEX IF NOT EXISTS idx_change_log_timestamp ON change_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_change_log_entity ON change_log(entity_type, entity_id)"
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()
        conn.close()

    def acquire_lock(self, timeout: int = 30) -> bool:
        """Acquire file lock for safe concurrent access"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if not self.lock_file.exists():
                    self.lock_file.write_text(str(os.getpid()))
                    return True
                else:
                    # Check if lock is stale
                    lock_content = self.lock_file.read_text().strip()
                    if lock_content.isdigit():
                        lock_pid = int(lock_content)
                        try:
                            # Check if process is still running
                            os.kill(lock_pid, 0)
                        except OSError:
                            # Process doesn't exist, remove stale lock
                            self.lock_file.unlink()
                            continue

                    time.sleep(0.1)
            except Exception:
                time.sleep(0.1)

        return False

    def release_lock(self):
        """Release file lock"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception:
            pass

    def calculate_checksum(self, data: Any) -> str:
        """Calculate checksum for data integrity"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def save_data(self, data_type: str, data: List[Dict], validate: bool = True) -> bool:
        """Enhanced save with validation, change tracking, and performance monitoring"""
        start_time = time.time()

        try:
            # Acquire lock
            if not self.acquire_lock():
                st.error("Could not acquire data lock. Please try again.")
                return False

            # Validate data if requested
            if validate:
                if data_type == 'tasks':
                    for task in data:
                        valid, errors = DataValidator.validate_task(task)
                        if not valid:
                            st.error(f"Task validation failed: {'; '.join(errors)}")
                            return False
                elif data_type == 'habits':
                    for habit in data:
                        valid, errors = DataValidator.validate_habit(habit)
                        if not valid:
                            st.error(f"Habit validation failed: {'; '.join(errors)}")
                            return False

            # Add checksums and version info
            for item in data:
                if 'updated_at' not in item:
                    item['updated_at'] = datetime.now().isoformat()
                item['checksum'] = self.calculate_checksum(item)
                item['version'] = item.get('version', 1) + 1

            # Save based on storage type
            success = False
            if self.storage_type == "file":
                success = self._save_to_file(data_type, data)
            elif self.storage_type == "sqlite":
                success = self._save_to_sqlite(data_type, data)

            if success:
                # Log changes
                self._log_change(data_type, 'bulk_update', {'count': len(data)})

                # Update performance metrics
                save_time = time.time() - start_time
                self.performance_metrics['save_times'].append(save_time)
                self.performance_metrics['data_sizes'].append(len(json.dumps(data)))

                # Keep only last 100 metrics
                for metric_list in self.performance_metrics.values():
                    if len(metric_list) > 100:
                        metric_list[:] = metric_list[-100:]

                # Auto-backup if enabled
                if self.auto_backup and len(data) > 0:
                    self.create_auto_backup()

                self.last_save_time = datetime.now()
                return True

            return False

        except Exception as e:
            st.error(f"Save failed: {str(e)}")
            return False
        finally:
            self.release_lock()

    def load_data(self, data_type: str, validate: bool = True) -> List[Dict]:
        """Enhanced load with validation and error recovery"""
        start_time = time.time()

        try:
            # Load based on storage type
            data = []
            if self.storage_type == "file":
                data = self._load_from_file(data_type)
            elif self.storage_type == "sqlite":
                data = self._load_from_sqlite(data_type)

            # Validate loaded data
            if validate and data:
                validated_data = []
                for item in data:
                    if data_type == 'tasks':
                        valid, errors = DataValidator.validate_task(item)
                    elif data_type == 'habits':
                        valid, errors = DataValidator.validate_habit(item)
                    else:
                        valid = True

                    if valid:
                        validated_data.append(item)
                    else:
                        st.warning(f"Skipped invalid {data_type[:-1]}: {'; '.join(errors)}")

                data = validated_data

            # Update performance metrics
            load_time = time.time() - start_time
            self.performance_metrics['load_times'].append(load_time)

            return data

        except Exception as e:
            st.error(f"Load failed: {str(e)}")

            # Try to recover from backup
            if self.auto_backup:
                st.info("Attempting to recover from backup...")
                return self._recover_from_backup(data_type)

            return []

    def _save_to_file(self, data_type: str, data: List[Dict]) -> bool:
        """Enhanced file saving with atomic writes"""
        file_path = self.data_dir / f"{data_type}.json"
        temp_path = self.data_dir / f"{data_type}.json.tmp"

        try:
            # Convert data for JSON serialization
            serializable_data = []
            for item in data:
                serializable_item = self._prepare_for_json(item)
                serializable_data.append(serializable_item)

            # Write to temporary file first
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'timestamp': datetime.now().isoformat(),
                        'version': '2.0',
                        'count': len(serializable_data),
                        'checksum': self.calculate_checksum(serializable_data)
                    },
                    'data': serializable_data
                }, f, indent=2, default=str, ensure_ascii=False)

            # Atomic move
            temp_path.replace(file_path)
            return True

        except Exception as e:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise e

    def _load_from_file(self, data_type: str) -> List[Dict]:
        """Enhanced file loading with metadata validation"""
        file_path = self.data_dir / f"{data_type}.json"

        if not file_path.exists():
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = json.load(f)

            # Handle both old and new format
            if isinstance(file_content, list):
                # Old format
                data = file_content
            else:
                # New format with metadata
                metadata = file_content.get('metadata', {})
                data = file_content.get('data', [])

                # Validate checksum if available
                if 'checksum' in metadata:
                    calculated_checksum = self.calculate_checksum(data)
                    if calculated_checksum != metadata['checksum']:
                        st.warning(f"Data integrity check failed for {data_type}")

            # Process loaded data
            processed_data = []
            for item in data:
                processed_item = self._process_loaded_item(item)
                processed_data.append(processed_item)

            return processed_data

        except Exception as e:
            st.error(f"Error loading {data_type}: {str(e)}")
            return []

    def _prepare_for_json(self, item: Dict) -> Dict:
        """Prepare item for JSON serialization"""
        serializable_item = item.copy()

        for key, value in serializable_item.items():
            if isinstance(value, (date, datetime)):
                serializable_item[key] = value.isoformat()
            elif isinstance(value, list) and key in ['tags', 'subtasks', 'completion_dates', 'dependencies']:
                serializable_item[key] = json.dumps(value) if value else "[]"
            elif isinstance(value, dict):
                serializable_item[key] = json.dumps(value)

        return serializable_item

    def _process_loaded_item(self, item: Dict) -> Dict:
        """Process item after loading from storage"""
        processed_item = item.copy()

        # Handle list fields that were stored as JSON strings
        list_fields = ['tags', 'subtasks', 'completion_dates', 'dependencies', 'notes']
        for field in list_fields:
            if field in processed_item and isinstance(processed_item[field], str):
                try:
                    processed_item[field] = json.loads(processed_item[field])
                except:
                    processed_item[field] = []

        return processed_item

    def _save_to_sqlite(self, data_type: str, data: List[Dict]) -> bool:
        """Enhanced SQLite saving with transactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION")

            if data_type == "tasks":
                cursor.execute("DELETE FROM tasks")
                for task in data:
                    cursor.execute("""
                        INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        task['id'], task['title'], task.get('description', ''),
                        task.get('due_date'), task['priority'], task['list_name'],
                        task['status'], task['created_at'], task.get('updated_at'),
                        task.get('completed_at'), json.dumps(task.get('tags', [])),
                        json.dumps(task.get('subtasks', [])), task.get('recurring'),
                        task.get('reminder'), task.get('estimated_time'),
                        task.get('actual_time'), task.get('completion_percentage', 0),
                        task.get('parent_task_id'), json.dumps(task.get('dependencies', [])),
                        json.dumps(task.get('notes', [])), task.get('version', 1),
                        task.get('checksum', '')
                    ))

            elif data_type == "habits":
                cursor.execute("DELETE FROM habits")
                for habit in data:
                    cursor.execute("""
                        INSERT INTO habits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        habit['id'], habit['name'], habit['frequency'],
                        habit['target'], habit.get('reminder_time'),
                        habit.get('category', 'General'), habit['created_at'],
                        habit.get('updated_at'), json.dumps(habit.get('completion_dates', [])),
                        habit.get('streak', 0), habit.get('best_streak', 0),
                        habit.get('total_completions', 0), habit.get('active', True),
                        habit.get('notes', ''), habit.get('version', 1),
                        habit.get('checksum', '')
                    ))

            cursor.execute("COMMIT")
            return True

        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
        finally:
            conn.close()

    def _load_from_sqlite(self, data_type: str) -> List[Dict]:
        """Enhanced SQLite loading with proper data typing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if data_type == "tasks":
                cursor.execute("SELECT * FROM tasks")
                rows = cursor.fetchall()

                columns = [
                    'id', 'title', 'description', 'due_date', 'priority',
                    'list_name', 'status', 'created_at', 'updated_at', 'completed_at',
                    'tags', 'subtasks', 'recurring', 'reminder', 'estimated_time',
                    'actual_time', 'completion_percentage', 'parent_task_id',
                    'dependencies', 'notes', 'version', 'checksum'
                ]

                tasks = []
                for row in rows:
                    task = dict(zip(columns, row))
                    # Parse JSON fields
                    for field in ['tags', 'subtasks', 'dependencies', 'notes']:
                        if task[field]:
                            try:
                                task[field] = json.loads(task[field])
                            except:
                                task[field] = []
                    tasks.append(task)

                return tasks

            elif data_type == "habits":
                cursor.execute("SELECT * FROM habits")
                rows = cursor.fetchall()

                columns = [
                    'id', 'name', 'frequency', 'target', 'reminder_time',
                    'category', 'created_at', 'updated_at', 'completion_dates',
                    'streak', 'best_streak', 'total_completions', 'active',
                    'notes', 'version', 'checksum'
                ]

                habits = []
                for row in rows:
                    habit = dict(zip(columns, row))
                    # Parse JSON field
                    if habit['completion_dates']:
                        try:
                            habit['completion_dates'] = json.loads(habit['completion_dates'])
                        except:
                            habit['completion_dates'] = []
                    habits.append(habit)

                return habits

        except Exception as e:
            st.error(f"Error loading {data_type} from database: {str(e)}")
            return []
        finally:
            conn.close()

    def create_backup(self, description: str = None, backup_type: str = "manual") -> str:
        """Create comprehensive backup with metadata"""
        start_time = time.time()

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"backup_{timestamp}"
            backup_path = self.backup_dir / f"{backup_id}.zip"

            # Collect all data
            backup_data = {
                'metadata': {
                    'id': backup_id,
                    'timestamp': datetime.now().isoformat(),
                    'version': '2.0',
                    'description': description,
                    'backup_type': backup_type
                },
                'tasks': self.load_data('tasks', validate=False),
                'habits': self.load_data('habits', validate=False),
                'lists': st.session_state.get('lists', []),
                'folders': st.session_state.get('folders', []),
                'templates': st.session_state.get('task_templates', []),
                'settings': st.session_state.get('app_settings', {}),
                'productivity_metrics': st.session_state.get('productivity_metrics', {}),
                'notification_preferences': st.session_state.get('notification_preferences', {})
            }

            # Calculate metadata
            file_count = sum(1 for key in backup_data.keys() if key != 'metadata' and backup_data[key])
            backup_json = json.dumps(backup_data, default=str, ensure_ascii=False)
            total_size = len(backup_json.encode('utf-8'))
            checksum = self.calculate_checksum(backup_data)

            # Update metadata
            backup_data['metadata'].update({
                'file_count': file_count,
                'total_size': total_size,
                'checksum': checksum
            })

            # Create zip file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add main data file
                zipf.writestr('data.json', json.dumps(backup_data, indent=2, default=str, ensure_ascii=False))

                # Add individual files for easier inspection
                for key, value in backup_data.items():
                    if key != 'metadata' and value:
                        zipf.writestr(f'{key}.json', json.dumps(value, indent=2, default=str, ensure_ascii=False))

                # Add performance metrics
                zipf.writestr('performance_metrics.json',
                              json.dumps(self.performance_metrics, indent=2, default=str))

                # Add change log if available
                if self.change_log:
                    zipf.writestr('change_log.json',
                                  json.dumps(self.change_log, indent=2, default=str))

            # Store backup metadata
            backup_metadata = BackupMetadata(
                timestamp=datetime.now().isoformat(),
                version='2.0',
                file_count=file_count,
                total_size=total_size,
                checksum=checksum,
                backup_type=backup_type,
                description=description
            )

            # Update performance metrics
            backup_time = time.time() - start_time
            self.performance_metrics['backup_times'].append(backup_time)

            # Clean up old backups
            self.cleanup_old_backups()

            return str(backup_path)

        except Exception as e:
            st.error(f"Backup creation failed: {str(e)}")
            return None

    def restore_backup(self, backup_path: str, selective: bool = False,
                       restore_items: List[str] = None) -> bool:
        """Restore from backup with selective restore options"""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                st.error("Backup file not found")
                return False

            # Create current state backup before restore
            current_backup = self.create_backup("Pre-restore backup", "auto")
            if not current_backup:
                st.warning("Could not create pre-restore backup")

            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Read main data file
                data_content = zipf.read('data.json')
                backup_data = json.loads(data_content.decode('utf-8'))

                # Validate backup
                metadata = backup_data.get('metadata', {})
                expected_checksum = metadata.get('checksum')
                if expected_checksum:
                    # Remove metadata for checksum calculation
                    data_for_checksum = {k: v for k, v in backup_data.items() if k != 'metadata'}
                    calculated_checksum = self.calculate_checksum(data_for_checksum)
                    if calculated_checksum != expected_checksum:
                        st.error("Backup integrity check failed")
                        return False

                # Determine what to restore
                if selective and restore_items:
                    items_to_restore = restore_items
                else:
                    items_to_restore = ['tasks', 'habits', 'lists', 'folders', 'templates',
                                        'settings', 'productivity_metrics', 'notification_preferences']

                # Restore data
                restore_success = True

                for item in items_to_restore:
                    if item in backup_data and backup_data[item]:
                        try:
                            if item == 'tasks':
                                # Validate tasks before restore
                                valid_tasks = []
                                for task in backup_data[item]:
                                    valid, errors = DataValidator.validate_task(task)
                                    if valid:
                                        valid_tasks.append(task)
                                    else:
                                        st.warning(f"Skipped invalid task during restore: {'; '.join(errors)}")

                                st.session_state.tasks = valid_tasks
                                self.save_data('tasks', valid_tasks)

                            elif item == 'habits':
                                # Validate habits before restore
                                valid_habits = []
                                for habit in backup_data[item]:
                                    valid, errors = DataValidator.validate_habit(habit)
                                    if valid:
                                        valid_habits.append(habit)
                                    else:
                                        st.warning(f"Skipped invalid habit during restore: {'; '.join(errors)}")

                                st.session_state.habits = valid_habits
                                self.save_data('habits', valid_habits)

                            else:
                                st.session_state[item] = backup_data[item]

                        except Exception as e:
                            st.error(f"Failed to restore {item}: {str(e)}")
                            restore_success = False

                # Log the restore operation
                self._log_change('system', 'restore', {
                    'backup_file': str(backup_path),
                    'items_restored': items_to_restore,
                    'success': restore_success
                })

                return restore_success

        except Exception as e:
            st.error(f"Restore failed: {str(e)}")
            return False

    def create_auto_backup(self):
        """Create automatic backup in background"""
        if self._backup_thread and self._backup_thread.is_alive():
            return  # Backup already in progress

        def backup_worker():
            try:
                # Check if enough time has passed since last backup
                last_backup_time = self._get_last_backup_time()
                if last_backup_time:
                    time_since_backup = datetime.now() - last_backup_time
                    if time_since_backup.total_seconds() < 3600:  # Less than 1 hour
                        return

                # Create backup
                self.create_backup("Automatic backup", "auto")

            except Exception as e:
                st.error(f"Auto backup failed: {str(e)}")

        self._backup_thread = threading.Thread(target=backup_worker)
        self._backup_thread.daemon = True
        self._backup_thread.start()

    def _get_last_backup_time(self) -> Optional[datetime]:
        """Get timestamp of last backup"""
        backup_files = list(self.backup_dir.glob("backup_*.zip"))
        if not backup_files:
            return None

        # Sort by modification time
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_backup = backup_files[0]

        return datetime.fromtimestamp(latest_backup.stat().st_mtime)

    def cleanup_old_backups(self, keep_count: int = 20, keep_days: int = 30):
        """Enhanced backup cleanup with retention policies"""
        backup_files = list(self.backup_dir.glob("backup_*.zip"))

        if len(backup_files) <= keep_count:
            return

        # Categorize backups
        manual_backups = []
        auto_backups = []

        for backup_file in backup_files:
            try:
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    data_content = zipf.read('data.json')
                    backup_data = json.loads(data_content.decode('utf-8'))
                    backup_type = backup_data.get('metadata', {}).get('backup_type', 'manual')

                    if backup_type == 'manual':
                        manual_backups.append(backup_file)
                    else:
                        auto_backups.append(backup_file)
            except:
                # If we can't read the backup, treat it as auto
                auto_backups.append(backup_file)

        # Keep more manual backups than auto backups
        manual_keep = max(5, keep_count // 2)
        auto_keep = keep_count - manual_keep

        # Sort by modification time (newest first)
        manual_backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        auto_backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Delete old auto backups
        for old_backup in auto_backups[auto_keep:]:
            try:
                old_backup.unlink()
            except Exception as e:
                st.warning(f"Could not delete old backup {old_backup.name}: {str(e)}")

        # Delete old manual backups (keep more of these)
        for old_backup in manual_backups[manual_keep:]:
            try:
                # Only delete if older than keep_days
                file_age = datetime.now() - datetime.fromtimestamp(old_backup.stat().st_mtime)
                if file_age.days > keep_days:
                    old_backup.unlink()
            except Exception as e:
                st.warning(f"Could not delete old backup {old_backup.name}: {str(e)}")

    def export_to_formats(self, formats: List[str] = None) -> Dict[str, str]:
        """Export data to multiple formats"""
        if formats is None:
            formats = ['json', 'csv']

        export_data = {}

        try:
            # Load all data
            tasks = self.load_data('tasks')
            habits = self.load_data('habits')

            for format_type in formats:
                if format_type.lower() == 'json':
                    export_data['json'] = self._export_to_json(tasks, habits)
                elif format_type.lower() == 'csv':
                    export_data.update(self._export_to_csv(tasks, habits))
                elif format_type.lower() == 'xlsx':
                    export_data['xlsx'] = self._export_to_excel(tasks, habits)

        except Exception as e:
            st.error(f"Export failed: {str(e)}")

        return export_data

    def _export_to_json(self, tasks: List[Dict], habits: List[Dict]) -> str:
        """Export to enhanced JSON format"""
        export_data = {
            'export_metadata': {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0',
                'format': 'json',
                'total_tasks': len(tasks),
                'total_habits': len(habits)
            },
            'tasks': tasks,
            'habits': habits,
            'lists': st.session_state.get('lists', []),
            'folders': st.session_state.get('folders', []),
            'task_templates': st.session_state.get('task_templates', []),
            'settings': st.session_state.get('app_settings', {}),
            'performance_metrics': self.performance_metrics
        }

        return json.dumps(export_data, indent=2, default=str, ensure_ascii=False)

    def _export_to_csv(self, tasks: List[Dict], habits: List[Dict]) -> Dict[str, str]:
        """Export to CSV format with multiple files"""
        csv_exports = {}

        # Export tasks
        if tasks:
            tasks_df = pd.DataFrame(tasks)
            # Flatten complex fields
            for col in ['tags', 'subtasks', 'dependencies']:
                if col in tasks_df.columns:
                    tasks_df[col] = tasks_df[col].apply(lambda x: json.dumps(x) if isinstance(x, list) else str(x))

            csv_exports['tasks_csv'] = tasks_df.to_csv(index=False)

        # Export habits
        if habits:
            # Flatten habit data for CSV
            habit_rows = []
            for habit in habits:
                base_row = {key: value for key, value in habit.items()
                            if key != 'completion_dates'}

                # Handle completion dates
                completion_dates = habit.get('completion_dates', [])
                if completion_dates:
                    for completion_date in completion_dates:
                        row = base_row.copy()
                        row['completion_date'] = completion_date
                        habit_rows.append(row)
                else:
                    habit_rows.append(base_row)

            if habit_rows:
                habits_df = pd.DataFrame(habit_rows)
                csv_exports['habits_csv'] = habits_df.to_csv(index=False)

        return csv_exports

    def _export_to_excel(self, tasks: List[Dict], habits: List[Dict]) -> bytes:
        """Export to Excel format with multiple sheets"""
        try:
            from io import BytesIO

            output = BytesIO()

            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Tasks sheet
                if tasks:
                    tasks_df = pd.DataFrame(tasks)
                    # Clean data for Excel
                    for col in ['tags', 'subtasks', 'dependencies']:
                        if col in tasks_df.columns:
                            tasks_df[col] = tasks_df[col].apply(
                                lambda x: ', '.join(x) if isinstance(x, list) else str(x)
                            )
                    tasks_df.to_excel(writer, sheet_name='Tasks', index=False)

                # Habits sheet
                if habits:
                    habits_df = pd.DataFrame(habits)
                    habits_df['completion_dates'] = habits_df['completion_dates'].apply(
                        lambda x: ', '.join(x) if isinstance(x, list) else str(x)
                    )
                    habits_df.to_excel(writer, sheet_name='Habits', index=False)

                # Summary sheet
                summary_data = {
                    'Metric': ['Total Tasks', 'Completed Tasks', 'Total Habits', 'Export Date'],
                    'Value': [
                        len(tasks),
                        len([t for t in tasks if t.get('status') == 'completed']),
                        len(habits),
                        datetime.now().strftime('%Y-%m-%d %H:%M')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

            return output.getvalue()

        except ImportError:
            st.error("Excel export requires openpyxl package")
            return None

    def get_storage_analytics(self) -> Dict:
        """Get comprehensive storage analytics"""
        analytics = {
            'storage_type': self.storage_type,
            'data_directory': str(self.data_dir),
            'performance_metrics': self.performance_metrics.copy(),
            'files': {},
            'backup_info': {},
            'data_quality': {}
        }

        # File information
        for file_path in self.data_dir.glob("*.json"):
            file_stats = file_path.stat()
            analytics['files'][file_path.name] = {
                'size_bytes': file_stats.st_size,
                'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'readable': file_path.is_file() and os.access(file_path, os.R_OK)
            }

        # Backup information
        backup_files = list(self.backup_dir.glob("backup_*.zip"))
        analytics['backup_info'] = {
            'backup_count': len(backup_files),
            'total_backup_size': sum(f.stat().st_size for f in backup_files),
            'latest_backup': max((f.stat().st_mtime for f in backup_files), default=0),
            'oldest_backup': min((f.stat().st_mtime for f in backup_files), default=0)
        }

        # Data quality metrics
        try:
            tasks = self.load_data('tasks', validate=False)
            habits = self.load_data('habits', validate=False)

            task_issues = 0
            habit_issues = 0

            for task in tasks:
                valid, _ = DataValidator.validate_task(task)
                if not valid:
                    task_issues += 1

            for habit in habits:
                valid, _ = DataValidator.validate_habit(habit)
                if not valid:
                    habit_issues += 1

            analytics['data_quality'] = {
                'total_tasks': len(tasks),
                'task_validation_issues': task_issues,
                'total_habits': len(habits),
                'habit_validation_issues': habit_issues,
                'data_integrity_score': ((len(tasks) - task_issues) + (len(habits) - habit_issues)) / max(1,
                                                                                                          len(tasks) + len(
                                                                                                              habits)) * 100
            }

        except Exception as e:
            analytics['data_quality'] = {'error': str(e)}

        return analytics

    def _log_change(self, entity_type: str, action: str, details: Dict):
        """Log changes for audit trail"""
        change_entry = {
            'timestamp': datetime.now().isoformat(),
            'entity_type': entity_type,
            'action': action,
            'details': details,
            'user_session': id(st.session_state)  # Simple session identifier
        }

        self.change_log.append(change_entry)

        # Keep only last 1000 entries
        if len(self.change_log) > 1000:
            self.change_log = self.change_log[-1000:]

    def _recover_from_backup(self, data_type: str) -> List[Dict]:
        """Attempt to recover data from most recent backup"""
        try:
            backup_files = list(self.backup_dir.glob("backup_*.zip"))
            if not backup_files:
                return []

            # Get most recent backup
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)

            with zipfile.ZipFile(latest_backup, 'r') as zipf:
                data_content = zipf.read('data.json')
                backup_data = json.loads(data_content.decode('utf-8'))

                recovered_data = backup_data.get(data_type, [])
                st.success(f"Recovered {len(recovered_data)} {data_type} from backup")

                return recovered_data

        except Exception as e:
            st.error(f"Recovery from backup failed: {str(e)}")
            return []

    def optimize_storage(self):
        """Optimize storage performance and cleanup"""
        try:
            # Vacuum SQLite database if using SQLite
            if self.storage_type == "sqlite" and self.db_path.exists():
                conn = sqlite3.connect(self.db_path)
                conn.execute("VACUUM")
                conn.close()

            # Clean up cache directory
            if self.cache_dir.exists():
                for cache_file in self.cache_dir.glob("*"):
                    if cache_file.is_file():
                        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                        if file_age.days > 7:  # Remove cache files older than 7 days
                            cache_file.unlink()

            # Cleanup old temporary files
            for temp_file in self.data_dir.glob("*.tmp"):
                temp_file.unlink()

            # Cleanup old backups
            self.cleanup_old_backups()

            st.success("Storage optimization completed")

        except Exception as e:
            st.error(f"Storage optimization failed: {str(e)}")


# Convenience functions
def auto_save_data():
    """Enhanced auto-save with error handling"""
    if 'smart_data_manager' not in st.session_state:
        st.session_state.smart_data_manager = SmartDataManager("file")

    data_manager = st.session_state.smart_data_manager

    try:
        saved_any = False

        # Save tasks
        if 'tasks' in st.session_state:
            if data_manager.save_data('tasks', st.session_state.tasks):
                saved_any = True

        # Save habits
        if 'habits' in st.session_state:
            if data_manager.save_data('habits', st.session_state.habits):
                saved_any = True

        if saved_any:
            st.session_state.last_auto_save = datetime.now()

    except Exception as e:
        st.error(f"Auto-save failed: {str(e)}")


def load_saved_data():
    """Enhanced data loading with validation"""
    if 'smart_data_manager' not in st.session_state:
        st.session_state.smart_data_manager = SmartDataManager("file")

    data_manager = st.session_state.smart_data_manager

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


def create_smart_data_manager(storage_type: str = "file", auto_backup: bool = True) -> SmartDataManager:
    """Factory function to create enhanced data manager"""
    return SmartDataManager(storage_type, auto_backup)


# Make sure these functions are available at module level
__all__ = [
    'SmartDataManager',
    'DataValidator',
    'BackupMetadata',
    'SyncStatus',
    'auto_save_data',
    'load_saved_data',
    'create_smart_data_manager'
]