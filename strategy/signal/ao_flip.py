from dataclasses import dataclass

from core.models.parameter import (
    Parameter,
    StaticParameter,
)
from strategy.signal.base import BaseSignal, SignalType


@dataclass(frozen=True)
class AOFlipSignal(BaseSignal):
    type: SignalType = SignalType.AoFlip
    short_period: Parameter = StaticParameter(5.0)
    long_period: Parameter = StaticParameter(34.0)