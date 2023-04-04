from ta.indicators.base.abstract_indicator import AbstractIndicator
from ta.indicators.base.ma import MovingAverage


class AwesomeOscillator(AbstractIndicator):
    def __init__(self, ao_short_period=5, ao_long_period=34):
        self.short_period_ma = MovingAverage(ao_short_period)
        self.long_period_ma = MovingAverage(ao_long_period)

    def call(self, data):
        median_price = (data['high'] + data['low']) / 2

        sma_short = self.short_period_ma.sma(median_price)
        sma_long = self.long_period_ma.sma(median_price)

        return sma_short - sma_long