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
        result.update({"taker_fee": float(data['taker_fee'])})
    if "min_difference" in data:
        result.update({"min_difference": float(data['min_difference'])})
    if "order_amount_prc" in data:
        result.update({"order_amount_prc": float(data['order_amount_prc'])})
    if "amount_btc_lock" in data:
        result.update({"amount_btc_lock": float(data['amount_btc_lock'])})
    if "btc_hold_price" in data:
        result.update({"btc_hold_price": float(data['btc_hold_price'])})
    if "recv_window" in data:
        result.update({"recv_window": float(data['recv_window'])})
    if "forward" in data:
        result.update({"forward": bool(data['forward'])})
    if "backward" in data:
        result.update({"backward": bool(data['backward'])})
    if "trading" in data:
        result.update({"trading": bool(data['trading'])})
    return result
