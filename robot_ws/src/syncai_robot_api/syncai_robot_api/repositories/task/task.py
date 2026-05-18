import time
import structlog
import threading

from typing import Optional, Dict, List

from syncai_robot_api.repositories.task.schema import Task, TaskStatus, StepStatus


class TaskRepo:

    TASK_TTL_SECONDS = 3600  # evict terminal tasks older than 1 hour

    def __init__(self, logger: structlog.BoundLogger):
        self._logger = logger

        self._lock = threading.Lock()
        self._tasks: Dict[str, Task] = {}
        self._active_task_id: Optional[str] = None
        self._cancel_event: threading.Event = threading.Event()

    def add_task(self, task: Task) -> bool:
        with self._lock:
            if task.id in self._tasks:
                return False

            self._cleanup_expired_tasks()
            self._tasks[task.id] = task
            return True

    def _cleanup_expired_tasks(self):
        """Remove terminal tasks where completed_at is older than TTL. Called under lock."""
        now = time.time()
        terminal = (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
        self._tasks = {
            tid: t for tid, t in self._tasks.items()
            if not (
                t.status in terminal
                and t.completed_at is not None
                and now - t.completed_at > self.TASK_TTL_SECONDS
            )
        }

    def get_task(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        with self._lock:
            return list(self._tasks.values())

    def get_active_task(self) -> Optional[Task]:
        with self._lock:
            if self._active_task_id is None:
                return None
            return self._tasks.get(self._active_task_id)

    def set_active_task(self, task_id: str):
        with self._lock:
            self._active_task_id = task_id
            self._cancel_event.clear()

    def clear_active_task(self):
        with self._lock:
            self._active_task_id = None
            self._cancel_event.clear()

    def request_cancel(self):
        self._cancel_event.set()

    def is_cancel_requested(self) -> bool:
        return self._cancel_event.is_set()

    def update_task_status(self, task_id: str, status: TaskStatus, error_msg: Optional[str] = None):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            
            task.status = status

            if not error_msg:
                return
            
            task.error_msg = error_msg


    def update_step_status(self, task_id: str, step_index: int, status: StepStatus, error_msg: Optional[str] = None):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            
            if step_index >= len(task.payload.steps):
                return
            
            task.payload.steps[step_index].status = status

            if not error_msg:
                return
            
            task.error_msg = error_msg


    def update_current_step_index(self, task_id: str, index: int):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            
            task.current_step_index = index

    def update_workflow_id(self, task_id: str, workflow_id: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.workflow_id = workflow_id

    def set_completed_at(self, task_id: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.completed_at = time.time()


def init_task_repo(logger: structlog.stdlib.BoundLogger) -> TaskRepo:
    return TaskRepo(logger=logger)
