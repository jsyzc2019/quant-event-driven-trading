import asyncio
from typing import Union

from core.events.position import BrokerPositionClosed, BrokerPositionOpened, PositionCloseRequested, PositionInitialized
from core.interfaces.abstract_actor import AbstractActor
from core.models.order import Order, OrderStatus
from core.models.position import Position, PositionSide
from core.models.strategy import Strategy
from core.models.symbol import Symbol
from core.models.timeframe import Timeframe

PositionEvent = Union[PositionInitialized, PositionCloseRequested]

class PaperExecutor(AbstractActor):
    def __init__(self, symbol: Symbol, timeframe: Timeframe, strategy: Strategy, slippage: float):
        super().__init__()
        self._symbol = symbol
        self._timeframe = timeframe
        self._strategy = strategy
        self.slippage = slippage
        self._running = None
        self._lock = asyncio.Lock()

    @property
    def id(self):
        return f"{self.symbol}_{self.timeframe}_PAPER"
    
    @property
    def symbol(self):
        return self._symbol
    
    @property
    def timeframe(self):
        return self._timeframe
    
    @property
    def strategy(self):
        return self._strategy
    
    @property
    def running(self) -> bool:
        return bool(self._running)
    
    async def start(self):
        if self.running:
            raise RuntimeError("Start: executor is running")
        
        for event in [PositionInitialized, PositionCloseRequested]:
            self._dispatcher.register(event, self.handle, self._filter_event)

        async with self._lock:
            self._running = True
    
    async def stop(self):
        if not self.running:
            raise RuntimeError("Stop: executor is not started")
        
        for event in [PositionInitialized, PositionCloseRequested]:
            self._dispatcher.unregister(event, self.handle)

        async with self._lock:
            self._running = False

    async def handle(self, event: PositionEvent):
        if isinstance(event, PositionInitialized):
            return await self._execute_order(event.position)
        elif isinstance(event, PositionCloseRequested):
            return await self._close_position(event.position)
    
    def _filter_event(self, event: PositionEvent):
        signal = event.position.signal
        return signal.symbol == self._symbol and signal.timeframe == self._timeframe

    async def _execute_order(self, position: Position):
        entry_price = self._apply_slippage(position, 1 + self.slippage)

        order = Order(status=OrderStatus.EXECUTED, price=entry_price, size=position.size)

        next_position = position.add_order(order).update_prices(order.price)
    
        await self.dispatch(BrokerPositionOpened(next_position))

    async def _close_position(self, position: Position):
        await self.dispatch(BrokerPositionClosed(position))

    @staticmethod
    def _apply_slippage(position: Position, factor: float) -> float:
        if position.side == PositionSide.LONG:
            return position.entry_price * factor
        elif position.side == PositionSide.SHORT:
            return position.entry_price / factor
