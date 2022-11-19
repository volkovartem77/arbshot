from decimal import Decimal

import requests
from binance.client import Client as binanceClient
from binance.exceptions import BinanceAPIException

from config import GENERAL_LOG
from exceptions import InvalidAPIKeyException, NoBalanceException, UnknownBinanceException, NoConnectionException, \
    UnknownOrderException, LimitPriceException, TimestampError
from utils import log, scientific_to_str


def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BinanceAPIException as e:
            log(e.message, GENERAL_LOG, f'INFO', to_mem=True)
            if e.message == 'Account has insufficient balance for requested action.':
                raise NoBalanceException
            elif e.message == 'Unknown order sent.':
                raise UnknownOrderException
            elif e.message == "Limit price can't be higher than":
                raise LimitPriceException
            elif 'Invalid JSON error message from Binance' in e.message:
                raise UnknownBinanceException(e.message)
            elif 'Timestamp for this request is outside of the recvWindow' in e.message:
                raise TimestampError
        except requests.exceptions.ConnectionError:
            log(f'Connection Error', GENERAL_LOG, to_mem=True)
            raise NoConnectionException
        except requests.exceptions.ReadTimeout:
            log(f'Connection Error', GENERAL_LOG, to_mem=True)
            raise NoConnectionException
    return wrapper


class RestBinanceSpot:
    def __init__(self, api_key, api_secret):
        self.APIKey = api_key
        self.APISecret = api_secret
        self.Client = binanceClient(self.APIKey, self.APISecret)
        self.validate_api()

    @exception_handler
    def validate_api(self):
        try:
            self.Client.get_account()
        except BinanceAPIException:
            raise InvalidAPIKeyException()

    @exception_handler
    def get_exchange_info(self):
        return self.Client.get_exchange_info()

    @exception_handler
    def get_market_info(self, symbol):
        return self.Client.get_symbol_info(symbol)

    @exception_handler
    def get_all_balances(self):
        account = self.Client.get_account()
        return dict((x['asset'], Decimal(str(x['free']))) for x in account["balances"] if Decimal(str(x['free'])) > 0)

    @exception_handler
    def place_limit(self, symbol, amount, price, side, time_in_force='GTC', client_order_id=None, recv_window=9999):
        return self.Client.create_order(
            symbol=symbol.upper(),
            side=side,
            quantity=amount,
            price=scientific_to_str(price),
            type='LIMIT',
            timeInForce=time_in_force,
            newClientOrderId=client_order_id,
            recvWindow=recv_window)

    @exception_handler
    def place_market(self, symbol, amount, side, client_order_id=None):
        return self.Client.create_order(
            symbol=symbol,
            side=side,
            quantity=amount,
            type='MARKET',
            newClientOrderId=client_order_id,
            recvWindow=9999)

    @exception_handler
    def place_market_quote(self, symbol, amount, side, client_order_id=None):
        return self.Client.create_order(
            symbol=symbol,
            side=side,
            quoteOrderQty=amount,
            type='MARKET',
            newClientOrderId=client_order_id,
            recvWindow=9999)

    @exception_handler
    def get_order_info_by_client_id(self, symbol, order_id):
        return self.Client.get_order(symbol=symbol, origClientOrderId=str(order_id))

    @exception_handler
    def cancel_order_by_id(self, symbol, order_id):
        self.Client.cancel_order(symbol=symbol, orderId=int(order_id))

    @exception_handler
    def cancel_order_by_client_id(self, symbol, order_id):
        self.Client.cancel_order(symbol=symbol, origClientOrderId=str(order_id))

    @exception_handler
    def stream_get_listen_key(self):
        return self.Client.stream_get_listen_key()

    @exception_handler
    def stream_keepalive(self, listen_key):
        return self.Client.stream_keepalive(listen_key)
