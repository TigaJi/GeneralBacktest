
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

class Bid:
    """
    Bid Class    
    
    Attributes
    ----------    
    - ticker: String
    - price: numerical
    - shares: positive int
    - bid_type: int (1 or 0)
        1 stands for buying
        0 stands for selling

    Methods
    ---------- 
    - show(): print out the bid info, for debugging or processing showing purpose

    """
    def __init__(self,ticker: String,price: float,shares: int,bid_type: int):
        if bid_type != 0 and bid_type != 1:
            raise ValueError("Bid type = {} is not valid.".format(bid_type))
        self.ticker = ticker
        self.price = price
        self.shares = shares
        self.bid_type = bid_type
    

    def show(self):
        print("---------------")
        if self.bid_type == 1:
            print("Buying:")
        else:
            print("Selling")
        print("Ticker: {}".format(self.ticker))
        print("Shares: {}".format(self.shares))
        print("Price: {}".format(self.price))
        print("---------------")




class Position:
    """
    Position Class    
    
    Attributes
    ----------    
    - ticker: String

    - shares: int
        must be positive
        stands for the shares currently held 

    - price: numerical
        the latest price (will be updateed every round during backtesting)

    - purchase_history: dict
        k,v: price,# of shares purchased at that price
        used to calculate cost
    
    - wa_cost_price: numerical
        weighted average cost of this position

    Methods
    ---------- 
    - init(Bid): initilization with a Bid instance

    - change_positive(Bid): change the current position with another Bid, returns the cost

    - update_cost(Bid): when position changes, update purchase history and weighted average cost

    - show(): print out the position info, for debugging or processing showing purpose

    """
    def __init__(self,bid: Bid):
        self.ticker = bid.ticker
        self.shares = bid.shares
        self.price = bid.price
        
        #k，v: price, number of shares purchased at that price
        self.purchase_history = {bid.price:bid.shares}
        self.wa_cost_price = bid.price
        

    def change_position(self,bid: Bid) -> float:
        """
        Parameters
        ----------
        a Bid instance

        Returns
        -------
        if buying: return -1
        if selling:
            if succesful: return the cost, more details in the update_cost function
            if not succesful: return -1
        """

        #update price
        self.price = bid.price

        #if buying
        if bid.bid_type == 1:
            #update cost & shares
            cost = self.update_cost(bid)
            self.shares += bid.shares
            return cost
        
        #if selling
        if bid.bid_type == 0:
            #if not have enough shares, remain the position and return -1
            if self.shares < bid.shares:
                print("Try to sell {} shares, but only got {} shares.".format(bid.shares,self.shares))
                return -1

            #else, update cost & shares
            #return the amount used when buying those amount of shares
            cost = self.update_cost(bid)
            self.shares -= bid.shares
            return cost
            


        
    def update_cost(self,bid:Bid) -> float:
        """
        Parameters
        ----------
        a Bid instance

        Returns
        -------
        if buying: return -1
        if selling: return the cost, i.e. dollar value used to purchase those amount of shares
        
        Notes
        -------
        if the all the shares are sold, the cost will be shares * wa_cost_price
        However, if only a portion of the postition is sold, the calculation of cost follows the Fisrt-In-Lowest-Out rule
        The lowest possible cost will be calculated from the purchase_histroy dictionary to maximize the pnl for this single trade

        """

        #buy
        if bid.bid_type == 1:
            #if have purchased at this price
            if bid.price in self.purchase_history.keys():
                self.purchase_history[bid.price] += bid.shares
            else:
                self.purchase_history[bid.price] = bid.shares
            self.wa_cost_price = sum([i*j for i,j in self.purchase_history.items()])/(self.shares+bid.shares)
            return -1
            
            
                
        #sell
        else:
            
            #if empty position, return shares * weighted average cost
            if bid.shares == self.shares:
                return self.wa_cost_price * self.shares

            #if selling a portion: n shares, such that n < self.shares
            #loop through the purchase_history dictionary from the lowest key(cheapest cost)
            #accumalate the cost and update the purchase_history along
            else:
                shares_left = bid.shares
                temp_cost = 0
                for price in sorted(self.purchase_history.keys()):
                    if shares_left > self.purchase_history[price]:
                        shares_left -= self.purchase_history[price]
                        temp_cost += price * self.purchase_history[price]
                        del self.purchase_history[price]
                    else:
                        self.purchase_history[price] -= shares_left
                        temp_cost += price * shares_left
                
                #update the weight average cost price and return the cost
                self.wa_cost_price = sum([i*j for i,j in self.purchase_history.items()])/(self.shares-bid.shares)
                return temp_cost
                   
    
    def show(self):
        print("Ticker: {}".format(self.ticker))
        print("Shares_held: {}".format(self.shares))
        print("Latest_price: {}".format(self.price))
        print("weighted_average_cost: {}".format(self.wa_cost_price))
        print("----------------")
        print("Purchasing History")
        print("Price\tShares")
        for item in self.purchase_history.items():
            print(str(item[0])+'\t'+str(item[1]))


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
        self.transaction_history = pd.DataFrame(columns = ["dt","ticker","type","price","shares","amount","cash_left","transaction_cost","pnl"])
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
        record = [ti,bid.ticker,bid.bid_type,bid.price,bid.shares,bid.price*bid.shares,self.cash,bid.price*bid.shares*self.tc,pnl]
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
        self.process_bids(bid_list)


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
        for bid in bid_list:
            #if already have a position
            if bid.ticker in self.positions.keys():
                pos = self.positions[bid.ticker]

                #if increase position
                if bid.bid_type == 1:
                    cost = bid.shares * bid.price
                    if self.cash < cost * (1+self.tc):
                        print("Not enough cash to build a position for "+bid.ticker)
                        continue

                    #update cash
                    self.cash -= cost * (1+self.tc)

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
                        self.cash += income
                        self.cash -= income*self.tc
                        #calculate pnl
                        pnl = income-temp_cost
                        #record this transaction
                        self.record_transaction(ti,bid,pnl)
                    
                    
                    if pos.shares == 0:
                        del self.positions[bid.ticker]

            #if not have a position yet
            else:
                cost = bid.shares * bid.price
                if self.cash < cost * (1+self.tc):
                    print("Not enough cash to build a position for "+bid.ticker)
                    continue

                #update cash
                self.cash -= cost * (1+self.tc)

                #build position
                self.positions[bid.ticker] = Position(bid)

                #record this transaction
                self.record_transaction(ti,bid,0)

        self.update_tracker(ti,bid_list)
        
        
        
    def plot(self):
        plt.figure()
        plt.plot(self.portfolio_tracker['total_value'], label = 'random_strat')
        plt.plot(self.portfolio_tracker['bah'],label = 'bah')
        plt.legend()
        plt.show()
        
        
        
    def backtest_full(self):
        for ti in self.df.index:
            self.update_positions(ti)
            bid_list = self.strategy.predict(ti,self.df.loc[:ti],self.positions,self.cash,self.full_data.loc[:ti])
            self.process_bids(bid_list = bid_list,ti = ti)
        if len(self.positions) > 0:
            self.clear_positions()

