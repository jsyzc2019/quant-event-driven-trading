from dataclasses import dataclass

from core.models.macd import MACDType
from core.models.parameter import (
    CategoricalParameter,
    Parameter,
    StaticParameter,
)
from strategy.regime.base import BaseRegime, FilterType


@dataclass(frozen=True)
class MACDFilter(BaseRegime):
    type: FilterType = FilterType.Macd
    macd_type: Parameter = CategoricalParameter(MACDType)
    fast_period: Parameter = StaticParameter(12.0)
    slow_period: Parameter = StaticParameter(26.0)
    signal_smoothing: Parameter = StaticParameter(9.0)