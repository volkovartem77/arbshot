import asyncio
import time
import traceback
from decimal import Decimal

from pynats import NATSClient

from config import GENERAL_LOG, SYMBOLS_INFO, ORDER_SIDE_BUY, ORDER_STATUS_FILLED, ORDER_SIDE_SELL
from models import Params
from rest.restBinanceSpot import RestBinanceSpot
from utils import mem_get_balance, quote_to_base, decimal, round_up, round_down, time_diff_ms, datetime_str_ms, log


class Trading:
    def __init__(self, params: Params):
        self.rest = RestBinanceSpot(params.APIKey, params.APISecret)
        self.OrderAmountPrc = params.OrderAmountPrc
        self.TakerFee = params.TakerFee

        self.Balance = {}

        # Init NATSConnection
        self.NATS = NATSClient()
        self.NATS.connect()

    def log(self, text, module, mark=''):
        dt = datetime_str_ms()
        payload = dt + ' ' + mark + ' ' + text + '\n'
        try:
            self.NATS.publish(subject=module, payload=payload.encode())
        except BrokenPipeError:
            self.NATS.connect()
            self.NATS.publish(subject=module, payload=payload.encode())

    @staticmethod
    def price_to_precision(symbol, price: Decimal):
        return round(price, decimal(SYMBOLS_INFO[symbol]['price_precision']))

    @staticmethod
    def amount_to_precision(symbol, amount: Decimal, price: Decimal):
        amount_precision = int(SYMBOLS_INFO[symbol]['amount_precision'])
        conv = decimal(SYMBOLS_INFO[symbol]['min_amount']) / price
        min_amount = round_up(conv, amount_precision)
        my_amount = round_down(amount, amount_precision)
        # log(f'Min {min_amount} My {my_amount} ({symbol} {price})', GENERAL_LOG, 'TEST')
        return my_amount if my_amount >= min_amount else 0

    def get_amount_btc(self, symbol, price):
        balance_usdt = self.Balance['USDT']
        amount_usdt = balance_usdt * decimal(self.OrderAmountPrc / 100)
        amount_btc = self.amount_to_precision(symbol, quote_to_base(amount_usdt, price), price)
        return amount_btc

    def get_amount_token(self, symbol, price):
        balance_usdt = self.Balance['USDT']
        amount_usdt = balance_usdt * decimal(self.OrderAmountPrc / 100)
        amount_token = self.amount_to_precision(symbol, quote_to_base(amount_usdt, price), price)
        return amount_token

    def place_limit_order(self, symbol, amount, price, side, base):
        self.log(f"Send LIMIT {symbol} {side} {amount} {base} @{price}", GENERAL_LOG, 'INFO')
        t = time.time()
        order = self.rest.place_limit(symbol, amount, price, side, time_in_force='GTC')
        placing_speed = time_diff_ms(t)
        self.log(f"Order {order['orderId']} {order['type']} {order['symbol']} {order['side']} "
                 f"{order['origQty']} {base} @{order['price']} {order['status']}", GENERAL_LOG, 'INFO')
        self.log(f"Order {order['orderId']} PlacingSpeed={placing_speed}ms TransactTime={order['transactTime']}",
                 GENERAL_LOG, 'INFO')
        return order

    def place_limit_fok_order(self, symbol, amount, price, side, base):
        self.log(f"Send LIMIT {symbol} {side} {amount} {base} @{price}", GENERAL_LOG, 'INFO')
        t = time.time()
        order = self.rest.place_limit(symbol, amount, price, side, time_in_force='FOK')
        placing_speed = time_diff_ms(t)
        self.log(f"Order {order['orderId']} {order['type']} {order['symbol']} {order['side']} "
                 f"{order['origQty']} {base} @{order['price']} {order['status']}", GENERAL_LOG, 'INFO')
        self.log(f"Order {order['orderId']} PlacingSpeed={placing_speed}ms TransactTime={order['transactTime']}",
                 GENERAL_LOG, 'INFO')
        return order

    async def place_limit_order_async(self, symbol, amount, price, side, base):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.place_limit_order, symbol, amount, price, side, base)

    def place_orders_async(self, params1, params2):
        async def place():
            task_1 = asyncio.create_task(self.place_limit_order_async(*params1))
            task_2 = asyncio.create_task(self.place_limit_order_async(*params2))

            order_1 = await task_1
            order_2 = await task_2
            return order_1, order_2

        return asyncio.run(place())

    def execute(self, chain):
        try:
            arb = chain[0]
            forward = chain[1]
            efficiency = decimal(chain[2])
            symbol_1 = chain[3]
            symbol_2 = chain[4]
            symbol_3 = chain[5]
            price_1 = decimal(chain[6])
            price_2 = decimal(chain[7])
            price_3 = decimal(chain[8])
            max_amount_token = decimal(chain[9])
            max_amount_btc = decimal(chain[10])

            if forward:
                amount_token = self.get_amount_token(symbol_1, price_1)
                if amount_token == 0:
                    self.log(f"SKIPPED Not enough balance for this trade", GENERAL_LOG, arb)
                    return

                if self.amount_to_precision(symbol_1, max_amount_token, price_1) == 0:
                    self.log(f"SKIPPED Amount in orderbook is too small", GENERAL_LOG, arb)
                    return

                # Step 1: Place LIMIT (FOK) BUY TOKEN/USDT
                token = SYMBOLS_INFO[symbol_1]['base']
                amount_token = min(amount_token, max_amount_token)
                order_1 = self.place_limit_fok_order(symbol_1, amount_token, price_1, ORDER_SIDE_BUY, token)
                if order_1['status'] == ORDER_STATUS_FILLED:
                    amount_spent_usdt = decimal(order_1['cummulativeQuoteQty'])
                    commission_token = sum([decimal(fill['commission']) for fill in order_1['fills']])
                    amount_received_token = amount_token - commission_token
                    amount_received_token = self.amount_to_precision(symbol_2, amount_received_token, price_2)
                    params1 = (symbol_2, amount_received_token, price_2, ORDER_SIDE_SELL, token)

                    fee = decimal(1 - (self.TakerFee / 100))
                    amount_received_btc = amount_received_token * price_2 * fee
                    amount_received_btc = self.amount_to_precision(symbol_3, amount_received_btc, price_3)
                    params2 = (symbol_3, amount_received_btc, price_3, ORDER_SIDE_SELL, token)

                    # Step 2: Place LIMIT LIMIT (GTC) TOKEN/BTC BTC/USDT
                    order_2, order_3 = self.place_orders_async(params1, params2)
                    self.log(f"ARBITRAGE HOLDING TradeSize {amount_spent_usdt} USDT", GENERAL_LOG, arb)
                    # todo: -> to stats
                else:
                    self.log(f"ARBITRAGE CANCELLED", GENERAL_LOG, arb)
            else:
                self.log(f"Backward not implemented", GENERAL_LOG, arb)

            # Update balance
            self.Balance = mem_get_balance()
            self.log(f"Balance now {self.Balance['USDT']} USDT  {self.Balance['BTC']} BTC", GENERAL_LOG, 'INFO')

        except Exception:
            log(traceback.format_exc(), GENERAL_LOG, 'ERROR', to_mem=True)
