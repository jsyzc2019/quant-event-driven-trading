import asyncio
from typing import Dict

from core.models.portfolio import Performance
from core.models.position import Position
from core.models.strategy import Strategy
from core.models.symbol import Symbol
from core.models.timeframe import Timeframe


class PortfolioStorage:
    def __init__(self):
        self.data: Dict[Strategy, Performance] = {}
        self._lock = asyncio.Lock()

    async def next(self, position: Position, account_size: int, risk_per_trade: float):
        async with self._lock:
            key = self._get_key(
                position.signal.symbol,
                position.signal.timeframe,
                position.signal.strategy,
            )
            performance = self.data.get(key)

            if performance:
                self.data[key] = performance.next(position.pnl)
            else:
                self.data[key] = Performance(account_size, risk_per_trade).next(
                    position.pnl
                )

    async def get(self, position: Position):
        async with self._lock:
            key = self._get_key(
                position.signal.symbol,
                position.signal.timeframe,
                position.signal.strategy,
            )

            return self.data.get(key)

    async def reset(self, symbol, timeframe, strategy):
        async with self._lock:
            key = self._get_key(symbol, timeframe, strategy)
            self.data[key] = {}

    async def reset_all(self):
        async with self._lock:
            self.data = {}

    async def get_equity(
        self, symbol: Symbol, timeframe: Timeframe, strategy: Strategy
    ):
        async with self._lock:
            key = self._get_key(symbol, timeframe, strategy)
            performance = self.data.get(key)

            return performance.equity[-1] if performance else 0

    async def get_kelly(self, symbol: Symbol, timeframe: Timeframe, strategy: Strategy):
        async with self._lock:
            key = self._get_key(symbol, timeframe, strategy)
            performance = self.data.get(key)

            return performance.kelly if performance else 0

    async def get_optimalf(
        self, symbol: Symbol, timeframe: Timeframe, strategy: Strategy
    ):
        async with self._lock:
            key = self._get_key(symbol, timeframe, strategy)
            performance = self.data.get(key)

            return performance.optimal_f if performance else 0

    async def get_fitness(
        self, symbol: Symbol, timeframe: Timeframe, strategy: Strategy
    ):
        async with self._lock:
            key = self._get_key(symbol, timeframe, strategy)
            performance = self.data.get(key)

            if not performance:
                return 0

            return performance.sharpe_ratio

    def _get_key(self, symbol, timeframe, strategy):
        return (symbol, timeframe, strategy)
