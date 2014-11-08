#!/usr/bin/env python
# coding=iso-8859-1

# MarketUnity.py: unified interface to cryptocurrency markets
#
# Copyright © 2014 Scott Alfter
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import sys
sys.path.insert(0, './PyCryptsy/')
from PyCryptsy import PyCryptsy
sys.path.insert(0, './python-bittrex/bittrex/')
from bittrex import Bittrex
import time
from decimal import *

class MarketUnity:

  # constructor

  def __init__(self, credentials, coins):
    self.credentials=credentials
    self.coins=coins
    self.exchanges={}
    self.last_market_update=0
    for i, exch in enumerate(self.credentials):
      self.exchanges[exch]={}
      processed=False
      if (exch=="cryptsy"):
        self.exchanges[exch]["connection"]=PyCryptsy(str(self.credentials[exch]["pubkey"]), str(self.credentials[exch]["privkey"]))
        processed=True
      if (exch=="bittrex"):
        self.exchanges[exch]["connection"]=Bittrex(str(self.credentials[exch]["pubkey"]), str(self.credentials[exch]["privkey"]))
        processed=True
      if (processed==False):
        raise ValueError("unknown exchange")
    self.update_markets()

  # test if coin identifier is one we care about
  
  def check_coin_id(self, id):
    if (self.coins=={}): # null set means check all coins
      return True
    try:
      if (self.coins[id]==1):
        return True
    except:
      return False

  # get new market identifiers if they're at least one hour old

  def update_markets(self):
    if (time.time()-self.last_market_update>=3600):
      for i, exch in enumerate(self.exchanges):
        self.exchanges[exch]["markets"]={}
        markets=self.exchanges[exch]["markets"]
        conn=self.exchanges[exch]["connection"]
        if (exch=="cryptsy"):
          cm=conn.Query("getmarkets", {})["return"]
          for j, market in enumerate(cm):
            if (market["secondary_currency_code"].upper()=="BTC" and self.check_coin_id(market["primary_currency_code"].upper())):
              markets[market["primary_currency_code"].upper()]={}
              markets[market["primary_currency_code"].upper()]["id"]=int(market["marketid"])
        if (exch=="bittrex"):
          cm=conn.get_markets()["result"]
          for j, market in enumerate(cm):
            if (market["BaseCurrency"].upper()=="BTC" and self.check_coin_id(market["MarketCurrency"].upper())):
              markets[market["MarketCurrency"].upper()]={}
              markets[market["MarketCurrency"].upper()]["id"]=market["MarketName"]
    self.last_market_update=time.time()
      
  # update prices
  
  def update_prices(self):
    for i, exch in enumerate(self.exchanges):
      conn=self.exchanges[exch]["connection"]
      if (exch=="cryptsy"):
        for j, mkt in enumerate(self.exchanges[exch]["markets"]):
          orders=conn.Query("marketorders", {"marketid": self.exchanges[exch]["markets"][mkt]["id"]})["return"]
          try:
            self.exchanges[exch]["markets"][mkt]["bid"]=Decimal(orders["buyorders"][0]["buyprice"]).quantize(Decimal("1.00000000"))
          except:
            self.exchanges[exch]["markets"][mkt]["bid"]=0
          try:
            self.exchanges[exch]["markets"][mkt]["ask"]=Decimal(orders["sellorders"][0]["sellprice"]).quantize(Decimal("1.00000000"))
          except:
            self.exchanges[exch]["markets"][mkt]["ask"]=0
      if (exch=="bittrex"):
        summ=conn.get_market_summaries()["result"]
        mkts={}
        for j, mkt in enumerate(summ):
          mkts[mkt["MarketName"]]=mkt
        for j, mkt in enumerate(self.exchanges[exch]["markets"]):
          self.exchanges[exch]["markets"][mkt]["bid"]=Decimal(mkts[self.exchanges[exch]["markets"][mkt]["id"]]["Bid"]).quantize(Decimal("1.00000000"))
          self.exchanges[exch]["markets"][mkt]["ask"]=Decimal(mkts[self.exchanges[exch]["markets"][mkt]["id"]]["Ask"]).quantize(Decimal("1.00000000"))

  # find best bid/ask
  
  def find_best(self):
    coins={}
    for i, ex in enumerate(self.exchanges):
      for j, cn in enumerate(self.exchanges[ex]["markets"]):
        try:
          if (coins[cn]["ask"]>self.exchanges[ex]["markets"][cn]["ask"]):
            coins[cn]["ask"]=self.exchanges[ex]["markets"][cn]["ask"]
            coins[cn]["ask_exch"]=ex
          if (coins[cn]["bid"]<self.exchanges[ex]["markets"][cn]["bid"]):
            coins[cn]["bid"]=self.exchanges[ex]["markets"][cn]["bid"]
            coins[cn]["bid_exch"]=ex
        except:
          coins[cn]={}
          coins[cn]["ask"]=self.exchanges[ex]["markets"][cn]["ask"]
          coins[cn]["ask_exch"]=ex
          coins[cn]["bid"]=self.exchanges[ex]["markets"][cn]["bid"]
          coins[cn]["bid_exch"]=ex
    return coins
