__version__ = "1.0"
__author__ = "Amit Kumar"

import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect

from indicators import Indicator
from livefeed import LiveFeed
from models import *
from orderclient import OrderClient, get_quote
from portfolio import Portfolio
from watchlist import Watchlist

# Add async to the function which are slower than others

app = FastAPI()
active_connections = set()
subscribed_flag = False


@app.on_event("startup")
def startup_event():
    return


@app.on_event("shutdown")
def shutdown_event():
    if subscribed_flag:
        livefeed.unsubscribe()
    return


@app.get("/")
def hello():
    return {"data": ["hello", "world"]}


@app.websocket("/livefeed")
async def get_livefeed(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            data = LiveFeed.df_notify
            for connection in active_connections:
                await connection.send_json(data)
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/subscribe")
async def subscribe():
    global subscribed_flag
    if subscribed_flag:
        return {"status": "success", "message": "Already Subscribed"}

    global portfolio, indicator, livefeed
    livefeed = LiveFeed()

    response = await livefeed.subscribe()
    if response["status"] == "success":
        subscribed_flag = True
        portfolio = Portfolio()
        indicator = Indicator()
        indicator.attachObserver(portfolio)
        livefeed.attachObserver(indicator)
    return response


@app.get("/unsubscribe")
def unsubscribe():
    global subscribed_flag
    if not subscribed_flag:
        return {"status": "success", "message": "Already Unsubscribed"}

    global portfolio, indicator, livefeed
    response = livefeed.unsubscribe()
    if response["status"] == "success":
        subscribed_flag = False
        del livefeed
        del indicator
        del portfolio
    return response


@app.get("/orders")
def get_orders():
    response = OrderClient().get_order_report()
    return response


@app.get("/trades")
def get_trades():
    response = OrderClient().get_trade_report()
    return response


@app.get("/funds")
def get_funds():
    response = OrderClient().get_funds()
    return response


@app.get("/margin")
def get_margin(
    type: str = Query(
        ..., min_length=1, max_length=6, title="Transaction Type"
    ),
    token: str = Query(
        ..., min_length=1, max_length=6, title="Instrument Token"
    ),
    quantity: Optional[int] = Query(1, title="Quantity"),
    price: Optional[float] = Query(0, title="Price"),
):
    if type == "buy":
        transactionType = TransactionType.buy
    else:
        transactionType = TransactionType.sell
        
    response = OrderClient().get_required_margin(
        transactionType, [OrderParams(token, quantity, price)]
    )
    return response


@app.get("/quote/{quote_type}")
def get_Quote(
    quote_type: str,
    token: str = Query(
        ..., min_length=1, max_length=6, title="Instrument Token"
    ),
):
    quoteType = None
    if quote_type == "ltp":
        quoteType = QuoteType.ltp
    elif quote_type == "depth":
        quoteType = QuoteType.depth
    else:
        quoteType = QuoteType.ohlc
    response = get_quote(instrumentToken=token, quote_type=quoteType)
    return response


@app.get("/position/{position_type}")
def get_Open_position(position_type: str):
    if position_type == "open":
        positionType = PositionType.open
    elif position_type == "stocks":
        positionType = PositionType.stocks
    else:
        positionType = PositionType.today
    response = OrderClient().get_position(positionType)
    return response


@app.get("/fetchTokens")
def get_tokens():
    response = Watchlist().fetch_tokens()
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
