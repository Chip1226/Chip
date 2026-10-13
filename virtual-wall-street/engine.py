"""The trading engine: runs the bots in a background thread.

Two markets plug into it:
- DemoMarket: made-up random prices, no account needed. Same strategies, same math.
- AlpacaMarket: real prices and real (paper / fake money) orders on Alpaca.

The pygame window only reads bot state and pulls events off `engine.events`,
so slow network calls never freeze the screen.
"""

import math
import queue
import random
import re
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

import config
from strategies import STRATEGIES

DUST = 1e-6  # share amounts smaller than this count as "no position"


class Bot:
    def __init__(self, name, symbol, strategy):
        self.name = name
        self.symbol = symbol
        self.strategy_name = strategy
        self.strategy = STRATEGIES[strategy]
        self.shares = 0.0
        self.cash_flow = 0.0   # money in from sells minus money out on buys
        self.cost_basis = 0.0  # what the shares currently held cost
        self.price = None
        # Prefix on every Alpaca order this bot places, so its trades can be told
        # apart from other bots' and rebuilt from order history after a restart.
        self.order_prefix = f"vws-{re.sub(r'[^a-z0-9]', '', name.lower())}-"

    @property
    def holding(self):
        return self.shares > DUST

    @property
    def pnl(self):
        """Total profit or loss: closed trades plus the current value of open shares."""
        return self.cash_flow + self.shares * (self.price or 0)

    def record_fill(self, side, qty, price):
        """Apply a filled order. Returns the profit of a sell (None for a buy)."""
        if side == "buy":
            self.shares += qty
            self.cash_flow -= qty * price
            self.cost_basis += qty * price
            return None
        sold_cost = self.cost_basis * min(qty / self.shares, 1) if self.shares > 0 else 0
        self.shares -= qty
        self.cash_flow += qty * price
        self.cost_basis -= sold_cost
        if self.shares <= DUST:
            self.shares = 0.0
            self.cost_basis = 0.0
        return qty * price - sold_cost


def make_bots():
    return [Bot(b["name"], b["symbol"], b["strategy"]) for b in config.BOTS]


class Engine(threading.Thread):
    def __init__(self, market, bots):
        super().__init__(daemon=True)
        self.market = market
        self.bots = bots
        self.events = queue.Queue()  # (bot, text, color_key) for floating text
        self.paused = False
        self.status = "Starting..."
        self.error = ""
        self.equity = None

    def emit(self, bot, text, kind):
        self.events.put((bot, text, kind))

    def run(self):
        while True:
            started = time.monotonic()
            try:
                self.market.step(self)
                self.error = ""
            except Exception as e:  # keep running; show the problem on screen
                self.error = f"{type(e).__name__}: {e}"[:120]
            time.sleep(max(0, self.market.interval - (time.monotonic() - started)))


class DemoMarket:
    """Random-walk prices so you can watch the strategies without an account."""

    name = "DEMO MODE - simulated prices, no account"
    interval = config.DEMO_TICK_SECONDS

    def __init__(self, bots, seed=None):
        self.rng = random.Random(seed)
        self.history = {}
        for symbol in {b.symbol for b in bots}:
            prices = [100.0]
            for _ in range(59):  # warm-up so strategies have data from the start
                prices.append(self._next(prices[-1]))
            self.history[symbol] = prices

    def _next(self, price):
        # No built-in upward drift: on average the market goes nowhere.
        return price * math.exp(self.rng.gauss(0, 0.002))

    def step(self, engine):
        for prices in self.history.values():
            prices.append(self._next(prices[-1]))
            del prices[:-200]
        engine.status = "Prices tick every %.1fs" % self.interval
        for bot in engine.bots:
            prices = self.history[bot.symbol]
            bot.price = prices[-1]
            if engine.paused:
                continue
            action = bot.strategy(prices, bot.holding)
            if action == "buy":
                bot.record_fill("buy", config.TRADE_DOLLARS / bot.price, bot.price)
                engine.emit(bot, f"BUY ${config.TRADE_DOLLARS:,.0f}", "buy")
            elif action == "sell":
                profit = bot.record_fill("sell", bot.shares, bot.price)
                engine.emit(bot, f"SELL {profit:+.2f}", "profit" if profit >= 0 else "loss")


class AlpacaMarket:
    """Real market prices and paper orders on Alpaca. Never touches real money."""

    name = "ALPACA PAPER TRADING - real prices, fake money"
    interval = config.CHECK_INTERVAL_SECONDS
    FINAL = {"filled", "canceled", "expired", "rejected", "done_for_day", "stopped", "suspended"}

    def __init__(self, key, secret, trading=None, data=None):
        # Paper keys start with "PK"; live-money keys start with "AK". Refuse live ones
        # outright so a pasted wrong key can never trade real money.
        if not key.startswith("PK"):
            raise ValueError("ALPACA_API_KEY is not a paper-trading key (paper keys start with PK). "
                             "Use the keys from the Paper Trading dashboard.")
        if trading is None:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.trading.client import TradingClient
            trading = TradingClient(key, secret, paper=True)
            data = StockHistoricalDataClient(key, secret)
        self.trading = trading
        self.data = data

    def latest_closes(self, symbol, count=100):
        from alpaca.common.enums import Sort
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=datetime.now(timezone.utc) - timedelta(days=7),
            limit=count,
            sort=Sort.DESC,
            feed=DataFeed.IEX,  # the free data feed
        )
        bars = self.data.get_stock_bars(request).data.get(symbol, [])
        return [float(b.close) for b in reversed(bars)]

    def sync_bots(self, bots):
        """Rebuild each bot's position from its own Alpaca orders. Returns bots with an open order."""
        from alpaca.common.enums import Sort
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus

        # Alpaca returns at most 500 orders per call, so page backwards through history.
        by_id, until = {}, None
        while True:
            page = self.trading.get_orders(GetOrdersRequest(
                status=QueryOrderStatus.ALL, limit=500, direction=Sort.DESC, until=until))
            by_id.update((o.id, o) for o in page)
            if len(page) < 500 or page[-1].submitted_at == until:
                break
            until = page[-1].submitted_at
        orders = sorted(by_id.values(), key=lambda o: o.submitted_at)  # replay oldest first
        busy = set()
        for bot in bots:
            fresh = Bot(bot.name, bot.symbol, bot.strategy_name)
            for o in orders:
                if not (o.client_order_id or "").startswith(bot.order_prefix):
                    continue
                if _value(o.status) not in self.FINAL:
                    busy.add(bot.name)
                qty = float(o.filled_qty or 0)
                if qty > 0 and o.filled_avg_price:
                    fresh.record_fill(_value(o.side), qty, float(o.filled_avg_price))
            bot.shares, bot.cash_flow, bot.cost_basis = fresh.shares, fresh.cash_flow, fresh.cost_basis
        return busy

    def place(self, bot, side):
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest

        args = dict(symbol=bot.symbol, time_in_force=TimeInForce.DAY,
                    client_order_id=bot.order_prefix + uuid.uuid4().hex[:16])
        if side == "buy":
            request = MarketOrderRequest(side=OrderSide.BUY, notional=round(config.TRADE_DOLLARS, 2), **args)
        else:
            qty = math.floor(bot.shares * 1e9) / 1e9  # never ask to sell more than we hold
            request = MarketOrderRequest(side=OrderSide.SELL, qty=qty, **args)
        order = self.trading.submit_order(request)
        # Wait for the fill before the next bot trades. Two opposite orders open on the
        # same symbol at once get rejected by Alpaca as a possible wash trade.
        for _ in range(20):
            if _value(order.status) in self.FINAL:
                break
            time.sleep(0.5)
            order = self.trading.get_order_by_id(order.id)
        return order

    def step(self, engine):
        engine.equity = float(self.trading.get_account().equity)
        prices = {s: self.latest_closes(s) for s in {b.symbol for b in engine.bots}}
        busy = self.sync_bots(engine.bots)
        for bot in engine.bots:
            if prices[bot.symbol]:
                bot.price = prices[bot.symbol][-1]

        clock = self.trading.get_clock()
        if not clock.is_open:
            engine.status = f"Market closed - opens {clock.next_open:%a %b %d %I:%M %p} ET"
            return
        engine.status = f"Market open - checking every {self.interval}s"
        if engine.paused:
            return

        for bot in engine.bots:
            closes = prices[bot.symbol]
            if not closes or bot.name in busy:
                continue
            action = bot.strategy(closes, bot.holding)
            if action is None:
                continue
            order = self.place(bot, action)
            status = _value(order.status)
            if status != "filled":
                engine.emit(bot, f"{action.upper()} {status}", "info")
                continue
            qty, price = float(order.filled_qty), float(order.filled_avg_price)
            if action == "buy":
                bot.record_fill("buy", qty, price)
                engine.emit(bot, f"BUY ${qty * price:,.0f}", "buy")
            else:
                profit = bot.record_fill("sell", qty, price)
                engine.emit(bot, f"SELL {profit:+.2f}", "profit" if profit >= 0 else "loss")


def _value(enum_or_str):
    return getattr(enum_or_str, "value", enum_or_str)
