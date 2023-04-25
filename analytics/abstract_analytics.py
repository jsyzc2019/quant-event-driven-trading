from abc import abstractmethod
from typing import List
from core.abstract_event_manager import AbstractEventManager
from core.position import Position


class AbstractAnalytics(AbstractEventManager):
    @abstractmethod
    def calculate(self, account_size: float, positions: List[Position]):
        pass