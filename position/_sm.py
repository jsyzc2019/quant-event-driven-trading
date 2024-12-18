import logging
from enum import Enum, auto
from typing import Callable, Dict, Tuple, Type, Union

from core.actors import StrategyActor
from core.actors.state import InMemory
from core.events.backtest import BacktestEnded
from core.events.position import (
    BrokerPositionClosed,
    BrokerPositionOpened,
)
from core.events.risk import RiskLongThresholdBreached, RiskShortThresholdBreached
from core.events.signal import (
    GoLongSignalReceived,
    GoShortSignalReceived,
)
from core.models.side import PositionSide
from core.models.symbol import Symbol
from core.models.timeframe import Timeframe

logger = logging.getLogger(__name__)


class PositionState(Enum):
    IDLE = auto()
    WAITING_BROKER_CONFIRMATION = auto()
    OPENED = auto()
    CLOSE = auto()


PositionEvent = Union[
    BrokerPositionOpened,
    BrokerPositionClosed,
    GoLongSignalReceived,
    GoShortSignalReceived,
    RiskLongThresholdBreached,
    RiskShortThresholdBreached,
    BacktestEnded,
]

HandlerFunction = Callable[[PositionEvent], bool]
Transitions = Dict[Tuple[PositionState, PositionEvent], Tuple[PositionState, str]]

TRANSITIONS: Transitions = {
    (PositionState.IDLE, GoLongSignalReceived): (
        PositionState.WAITING_BROKER_CONFIRMATION,
        "handle_signal_received",
    ),
    (PositionState.IDLE, GoShortSignalReceived): (
        PositionState.WAITING_BROKER_CONFIRMATION,
        "handle_signal_received",
    ),
    (PositionState.WAITING_BROKER_CONFIRMATION, BrokerPositionOpened): (
        PositionState.OPENED,
        "handle_position_opened",
    ),
    (PositionState.WAITING_BROKER_CONFIRMATION, BrokerPositionClosed): (
        PositionState.IDLE,
        "handle_position_closed",
    ),
    (PositionState.WAITING_BROKER_CONFIRMATION, BacktestEnded): (
        PositionState.CLOSE,
        "handle_backtest",
    ),
    (PositionState.OPENED, RiskLongThresholdBreached): (
        PositionState.CLOSE,
        "handle_exit_received",
    ),
    (PositionState.OPENED, RiskShortThresholdBreached): (
        PositionState.CLOSE,
        "handle_exit_received",
    ),
    (PositionState.OPENED, BacktestEnded): (
        PositionState.CLOSE,
        "handle_backtest",
    ),
    (PositionState.CLOSE, BrokerPositionClosed): (
        PositionState.IDLE,
        "handle_position_closed",
    ),
}

SMKey = Tuple[Symbol, Timeframe, PositionSide]


class PositionStateMachine:
    def __init__(self, actor: Type[StrategyActor], transitions: Transitions):
        self._actor = actor
        self._transitions = transitions
        self._state = InMemory[SMKey, PositionState]()

    async def process_event(self, event: PositionEvent, side: PositionSide):
        key = self._get_key(side)

        current_state = await self._state.get(key, PositionState.IDLE)

        if not self._is_valid_state(self._transitions, current_state, event):
            return

        next_state, handler_name = self._transitions[(current_state, type(event))]

        handler = getattr(self._actor, handler_name)

        if not await handler(event):
            return

        await self._state.set(key, next_state)

        logger.debug(
            f"SM: key={key}, event={event}, side: {side}, curr_state={current_state}, next_state={next_state}"
        )

    def _get_key(self, side: PositionSide) -> SMKey:
        return self._actor.symbol, self._actor.timeframe, side

    @staticmethod
    def _is_valid_state(
        transitions: Transitions, state: PositionState, event: PositionEvent
    ) -> bool:
        return (state, type(event)) in transitions
