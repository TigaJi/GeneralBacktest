
from tokenize import String
import pandas as pd
import numpy as np
import random
import sys
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
from ._position import Position
from ._bid import Bid
from tqdm import tqdm

class Backtest:

    """
    Backtest Class

    Attributes
    ----------
    - df: pandas dataframe
    a m(number of periods) * n(number of tickers) pandas dataframe
    stores all the price, must have a datetime index, must not have null values

    - strategy : Python class
    must have a "predict" method

    - positions : dict
    k,v : ticker, the position held on this ticker


    - tc: float, default 0
    transaction cost that will be applied to each transaction

    - transaction_history: pandas dataframe
    stores each transactions

    - portfolio_tracker: pandas dataframe
    stores the total value, # of postitions, etc.. at each step

    - cash: float, default 100000

    - initial_amount: float, default 100000

    - tc: float, default 0
    transaction cost that will be applied to each transaction

    - full_data: pandas dataframe, default empty
    used to store OHLCV information needed for strategy, must have same index as price data


    Methods
    ----------

    """
    def __init__(self,price_data: pd.DataFrame,strategy: type,initial_amount = 100000, tc = 0, full_data = None):
        """
        initialize a backtest instance

        """

        #check for datetime index
        self.check_input_data(price_data)
        self.df = price_data


        self.strategy = strategy
        self.positions = {}
        self.cash = initial_amount
        self.initial_amount = initial_amount
        self.tc = tc
        self.transaction_history = pd.DataFrame(columns = ["dt","ticker","type","price","shares","amount","transaction_cost","pnl"])
        self.portfolio_tracker = pd.DataFrame(columns = ["dt","bid_count","position_count","cash_value","positions_value","total_value","bah"])

        if full_data != None:
            self.check_input_data(full_data)
            self.full_data = full_data
        else:
            self.full_data  = pd.DataFrame(index = self.df.index)

    
    def check_input_data(self,df:pd.DataFrame):
        """
        
        check input data for datetime index and null values
        
        Parameters
        ----------
        df: pandas DataFrame

        """



        if df.index.inferred_type != "datetime64":
            raise ValueError("input dataframe must have a datetime64 index")

        if df.isnull().values.any():
            raise ValueError("input dataframe contains null values")



    def update_positions(self,ti:pd.DatetimeIndex):

        """"""
        """
        update positions' latest price

        Parameters
        ----------
        ti: pandas DataTimeIndex
        
        """
        current_price = self.df.loc[ti]
        for position in list(self.positions.values()):
            position.price = current_price[position.ticker]
    

    
    def record_transaction(self,ti:pd.DatetimeIndex, bid: Bid, pnl: int):
        """
        record a succesful transaction

        Parameters
        ----------
        bid: Bid
        pnl: int

        """
        record = [ti,bid.ticker,bid.bid_type,bid.price,bid.shares,bid.price*bid.shares,bid.price*bid.shares*self.tc,pnl]
        self.transaction_history.loc[len(self.transaction_history)] = record
        
    def update_tracker(self,ti: pd.DatetimeIndex, bid_list: list):
        """
        Paramters
        record the portfolio status as well as a buy and hold benchmark at each step
        

        Parameters
        ----------
        ti: pandas DataTimeIndex
        bid_list: list

        """

        rets = [end/start for start,end in zip(self.df.iloc[0].values,self.df.loc[ti].values)]
        bah_value = sum(([self.initial_amount/len(self.df.columns)*ret for ret in rets]))
        positions_value = sum([pos.price*pos.shares for pos in self.positions.values()])
        record = [ti,len(bid_list),len(self.positions),self.cash,positions_value,positions_value+self.cash,bah_value]
        self.portfolio_tracker.loc[len(self.portfolio_tracker)] = record

    def clear_positions(self):
        """
        a function used to sell all current held positions

        """
        bid_list = []
        for pos in self.positions.values():
            bid = Bid(ticker = pos.ticker,shares = pos.shares,price = self.df.iloc[-1][pos.ticker],bid_type = 0)
            bid_list.append(bid)
        self.process_bids(self.df.index[-1],bid_list)


    def upload_to_dashboard(self,name: String):
        """
        Upload the backtest result to dashboard
        must ensure the credential file if under current directory

        Parameters
        ----------
        name: String
        the name of this strategy, e.g. LSTM

        """

        #check for credential and status
        if len(self.portfolio_tracker) < len(self.df):
            print("Unable to upload: Backtest is unfinished.")
            return
        if "algo-trade-dashboard-80cae071e907.json" not in os.listdir():
            print("Unable to upload: Couldn't find credential file (algo-trade-dashboard-80cae071e907.json)")
            return
        
        
        #get file
        self.portfolio_tracker.to_csv(name+"_backtest_result.csv")
        

        #connect to google drive
        gauth = GoogleAuth()
        scope = ['https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive.metadata'
          ]
        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name("algo-trade-dashboard-80cae071e907.json", scope)
        drive = GoogleDrive(gauth)

        #get current file list
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

        #if file already exist, then overwrite
        for file in file_list:
            id = file['id']
            if name+"_backtest_result.csv" == file['title']:
                f1 = drive.CreateFile({'name':name+"_backtest_result.csv",'id':id})
                f1.SetContentFile(name+"_backtest_result.csv")
                f1.Upload()
                print("Data uploaded.")
                return

        #else, create new file and upload
        f1 = drive.CreateFile({'name':name+"_backtest_result.csv"})
        f1.SetContentFile(name+"_backtest_result.csv")
        f1.Upload()

        os.remove(name+"_backtest_result.csv")

        print("Data uploaded.")
    
    
    def process_bids(self,ti,bid_list):

        cash_change = 0

        for bid in bid_list:
            if bid.shares <= 0:
                print("#shares of {} is invaild".format(bid.shares))
                continue



            if bid.ticker not in self.df.columns:
                print("Ticker: {} is unavaliable.".format(bid.ticker))
                continue

            if bid.price != self.df.loc[ti][bid.ticker]:
                print("Unmatch price: bid.price {}, actual price {}".format(bid.price,self.df.loc[ti][bid.ticker]))
                continue

            #if already have a position
            if bid.ticker in self.positions.keys():
                pos = self.positions[bid.ticker]

                #if increase position
                if bid.bid_type == 1:
                    cost = bid.shares * bid.price

                    #update cash
                    cash_change -= cost * (1+self.tc)

                    #update position
                    pos.change_position(bid)
                    self.record_transaction(ti,bid,0)

                #if decrease position
                else:
                    income = bid.shares * bid.price

                    #update position,and get a cost
                    temp_cost = pos.change_position(bid)

                    #if successful
                    if temp_cost != -1:
                        #update cash
                        cash_change += income
                        cash_change -= income*self.tc
                        #calculate pnl
                        pnl = income-temp_cost
                        #record this transaction
                        self.record_transaction(ti,bid,pnl)
                    
                    
                    if pos.shares == 0:
                        del self.positions[bid.ticker]

            #if not have a position yet
            else:
                if bid.bid_type == 0:
                    print("Try to sell {} shares, but only got 0 shares.".format(bid.shares))
                    continue


                cost = bid.shares * bid.price

                #update cash
                cash_change -= cost * (1+self.tc)

                #build position
                self.positions[bid.ticker] = Position(bid)

                #record this transaction
                self.record_transaction(ti,bid,0)

        return cash_change
        
        
        
    def plot(self):
        plt.figure()
        plt.plot(self.portfolio_tracker['total_value'], label = 'random_strat')
        plt.plot(self.portfolio_tracker['bah'],label = 'bah')
        plt.legend()
        plt.show()
        
        
        
    def backtest_full(self):
        print("====================Start====================")
        print()

        for ti in tqdm(self.df.index,position = 0, leave = True):
            self.update_positions(ti)
            bid_list = self.strategy.predict(ti,self.df.loc[:ti],self.positions,self.cash,self.full_data.loc[:ti])
            cash_change = self.process_bids(bid_list = bid_list,ti = ti)
            self.cash += cash_change
            self.update_tracker(ti,bid_list)
            if self.cash<0:
                raise ValueError("Negative cash. Please reconstruct your strategy.")

        if len(self.positions) > 0:
            self.clear_positions()


