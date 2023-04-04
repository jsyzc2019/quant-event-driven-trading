from ta.indicators.base.abstract_indicator import AbstractIndicator


class VWAPIndicator(AbstractIndicator):
    def __init__(self, window=20):
        self.window = window

    def call(self, data):
        volume = data['volume'].values
        price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (price * volume).rolling(window=self.window).sum() / \
            data['volume'].rolling(window=self.window).sum()
        return vwap

    def __str__(self) -> str:
        return f'VWAPIndicator(window={self.window})'