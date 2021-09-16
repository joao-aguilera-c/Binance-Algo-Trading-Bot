"""Nesse arquivo colocarei todas as estratégias existentes. começando pela mais simples: stochtest"""
import datetime
import pandas as pd
from io import StringIO
from collections import deque
from binance.client import Client
from ta.momentum import stoch_signal
from ta.trend import ema_indicator
from binance.enums import *
import math
import binance.exceptions as exceptions
import send_email as email
import numpy as np
import order_management as orders


def format_float(num):
    return np.format_float_positional(num, trim='-')


def utcnow():
    return datetime.datetime.utcnow()


def strutcnow():
    now = datetime.datetime.utcnow()
    strnow = f'{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}'
    return strnow


def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper


def reset_my_index(data_frame):
    res = data_frame[::-1].reset_index(drop=True)
    return res


def input_csv_data(directory, symbol, how_many_candles):
    with open('%s/%s.csv' % (directory, symbol), 'r') as f:
        q = deque(f, how_many_candles)  # replace 2 with n (lines read at the end)
    df = pd.read_csv(StringIO(''.join(q)), header=None)

    df[1] = [float(n) for n in df[1]]
    df[2] = [float(n) for n in df[2]]
    df[3] = [float(n) for n in df[3]]
    df[4] = [float(n) for n in df[4]]

    df.rename(columns={0: 'time', 1: 'open', 2: 'high', 3: 'low', 4: 'close'}, inplace=True)
    return df


def get_decimal_digits(string_number):
    number = float(string_number)
    digits = 0
    while number < 1:
        number = number * 10
        digits += 1
    return digits


async def test_brackets_buy(client, df, symbol, s_dict, ratio=10, max_usd_loss=1):
    symbol_info = s_dict[symbol]
    symbol_info_filters = symbol_info['filters']
    min_price = symbol_info_filters[0]['minPrice']
    step_size = symbol_info_filters[2]['stepSize']
    min_notional = symbol_info_filters[3]['minNotional']

    min_price_digits = get_decimal_digits(min_price)
    step_size_digits = get_decimal_digits(step_size)

    entry = df['high'][0]
    sl = df['low'][0]
    tp = truncate(
        (ratio * (entry - sl) + entry),
        min_price_digits
    )

    size = truncate(
        abs(max_usd_loss / (entry - sl)),
        digits=step_size_digits
    )
    print("{} - Size para {} é: {} {}.".format(
        strutcnow(), symbol, size, symbol[:-4]))

    try:
        main_order = await client.create_test_order(symbol=symbol,
                                                    side=SIDE_BUY,
                                                    type=ORDER_TYPE_STOP_LOSS_LIMIT,
                                                    quantity=size,
                                                    stopPrice=entry * 2,
                                                    price=entry * 2,
                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                    newClientOrderId='main_order')
    except exceptions.BinanceAPIException as e:
        tittle = ('%s ERROR ON %s SL ORDER: %s' % (strutcnow(), symbol, e.message))
        message = ("{} - data on the order is: entry: {} // sl: {} // tp: {} //// {}".format(strutcnow(),
                                                                                             entry,
                                                                                             sl,
                                                                                             tp,
                                                                                             e.message))
        print(tittle)
        email.send_email(tittle.encode('utf-8'), message.encode('utf-8'))

    try:
        stop_loss_order = await client.create_test_order(symbol=symbol,
                                                         side=SIDE_SELL,
                                                         type=ORDER_TYPE_STOP_LOSS_LIMIT,
                                                         timeInForce=TIME_IN_FORCE_GTC,
                                                         quantity=size,
                                                         price=entry,
                                                         stopPrice=sl,
                                                         newClientOrderId='stop_loss_order'
                                                         )
    except exceptions.BinanceAPIException as e:
        print('%s ERROR ON TP %s: %s' % (strutcnow(), symbol, e.message))

    try:
        take_profit_order = await client.create_test_order(symbol=symbol,
                                                           side=SIDE_SELL,
                                                           type=ORDER_TYPE_TAKE_PROFIT_LIMIT,
                                                           timeInForce=TIME_IN_FORCE_GTC,
                                                           quantity=size,
                                                           price=entry,
                                                           stopPrice=tp,
                                                           newClientOrderId='takeprft_order'
                                                           )
    except exceptions.BinanceAPIException as e:
        print('%s ERROR ON TP %s: %s' % (strutcnow(), symbol, e.message))

    try:
        print("%s - %s main order: %s" % (strutcnow(), symbol, main_order))
    except UnboundLocalError as e:
        print('%s ERROR ON %s: %s' % (strutcnow(), symbol, e))

    try:
        print("%s - %s stop order: %s" % (strutcnow(), symbol, stop_loss_order))
    except UnboundLocalError as e:
        print('%s ERROR ON %s: %s' % (strutcnow(), symbol, e))

    try:
        print("%s - %s tp order: %s" % (strutcnow(), symbol, take_profit_order))
    except UnboundLocalError as e:
        print('%s ERROR ON %s: %s' % (strutcnow(), symbol, e))




async def stoch_brackets_buy(client, df, symbol, s_dict, ratio=10, max_usd_loss=1):
    symbol_info = s_dict[symbol]
    symbol_info_filters = symbol_info['filters']
    min_price = symbol_info_filters[0]['minPrice']
    step_size = symbol_info_filters[2]['stepSize']
    min_notional = symbol_info_filters[3]['minNotional']

    min_price_digits = get_decimal_digits(min_price)
    step_size_digits = get_decimal_digits(step_size)

    entry = df['high'][0]
    entry = str(format_float(round(entry, min_price_digits)))

    sl = df['low'][0]
    sl = format_float(sl)

    tp = round(
        (float(ratio) * (float(entry) - float(sl)) + float(entry)),
        ndigits=min_price_digits
    )
    tp = format_float(tp)

    size = round(
        abs(float(max_usd_loss) / (float(entry) - float(sl))),
        ndigits=step_size_digits
    )
    size = format_float(size)

    print("{} - Generating new order on {}. Size: {} / Price: {} / Sl: {} / Tp: {}".format(
        strutcnow(), symbol, str(size), entry, sl, tp))


    orders.generate_stoch_brackets(time=utcnow(),
                                     strategy='stoch',
                                     symbol=symbol,
                                     entry=entry,
                                     sl=sl,
                                     tp=tp,
                                     size=size,
                                     id='s_stoch')

    orders.stoch_manage_open_orders(symbol)


async def stochtest(client, symbol, directory, s_dict):
    """Estratégia que utiliza o stoch lento. Será usada para teste(sempre entrará e lançará ordens teste)"""
    print('%s - Strategy StormTest for %s starting...' % (strutcnow(), symbol))

    df = input_csv_data(directory, symbol, how_many_candles=20)
    stoch_slow = stoch_signal(high=df['high'], low=df['low'], close=df['close'], window=8, smooth_window=3)
    stoch_slow = reset_my_index(stoch_slow)
    df = reset_my_index(df)

    print('%s - Last Candle close price is: %s' % (strutcnow(), df['close'].iloc[0]))
    print('%s - Last Candle stoch value is: %s' % (strutcnow(), stoch_slow.iloc[0]))

    if stoch_slow.iloc[0] < 200:
        await test_brackets_buy(client, df, symbol, s_dict)


def convert_from_15m_to_2h_candles(df):

    i = 0
    bar2h = []
    bars_list = df.values.tolist()
    ts = datetime.datetime.strptime(bars_list[i][0], '%Y.%m.%d %H:%M:%S')
    # print('ts hour = ', ts.hour)
    # print('ts minute = ', ts.minute)



    while (float(ts.hour) % 2) == 1 or float(ts.minute) != 0:
        # print("ts descartado:", ts)
        i += 1
        ts = datetime.datetime.strptime(bars_list[i][0], '%Y.%m.%d %H:%M:%S')

    else:
        # print("entrou no primeiro candle par:00", ts)
        # print("i = %s e len(bars_list) -1 %s: "% (i, len(bars_list) - 1))
        while i + 7 <= len(bars_list) - 1:
            """Time will need to take the value from the first candle of the aggregate.
               O will need to take the value from the first candle of the aggregate
               H will need to take the max value of the aggregated candles
               L will need to take the low value of the aggregated candles
               C will need to take the value of the last candle of the aggregate"""
            second = i + 1
            third = i + 2
            fourth = i + 3
            fifth = i + 4
            sixth = i + 5
            seventh = i + 6
            eighth = i + 7

            ctime = bars_list[i][0]
            o = bars_list[i][1]
            h = max(bars_list[i][2], bars_list[second][2], bars_list[third][2], bars_list[fourth][2],
                    bars_list[fifth][2], bars_list[sixth][2], bars_list[seventh][2], bars_list[eighth][2])

            lo = min(bars_list[i][3], bars_list[second][3], bars_list[third][3], bars_list[fourth][3],
                     bars_list[fifth][3], bars_list[sixth][3], bars_list[seventh][3], bars_list[eighth][3])

            c = bars_list[eighth][4]
            bar2h.append([ctime, o, h, lo, c])
            # print("por enquanto bar3h 茅: ", bar3h)
            i += 8
        else:
            bar2h = pd.DataFrame(bar2h)
            bar2h.rename(columns={0: 'time', 1: 'open', 2: 'high', 3: 'low', 4: 'close'}, inplace=True)
            # pd.set_option('display.max_rows', None)
            # print(bar2h)

            return bar2h


async def stoch(client, symbol, directory, s_dict):
    """Estratégia que utiliza o stoch lento.
       PS: Estratégia usa candles 2h, realizar conversão"""
    print('%s - New 2h Candle, starting to run stoch Strategy for %s' % (
        strutcnow(), symbol))

    df = input_csv_data(directory, symbol, how_many_candles=8 * 816)
    # print("%s - %s" % (symbol, df))

    df = convert_from_15m_to_2h_candles(df)
    # print(df)
    pd.set_option('display.max_rows', None)
    stoch_slow = stoch_signal(high=df['high'], low=df['low'], close=df['close'], window=8, smooth_window=3)
    ema = ema_indicator(close=df['close'], window=400)

    ema = reset_my_index(ema)
    stoch_slow = reset_my_index(stoch_slow)
    df = reset_my_index(df)
    # pd.set_option('display.max_rows', None)

    ema_slope = ema.iloc[0] - ema.iloc[1]


    print(f'{strutcnow()} - Last Candle time is {df["time"].iloc[0]},'
          f' close is {df["close"].iloc[0]}, '
          f'stoch is {round(stoch_slow.iloc[0], 2)} and '
          f'ema slope is {round(ema_slope, 2)}')


    if stoch_slow.iloc[0] < 25 and ema_slope > 0:
        await stoch_brackets_buy(client, df, symbol, s_dict)