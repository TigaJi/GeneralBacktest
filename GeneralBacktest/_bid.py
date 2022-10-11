from email.policy import strict
from tokenize import String

class Bid:
    
    """
    Bid Class    
    
    ... 


    Attributes
    ----------    
    ticker : str
        ticker(name) of this bid
    price : float
        intended price to buy/sell at
    shares : int
        intended shares to buy/sell
    bid_type: int
        1 stands for buying
        0 stands for selling

    Methods
    ---------- 
    show(): 
        print out the bid info, for debugging or processing showing purpose

    """

    def __init__(self,ticker: str,price: float,shares: int,bid_type: int):
        """
        Initialize a Bid instance

        Parameters
        ----------
            ticker : str
                ticker(name) of this bid
            price : float
                intended price to buy/sell at
            shares : int
                intended shares to buy/sell
            bid_type: int
                1 stands for buying
                0 stands for selling

        """

        if bid_type != 0 and bid_type != 1:
            raise ValueError("Bid type = {} is not valid.".format(bid_type))
        self.ticker = ticker
        self.price = price
        self.shares = shares
        self.bid_type = bid_type
    

    def show(self):
        """Print out the Bid info

        
        """

        print("---------------")
        if self.bid_type == 1:
            print("Buying:")
        else:
            print("Selling")
        print("Ticker: {}".format(self.ticker))
        print("Shares: {}".format(self.shares))
        print("Price: {}".format(self.price))
        print("---------------")

