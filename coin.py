import time
import requests
import pyupbit
import datetime
import schedule
from fbprophet import Prophet


myToken = "xoxb-3209322726289-3220474532928-A8JSmwJDqcBA2GWas7c0cJzH"
access = "vvxx0PxmxkOqmSG9Wf7rBbmu63PfA9rmyGOTWGh9"
secret = "7IEKwV6CN6PsN6ERwiJPxhR1gBZMP1jcxieYrwgY"

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )
    print(response)

def get_target_price(ticker, k):
    df = pyupbit.get_ohlcv(ticker, interval="minute", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

predicted_close_price = 0
def predict_price(ticker):
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute10")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=4, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
    closeDf = closeDf.fillna(0)
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue
predict_price("KRW-BTC")
schedule.every().hour.do(lambda: predict_price("KRW-BTC"))

upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(minutes=10)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(minutes=10):
            target_price = get_target_price("KRW-BTC", 0.1)
            current_price = get_current_price("KRW-BTC")
            if target_price < current_price and current_price < predicted_close_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-BTC", krw*0.9995)
                    post_message(myToken,"#ahffk","코인 구매")
        else:
            btc = get_balance("BTC")
            if btc > 0.00008:
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                post_message(myToken,"#ahffk","코인 판매")
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
