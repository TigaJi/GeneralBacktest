# GeneralBacktest

A simple, realitic package to backtest trading strategies

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
        bid_list = []

        if ti.weekday() == 0:
            bid = Bid(ticker = 'AAPL', shares = 100, price = df.iloc[-1]['AAPL'],bid_type = 1)

            bid_list.append(bid)
        
        if ti.weekday() == 4:
            bid = Bid(ticker = 'AAPL', shares = 100, price = df.iloc[-1]['AAPL'],bid_type = 0)

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
For more detailed examples and illstruations,please check this [notebook]
(https://github.com/TigaJi/GeneralBacktest/blob/main/Demo/demos.ipynb)
