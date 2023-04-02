from dotenv import load_dotenv
import os
import websocket
import json
from analytics.performance import PerformanceStats
from broker.futures_bybit_broker import FuturesBybitBroker
from broker.margin_mode import MarginMode
from broker.position_mode import PositionMode
from risk_management.stop_loss.atr_stop_loss_finder import ATRStopLossFinder
from risk_management.stop_loss.trailing_stop_loss_finder import TrailingStopLossFinder
from risk_management.take_profit.risk_reward_take_profit_finder import RiskRewardTakeProfitFinder
from strategy.aobb_strategy import AwesomeOscillatorBBStrategy

from risk_management.risk_manager import RiskManager
from trader.simple_trader import SimpleTrader

load_dotenv()

symbol = 'SPELLUSDT'
timeframe = '1'
leverage = 1
channels = [f"kline.{timeframe}.{symbol}"]

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

atr_multi = 0.85
risk_reward_ratio = 4
risk_per_trade = 0.00001
lookback_period = 20
slow_sma_period = 100

broker = FuturesBybitBroker(API_KEY, API_SECRET)
broker.set_leverage(symbol, leverage)
broker.set_position_mode(symbol, PositionMode.ONE_WAY)
broker.set_margin_mode(symbol, mode=MarginMode.ISOLATED, leverage=leverage)

atr_stop_loss_finder = ATRStopLossFinder(multiplier=atr_multi)
stop_loss_finder = TrailingStopLossFinder(stop_loss_finder=atr_stop_loss_finder)
take_profit_finder = RiskRewardTakeProfitFinder(risk_reward_ratio=risk_reward_ratio)

market = broker.get_symbol_info(symbol)
initial_balance = broker.get_account_balance()

rm = RiskManager(stop_loss_finder, take_profit_finder, risk_per_trade=risk_per_trade, trading_fee=market['trading_fee'], price_precision=market['price_precision'], position_precision=market['position_precision'])
analytics = PerformanceStats(initial_balance)
trader = SimpleTrader(broker, rm, analytics)
wss = 'wss://stream.bybit.com/v5/public/linear'
strategy = AwesomeOscillatorBBStrategy(sma_period=slow_sma_period)

def on_open(ws):
    print("WebSocket connection opened")
    for channel in channels:
        ws.send(json.dumps({"op": "subscribe", "args": [channel]}))

def on_message(ws, message):
    trader.trade(strategy, symbol, f"{timeframe}m")

def on_error(ws, error):
    print(f"WebSocket error: {error}")
    for channel in channels:
        ws.send(json.dumps({"op": "unsubscribe", "args": [channel]}))

def on_close(ws):
    print("WebSocket connection closed")

ws = websocket.WebSocketApp(
    wss,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
