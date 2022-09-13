import pandas as pd
import numpy as np
import random
import sys
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

class Backtest:
    def __init__(self,price_data,strategy,initial_amount = 100000, has_tc = True, is_print = False):
        if self.check_input_data(price_data) == True:
            self.df = price_data
        else:
            return
        
        #k,v : String of ticker, a Position type instance
        self.positions = {}
        
        
        self.cash = initial_amount
        self.values = []
        self.strategy = strategy
        
        if has_tc == True:
            self.tc = 0.002
        else:
            self.tc = 0
        
        self.transaction_history = pd.DataFrame(columns = ["dt","ticker","type","price","shares","amount","cash_left","transaction_cost","pnl"])
        self.portfolio_tracker = pd.DataFrame(columns = ["dt","bid_count","position_count","cash_value","positions_value","total_value","bah"])
        
        self.is_print = is_print
    
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
        
        total_position_value = sum([pos.price*pos.shares for pos in self.positions.values()])
        self.values.append(total_position_value+self.cash)
    
    def show_status(self):
        print("cash: {}".format(self.cash))
        print("# of positions: {}".format(len(self.positions)))
        
        for pos in self.positions.values():
            pos.show()
        total_position_value = sum([pos.price*pos.shares for pos in self.positions.values()])
        print("total_position_value: {}".format(total_position_value))
    
    def record_transaction(self,ti,bid,pnl):
        record = [ti,bid.ticker,bid.bid_type,bid.price,bid.shares,bid.price*bid.shares,self.cash,bid.price*bid.shares*self.tc,pnl]
        self.transaction_history.loc[len(self.transaction_history)] = record
        
    def update_tracker(self,ti,bid_list,positions,cash):
        rets = [end/start for start,end in zip(self.df.iloc[0].values,self.df.loc[ti].values)]
        bah_value = sum(([100000//len(self.df.columns)*ret for ret in rets]))
        positions_value = sum([pos.price*pos.shares for pos in self.positions.values()])
        record = [ti,len(bid_list),len(positions),cash,positions_value,positions_value+cash,bah_value]
        self.portfolio_tracker.loc[len(self.portfolio_tracker)] = record
    
    def upload_to_dashboard(self,name):
        if len(self.portfolio_tracker) != len(self.df):
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
            if name+"_backtest_result.csv" == file['title']:
                file.SetContentFile(name+"_backtest_result.csv")
                print("Data uploaded.")
                return

        f1 = drive.CreateFile({'name':name+"_backtest_result.csv"})

        f1.SetContentFile(name+"_backtest_result.csv")
        f1.Upload()
        os.remove(name+"_backtest_result.csv")
        print("Data uploaded.")
     
    def backtest(self):
    
        for ti in self.df.index:
            
            if self.is_print == True:
                print("=====================================================================")
                print(ti)
            self.update_positions(ti)
            
            #self.show_status()
            
            
            
            #where the strategy kick in and gives a list of bids
            bid_list = self.strategy(ti,self.df.loc[:ti],self.positions,self.cash)
            
            
            
            #process the bids
            for bid in bid_list:
                #if already have a positionn
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
                        if self.positions[bid.ticker].shares < bid.shares:
                            print("Try to sell {} shares, but only got {} shares.".format(bid.shares,self.positions[bid.ticker].shares))
                            continue
                        
                        #update cash
                        self.cash += income
                        self.cash -= income*self.tc
                        
                        #update position,and get a cost

                        temp_cost = pos.change_position(bid)
                       
                        #calculate pnl
                        pnl = income-temp_cost
                        
                        #record this transaction
                        self.record_transaction(ti,bid,pnl)
                        if pos.shares == 0:
                            del pos
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
    

class Bid:
    def __init__(self,ticker,price,shares,bid_type):
        self.ticker = ticker
        self.price = price
        self.shares = shares
        self.bid_type = bid_type
    
    def show(self):
        if self.bid_type == 1:
            print("Buying:")
        else:
            print("Selling")
        print("Ticker: {}".format(self.ticker))
        print("Shares: {}".format(self.shares))
        print("Price: {}".format(self.price))

class Position:
    def __init__(self,bid):
        self.ticker = bid.ticker
        self.share = bid.shares
        self.price = bid.price
        
        #k，v: price, number of shares purchased at that price
        self.purchase_history = {}
        self.wa_cost_price = bid.price
        self.update_cost(bid)
    
    def change_position(self,bid):
        self.price = bid.price
        if bid.bid_type == 1:
            self.shares += bid.shares
            self.update_cost(bid)
            
        
        if bid.bid_type == 0:
            self.shares -= bid.shares
            return self.update_cost(bid)
        
        

   
    def update_cost(self,bid):
        #buy
        if bid.bid_type == 1:
            #if have purchased at this price
            if bid.price in self.purchase_history.keys():
                self.purchase_history[bid.price] += bid.shares
            else:
                self.purchase_history[bid.price] = bid.shares
            self.wa_cost_price = sum([i*j for i,j in zip(self.purchase_history.keys(),self.purchase_history.values())])/self.shares
            
                
        #sell
        else:
            
            #if empty position
            if bid.shares == self.shares:
                #weighted average
                self.wa_cost_price = sum([i*j for i,j in zip(self.purchase_history.keys(),self.purchase_history.values())])/self.shares
                return sum([i*j for i,j in zip(self.purchase_history.keys(),self.purchase_history.values())])
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
                self.wa_cost_price = sum([i*j for i,j in zip(self.purchase_history.keys(),self.purchase_history.values())])/self.shares
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
            