from abc import ABC, abstractmethod

from core.models.strategy import Strategy
from core.models.symbol import Symbol
from core.models.timeframe import Timeframe

from .abstract_actor import AbstractActor


class AbstractPositionActorFactory(ABC):
    @abstractmethod
    def create_actor(
        self, symbol: Symbol, timeframe: Timeframe, strategy: Strategy, is_trading: bool
    ) -> AbstractActor:
        pass
