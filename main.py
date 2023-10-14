__version__ = "1.0"
__author__ = "Amit Kumar"

import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect

from indicators import Indicator
from kotakclient import KotakClient
from livefeed import LiveFeed
from models import *
from orderclient import OrderClient, get_quote
from portfolio import Portfolio
from watchlist import Watchlist

# Add async to the function which are slower than others

app = FastAPI()
active_connections = set()
subscribed_flag = False
livefeed = LiveFeed()


@app.on_event("startup")
def startup_event():
    global portfolio, indicator
    portfolio = Portfolio()
    indicator = Indicator()
    indicator.attachObserver(portfolio)
    livefeed.attachObserver(indicator)
    livefeed.attachObserver(portfolio)


@app.on_event("shutdown")
def shutdown_event():
    if subscribed_flag:
        livefeed.unsubscribe()
    livefeed.detachObserver(indicator)
    indicator.detachObserver(portfolio)


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
    result = await livefeed.subscribe()
    if result["status"] == "success":
        subscribed_flag = True
    return result


@app.get("/unsubscribe")
def unsubscribe():
    global subscribed_flag
    result = livefeed.unsubscribe()
    if result["status"] == "success":
        subscribed_flag = False
    return result


@app.get("/orders")
def get_orders():
    return OrderClient().get_order_report()


@app.get("/trades")
def get_trades():
    return OrderClient().get_trade_report()


@app.get("/funds")
def get_funds():
    return OrderClient().get_funds()


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
    return OrderClient().get_required_margin(
        transactionType, [OrderParams(token, quantity, price)]
    )


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
    return get_quote(quoteType, token)


@app.get("/position/{position_type}")
def get_Open_position(position_type: str):
    if position_type == "open":
        positionType = PositionType.open
    elif position_type == "stocks":
        positionType = PositionType.stocks
    else:
        positionType = PositionType.today

    return OrderClient().get_position(positionType)


@app.get("/fetchTokens")
def get_tokens():
    return Watchlist().fetch_tokens()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
