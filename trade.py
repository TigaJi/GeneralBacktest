import os
import openpyxl
import pandas as pd
import numpy as np
import requests.exceptions
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler
import scipy.stats
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout, GRU, Bidirectional
import keras.optimizers
from math import isnan
from sklearn.metrics import mean_squared_error
from keras import backend as K
import time
import datetime
from datetime import datetime as dx
import datetime as dt
from pytz import timezone
import csv
import yfinance as yf
from urllib3.exceptions import MaxRetryError, ConnectTimeoutError
from syncdata import sync_data
import schedule
import calculate_precision

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def trade_decision(content):
    tz = timezone('EST')
    present = dx.now(tz)
    print(present)
    target = present + dt.timedelta(seconds=180)
    print(target)
    stock = []
    dic = {}
    for i in content.columns:
        if has_numbers(i):
            continue
        else:
            stock.append(i)
    model = keras.models.load_model(r"E:\data streaming\stockprediction.h5")
    for j in range(len(stock)):
        test = []
        for i in range(10):
            test.append(float(content.at[i, stock[j] + '.3']))
        my_array = np.asarray(test)
        scaler = MinMaxScaler(feature_range=(0, 1))
        my_array = my_array.reshape(-1, 1)
        scaled_Close = scaler.fit_transform(my_array)
        scaled_X = scaled_Close.reshape((1, 1, 10))

        y = model.predict(scaled_X)
        b = scaler.inverse_transform(y)
        r = (b[0] - test[9]) / test[9]
        dic[stock[j]] = r

    clean_dict = {k: dic[k] for k in dic if not isnan(dic[k])}
    dic = clean_dict

    max_key = max(dic, key=dic.get)
    a = dic[max_key]
    price = content.at[9, max_key]
    file_object = open('trade.txt', 'a')
    present = dx.now(tz)
    date_time = present.strftime("%m/%d/%Y, %H:%M:%S")
    budget = 10000
    #print(max_key,a,price,date_time)
    print(dic)
    if a <= 0:
        print(date_time + "  short " + max_key + "  1   " + str(price))
        file_object.write(date_time + "  short " + max_key + "  1   " + str(price))
        file_object.write(str(a))
        return date_time, max_key, str(-1*(budget//price)), price, a
    if a > 0:
        print(date_time + "  buy " + max_key + "  1   " + str(price))
        file_object.write(date_time + "  buy " + max_key + "  1   " + str(price))
        file_object.write(str(a))
        return date_time, max_key, str(1*(budget//price)), price, a
    file_object.close()

def close_trade():
    directory = "E:\\python_portfolio_tracker\\data\\raw"
    os.chdir(directory)
    x = pd.read_csv('purchase_info.csv', index_col=0)
    hold = x.iloc[-1]['total_shares_held']
    commodity = x.iloc[-1]['yahoo_ticker']
    cost = x.iloc[-1]['stock_price_usd']
    if hold!=0:
        quantity = hold*(-1)
        if float(quantity)>0:
            action = 'BUY'
        else:
            action = "SELL"
        print(commodity)
        try:
            stock_info = yf.Ticker(commodity).info
            price = stock_info['regularMarketPrice']
        except (MaxRetryError,ConnectTimeoutError, TimeoutError,requests.exceptions.ConnectTimeout):
            price = x.iloc[-1]['stock_price_usd']
        tz = timezone('EST')
        present = dx.now(tz)
        date_time = present.strftime("%m/%d/%Y, %H:%M:%S")
        f = open('purchase_info.csv', 'a', newline='')  # Make file object first
        csv_writer_object = csv.writer(f)  # Make csv writer object
        a = [date_time, action, commodity, commodity, 'USD', abs(float(quantity)), price, 0, float(quantity) * float(price),
             0,(price-cost)/cost]
        csv_writer_object.writerow(a)
        f.close()

def record(date, commodity, quantity, price,project_return):
    close_trade()
    directory = "E:\\python_portfolio_tracker\\data\\raw"
    os.chdir(directory)
    x = pd.read_csv('purchase_info.csv', index_col=0)
    if float(quantity)<0:
        action = "SELL"
    else:
        action = "BUY"
    f = open('purchase_info.csv', 'a',newline='')  # Make file object first

    csv_writer_object = csv.writer(f)  # Make csv writer object
    a = [date,action,commodity,commodity,'USD',abs(float(quantity)),price,0,float(quantity) * float(price),float(quantity),float(project_return)]
    csv_writer_object.writerow(a)
    f.close()

    '''
    a = {'date': date, 'action': action, 'company': commodity, 'yahoo_ticker': commodity, 'currency': 'USD',
         'num_shares': abs(int(quantity)), 'stock_price_usd': price, 'trading_costs_usd': 0,
         'total_usd': float(quantity) * float(price), "total_shares_held": int(quantity)}
         
    x = x.append(a, ignore_index=True)
    x.to_csv('purchase_info.csv', index=False)
    '''
def execute():
    today = datetime.date.today()
    todaytime = today.strftime("%Y%m%d")
    directory = "E:\\data streaming\\data\\real_time_data\\" + "allstocks_" + todaytime
    os.chdir(directory)

    currenttime = datetime.datetime.today()
    timecurrent = currenttime.strftime("%H%M%S")
    weekday = datetime.datetime.today().weekday()


    model = keras.models.load_model(r"E:\data streaming\stockprediction.h5")
    kk = 0
    while kk!=1 and (int(timecurrent) >= 124000 and int(timecurrent) <= 200000) and (weekday >= 0 and weekday <= 4):
        directory = "E:\\data streaming\\data\\real_time_data\\" + "allstocks_" + todaytime
        os.chdir(directory)
        arr = os.listdir()

        directory = "E:\\data streaming\\data\\real_time_data\\" + "allstocks_" + todaytime+"\\"+arr[-1]
        os.chdir(directory)
        price_list=[]
        arr = os.listdir()
        for file in arr:
            if(file.find('csv')!=-1):
                price_list.append(file)

        content = pd.read_csv(price_list[0])[-11:-1]
        content = content.reset_index(drop=True)
        dic = {}
        '''
        tz = timezone('EST')
        present = dx.now(tz)
        print(present)
        target = present + dt.timedelta(seconds=200)
        print(target)
        '''
        try:

            date,commodity, quantity, price, project_return = trade_decision(content)
            record(date, commodity, quantity, price, project_return)
            try:
                sync_data()
            except Exception as e:
                print(e)
            print("sleep")
            time.sleep(660)
        except (ValueError,KeyError,IndexError):
            print("void")
            time.sleep(60)
        currenttime = datetime.datetime.today()
        timecurrent = currenttime.strftime("%H%M%S")
        weekday = datetime.datetime.today().weekday()
        '''
        present = dx.now(tz)
        time.sleep((target-present).total_seconds())
        '''
schedule.every().day.at("17:51").do(execute)
while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
