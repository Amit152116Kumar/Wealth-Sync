import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect

from livefeed import LiveFeed
from models import *
from orderclient import OrderClient
from portfolio import Portfolio
from watchlist import Watchlist

# Add async to the function which are slower than others

app = FastAPI()
active_connections = set()
portfolio = Portfolio()


@app.get("/")
def hello():
    return {"data": ["hello", "world"]}


@app.websocket("/livefeed")
async def livefeed(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            data = LiveFeed.dataList
            for connection in active_connections:
                await connection.send_json(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/subscribe")
def subscribe():
    livefeed = LiveFeed()
    livefeed.attachObserver(portfolio)
    return livefeed.subscribe()


@app.get("/unsubscribe")
def unsubscribe():
    livefeed = LiveFeed()
    livefeed.detachObserver(portfolio)
    return livefeed.unsubscribe()


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
    type: str = Query(..., min_length=1, max_length=6, title="Transaction Type"),
    token: str = Query(..., min_length=1, max_length=6, title="Instrument Token"),
    quantity: Optional[int] = Query(1, title="Quantity"),
    price: Optional[float] = Query(0, title="Price"),
):
    if type == "buy":
        transactionType = TransactionType.buy
    else:
        transactionType = TransactionType.sell
    return OrderClient().get_required_margin(transactionType, [OrderParams(token, quantity, price)])


@app.get("/quote/{quote_type}")
def get_quote(quote_type: str, token: str = Query(..., min_length=1, max_length=6, title="Instrument Token")):
    quoteType = None
    if quote_type == "ltp":
        quoteType = QuoteType.ltp
    elif quote_type == "depth":
        quoteType = QuoteType.depth
    else:
        quoteType = QuoteType.ohlc
    return OrderClient().get_quote(quoteType, token)


@app.get("/position/{position_type}")
def get_Open_position(position_type: str):
    if position_type == "open":
        positionType = PositionType.open
    elif position_type == "stocks":
        positionType = PositionType.stocks
    else:
        positionType = PositionType.today

    return OrderClient().get_position(positionType)


@app.get("/watchlist")
def get_watchlist():
    return Watchlist().get_watchlist()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
