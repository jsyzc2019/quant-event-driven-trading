import asyncio
import logging

import numpy as np

from coral import DataSourceFactory
from core.commands.position import ClosePosition, OpenPosition
from core.event_decorators import command_handler, query_handler
from core.interfaces.abstract_config import AbstractConfig
from core.interfaces.abstract_event_manager import AbstractEventManager
from core.models.datasource_type import DataSourceType
from core.models.entity.order import Order
from core.models.order_type import OrderStatus
from core.models.protocol_type import ProtocolType
from core.models.side import PositionSide
from core.models.symbol import Symbol
from core.queries.account import GetBalance
from core.queries.position import GetClosePosition, GetOpenPosition, HasPosition

from ._twap import TWAP

logger = logging.getLogger(__name__)


class SmartRouter(AbstractEventManager):
    def __init__(
        self, datasource_factory: DataSourceFactory, config_service: AbstractConfig
    ):
        super().__init__()
        self.exchange = datasource_factory.create(
            DataSourceType.BYBIT, ProtocolType.REST
        )
        self.algo_price = TWAP(config_service)
        self.config = config_service.get("position")

    @query_handler(GetBalance)
    def get_account_balance(self, query: GetBalance):
        return self.exchange.fetch_account_balance(query.currency)

    @query_handler(GetOpenPosition)
    def get_open_position(self, query: GetOpenPosition):
        position = query.position

        broker_position = self.exchange.fetch_position(
            position.signal.symbol, position.side
        )

        logging.info(f"Broker open position: {broker_position}")

        if not broker_position:
            return Order(status=OrderStatus.FAILED, price=0, size=0)
        else:
            return Order(
                status=OrderStatus.EXECUTED,
                size=broker_position.get("position_size", 0),
                price=broker_position.get("entry_price", 0),
                fee=broker_position.get("open_fee", 0),
            )

    @query_handler(GetClosePosition)
    def get_close_position(self, query: GetClosePosition):
        position = query.position
        symbol = position.signal.symbol

        trade = self.exchange.fetch_trade(
            symbol,
            position.side,
            position.last_modified,
            position.size,
        )

        logging.info(f"Broker close position: {trade}")

        if not trade:
            return Order(status=OrderStatus.FAILED, price=0, size=0)

        return Order(
            status=OrderStatus.CLOSED,
            size=trade.get("amount", 0),
            price=trade.get("price", 0),
            fee=trade.get("fee", 0),
        )

    @query_handler(HasPosition)
    def has_position(self, query: HasPosition):
        position = query.position
        symbol = position.signal.symbol
        side = position.side

        existing_position = self.exchange.fetch_position(symbol, side)

        if existing_position:
            logging.info(f"Position check: {side} position for {symbol} exists.")
            return True

        logging.info(f"Position check: No existing {side} position found for {symbol}.")
        return False

    @command_handler(OpenPosition)
    async def open_position(self, command: OpenPosition):
        position = command.position
        symbol = position.signal.symbol
        position_side = position.side

        logger.info(f"Trying to open position: {symbol}_{position_side}")

        if self.exchange.fetch_position(symbol, position_side):
            logger.info(f"Position for {symbol} already exists.")
            return

        pending_order = position.entry_order

        order_size_generator = self._calculate_order_slices(symbol, pending_order.size)

        async for bid, ask in self.algo_price.next_value(symbol, self.exchange):
            price = ask if position.side == PositionSide.LONG else bid

            existing_position = await asyncio.to_thread(
                self.exchange.fetch_position, symbol, position_side
            )

            current_position_size = (
                existing_position.get("position_size", 0) if existing_position else 0
            )

            remaining_size = pending_order.size - current_position_size

            if remaining_size <= 0:
                logger.info(
                    f"Position for {symbol} has reached or exceeded the target size. No more orders will be placed."
                )
                break

            order_size = min(next(order_size_generator), remaining_size)

            if not await asyncio.to_thread(
                self.exchange.has_open_orders,
                symbol,
                position_side,
            ):
                logger.info(
                    f"Placing limit order for {symbol}: size={order_size}, price={price}, remaining size={remaining_size}"
                )

                await asyncio.to_thread(
                    self.exchange.create_limit_order,
                    symbol,
                    position_side,
                    order_size,
                    price,
                )

            await asyncio.sleep(np.random.exponential(0.1))

    @command_handler(ClosePosition)
    async def close_position(self, command: ClosePosition):
        position = command.position

        symbol = position.signal.symbol
        position_side = position.side

        logger.info(f"Trying to close position for {symbol}_{position_side}")

        if not self.exchange.fetch_position(symbol, position_side):
            logger.warn(f"Position for {symbol} does not exist. No action taken.")
            return

        exit_order = position.exit_order

        async for bid, ask in self.algo_price.next_value(symbol, self.exchange):
            price = bid if position.side == PositionSide.LONG else ask

            logger.info(
                f"Reducing position for {symbol} -> Algo Price: {price}, "
                f"Theoretical Exit Price: {exit_order.price}"
            )

            existing_position = await asyncio.to_thread(
                self.exchange.fetch_position, symbol, position_side
            )

            if not existing_position:
                logger.info(f"Position for {symbol} already closed.")
                break

            current_position_size = existing_position.get("position_size", 0)

            order_size = next(
                self._calculate_order_slices(symbol, current_position_size)
            )

            logger.info(
                f"Placing reduce order for {symbol}: size={order_size}, price={price}, "
                f"Remaining Position Size={current_position_size}"
            )

            await asyncio.to_thread(
                self.exchange.create_reduce_order,
                symbol,
                position_side,
                order_size,
                price,
            )

            await asyncio.sleep(np.random.exponential(0.5))

    def _calculate_order_slices(self, symbol: Symbol, total_size: int):
        x_min = symbol.min_position_size
        alpha = np.random.uniform(1.3, 1.5)
        decay_factor = 0.88

        while True:
            u = np.random.rand() ** decay_factor

            order_size = x_min * (1 - u) ** (-1 / (alpha - 1))

            order_size = min(order_size, total_size)

            yield order_size
