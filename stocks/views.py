from django.http import HttpResponse
from django.shortcuts import render
import yfinance as yf
from datetime import datetime
import pandas as pd

def days_between_now(d1):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.today()
    return abs((d2 - d1).days)

def NakedYieldPct(strike,premium):
        return premium*100/strike

def NakedYieldAnnPct(strike,premium,days):
        return NakedYieldPct(strike,premium)*365/days

def days_between_now(d1):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.today()
    return abs((d2 - d1).days)

def BreakEvenPct(strike,premium,price):
    return 100 - ((strike-premium)*100/price)

def index(request):   
    return render(request, 'ticker/index.html')

def expirations(request, ticker):
    yf_ticker = yf.Ticker(ticker)
    expirations = pd.DataFrame({ 'ExpirationDate': yf_ticker.options})
    expirations['DTE'] = expirations.apply(lambda x: days_between_now(x['ExpirationDate']), axis=1)
    return render(request, 'ticker/expirations.html', {'expirations': expirations, 'ticker': ticker})

def options(request, ticker, date):
    yf_ticker = yf.Ticker(ticker)
    lastPrice = yf_ticker.fast_info['last_price']
    chain_puts = yf_ticker.option_chain(date).puts
    chain_puts['BreakEvenPct'] = chain_puts.apply(lambda x: BreakEvenPct(x['strike'], x['bid'],lastPrice), axis=1)
    chain_puts['NakedYieldAnnPct'] = chain_puts.apply(lambda x: NakedYieldAnnPct(x['strike'], x['bid'],days_between_now(date)), axis=1)
    chain_puts = chain_puts.drop(['contractSymbol','contractSize', 'lastTradeDate','currency','change','percentChange'], axis=1)
    context = {'chain_puts': chain_puts, 'ticker': ticker, 'date': date, 'dte': days_between_now(date), 'last_price': lastPrice}
    return render(request, 'ticker/options.html', context)

def get_dataframe_slice(yf_ticker, type, date, min, max):
    if type=='puts':
        df = yf_ticker.option_chain(date).puts
    else:
         df = yf_ticker.option_chain(date).calls

    lastPrice = yf_ticker.fast_info['last_price']
    df = df.drop(['contractSymbol','contractSize', 'lastTradeDate','currency','change','percentChange'], axis=1)
    df = df[(df.strike >= lastPrice * min)]
    df = df[(df.strike <= lastPrice * max)]
    return df

def safewheel(request,ticker): 
    yf_ticker = yf.Ticker(ticker)
    lastPrice = yf_ticker.fast_info['last_price']
    lastPrice70 = lastPrice * 0.7
    lastPrice80 = lastPrice * 0.8
    lastPrice1 = lastPrice/100

    stock_exps = yf_ticker.options
    expirations = pd.DataFrame({ 'ExpirationDate': stock_exps})
    expirations['DTE'] = expirations.apply(lambda x: days_between_now(x['ExpirationDate']), axis=1)

    next_week_expiration = stock_exps[0]

    # get 150 days expiration
    for idx, x in enumerate(stock_exps):
        if days_between_now(x) > 150:
            cputs_150p = stock_exps[idx]
            cputs_150m = stock_exps[idx-1]
            cputs_150mm = stock_exps[idx-2]
            break


    context = {
        'ticker': ticker, 
        'last_price': yf_ticker.fast_info['last_price'],
        'lastPrice70':lastPrice70,
        'lastPrice80':lastPrice80,
        'lastPrice1':lastPrice1,
        'expirations': expirations,
        'chain_puts_next_week': get_dataframe_slice(yf_ticker,'puts',next_week_expiration,0.9,1.1),
        'chain_calls_next_week': get_dataframe_slice(yf_ticker,'calls',next_week_expiration,0.9,1.1),
        'next_week_expiration': next_week_expiration,
        'cputs_150p':cputs_150p,
        'cputs_150m':cputs_150m,
        'cputs_150mm':cputs_150mm,
        'cputs_150p_dte':days_between_now(cputs_150p),
        'cputs_150m_dte':days_between_now(cputs_150m),
        'cputs_150mm_dte':days_between_now(cputs_150mm),
        'cputs_150p_data': get_dataframe_slice(yf_ticker,'puts',cputs_150p,0.65,0.95),
        'cputs_150m_data': get_dataframe_slice(yf_ticker,'puts',cputs_150m,0.65,0.95),
        'cputs_150mm_data': get_dataframe_slice(yf_ticker,'puts',cputs_150m,0.65,0.95)
    }
    
    return render(request, 'ticker/safewheel.html', context)
