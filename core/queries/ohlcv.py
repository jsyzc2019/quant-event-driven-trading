from dataclasses import dataclass, field
from typing import List

from core.events.base import EventMeta
from core.models.ohlcv import OHLCV
from core.models.symbol import Symbol
from core.models.ta import TechAnalysis
from core.models.timeframe import Timeframe

from .base import Query, QueryGroup


@dataclass(frozen=True)
class NextBar(Query[OHLCV]):
    symbol: Symbol
    timeframe: Timeframe
    ohlcv: OHLCV
    meta: EventMeta = field(
        default_factory=lambda: EventMeta(priority=3, group=QueryGroup.market),
        init=False,
    )


@dataclass(frozen=True)
class PrevBar(Query[OHLCV]):
    symbol: Symbol
    timeframe: Timeframe
    ohlcv: OHLCV
    meta: EventMeta = field(
        default_factory=lambda: EventMeta(priority=4, group=QueryGroup.market),
        init=False,
    )


@dataclass(frozen=True)
class BackNBars(Query[List[OHLCV]]):
    symbol: Symbol
    timeframe: Timeframe
    ohlcv: OHLCV
    n: int
    meta: EventMeta = field(
        default_factory=lambda: EventMeta(priority=4, group=QueryGroup.market),
        init=False,
    )


@dataclass(frozen=True)
class TA(Query[TechAnalysis]):
    symbol: Symbol
    timeframe: Timeframe
    ohlcv: OHLCV
    meta: EventMeta = field(
        default_factory=lambda: EventMeta(priority=2, group=QueryGroup.ta),
        init=False,
    )