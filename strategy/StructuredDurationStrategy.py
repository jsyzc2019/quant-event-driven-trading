from ta.RSIIndicator import RSIIndicator
from strategy.AbstractStrategy import AbstractStrategy

class StructuredDurationStrategy(AbstractStrategy):
    def __init__(self, upper_barrier=80, lower_barrier=20, lookback=5):
        super().__init__()
        self.upper_barrier = upper_barrier
        self.lower_barrier = lower_barrier
        self.lookback = lookback
        self.rsi_indicator = RSIIndicator(lookback)

    def add_indicators(self, data):
        data = data.copy()
        data['rsi'] = self.rsi_indicator.rsi(data['close'])
        return data

    def entry(self, data):
        if len(data) < self.lookback + 1:
            return False, False

        data = self.add_indicators(data)

        last_row = data.iloc[-1]
        previous_rows = data.iloc[-(self.lookback + 1):-1]

        buy_signal = (
            last_row['rsi'] > self.lower_barrier
            and last_row['low'] < data.iloc[-2]['low']
            and all(previous_rows['rsi'] < self.lower_barrier)
        )

        sell_signal = (
            last_row['rsi'] < self.upper_barrier
            and last_row['high'] > data.iloc[-2]['high']
            and all(previous_rows['rsi'] > self.upper_barrier)
        )

        return buy_signal, sell_signal

    def __str__(self) -> str:
        return f'StructuredDurationIndicatorStrategy(upper_barrier={self.upper_barrier}, lower_barrier={self.lower_barrier}, lookback={self.lookback})'
