import time

from rest.restBinanceSpot import RestBinanceSpot

rest = RestBinanceSpot("fFXUKcEHPPB0OyfD1rmqjy8JY7aMLM05I3tiEFLius9F6pN62qkotZC2FlX30NO3",
                       "UM19eQXyA3pTzMIifZk3V0uLAXOQDPoug7ZRB1coMiGLApLwYbjF93LCB0KwwIAr")

rest_cl = rest.Client
t = time.time()
b_time = rest_cl.get_server_time()
tt = time.time()
print('send', t)
print('receive', tt, b_time)
print('server -> binance', b_time['serverTime'] - int(t * 1000), 'ms')
print('binance -> server', int(tt * 1000) - b_time['serverTime'], 'ms')
print('total', (tt - t) * 1000, 'ms')
exit()
