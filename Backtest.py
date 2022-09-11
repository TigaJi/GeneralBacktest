import pandas


class Backtest:
    def __init__(self,price_data,initial_amount,strategy):
        if self.check_input_data(price_data) == True:
            self.df = price_data
        else:
            return
        self.positions = {}
        self.cash = initial_amount
        self.values = []
        self.strategy = strategy
    
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
    
    def show_status(self,is_print):
        print("cash: {}".format(self.cash))
        print("# of positions: {}".format(len(self.positions)))
        
        if is_print == True:
            for pos in self.positions.values():
                pos.show()
        total_position_value = sum([pos.price*pos.shares for pos in self.positions.values()])
        print("total_position_value: {}".format(total_position_value))
    
        
    def backtest(self):
        for ti in self.df.index:
            print("=====================================================================")
            print(ti)
            self.update_positions(ti)
            
            
            
            #if ti.hour == 9:
            self.show_status(is_print = False)
            
            
            
            #where the strategy kick in and gives a list of bids
            bid_list = self.strategy(ti,self.df.loc[:ti],self.positions,self.cash)
            
            
            
            #process the bids
            for bid in bid_list:
                if bid.shares == 0:
                    continue
                
                #if already have a positionn
                if bid.ticker in self.positions.keys():
                    #pos = self.positions[bid.ticker]
                    
                    #if increase position
                    if bid.bid_type == 1:
                        cost = bid.shares * bid.price
                        if self.cash < cost:
                            print("Not enough cash to build a position for "+bid.ticker)
                            continue
                        self.cash -= cost
                        
                        self.positions[bid.ticker].change_position(bid)
                    
                    #if decrease position
                    else:

                        if self.positions[bid.ticker].shares < bid.shares:
                            print("Try to sell {} shares, but only got {} shares.".format(bid.shares,self.positions[bid.ticker].shares))
                            continue
                            
                        self.positions[bid.ticker].change_position(bid)
                        self.cash += bid.shares * bid.price
                        
                        if self.positions[bid.ticker].shares == 0:
                            del self.positions[bid.ticker]      
                    
                
                #if not have a position yet
                else:
                    if bid.bid_type == 0:
                        print("Can't sell, don't have a position yet.")
                        continue
                    cost = bid.shares * bid.price
                    if self.cash < cost:
                        print("Not enough cash to build a position for "+bid.ticker)
                        continue
                    self.cash -= cost
                    self.positions[bid.ticker] = Position(bid)

class Bid:
    def __init__(self,ticker,price,shares,bid_type):
        self.ticker = ticker
        self.price = price
        self.shares = shares
        self.bid_type = bid_type
    
    def show(self):
        if self.bid_type == 1:
            print("buying:")
        else:
            print("selling:")
        print("Ticker: {}".format(self.ticker))
        print("Shares: {}".format(self.shares))
        print("price: {}".format(self.price))

class Position:
    def __init__(self,bid):
        self.ticker = bid.ticker
        self.shares = bid.shares
        self.price = bid.price

    
    def change_position(self,bid):
        if bid.bid_type == 1:
            self.shares += bid.shares
        
        if bid.bid_type == 0:
            if self.shares < bid.shares:
                print("WARNING")
                bid.show()
                self.show()
            self.shares -= bid.shares
    
    def show(self):
        print("Ticker: {}".format(self.ticker))
        print("Shares: {}".format(self.shares))
        print("price: {}".format(self.price))