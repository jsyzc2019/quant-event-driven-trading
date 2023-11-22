from dataclasses import dataclass

from core.models.parameter import CategoricalParameter, Parameter, RandomParameter
from core.models.rsi import RSIType
from strategy.regime.base import BaseRegime, FilterType


@dataclass(frozen=True)
class RSIFilter(BaseRegime):
    type: FilterType = FilterType.Rsi
    rsi_type: Parameter = CategoricalParameter(RSIType)
    period: Parameter = RandomParameter(50.0, 55.0, 1.0)
    threshold: Parameter = RandomParameter(0.0, 5.0, 1.0)