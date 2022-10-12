# GeneralBacktest

A simple, realistic package to backtest trading strategies

## Author Email: dj2194@nyu.edu

## Installation

Install from github

```bash
pip install git+https://github.com/TigaJi/GeneralBacktest#egg=GeneralBacktest
```

## Sample

## Import
```python
From GeneralBacktest import Backtest, Position, Bid
```

## A demo strategy
## buy 100 shares of 'AAPL' every Monday, sell on Friday

```python
class DemoStrategy:
    
    def predict(ti,df,positions,cash,full_data):
        """A function that will be called at every ti that returns a list of bids(orders)

        Args:
            ti (pd.DatetimeIndex): current time
            df (pd.DataFrame): all history prices up to ti
            cash (float): starting cash at this round
            full_data(pd.DataFrame): OHLCV up to this ti, optional to be empty

        Returns:
            a list of Bid instances to execute at this round
        
        """

        
        bid_list = []

        # if Monday
        if ti.weekday() == 0:
            price = df.iloc[-1]['AAPL'] #AAPL's current price
            bid = Bid(ticker = 'AAPL', shares = 100, price = price,bid_type = 1)

            bid_list.append(bid)
        
        #if Friday
        if ti.weekday() == 4:
            price = df.iloc[-1]['AAPL'] #AAPL's current price
            bid = Bid(ticker = 'AAPL', shares = 100, price = price,bid_type = 0)

            bid_list.append(bid)
        
        return bid_list
```

## Test
```python
#load a sample dataset
data = pd.read_csv("test_data.csv", index_col = 0)
data.index = pd.to_datetime(data.index)

#a backtest instance
demo = Backtest(data, DemoStrategy)

#start testing
demo.backtest_full()
```
    
## A detailed example
For more detailed illstruations,please check this [notebook](https://github.com/TigaJi/GeneralBacktest/blob/main/Demo/demo.ipynb)
