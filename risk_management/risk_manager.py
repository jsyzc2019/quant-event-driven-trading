import asyncio
from core.event_dispatcher import register_handler
from core.events.position import PositionSide
from core.events.risk import RiskEvaluate, RiskExit
from risk_management.abstract_risk_manager import AbstractRiskManager


class RiskManager(AbstractRiskManager):
    def __init__(self, trailing_stop_loss=False, max_stop_loss_adjustments=10):
        super().__init__()
        self.trailing_stop_loss = trailing_stop_loss
        self.trailing_stop_loss_prices = {}
        self.max_stop_loss_adjustments = max_stop_loss_adjustments
        self.stop_loss_adjustment_count = {}

        self.stop_loss_lock = asyncio.Lock()

    @register_handler(RiskEvaluate)
    async def _on_check_exit_conditions(self, event: RiskEvaluate):
        symbol, timeframe, position_side, position_size, entry_price, take_profit_price, stop_loss_price, risk_per_trade, ohlcv, strategy = self._unpack_event(event)

        async with self.stop_loss_lock:
            if symbol not in self.stop_loss_adjustment_count:
                self._initialize_symbol_data(symbol)

            if self.should_update_trailing_stop_loss(symbol, position_side):
                stop_loss_price = self._update_trailing_stop_loss(position_side, position_size, stop_loss_price, entry_price, ohlcv, risk_per_trade)

        if not self._should_exit(position_side, stop_loss_price, take_profit_price, ohlcv.low, ohlcv.high):
            return

        async with self.stop_loss_lock:
            self._reset_trailing_stop_loss_data(symbol, position_side)

        exit_price = self._calculate_exit_price(position_side, ohlcv.close, take_profit_price, stop_loss_price)

        await self.dispatcher.dispatch(RiskExit(symbol=symbol, timeframe=timeframe, strategy=strategy, exit=exit_price))

    def _initialize_symbol_data(self, symbol):
        self.trailing_stop_loss_prices[symbol] = {PositionSide.LONG: None, PositionSide.SHORT: None}
        self.stop_loss_adjustment_count[symbol] = {PositionSide.LONG: 0, PositionSide.SHORT: 0}

    def should_update_trailing_stop_loss(self, symbol, position_side):
        return self.trailing_stop_loss and self.stop_loss_adjustment_count[symbol][position_side] < self.max_stop_loss_adjustments

    def _reset_trailing_stop_loss_data(self, symbol, position_side):
        self.trailing_stop_loss_prices[symbol][position_side] = None
        self.stop_loss_adjustment_count[symbol][position_side] = 0

    def _unpack_event(self, event):
        return event.symbol, event.timeframe, event.side, event.size, event.entry, event.take_profit, event.stop_loss, event.risk, event.ohlcv, event.strategy

    def _should_exit(self, position_side, stop_loss_price, take_profit_price, low, high):
        if position_side == PositionSide.LONG:
            return self._long_exit_conditions(stop_loss_price, take_profit_price, low, high)
        elif position_side == PositionSide.SHORT:
            return self._short_exit_conditions(stop_loss_price, take_profit_price, low, high)

    def _update_trailing_stop_loss(self, position_side, position_size, stop_loss_price, entry_price, current_row, risk_per_trade):
        if position_side not in self.trailing_stop_loss_prices:
            self.trailing_stop_loss_prices[position_side] = stop_loss_price

        if position_side == PositionSide.LONG:
            new_stop_loss_price = current_row.high - (current_row.high - stop_loss_price) * risk_per_trade

            if new_stop_loss_price > self.trailing_stop_loss_prices[position_side]:
                self.trailing_stop_loss_prices[position_side] = new_stop_loss_price
                self.stop_loss_adjustment_count[position_side] += 1

                if self.trailing_stop_loss_prices[position_side] - entry_price >= risk_per_trade * position_size:
                    self.trailing_stop_loss_prices[position_side] = entry_price

        elif position_side == PositionSide.SHORT:
            new_stop_loss_price = current_row.low + (stop_loss_price - current_row.low) * risk_per_trade

            if new_stop_loss_price < self.trailing_stop_loss_prices[position_side]:
                self.trailing_stop_loss_prices[position_side] = new_stop_loss_price
                self.stop_loss_adjustment_count[position_side] += 1

                if entry_price - self.trailing_stop_loss_prices[position_side] >= risk_per_trade * position_size:
                    self.trailing_stop_loss_prices[position_side] = entry_price

        return self.trailing_stop_loss_prices[position_side]

    @staticmethod
    def _calculate_exit_price(position_side, current_close, take_profit_price, stop_loss_price):
        if position_side == PositionSide.LONG:
            exit_price = max(min(current_close, take_profit_price or current_close),
                             stop_loss_price or current_close)
        elif position_side == PositionSide.SHORT:
            exit_price = min(max(current_close, take_profit_price or current_close),
                             stop_loss_price or current_close)
        return exit_price

    @staticmethod
    def _long_exit_conditions(stop_loss_price, take_profit_price, low, high):
        return (stop_loss_price is not None and low <= stop_loss_price) or \
               (take_profit_price is not None and high >= take_profit_price)

    @staticmethod
    def _short_exit_conditions(stop_loss_price, take_profit_price, low, high):
        return (stop_loss_price is not None and high >= stop_loss_price) or \
               (take_profit_price is not None and low <= take_profit_price)
