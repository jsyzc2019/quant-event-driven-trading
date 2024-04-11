from dataclasses import dataclass

from core.models.parameter import Parameter, StaticParameter
from core.models.smooth import Smooth

from .base import Signal, SignalType


@dataclass(frozen=True)
class DsoCrossSignal(Signal):
    type: Signal = SignalType.DsoCross
    smooth_type: Parameter = StaticParameter(Smooth.EMA)
    smooth_period: Parameter = StaticParameter(13.0)
    k_period: Parameter = StaticParameter(8.0)
    d_period: Parameter = StaticParameter(9.0)
