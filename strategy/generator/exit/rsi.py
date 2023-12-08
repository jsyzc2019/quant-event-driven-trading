from dataclasses import dataclass

from core.models.parameter import CategoricalParameter, Parameter, RandomParameter
from core.models.rsi import RSIType

from .base import Exit, ExitType


@dataclass(frozen=True)
class RsiExit(Exit):
    type: ExitType = ExitType.Rsi
    rsi_type: Parameter = CategoricalParameter(RSIType)
    period: Parameter = RandomParameter(14.0, 30.0, 1.0)
    threshold: Parameter = RandomParameter(0.0, 5.0, 1.0)