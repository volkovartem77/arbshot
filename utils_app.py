from subprocess import Popen, PIPE

from config import COMMAND_STOP, COMMAND_START, GENERAL_LOG
from utils import log, decimal


def get_supervisor_status():
    r = Popen([f'''supervisorctl status'''], stdout=PIPE, shell=True)
    resp = str(r.stdout.read().decode())
    lines = resp.split('\n')
    result = []
    for line in [ln for ln in lines if ln != '']:
        line = [ln for ln in line.split(' ') if ln != '']
        result.append({
            'process_name': line[0],
            'status': line[1],
            'comment': ' '.join(line[2:])
        })
    return result


def module(module_name, command):
    r = Popen([f'''supervisorctl {command} {module_name}'''], stdout=PIPE, shell=True)
    resp = str(r.stdout.read())
    if 'ERROR (no such process)' in resp:
        raise Exception(f'<Supervisor> {module_name}: ERROR (no such process)')
    if 'ERROR (already started)' in resp:
        raise Exception(f'<Supervisor> {module_name}: ERROR (already started)')
    if 'ERROR (not running)' in resp:
        if command == COMMAND_STOP:
            return True
        raise Exception(f'<Supervisor> {module_name}: ERROR (not running)')
    command = command if command == 'start' else command + 'p'
    if f'{command}ed' in resp:
        log(f'{command} module: {module_name}', GENERAL_LOG)
        return True
    log(f'{command} module failure: {module_name}', GENERAL_LOG)
    return False


def start_stop_bot(command):
    try:
        trading = module('monitoring', command)
        return trading
    except Exception as e:
        log(f'Exception: {e}', GENERAL_LOG)
        return False


def start_bot():
    return start_stop_bot(COMMAND_START)


def stop_bot():
    return start_stop_bot(COMMAND_STOP)


def format_preferences(data):
    result = {}
    if "api_key" in data:
        result.update({"api_key": str(data['api_key'])})
    if "api_secret" in data:
        result.update({"api_secret": str(data['api_secret'])})
    if "taker_fee" in data:
        result.update({"taker_fee": decimal(data['taker_fee'])})
    if "min_difference" in data:
        result.update({"min_difference": decimal(data['min_difference'])})
    if "orderbook_deep" in data:
        result.update({"orderbook_deep": int(data['orderbook_deep'])})
    if "order_amount_prc" in data:
        result.update({"order_amount_prc": decimal(data['order_amount_prc'])})
    if "timeout_filling" in data:
        result.update({"timeout_filling": int(data['timeout_filling'])})
    if "trade_forward" in data:
        result.update({"trade_forward": bool(data['trade_forward'])})
    if "trade_backward" in data:
        result.update({"trade_backward": bool(data['trade_backward'])})
    return result
