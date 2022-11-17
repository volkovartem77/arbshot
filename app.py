import traceback

from flask import Flask, jsonify
from flask_cors import cross_origin, CORS

from config import GENERAL_LOG, DEFAULT_SETTINGS
from utils import log, mem_get_settings, mem_set_settings, mem_get_log, mem_set_bot_status, mem_get_bot_status, \
    mem_get_balance, mem_get_history, mem_set_history
from utils_app import start_bot, stop_bot

# Load default setting to mem
if mem_get_settings() is None:
    mem_set_settings(DEFAULT_SETTINGS)
if mem_get_bot_status() is None:
    mem_set_bot_status("Stopped")

app = Flask(__name__)
CORS(app)


@app.route('/')
@cross_origin()
def index():
    return jsonify({'success': 'ok'})


@app.route('/get_bot_status', methods=['GET'])
@cross_origin()
def get_bot_status():
    """
    http://127.0.0.1:5000/get_bot_status
    """
    try:
        result = jsonify({'bot_status': str(mem_get_bot_status()), 'error': ''})
    except Exception as e:
        log(traceback.format_exc(), GENERAL_LOG, 'SERVER')
        result = jsonify({'bot_status': 'Error', 'error': f'{e}'})
    return result


@app.route('/start', methods=['GET'])
@cross_origin()
def start():
    """
    http://127.0.0.1:5000/start
    """
    try:
        if start_bot():
            mem_set_bot_status("Active")
        result = jsonify({'bot_status': str(mem_get_bot_status()), 'error': ''})
    except Exception as e:
        log(traceback.format_exc(), GENERAL_LOG, 'SERVER')
        result = jsonify({'bot_status': 'Error', 'error': f'{e}'})
    return result


@app.route('/stop', methods=['GET'])
@cross_origin()
def stop():
    """
    http://127.0.0.1:5000/stop
    """
    try:
        if stop_bot():
            mem_set_bot_status("Stopped")
        result = jsonify({'bot_status': str(mem_get_bot_status()), 'error': ''})
    except Exception as e:
        log(traceback.format_exc(), GENERAL_LOG, 'SERVER')
        result = jsonify({'bot_status': 'Error', 'error': f'{e}'})
    return result

# @app.route('/get_preferences', methods=['GET'])
# @cross_origin()
# def get_preferences():
#     """
#     http://127.0.0.1:5000/get_preferences
#     """
#     try:
#         preferences = mem_get_settings()
#         if preferences:
#             if 'api_key' in preferences:
#                 preferences['api_key'] = ''
#             if 'api_secret' in preferences:
#                 preferences['api_secret'] = ''
#             result = jsonify({'preferences': preferences})
#         else:
#             result = jsonify({'success': 'false', 'error': f'mem_get_settings: None'})
#     except Exception as e:
#         log(traceback.format_exc(), GENERAL_LOG, 'SERVER')
#         result = jsonify({'success': 'false', 'error': f'{e}'})
#     return result


@app.route('/get_history', methods=['GET'])
@cross_origin()
def get_history():
    """
    http://127.0.0.1:5000/get_history
    """
    try:
        history = mem_get_history()
        if history:
            result = jsonify({'history': history})
        else:
            result = jsonify({'history': {}})
    except Exception as e:
        log(traceback.format_exc(), GENERAL_LOG, 'ERROR')
        result = jsonify({'success': 'false', 'error': f'{e}', 'history': {}})
    return result


@app.route('/clear_history', methods=['GET'])
@cross_origin()
def clear_history():
    """
    http://127.0.0.1:5000/clear_history
    """
    try:
        mem_set_history({})
        history = mem_get_history()
        if history:
            result = jsonify({'history': history})
        else:
            result = jsonify({'history': {}})
    except Exception as e:
        log(traceback.format_exc(), GENERAL_LOG, 'ERROR')
        result = jsonify({'success': 'false', 'error': f'{e}', 'history': {}})
    return result


@app.route('/get_balance', methods=['GET'])
@cross_origin()
def get_balance():
    """
    http://127.0.0.1:5000/get_balance
    """
    try:
        balance = mem_get_balance()
        if balance:
            balance = dict((a, float(v)) for a, v in balance.items() if a == 'USDT' or a == 'BTC')
            result = jsonify({'balance': balance})
        else:
            result = jsonify({'success': 'false', 'error': f'mem_get_balance: None', 'balance': {}})
    except Exception as e:
        log(traceback.format_exc(), GENERAL_LOG, 'ERROR')
        result = jsonify({'success': 'false', 'error': f'{e}', 'balance': {}})
    return result


@app.route('/get_log', methods=['GET'])
@cross_origin()
def get_log():
    """
    http://127.0.0.1:5000/get_log
    """
    try:
        data = mem_get_log(GENERAL_LOG)
        if data is not None:
            result = jsonify({'log': data})
        else:
            result = jsonify({'log': []})
    except Exception as e:
        log(traceback.format_exc(), GENERAL_LOG, 'ERROR')
        result = jsonify({'success': 'false', 'error': f'{e}', 'log': []})
    return result


# @app.route('/set_preferences', methods=['POST'])
# @cross_origin()
# def set_preferences():
#     """
#         http://127.0.0.1:5000/set_preferences
#         application/json
#         {
#             "api_key": "",
#             "api_secret": "",
#             "taker_fee": 0.1,
#             "min_difference": -0.35,
#             "orderbook_deep": 1,
#             "order_amount_prc": 100,
#             "timeout_filling": 1,
#             "trade_forward": true,
#             "trade_backward": true
#           }
#         }
#     """
#     if request.data:
#         data = simplejson.loads(request.data)
#         try:
#             settings = mem_get_settings()
#             if settings:
#                 data = format_preferences(data)
#                 if 'api_key' in data and data['api_key'] == '':
#                     data['api_key'] = settings['api_key']
#                 if 'api_secret' in data and data['api_secret'] == '':
#                     data['api_secret'] = settings['api_secret']
#
#                 settings.update(data)
#                 mem_set_settings(settings)
#                 log(f"Setting saved", GENERAL_LOG, 'INFO', to_mem=True)
#
#                 settings = mem_get_settings()
#                 if settings:
#                     settings['api_key'] = ''
#                     settings['api_secret'] = ''
#                     result = jsonify({'preferences': settings})
#                 else:
#                     result = jsonify({'success': 'false', 'error': f'mem_get_settings2: None'})
#             else:
#                 result = jsonify({'success': 'false', 'error': f'mem_get_settings: None'})
#         except Exception as e:
#             log(traceback.format_exc(), GENERAL_LOG, 'SERVER')
#             result = jsonify({'success': 'false', 'error': f'{e}|type {type(e)}'})
#     else:
#         result = jsonify({'success': 'false', 'error': f'request.data: None'})
#     return result
