import simplejson
from pymemcache.client.base import Client

PROJECT_PATH = '/home/artem/PycharmProjects/arbshot/'
SUPERVISOR_PATH = '/etc/supervisor/conf.d/'


def get_symbols():
    ff = open(PROJECT_PATH + 'symbols.json', "r")
    result = simplejson.loads(ff.read())
    ff.close()
    return result


def get_symbols_info():
    ff = open(PROJECT_PATH + 'symbols_info.json', "r")
    result = simplejson.loads(ff.read())
    result = format_symbols_info(result)
    ff.close()
    return result


def get_preferences():
    ff = open(PROJECT_PATH + 'preferences.json', "r")
    # ff = open(PROJECT_PATH + 'test_preferences.json', "r")  # TEST
    preferences = simplejson.loads(ff.read())
    ff.close()
    return preferences


def format_symbols_info(symbols_info):
    def _format(data):
        return {
            "price_precision": int(data['price_precision']),
            "amount_precision": int(data['amount_precision']),
            "min_amount": float(data['min_amount']),
            "tick_size": float(data['tick_size']),
            "base": str(data['base']),
            "quote": str(data['quote'])
        }
    return dict((k, _format(v)) for k, v in symbols_info.items())


# MEM CACHE SERVER
MEMORY_CACHE = Client('127.0.0.1:11211', no_delay=True)
# MEM CACHE CONST
MEMORY_CACHE_LOG = 'memory_cache'
MEM_SETTINGS = 'settings'
MEM_BALANCE = 'balance'
MEM_BOT_STATUS = 'bot_status'
MEM_LOG = 'log'

SYMBOLS = [s['symbol'] for s in get_symbols()['symbols']]
SYMBOLS_LOWER = [s.lower() for s in SYMBOLS]
SYMBOLS_INFO = get_symbols_info()
TOKENS_BTC = [s['base'] for s in get_symbols()['symbols'] if s['quote'] == 'BTC']
TOKENS = sorted(list(set([s['base'] for s in get_symbols()['symbols'] if s['base'] in TOKENS_BTC])))

# Logging
LOG_PATH = PROJECT_PATH + 'log'
GENERAL_LOG = 'general'
STREAM_LOG = 'stream'

# TRADING
ORDER_STATUS_NEW = 'NEW'
ORDER_STATUS_FILLED = 'FILLED'
ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
ORDER_STATUS_CANCELED = 'CANCELED'
ORDER_STATUS_EXPIRED = 'EXPIRED'

ORDER_SIDE_BUY = 'BUY'
ORDER_SIDE_SELL = 'SELL'

# PREFERENCES
DEFAULT_SETTINGS = get_preferences()['default_settings']
FILTER_PROFIT_USDT = get_preferences()['filter_profit_usdt']
FILTER_MIN_AMOUNT_USDT = get_preferences()['filter_min_amount_usdt']
MEM_LOG_LENGTH = get_preferences()['mem_log_length']
LOG_SIZE_MB = get_preferences()['log_size_mb']
PRINT_LOG = get_preferences()['print_log']
TEST_MODE = get_preferences()['test_mode']
