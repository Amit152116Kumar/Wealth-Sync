import datetime
from dataclasses import dataclass, field
from enum import Enum

import pytz

IST = pytz.timezone("Asia/Kolkata")


class OrderType(Enum):
    normal_order = "N"
    superMultiple_order = "SM"
    smart_Order_Routing_order = "SOR"
    mtf_order = "MTF"
    mis_order = "MIS"


class TransactionType(Enum):
    buy = "BUY"
    sell = "SELL"


class PositionType(Enum):
    today = "TODAYS"
    stocks = "STOCKS"
    open = "OPEN"


class QuoteType(Enum):
    ltp = "LTP"
    depth = "DEPTH"
    ohlc = "OHLC"


class OptionType(Enum):
    call = "CE"
    put = "PE"
    both = "BOTH"


class Exchange(Enum):
    nse = "NSE"
    bse = "BSE"
    mcx = "MCX-CM"
    nsefx = "NSE-FX"


class OrderValidity(Enum):
    gfd = "GFD"
    ioc = "IOC"


def upcoming_expiry() -> str:
    today = datetime.datetime.now(IST).date()
    days_until_thursday = (3 - today.weekday()) % 7
    next_thursday = today + datetime.timedelta(days=days_until_thursday)
    return next_thursday.strftime("%d%b%y").upper()


@dataclass(
    frozen=True,
    order=True,
)
class OrderParams:
    instrument_token: int
    quantity: int
    price: float = field(default=0)
    amount: int = field(default=0, init=False)
    trigger_price: float = field(default=0)

    def __dict__(self):
        return {
            "instrumentToken": self.instrument_token,
            "quantity": self.quantity,
            "price": self.price,
            "amount": self.amount,
            "triggerPrice": self.trigger_price,
        }


@dataclass(frozen=True, order=True)
class CashTokens:
    instrumentName: str
    exchange: Exchange = field(default=Exchange.nse)


@dataclass(frozen=True, order=True)
class FnoTokens:
    instrumentName: str
    strike: int
    optionType: OptionType
    expiry: str = field(default=upcoming_expiry())
    exchange: Exchange = field(default=Exchange.nse)


@dataclass(frozen=True, order=True)
class PlaceOrderResponse:
    message: str
    orderId: str
    price: float
    quantity: int
    tag: str


@dataclass(frozen=True, order=True)
class _OrderBookParams:
    activityTimestamp: str
    disclosedQuantity: int
    exchOrderId: str
    exchTradeId: str
    exchangeStatus: str
    filledQuantity: int
    message: str
    orderQuantity: int
    price: float
    status: str
    statusInfo: str
    statusMessage: str
    triggerPrice: float
    validity: str
    version: int


@dataclass(frozen=True, order=True)
class OrderBookResponse:
    success: list[_OrderBookParams]


@dataclass(frozen=True, order=True)
class _MarginReqParams:
    instrumentToken: str
    mtf: float
    normal: float
    superMultiple: float


@dataclass(frozen=True, order=True)
class MarginReqResponse:
    Success: list[_MarginReqParams]


@dataclass(frozen=True, order=True)
class QuoteOHLCResponse:
    instrumentToken: str
    instrumentName: str
    stk_it: str = field(repr=False)
    open: str
    close: str
    high: str
    low: str
    stk_strike_price: str = field(repr=False)
    upper_ckt_limit: str = field(repr=False)
    lower_ckt_limit: str = field(repr=False)


@dataclass(frozen=True, order=True)
class _DepthLevel:
    price: str
    quantity: str
    orders: str


@dataclass(frozen=True, order=True)
class _Depth:
    buy: list[_DepthLevel]
    sell: list[_DepthLevel]
    stk_strike_price: int
    upper_ckt_limit: str
    lower_ckt_limit: str


@dataclass(frozen=True, order=True)
class QuoteDepthResponse:
    depth: list[_Depth]


@dataclass(frozen=True, order=True)
class _TradeParams:
    exchange: str
    exchangeTradeId: str
    expiryDate: str
    instrumentName: str
    instrumentToken: int
    instrumentType: str
    isFNO: str
    marketExchange: str
    marketLot: int
    multiplier: int
    optionType: str
    orderId: int
    orderTimestamp: str
    price: float
    product: str
    quantity: int
    statusInfo: str
    statusMessage: str
    strikePrice: int
    tradeId: int
    tradeTimestamp: str
    transactionType: str


@dataclass(frozen=True, order=True)
class TradeBookResponse:
    success: list[_TradeParams]


@dataclass
class _PositionTodayParams:
    actualNetTrdValue: float
    averageStockPrice: float
    buyOpenQtyLot: int
    buyOpenVal: float
    buyTradedQtyLot: int
    buyTradedVal: float
    buyTrdAvg: float
    deliveryStatus: int
    denominator: int
    exchange: str
    expiryDate: str
    exposureMargin: float
    exposureMarginTotal: float
    grossUtilization: float
    instrumentName: str
    instrumentToken: int
    lastPrice: float
    marginType: str
    marketLot: int
    maxCODQty: int
    maxSingleOrderQty: int
    maxSingleOrderValue: int
    multiplier: int
    netChange: float
    netTrdQtyLot: int
    netTrdValue: float
    normalSqOffQty: int
    optionType: str
    percentChange: float
    premium: float
    qtyUnit: str
    rbiRefRate: int
    realizedPL: float
    segment: str
    sellOpenQtyLot: int
    sellOpenVal: float
    sellTradedQtyLot: int
    sellTradedVal: float
    sellTrdAvg: float
    spanMargin: float
    spanMarginTotal: float
    spreadTotal: float
    strikePrice: int
    symbol: str
    totalStock: int


@dataclass(frozen=True, order=True, slots=True)
class FundsResponse:
    additionalOptionBrokerage: int = field(repr=False)
    availableCashBalance: float
    clientGroupLimit: int = field(repr=False)
    debtorFlag: int = field(repr=False)
    dtv: int = field(repr=False)
    dtvBTSTSell: int = field(repr=False)
    initialMargin: int = field(repr=False)
    marginAvailable: float
    marginUtilised: float
    mfLien: int = field(repr=False)
    mtm: int = field(repr=False)
    nriPinsBalance: int = field(repr=False)
    optionPremium: int
    realizedPL: int
    securityMargin: int = field(repr=False)
    totalMargin: float


@dataclass(frozen=True, order=True)
class Positions:
    Success: list[_PositionTodayParams]


@dataclass(frozen=True, order=True)
class Strategy:
    rsi: int
    sma: int
    fast_multiplier: int
    fast_period: int
    slow_multiplier: int
    slow_period: int
    timeframe: int
