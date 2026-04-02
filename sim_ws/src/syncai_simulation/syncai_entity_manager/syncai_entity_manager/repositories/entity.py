import threading
from typing import Dict, List, Optional

from rclpy.impl.rcutils_logger import RcutilsLogger
from pydantic import BaseModel


class EntityRecord(BaseModel):
    entity_name: str
    model_type: str


class EntityRepo:

    def __init__(self, logger: RcutilsLogger):
        self._logger = logger
        self._lock = threading.Lock()
        self._entities: Dict[str, str] = {}  # entity_name -> model_type

    def add(self, entity_name: str, model_type: str) -> None:
        with self._lock:
            self._entities[entity_name] = model_type

    def remove(self, entity_name: str) -> None:
        with self._lock:
            self._entities.pop(entity_name, None)

    def exists(self, entity_name: str) -> bool:
        with self._lock:
            return entity_name in self._entities

    def get_all(self) -> List[EntityRecord]:
        with self._lock:
            return [
                EntityRecord(entity_name=name, model_type=mtype)
                for name, mtype in self._entities.items()
            ]

    def get_model_type(self, entity_name: str) -> Optional[str]:
        with self._lock:
            return self._entities.get(entity_name)
