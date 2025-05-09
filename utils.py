import os
import time
import traceback
import uuid
from datetime import datetime
from decimal import Decimal

import pytz as pytz
import simplejson

from config import LOG_PATH, LOG_SIZE_MB, PRINT_LOG, MEMORY_CACHE, MEMORY_CACHE_LOG, MEM_LOG, MEM_LOG_LENGTH, \
    MEM_BOT_STATUS, MEM_SETTINGS, STREAM_LOG, MEM_BALANCE, MEM_RAW_STATS, MEM_ORDER, MEM_HISTORY, MEM_RAW_ORDERS, \
    MEM_TRADES


def set_mem_cache(key, prefix, data, expire=None):
    try:
        if expire:
            MEMORY_CACHE.set(f'{key}:{prefix}', simplejson.dumps(data), expire=expire)
        else:
            MEMORY_CACHE.set(f'{key}:{prefix}', simplejson.dumps(data))
    except TypeError:
        log(traceback.format_exc(), MEMORY_CACHE_LOG)


def get_mem_cache(var, prefix):
    try:
        data = MEMORY_CACHE.get(f'{var}:{prefix}')
        if data:
            return simplejson.loads(data)
    except TypeError:
        log(traceback.format_exc(), MEMORY_CACHE_LOG)


def delete_mem_cache(var, prefix):
    try:
        MEMORY_CACHE.delete(f'{var}:{prefix}')
    except TypeError:
        log(traceback.format_exc(), MEMORY_CACHE_LOG)


def mem_get_spread(symbols):
    return MEMORY_CACHE.get_many(symbols)


def mem_set_bot_status(status: str):
    prefix = f''.lower()
    set_mem_cache(MEM_BOT_STATUS, prefix, status)


def mem_get_bot_status():
    prefix = f''.lower()
    return get_mem_cache(MEM_BOT_STATUS, prefix)


def mem_set_settings(settings: dict):
    prefix = f''.lower()
    set_mem_cache(MEM_SETTINGS, prefix, settings)


def mem_get_settings():
    prefix = f''.lower()
    return get_mem_cache(MEM_SETTINGS, prefix)


def mem_update_settings(settings: dict):
    mem_settings = mem_get_settings()
    if mem_settings:
        mem_settings.update(settings)
        mem_set_settings(mem_settings)


def mem_set_balance(balances):
    prefix = f''.lower()
    set_mem_cache(MEM_BALANCE, prefix, balances)


def mem_get_balance():
    prefix = f''.lower()
    return format_balance(get_mem_cache(MEM_BALANCE, prefix))


def format_balance(data):
    if data is not None:
        return dict((str(asset), decimal(balance)) for asset, balance in data.items())


def mem_set_raw_stats(raw_stats: dict):
    prefix = f''.lower()
    set_mem_cache(MEM_RAW_STATS, prefix, raw_stats)


def mem_get_raw_stats():
    prefix = f''.lower()
    return get_mem_cache(MEM_RAW_STATS, prefix)


def mem_add_raw_stats(chain_id, raw_stat):
    raw_stats = mem_get_raw_stats()
    if raw_stats is None:
        mem_set_raw_stats({})
        raw_stats = mem_get_raw_stats()
    raw_stats.update({chain_id: raw_stat})
    mem_set_raw_stats(raw_stats)


def mem_remove_raw_stats(chain_id):
    raw_stats = mem_get_raw_stats()
    if raw_stats and chain_id in raw_stats:
        raw_stats.pop(chain_id)
        mem_set_raw_stats(raw_stats)


def mem_set_raw_orders(raw_orders: dict):
    prefix = f''.lower()
    set_mem_cache(MEM_RAW_ORDERS, prefix, raw_orders)


def mem_get_raw_orders():
    prefix = f''.lower()
    return get_mem_cache(MEM_RAW_ORDERS, prefix)


def mem_add_raw_order(order_id, raw_order):
    raw_orders = mem_get_raw_orders()
    if raw_orders is None:
        mem_set_raw_orders({})
        raw_orders = mem_get_raw_orders()
    raw_orders.update({order_id: raw_order})
    mem_set_raw_orders(raw_orders)


def mem_remove_raw_order(order_id):
    raw_orders = mem_get_raw_orders()
    if raw_orders and order_id in raw_orders:
        raw_orders.pop(order_id)
        mem_set_raw_orders(raw_orders)


def mem_set_order(order_id, order: dict, expire=None):
    prefix = f'{order_id}'.lower()
    set_mem_cache(MEM_ORDER, prefix, order, expire)


def mem_get_order(order_id):
    prefix = f'{order_id}'.lower()
    return get_mem_cache(MEM_ORDER, prefix)


def mem_rm_order(order_id):
    prefix = f'{order_id}'.lower()
    delete_mem_cache(MEM_ORDER, prefix)


def mem_set_history(history: dict):
    prefix = f''.lower()
    set_mem_cache(MEM_HISTORY, prefix, history)


def mem_get_history():
    prefix = f''.lower()
    return get_mem_cache(MEM_HISTORY, prefix)


def mem_add_history(chain_id, history):
    mem_history = mem_get_history()
    if mem_history is None:
        mem_set_history({})
        mem_history = mem_get_history()
    mem_history.update({chain_id: history})
    mem_set_history(mem_history)


def mem_set_trades(trades: dict):
    prefix = f''.lower()
    set_mem_cache(MEM_TRADES, prefix, trades)


def mem_get_trades():
    prefix = f''.lower()
    return get_mem_cache(MEM_TRADES, prefix)


def mem_add_trade(order_id, trade):
    mem_trades = mem_get_trades()
    if mem_trades is None:
        mem_set_trades({})
        mem_trades = mem_get_trades()
    mem_trades.update({order_id: trade})
    mem_set_trades(mem_trades)


def datetime_str():
    return datetime.now().replace(microsecond=0).isoformat().replace('T', ' ')


def datetime_str_ms(tz=False):
    now = datetime.now(pytz.timezone('Europe/Paris')) if tz else datetime.now()
    return now.isoformat().replace('T', ' ').split('+')[0]


def datetime_diff(timestamp_1, timestamp_2):
    datetime_1 = datetime.utcfromtimestamp(timestamp_1 / 1000)
    datetime_2 = datetime.utcfromtimestamp(timestamp_2 / 1000)
    diff = str(datetime_2 - datetime_1)
    return diff[:-3] if '.' in diff else diff


def timestamp_to_datetime_str(timestamp: int):
    try:
        return str(datetime.utcfromtimestamp(timestamp))
    except ValueError:
        try:
            return str(datetime.utcfromtimestamp(timestamp / 1000))[:-3]
        except ValueError:
            return str(datetime.utcfromtimestamp(timestamp / 1000000))


def mem_set_log(module, lines: list):
    prefix = f'{module}'.lower()
    set_mem_cache(MEM_LOG, prefix, lines)


def mem_get_log(module):
    prefix = f'{module}'.lower()
    return get_mem_cache(MEM_LOG, prefix)


def mem_add_to_log(module, line: str):
    log_list = mem_get_log(module)
    # Init if None
    if log_list is None:
        mem_set_log(module, [])
        log_list = mem_get_log(module)
    # Trim length
    if len(log_list) >= MEM_LOG_LENGTH:
        log_list.pop(0)
    # Append line
    log_list.append(line)
    mem_set_log(module, log_list)


def create_backlog(module):
    path = '{}/{}.log'.format(LOG_PATH, module)
    path2 = '{}/{}.backlog'.format(LOG_PATH, module)
    file = open(path, "r")
    lines = file.readlines()
    file.close()
    file = open(path2, "w")
    file.writelines(lines)
    file.close()


def log_to_file(msg, module):
    os.makedirs(LOG_PATH, exist_ok=True)
    path = '{}/{}.log'.format(LOG_PATH, module)
    try:
        file_size = os.path.getsize(path)
        if file_size / 1024 / 1024 > LOG_SIZE_MB:
            create_backlog(module)
            file = open(path, "w")
        else:
            file = open(path, "a")
    except FileNotFoundError:
        file = open(path, "a")

    file.write(msg)
    file.close()


def log(text, module, mark='', to_file=True, to_mem=False):
    dt = datetime_str_ms()
    if to_file:
        log_to_file(dt + ' ' + mark + ' ' + text + '\n', module)
    if to_mem:
        mem_add_to_log(module, dt + ' ' + mark + ' ' + text + '\n')
    if PRINT_LOG:
        print(dt + ' ' + mark + ' ' + text)


def time_now_mcs():
    return int(time.time() * 1000000)


def time_diff_ms(t):
    return round((time.time() - t) * 1000, 3)


def float_to_str(number):
    return "{0:.10f}".format(number)


def to_digits(number):
    number = float(number)
    if number >= 1:
        return - len(float_to_str(number).split('.')[0]) + 1
    else:
        return len(float_to_str(number).split('.')[1].split('1')[0]) + 1


def to_digits2(number):
    number = float(number)
    if number >= 1:
        return - len(float_to_str(number).split('.')[0]) + 1
    else:
        decimal_part_str = float_to_str(number).split('.')[1]
        decimal_part_list = list(decimal_part_str)
        try:
            while decimal_part_list[-1] == '0':
                decimal_part_list.pop(-1)
            result = "".join(decimal_part_list)
            return len(result)
        except IndexError:
            return 0


def decimal(number):
    return Decimal(str(number))


def time_now():
    return int(time.time())


def time_now_ms():
    return int(time.time() * 1000)


def round_up(number: Decimal, precision: int):
    result = round(number, precision)
    return scientific_to_decimal(result + decimal(1 / 10) ** precision if result < number else result)


def round_down(number: Decimal, precision: int):
    result = round(number, precision)
    return scientific_to_decimal(result - decimal(1 / 10) ** precision if result > number else result)


def round_down_float(number: float, precision: int):
    result = round(number, precision)
    return result - (1 / 10) ** precision if result > number else result


def base_to_quote(amount, price):
    return decimal(amount * price)


def quote_to_base(amount, price):
    return decimal(amount / price)


def timestamp_to_date(timestamp):
    return str(datetime.utcfromtimestamp(timestamp))


def scientific_to_str(num):
    return format(num, 'f')


def scientific_to_decimal(num: Decimal):
    return decimal(scientific_to_str(num))


def find_filter(filter_name, symbol_info):
    # *** for Binance ONLY ***
    return list(filter(lambda f: f['filterType'] == filter_name, symbol_info['filters']))[0]


def retrying(function, kwargs, exception, attempts: int, retrying_delay: int):
    for a in range(attempts - 1):
        try:
            return function(**kwargs)
        except exception as e:
            log(f'{e}. Try again in {retrying_delay} sec. '
                f'Attempts left {attempts - 1 - a}', STREAM_LOG, 'STREAM')
            time.sleep(retrying_delay)
    return function(**kwargs)


def make_chain_id():
    return uuid.uuid4().hex


def make_client_order_id():
    return 'arb_' + uuid.uuid4().hex
