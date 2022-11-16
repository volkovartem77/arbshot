import os
import time
import traceback
from datetime import datetime
from decimal import Decimal

import pytz as pytz
import simplejson

from config import LOG_PATH, LOG_SIZE_MB, PRINT_LOG, MEMORY_CACHE, MEMORY_CACHE_LOG, MEM_LOG, MEM_LOG_LENGTH, \
    MEM_BOT_STATUS, MEM_SETTINGS, STREAM_LOG, MEM_BALANCE


def set_mem_cache(key, prefix, data):
    try:
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


def datetime_str_ms(tz=False):
    now = datetime.now(pytz.timezone('Europe/Paris')) if tz else datetime.now()
    return now.isoformat().replace('T', ' ').split('+')[0]


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
