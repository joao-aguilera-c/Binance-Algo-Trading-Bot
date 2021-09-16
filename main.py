import asyncio
import datetime
import os
import sys

import pandas as pd
from binance import AsyncClient, BinanceSocketManager

import Get_Symbol_Info
import strategies as strats
import order_management as orders
import math
import csv
import time


def utcnow():
    """Função que retorna a data e hora atuais, no padrão UTC"""
    return datetime.datetime.utcnow()


def strutcnow():
    """Função que retorna a data e hora atuais, no padrão UTC, no formato String"""
    now = datetime.datetime.utcnow()
    strnow = f'{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}'
    return strnow


def timestamp_to_csvtime(ts):
    ts = ts.strftime('%Y.%m.%d %H:%M:%S')
    return ts


def csvtime_to_timestamp(strtime):
    strtime = datetime.datetime.strptime(strtime, '%Y.%m.%d %H:%M:%S')
    strtime = strtime.timestamp() * 1000
    return strtime


def get_last_csv_candle_time(directory, symbol):
    csv = pd.read_csv(r'%s/%s.csv' % (directory, symbol))
    last_date = csv.tail(1)
    last_date = last_date[csv.columns[0]].item()
    last_date = datetime.datetime.strptime(last_date, '%Y.%m.%d %H:%M:%S')
    return last_date


def there_is_new_candle(res, directory):
    """"Essa função tem objetivo de descobrir se há um novo candle na série histórica"""
    kline_data = res.get('data')
    kline_symbol = kline_data.get('s')
    kline_time = kline_data.get('k')
    kline_time = kline_time.get('t')
    # print('symbol is %s and time is %s' % (kline_symbol, kline_time))
    last_csv_candle_time = get_last_csv_candle_time(directory, kline_symbol)
    minutes_15 = pd.to_timedelta(15, unit='m')
    if datetime.datetime.utcfromtimestamp(kline_time / 1000) > last_csv_candle_time + minutes_15:
        # print("%s > %s" % (datetime.datetime.utcfromtimestamp(kline_time/1000), last_csv_candle_time + minutes_15))
        return True
    else:
        '''print('%s - Último candle recebido tem data de %s' % (strutcnow(),
                                                              datetime.datetime.utcfromtimestamp(kline_time/1000)))'''
        return False


def there_is_new2h_candle_stoch(res, directory, symbol):
    """"Essa função tem objetivo de descobrir se há um novo candle de 2h na série histórica para rodar stoch"""
    kline_data = res.get('data')
    kline_symbol = kline_data.get('s')
    # print('symbol is %s and time is %s' % (kline_symbol, kline_time))
    filename = "last_2h_candle_stoch.csv"
    df = pd.read_csv(filename)

    if df.empty:
        mode = 'a'
        header = False
    else:
        mode = 'w'
        header = True
    if df[df.symbol == symbol].empty:
        """aqui calculo o ultimo candle 2h do csv"""
        csvdf = strats.input_csv_data(directory, symbol, how_many_candles=17)
        # print("%s - %s" % (symbol, df))

        csvdf = strats.convert_from_15m_to_2h_candles(csvdf)

        last_csv_candle_time = csvdf._get_value(0, 'time')

        df2 = pd.DataFrame([[symbol, last_csv_candle_time]], columns=['symbol', 'last_candle'])
        df = df.append(df2)
        df.to_csv(filename, mode=mode, header=header, index=False)
        return True
    else:
        df2 = df[df.symbol == symbol]
        last_processed_2h_candle_time = df2.iloc[0]["last_candle"]

        """aqui calculo o ultimo candle 2h do csv"""
        csvdf = strats.input_csv_data(directory, symbol, how_many_candles=17)
        # print("%s - %s" % (symbol, df))

        csvdf = strats.convert_from_15m_to_2h_candles(csvdf)

        last_csv_candle_time = csvdf._get_value(len(csvdf) - 1, 'time')
        # last_csv_candle_time = df["time"].iloc[-1]
        if str(last_processed_2h_candle_time) == str(last_csv_candle_time):
            """Ultimo candle processado é de fato o ultimo candle"""
            return False
        else:
            """Ultimo candle processado não é o ultimo candle 2h que existe, coloque ele no lugar e retorne true"""
            df = df.set_index('symbol')
            df.at[symbol, 'last_candle'] = last_csv_candle_time

            df.to_csv(filename, mode=mode, header=header, index=True)

            return True


async def get_last_candle(client, symbol, directory):
    symbol = [symbol]
    # print('%s - starting to get new data for %s' % (strutcnow(), symbol))

    await Get_Symbol_Info.get_symbol_info(client, symbol, directory)
    """Bom acabo de me ver na seguinte situação:
       Já atualizo os meus candles aparentemente o mais rapido possivel(o que não é verdade, e para isso preciso criar
       uma nova funçao que use o get symbol info do proprio websocket, eu sei disso)
       então primeiro passo é:
       
            1. FAZER UMA NOVA FUNÇÃO QUE SEJA VERDADEIRAMENTE DESINCADA E QUE PEGUE AS INFORMAÇÕES E JOGUE-AS 
               NO MEU CSV (DONE!!)
            
            2. SÓ ENTÃO COMEÇAR A GERAR OS CALCULOS QUE DEFINEM AS MINHAS ESTRATÉGIAS"""


async def run_strategies(client, res, symbol, directory, s_dict, strategies_df):
    """acabo de entrar no momento em que precisarei ver quais estratégias rodar para cada symbol, então aqui irei
    bifurcar para varias estratégias por symbol, so:
        passar pelo strategies df linha a linha, receber as infos symbol e strategie da linha
         se symbol == symbol
            se strategia do symbol == XXX
                rodar XXX
            se strategia do ymbol for == YYY
                rodar YYY"""

    for index, row in strategies_df.iterrows():
        # print(row['symbol'], row['strategy'])
        if symbol == row['symbol']:
            if row['strategy'] == 'test':
                print('%s - New candle, starting to run Test Strategy for %s' % (strutcnow(), symbol))
                await strats.stochtest(client, symbol, directory, s_dict)
            if row['strategy'] == 'stoch':
                if there_is_new2h_candle_stoch(res, directory, symbol):
                    await strats.stoch(client, symbol, directory, s_dict)
                else:
                    await asyncio.sleep(2)
                    if there_is_new2h_candle_stoch(res, directory, symbol):
                        await strats.stoch(client, symbol, directory, s_dict)


async def symbol_info_dict(client, week_symbol_list):
    s_dict = {}
    for s in week_symbol_list:
        s_dict[s] = await client.get_symbol_info(s)
    return s_dict


class AttCounter(object):

    def __init__(self):
        self.first_run = True
        self.init_time = utcnow()
        self.last_kline_time = 0
        self.att_diferential = None
        self.max_diff = 0
        # print('{} - Initiating Update Observer'.format(strutcnow()))

    def counter(self, res, symbol):
        kline_data = res.get('data')
        kline_symbol = kline_data.get('s')
        kline_time = kline_data.get('E')
        if kline_symbol == symbol:
            if self.first_run:
                self.last_kline_time = kline_time
                self.first_run = False

            self.att_diferential = round(abs(self.last_kline_time - kline_time) / 1000)
            self.last_kline_time = kline_time
            self.max_diff = max(self.max_diff, self.att_diferential)

            if utcnow() - self.init_time > datetime.timedelta(minutes=60):
                self.init_time = utcnow()

                print('{} - Last update took {} seconds, biggest delay was {}seconds'.format(strutcnow(),
                                                                                             self.att_diferential,
                                                                                             self.max_diff))


class stream_io(object):
    """Este objeto tem a função de ligar e desligar o streaming dos preços em tempo real."""

    def __init__(self):
        self.time_init = utcnow()
        self.seconds_to_keep_open = 60
        self.open_requests = 0

    def stream_conditions(self):

        time_now = utcnow()
        """conditions para stoch are """
        on_minutes = [14, 29, 44, 59]
        for i in on_minutes:
            if time_now.minute == i and time_now.second > 30:
                self.time_init = utcnow()

        if time_now - self.time_init < datetime.timedelta(seconds=self.seconds_to_keep_open) or self.open_requests > 1:
            return True
        if orders.there_is_open_order():
            return True
        time.sleep(1)

        return False


async def kline_listener(client, socket_symbol_list, directory, symbol_list, s_dict, strategies_df, first_run=True):
    """Essa é a função em que o streaming de preços dos diferentes ativos ocorre.
       Como receber o streaming dos preços 24h por dia exige consumo de energia,
       E o programa foi criado pensado para rodar também em dispositivos mobile,
       Criei a função de controle do streaming, que só o liga em determinados momentos.
       Nesta demo, as operações acontecem nos timeframes de 15 minutos e 2 horas,
       portanto o streaming será ligado apenas momentos antes da mudança de candle de 15 minutos
       ou caso hajam orders abertas"""

    io_stream = stream_io()
    while True:
        stream_enabled = io_stream.stream_conditions()
        if stream_enabled or first_run:
            print(f"{strutcnow()} - Initiating stream")
            bm = BinanceSocketManager(client)
            new_candle_count = 0
            strategy_run_count = 0
            there_was_new_candle = False
            counter = AttCounter()
            kl_init_time = utcnow()
            i = 0

            async with bm.multiplex_socket(streams=socket_symbol_list) as stream:
                while stream_enabled or first_run:

                    res = await stream.recv()
                    counter.counter(res, symbol_list[0])

                    io_stream.open_requests += 1
                    loop.call_soon(asyncio.create_task, orders.order_executioner(res, client))
                    io_stream.open_requests -= 1
                    if there_is_new_candle(res, directory):

                        if new_candle_count < len(symbol_list):
                            for symbol in symbol_list:
                                print('%s - There is new candle on %s' % (strutcnow(), symbol))
                                io_stream.open_requests += 1
                                loop.call_soon(asyncio.create_task, get_last_candle(client, symbol, directory))
                                io_stream.open_requests -= 1
                                new_candle_count += 1
                        there_was_new_candle = True

                    if not there_is_new_candle(res, directory):
                        # print('there is no candle')
                        if there_was_new_candle or first_run:
                            # print('but this is the first run or a candle is just generated')
                            if strategy_run_count < len(symbol_list):
                                for symbol in symbol_list:
                                    loop.call_soon(asyncio.create_task, run_strategies(client,
                                                                                       res,
                                                                                       symbol,
                                                                                       directory,
                                                                                       s_dict,
                                                                                       strategies_df))

                                    strategy_run_count += 1
                        there_was_new_candle = False
                        strategy_run_count = 0
                        new_candle_count = 0
                    if utcnow() - kl_init_time > datetime.timedelta(minutes=30):


                        await client._keepalive_socket()

                    stream_enabled = io_stream.stream_conditions()

                    first_run = False

                else:
                    print(f"{strutcnow()} - Stop stream for now")
                    await stream.__aexit__(None, None, None)


def get_socket_symbol_list(alist):
    return_list = []
    for element in alist:
        socket_element = "%s@kline_15m" % element
        return_list.append(socket_element.lower())
    return return_list


def get_strategies_df():
    pathname = os.path.dirname(sys.argv[0])
    filename = "strategies_to_run.csv"
    df = pd.read_csv(r'%s/%s' % (pathname, filename))
    return df


def remove_duplicates(alist):
    alist = list(dict.fromkeys(alist))
    return alist


def s_data_inconsistencies_corrector(directory, week_symbol_list):
    def add_new_candle(f):
        print('%s - searching for problematic times on %s' % (strutcnow(), f))
        minutes_15 = pd.to_timedelta(15, unit='m')
        df = pd.read_csv('%s/%s.csv' % (directory, f), header=None)
        df_list = df.values.tolist()
        i = 0
        while i < (len(df_list) - 1):
            date = datetime.datetime.strptime(df_list[i][0], '%Y.%m.%d %H:%M:%S')
            next_should_date = date + minutes_15
            next_actual_date = datetime.datetime.strptime(df_list[i + 1][0], '%Y.%m.%d %H:%M:%S')
            if next_actual_date.second != 0:
                return print("ERROR SECOND != 0. i = ", i)

            if (next_actual_date.minute % 15) != 0:
                return print("ERROR MINUTE IS NOT DIVISIBLE PER 15 i = ", i)
            if next_should_date != next_actual_date:
                j = 1
                print('date is ', date)
                print('next should date is ', next_should_date)
                print('and next actual date is ', next_actual_date)
                while next_should_date < next_actual_date:
                    """Neste modulo adicionaremos candles vazios caso hajam bolhas"""
                    new_date = timestamp_to_csvtime(next_should_date)
                    df_list.insert(i + j, [new_date, None, None, None, None])  # inserting 3 at index

                    print("%s inserted" % [new_date, None, None, None, None])
                    print('at i = ', i + j)
                    j = j + 1
                    next_should_date = next_should_date + minutes_15
                if next_should_date > next_actual_date:  # Significa que tem data repetida.
                    """neste modulo removerei datas repetidas e de maneira radical a princípio. 
                       Removerei tudo o que vier depois"""
                    j = 0
                    remove_from = i+1
                    remove_to = len(df_list)
                    removed_elements = remove_to - remove_from
                    df_list = df_list[:-removed_elements or None]
                    i = i - 1

                df = pd.DataFrame(df_list)
                print(df.to_csv('%s/%s.csv' % (directory, f), mode='w', header=False, index=False))
            i = i + 1
        else:
            # print('programa terminado')
            return True

    def changing_nan_topreviouslyclose(f):
        print('%s - searching for Nan Values on %s' % (strutcnow(), f))
        df = pd.read_csv('%s/%s.csv' % (directory, f), header=None)
        df_list = df.values.tolist()
        i = 0
        while i < (len(df_list) - 1):
            o = df_list[i][1]
            t = df_list[i][0]
            if math.isnan(o):
                last_c = df_list[i - 1][4]
                i_last_close = i - 1
                print('o on i = %s is nan and last_c is %s' % (i, last_c))
                j = i
                while math.isnan(o):
                    j = j + 1
                    first_o = df_list[j][1]
                    o = first_o
                else:
                    print('first_ o on i = %s is %s' % (j, first_o))
                    n_linhas = j - i
                    step = (float(first_o) - float(last_c)) / n_linhas
                    new_i = i_last_close + 1
                    l_operator = 0
                    while new_i < j:
                        line = [df_list[new_i][0],
                                round(float(last_c) + (l_operator * step), 2),
                                round(float(last_c) + ((l_operator + 1) * step), 2),
                                round(float(last_c) + (l_operator * step), 2),
                                round(float(last_c) + ((l_operator + 1) * step), 2), ]
                        df_list[new_i] = line
                        l_operator += 1
                        new_i += 1
                    else:
                        df = pd.DataFrame(df_list)
                        print(df.to_csv('%s/%s.csv' % (directory, f), mode='w', header=False, index=False))
            i = i + 1
        else:
            # print('programa terminado')
            return True

    for s in week_symbol_list:
        while not add_new_candle(s):
            print("new candles added on %s" % s)

        while not changing_nan_topreviouslyclose(s):
            print("new candles values updated on %s" % s)

    pass


class Credentials(object):
    with open('credentials.csv', newline='') as f:
        reader = csv.reader(f)
        data = list(reader)

    api = data[1][0]
    secret = data[1][1]


async def main():
    print('%s - Olá, João! Iniciando seu bot. Você rodará as seguintes estratégias:' % strutcnow())
    directory = r'Symbols'
    strategies_df = get_strategies_df()
    print(strategies_df)
    week_symbol_list = remove_duplicates(strategies_df.symbol.tolist())
    api = Credentials.api
    secret = Credentials.secret
    socket_symbol_list = get_socket_symbol_list(week_symbol_list)
    """Find inconsistencies in symbols data and correct it before runing bot"""
    s_data_inconsistencies_corrector(directory, week_symbol_list)

    client = await AsyncClient.create(api_key=api, api_secret=secret)
    s_dict = await symbol_info_dict(client, week_symbol_list)

    await kline_listener(client, socket_symbol_list, directory, week_symbol_list, s_dict, strategies_df)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
