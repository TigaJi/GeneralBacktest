from tokenize import String

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

