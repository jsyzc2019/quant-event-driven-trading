from risk_management.stop_loss.atr_stop_loss_finder import ATRStopLossFinder
from risk_management.take_profit.risk_reward_take_profit_finder import RiskRewardTakeProfitFinder
from strategy.base_strategy import BaseStrategy
from ta.overlap.zlma import ZeroLagEMA
from ta.volatility.bbands import BollingerBands
from ta.volume.mfi import MoneyFlowIndex
from ta.momentum.aosc import AwesomeOscillator


class AwesomeOscillatorBollingerBands(BaseStrategy):
    NAME = "AOBB"

    def __init__(self, ao_short_period=5, ao_long_period=34, sma_period=25, stdev_multi=2, slow_sma_period=50, mfi_period=14, oversold=40, overbought=60, atr_multi=1.4, risk_reward_ratio=1.5):
        indicators = [
            (AwesomeOscillator(ao_short_period, ao_long_period), AwesomeOscillator.NAME),
            (BollingerBands(sma_period, stdev_multi), ('upper_band', 'middle_band', 'lower_band')),
            (ZeroLagEMA(slow_sma_period), ZeroLagEMA.NAME),
            (MoneyFlowIndex(period=mfi_period), MoneyFlowIndex.NAME)
        ]
        super().__init__(
            indicators,
            RiskRewardTakeProfitFinder(risk_reward_ratio=risk_reward_ratio),
            ATRStopLossFinder(atr_multi=atr_multi)
        )
        self.oversold = oversold
        self.overbought = overbought

    def _generate_conditions(self, data):
        close = data['close']

        price_change = close.shift() < close

        ao_change = data[AwesomeOscillator.NAME].shift() > data[AwesomeOscillator.NAME]
        price_touch_lower_band = close <= data['lower_band']
        price_touch_upper_band = close >= data['upper_band']
        mfi = data[MoneyFlowIndex.NAME]

        return price_change, ao_change, price_touch_lower_band, price_touch_upper_band, mfi

    def _generate_buy_signal(self, data):
        price_change, ao_change, price_touch_lower_band, _, mfi = self._generate_conditions(data)
        return price_change.iloc[-1] and ao_change.iloc[-1] and price_touch_lower_band.iloc[-1] and (mfi.iloc[-1] <= self.oversold)

    def _generate_sell_signal(self, data):
        price_change, ao_change, _, price_touch_upper_band, mfi = self._generate_conditions(data)
        return not price_change.iloc[-1] and not ao_change.iloc[-1] and price_touch_upper_band.iloc[-1] and (mfi.iloc[-1] >= self.overbought)