from email.policy import strict
from tokenize import String

class Bid:
    """_summary_

    """


    def __init__(self,ticker: str,price: float,shares: int,bid_type: int):
        """initialize a Bid instance

        Args:
            ticker (str): ticker(name) of this bid
            price (float): intended price to buy/sell at
            shares (int): intended shares to buy/sell
            bid_type (int): 1 for buying,0 for sellinng

        Raises:
            ValueError: if bid_type not in [0,1], raise ValueError
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

