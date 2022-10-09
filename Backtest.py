import pandas as pd
import numpy as np
import random
import sys
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt


class Backtest:
    def __init__(self,price_data,strategy,initial_amount = 100000, has_tc = True, full_data = None):
        if self.check_input_data(price_data) == True:
            self.df = price_data
        else:
            return
        
        #k,v : String of ticker, a Position type instance
        self.positions = {}
        
        #cash
        self.cash = initial_amount
        
        #strategy
        self.strategy = strategy
        
        #have transaction cost or not 
        if has_tc == True:
            self.tc = 0.002
        else:
            self.tc = 0
        
        #round for backtest step
        self.current = 0
        
        #dfs to record
        self.transaction_history = pd.DataFrame(columns = ["dt","ticker","type","price","shares","amount","cash_left","transaction_cost","pnl"])
        self.portfolio_tracker = pd.DataFrame(columns = ["dt","bid_count","position_count","cash_value","positions_value","total_value","bah"])
        #self.portfolio_tracker.loc[0] = [self.df.index[0],0,0,self.cash,0,self.cash,self.cash]
        
        #a dataframe contains predictions, used for model test
        if full_data != None:
            self.full_data = full_data
        else:
            self.full_data  = pd.DataFrame(index = self.df.index)

    
    def check_input_data(self,df):
        if df.index.inferred_type != "datetime64":
            print("input dataframe must have a datetime64 index")
            return False
        if df.isnull().values.any():
            print("input dataframe contains null values")
            return False
        return True


    def update_positions(self,ti):
        current_price = self.df.loc[ti]
        for position in list(self.positions.values()):
            position.price = current_price[position.ticker]
    

    
    def record_transaction(self,ti,bid,pnl):
        record = [ti,bid.ticker,bid.bid_type,bid.price,bid.shares,bid.price*bid.shares,self.cash,bid.price*bid.shares*self.tc,pnl]
        self.transaction_history.loc[len(self.transaction_history)] = record
        
    def update_tracker(self,ti,bid_list,positions,cash):
        rets = [end/start for start,end in zip(self.df.iloc[0].values,self.df.loc[ti].values)]
        bah_value = sum(([100000//len(self.df.columns)*ret for ret in rets]))
        positions_value = sum([pos.price*pos.shares for pos in self.positions.values()])
        record = [ti,len(bid_list),len(positions),cash,positions_value,positions_value+cash,bah_value]
        self.portfolio_tracker.loc[len(self.portfolio_tracker)] = record

    def clear_positions(self):
        bid_list = []
        for pos in self.positions.values():
            bid = Bid(ticker = pos.ticker,shares = pos.shares,price = self.df.iloc[-1][pos.ticker],bid_type = 0)
            bid_list.append(bid)
        self.process_bids(bid_list)

    def upload_to_dashboard(self,name):
        if len(self.portfolio_tracker) < len(self.df):
            print("Unable to upload: Backtest is unfinished.")
            return
        if "algo-trade-dashboard-80cae071e907.json" not in os.listdir():
            print("Unable to upload: Couldn't find credential file (algo-trade-dashboard-80cae071e907.json)")
            return
        
        
        self.portfolio_tracker.to_csv(name+"_backtest_result.csv")
        


        gauth = GoogleAuth()
        scope = ['https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive.metadata'
          ]
        

        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name("algo-trade-dashboard-80cae071e907.json", scope)
        drive = GoogleDrive(gauth)

        file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

        for file in file_list:
            id = file['id']
            if name+"_backtest_result.csv" == file['title']:
                f1 = drive.CreateFile({'name':name+"_backtest_result.csv",'id':id})
                f1.SetContentFile(name+"_backtest_result.csv")
                f1.Upload()
                print("Data uploaded.")
                return

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
                    if temp_cost != 0:
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

        self.update_tracker(ti,bid_list,self.positions,self.cash)
        
        
        
    def plot(self):
        plt.figure()
        plt.plot(self.portfolio_tracker['total_value'], label = 'random_strat')
        plt.plot(self.portfolio_tracker['bah'],label = 'bah')
        plt.legend()
        plt.show()
    
    def backtest_step(self):
        #current ti
        ti = self.df.index[self.current]
        
        self.update_positions(ti)
        bid_list = self.strategy.predict(ti,self.df.loc[:ti],self.positions,self.cash,self.full_data.loc[:ti])
        self.process_bids(bid_list = bid_list,ti = ti)
        self.current+=1
        
        
        
    def backtest_full(self):
        for ti in self.df.index:
            self.update_positions(ti)
            bid_list = self.strategy.predict(ti,self.df.loc[:ti],self.positions,self.cash,self.full_data.loc[:ti])
            self.process_bids(bid_list = bid_list,ti = ti)
        if len(self.positions) > 0:
            self.clear_positions()

class Bid:
    def __init__(self,ticker,price,shares,bid_type):
        self.ticker = ticker
        self.price = price
        self.shares = shares
        self.bid_type = bid_type
    
    def __del__(self):
        return

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
    def __init__(self,bid):
        self.ticker = bid.ticker
        self.shares = bid.shares
        self.price = bid.price
        
        #k，v: price, number of shares purchased at that price
        self.purchase_history = {bid.price:bid.shares}
        self.wa_cost_price = bid.price
        



    def change_position(self,bid):
        self.price = bid.price
        if bid.bid_type == 1:
            
            self.update_cost(bid)
            self.shares += bid.shares
            
        
        if bid.bid_type == 0:
            if self.shares < bid.shares:
                print("Try to sell {} shares, but only got {} shares.".format(bid.shares,self.shares))
                return 0

            
            cost = self.update_cost(bid)
            self.shares -= bid.shares
            return cost
            


        
    def update_cost(self,bid):
        #buy
        if bid.bid_type == 1:
            #if have purchased at this price
            if bid.price in self.purchase_history.keys():
                self.purchase_history[bid.price] += bid.shares
            else:
                self.purchase_history[bid.price] = bid.shares
            self.wa_cost_price = sum([i*j for i,j in self.purchase_history.items()])/(self.shares+bid.shares)

            
            
                
        #sell
        else:
            
            #if empty position
            if bid.shares == self.shares:

                #weighted average
                return self.wa_cost_price * self.shares
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
