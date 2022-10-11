from ._bid import Bid


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
        if bid.bid_type == 0:
            print("Try to sell {} shares, but only got 0 shares.".format(bid.shares))
            return -1
        self.ticker = bid.ticker
        self.shares = bid.shares
        self.price = bid.price
        
        #k，v: price, number of shares purchased at that price
        self.purchase_history = {bid.price:bid.shares}
        self.wa_cost_price = bid.price
        

    def change_position(self,bid: Bid) -> float:
        """Alter the current position given a new bid on this ticker

        :param bid: a Bid instance
        :type bid: Bid
        :return: 
            if buying: return -1
            if selling:
                if succesful: return the cost, more details in the update_cost function
                if not succesful: return -1
        :rtype: float
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
        """_summary_

        Args:
            bid (Bid): a Bid instance

        Returns:
            float: if buying,returns -1; if selling, return the cost, i.e. dollar value used to purchase those amount of shares

        Notes:

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