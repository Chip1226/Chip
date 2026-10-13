"""The trading engine: runs the bots in a background thread.

Every bot follows the same trading rules (Engine.trade); only the market under it changes:
- DemoMarket: simulated stock prices and option prices, no account needed.
- AlpacaMarket: real option quotes and real paper (fake money) orders on Alpaca.

The pygame window only reads bot state and pulls events off `engine.events`,
so slow network calls never freeze the screen.
"""

import json
import math
import os
import queue
import random
import threading
import time
import uuid
from datetime import date, datetime, timedelta
from datetime import time as clock_time
from zoneinfo import ZoneInfo

import config
from options import Contract, black_scholes, occ_symbol, parse_occ, pick_single, pick_spread, round_price
from strategies import SIGNALS

ET = ZoneInfo("America/New_York")
MARKET_OPEN, MARKET_CLOSE = clock_time(9, 30), clock_time(16, 0)


class Bot:
    def __init__(self, spec):
        self.spec = {**config.RULES, **spec}
        self.name = spec["name"]
        self.symbol = spec["symbol"]
        self.style = spec["style"]
        self.signal_name = spec["signal"]
        self.signal = SIGNALS.get(spec["signal"])  # None for "news": the engine asks the news watcher
        self.budget = float(spec["budget"])
        self.cash = self.budget
        # Open trade, or None. legs: [[option symbol, "long" or "short"], ...]
        # entry_cost: dollars paid for the whole position.
        self.position = None
        self.position_value = 0.0  # what the open position is worth now, in dollars
        self.cooldown_until = None
        self.exit_attempts = 0
        self.flip_since = None  # when the signal started pointing against the open trade
        self.trades = 0
        self.wins = 0
        self.price = None
        self.note = "starting"

    @property
    def holding(self):
        return self.position is not None

    @property
    def pnl(self):
        """Profit or loss since the start: cash plus open position value, minus starting budget."""
        return self.cash + (self.position_value if self.position else 0) - self.budget

    def loss_room(self):
        """Dollars this bot can still lose before hitting its hard loss limit.

        Counts the open position as already lost, since an option can go to zero.
        """
        at_risk = self.position["entry_cost"] if self.position else 0
        realized = self.cash + at_risk - self.budget
        return max(self.budget * self.spec["max_loss_pct"] + realized - at_risk, 0)

    def state(self):
        return {"cash": self.cash, "position": self.position, "position_value": self.position_value,
                "cooldown_until": self.cooldown_until.isoformat() if self.cooldown_until else None,
                "trades": self.trades, "wins": self.wins}

    def load_state(self, s):
        self.cash = s["cash"]
        self.position = s["position"]
        self.position_value = s["position_value"]
        self.cooldown_until = datetime.fromisoformat(s["cooldown_until"]) if s["cooldown_until"] else None
        self.trades = s["trades"]
        self.wins = s["wins"]


def make_bots():
    return [Bot(spec) for spec in config.BOTS]


def days_to_earnings(bot, today):
    if not bot.spec.get("earnings"):
        return None
    return (date.fromisoformat(bot.spec["earnings"]) - today).days


EXIT_LABELS = {"take_profit": "TAKE PROFIT", "stop_loss": "STOP LOSS", "expiring": "TIME STOP",
               "thesis_broken": "SIGNAL FLIP", "earnings": "PRE-EARNINGS"}


class Engine(threading.Thread):
    def __init__(self, market, bots, news=None):
        super().__init__(daemon=True)
        self.market = market
        self.bots = bots
        self.news = news  # NewsWatcher, or None when news is off
        self.news_error = ""
        self.busy = threading.Lock()
        self.events = queue.Queue()  # (bot, text, kind) -> floating text and beam
        self.paused = False
        self.status = "Starting..."
        self.error = ""
        self.equity = None
        self.market_open = None  # True / False once the market has been checked
        path = getattr(market, "state_path", None)
        if path and os.path.exists(path):
            with open(path) as f:
                saved = json.load(f)
            for bot in bots:
                if bot.name in saved:
                    bot.load_state(saved[bot.name])

    def emit(self, bot, text, kind):
        self.events.put((bot, text, kind))

    def run(self):
        while True:
            started = time.monotonic()
            with self.busy:  # held for a whole step, so stopping never cuts an order in half
                try:
                    self.market.step(self)
                    self.save()
                    self.error = ""
                except Exception as e:  # keep running; show the problem on screen
                    self.error = f"{type(e).__name__}: {e}"[:140]
            time.sleep(max(0, self.market.interval - (time.monotonic() - started)))

    def stop(self, timeout=90):
        """Wait for the current step (an order waiting to fill, say) to finish, then hold.

        Returns True if it got there in time. The thread is a daemon, so the program
        can exit right after this without leaving a trade half-recorded.
        """
        return self.busy.acquire(timeout=timeout)

    def save(self):
        path = getattr(self.market, "state_path", None)
        if not path:
            return
        with open(path + ".tmp", "w") as f:
            json.dump({b.name: b.state() for b in self.bots}, f, indent=2)
        os.replace(path + ".tmp", path)

    # --- Trading rules, shared by every market ---

    def trade_all(self):
        for bot in self.bots:
            closes = self.market.closes(bot.symbol)
            if not closes:
                bot.note = "no price data"
                continue
            bot.price = closes[-1]
            # Every Nth one-minute close, ending with the latest = N-minute bars
            bars = closes[::-1][::config.SIGNAL_BAR_MINUTES][::-1]
            if bot.signal_name == "news":
                signal = self.news.signal(bot.symbol, closes, self.market.now()) if self.news else None
            else:
                signal = bot.signal(bars)
            if bot.position:
                self.manage_open(bot, signal)
            else:
                self.maybe_open(bot, signal)

    def maybe_open(self, bot, signal):
        now = self.market.now()
        today = now.date()
        minutes_in = (now - datetime.combine(today, MARKET_OPEN)).total_seconds() / 60
        minutes_left = (datetime.combine(today, MARKET_CLOSE) - now).total_seconds() / 60
        to_earnings = days_to_earnings(bot, today)
        breaking = self.news.blocked(bot.symbol, now) if self.news and bot.signal_name != "news" else None
        if self.paused:
            bot.note = "paused"
        elif bot.signal_name == "news" and not self.news:
            bot.note = "news off (see README)"
        elif bot.loss_room() < 1:
            bot.note = f"STOPPED: hit -{bot.spec['max_loss_pct']:.0%} loss limit"
        elif bot.cooldown_until and now < bot.cooldown_until:
            bot.note = "cooling down"
        elif minutes_in < config.SKIP_OPEN_MINUTES or minutes_left < config.SKIP_CLOSE_MINUTES:
            bot.note = "no entries near open/close"
        elif to_earnings is not None and 0 <= to_earnings <= bot.spec.get("blackout_days", 0):
            bot.note = "earnings blackout"
        elif breaking:
            bot.note = "major news, waiting"
        elif signal is None:
            bot.note = "waiting for news" if bot.signal_name == "news" else "waiting for a signal"
        else:
            self.open_position(bot, signal, today)

    def open_position(self, bot, kind, today):
        s = bot.spec
        max_cost = min(bot.cash * s["risk_pct"], bot.loss_room())
        chain = self.market.chain(bot.symbol, kind, s["min_dte"], s["max_dte"], bot.price)
        cp = "C" if kind == "call" else "P"
        if bot.style == "spread":
            pick, why = pick_spread(chain, today, s["delta_min"], s["delta_max"], s["widths"], max_cost)
            if pick:
                long, short = pick
                legs = [[long.symbol, "long"], [short.symbol, "short"]]
                unit = long.mid - short.mid
                label = f"{long.strike:g}/{short.strike:g}{cp} {long.expiration:%m/%d}"
                expiration = long.expiration
        else:
            pick, why = pick_single(chain, today, s["delta_min"], s["delta_max"], max_cost)
            if pick:
                legs = [[pick.symbol, "long"]]
                unit = pick.mid
                label = f"{pick.strike:g}{cp} {pick.expiration:%m/%d}"
                expiration = pick.expiration
        if not pick:
            bot.note = why
            return

        limit = round_price(unit, bot.symbol)  # limit order at the mid, never a market order
        qty = math.floor(max_cost / (limit * 100)) if limit > 0 else 0
        if qty < 1:
            bot.note = f"too pricey (${limit * 100:,.0f})"
            return
        filled, price = self.market.submit(bot, legs, qty, limit, opening=True)
        if not filled:
            bot.note = "entry not filled at mid, retrying"
            return
        cost = price * 100 * filled
        bot.cash -= cost
        bot.position = {"kind": kind, "legs": legs, "qty": filled, "entry_cost": cost,
                        "expiration": expiration.isoformat(), "label": label}
        bot.position_value = cost
        bot.exit_attempts = 0
        bot.note = f"{filled}x {label}"
        self.emit(bot, f"BUY {kind.upper()} -${cost:,.0f}", kind)

    def manage_open(self, bot, signal):
        pos = bot.position
        quotes = self.market.quotes([sym for sym, _ in pos["legs"]])
        if any(sym not in quotes for sym, _ in pos["legs"]):
            bot.note = "waiting for option quotes"
            return
        sign = {"long": 1, "short": -1}
        mid = max(sum(sign[side] * (quotes[sym][0] + quotes[sym][1]) / 2 for sym, side in pos["legs"]), 0)
        bot.position_value = mid * 100 * pos["qty"]
        change = bot.position_value / pos["entry_cost"] - 1
        bot.note = f"{pos['qty']}x {pos['label']} {change:+.0%}"
        if self.paused:
            return

        s = bot.spec
        now = self.market.now()
        today = now.date()
        if signal is not None and signal != pos["kind"]:
            bot.flip_since = bot.flip_since or now
        else:
            bot.flip_since = None
        flip_confirmed = bot.flip_since and now - bot.flip_since >= timedelta(minutes=s["flip_confirm_minutes"])
        to_earnings = days_to_earnings(bot, today)
        last_day_before = 3 if today.weekday() == 4 else 1  # Friday: Monday report is 3 days out
        if to_earnings is not None and 0 <= to_earnings <= last_day_before:
            reason = "earnings"
        elif change >= s["take_profit"]:
            reason = "take_profit"
        elif change <= -s["stop_loss"]:
            reason = "stop_loss"
        elif (date.fromisoformat(pos["expiration"]) - today).days <= s["exit_dte"]:
            reason = "expiring"
        elif flip_confirmed:
            reason = "thesis_broken"
        else:
            return
        self.close_position(bot, reason, quotes, mid)

    def close_position(self, bot, reason, quotes, mid):
        pos = bot.position
        # Start at the mid. Each unfilled try moves a quarter of the way to the price
        # that fills right away (sell at bid, buy back at ask), so exits can't get stuck.
        natural = sum(quotes[sym][0] if side == "long" else -quotes[sym][1] for sym, side in pos["legs"])
        step = min(bot.exit_attempts, 4) / 4
        limit = max(round_price(mid - step * (mid - natural), bot.symbol), 0.01)
        filled, price = self.market.submit(bot, pos["legs"], pos["qty"], limit, opening=False)
        if not filled:
            bot.exit_attempts += 1
            bot.note = f"{EXIT_LABELS[reason].lower()}: not filled, retrying"
            return
        proceeds = price * 100 * filled
        cost = pos["entry_cost"] * filled / pos["qty"]
        profit = proceeds - cost
        bot.cash += proceeds
        if filled < pos["qty"]:
            pos["qty"] -= filled
            pos["entry_cost"] -= cost
        else:
            bot.position = None
            bot.position_value = 0.0
            bot.exit_attempts = 0
            bot.flip_since = None
            bot.cooldown_until = self.market.now() + timedelta(minutes=bot.spec["cooldown_minutes"])
        bot.trades += 1
        bot.wins += profit > 0
        bot.note = f"{EXIT_LABELS[reason].lower()} {profit:+,.0f}"
        self.emit(bot, f"{EXIT_LABELS[reason]} {profit:+,.0f}", "profit" if profit > 0 else "loss")


class DemoMarket:
    """Simulated stocks and options so you can watch the bots without an account.

    Each tick is one market minute. Option prices come from Black-Scholes, so time
    decay is real: a position that goes nowhere loses value every simulated day.
    """

    name = "DEMO MODE - simulated prices and options, no account"
    interval = config.DEMO_TICK_SECONDS

    def __init__(self, bots, seed=None, start=None):
        self.rng = random.Random(seed)
        day = start or datetime.now(ET).date()
        while day.weekday() >= 5:
            day += timedelta(days=1)
        self.clock = datetime.combine(day, MARKET_OPEN)
        self.night_ticks = 0
        self.params = {s: config.DEMO_UNDERLYINGS[s] for s in sorted({b.symbol for b in bots})}
        self.history = {s: [p[0]] for s, p in self.params.items()}
        for _ in range(60 * config.SIGNAL_BAR_MINUTES):  # warm-up so signals have data from the start
            self._tick_prices()

    def _tick_prices(self):
        for symbol, prices in self.history.items():
            # Moves are as big as the options are priced for: no edge built in.
            sigma = self.params[symbol][1] / math.sqrt(252 * 390)
            prices.append(prices[-1] * math.exp(self.rng.gauss(0, sigma) - sigma * sigma / 2))
            del prices[:-100 * config.SIGNAL_BAR_MINUTES]

    def now(self):
        return self.clock

    def closes(self, symbol):
        return self.history[symbol]

    def _quote(self, underlying, expiration, kind, strike):
        _, iv, _, spread_pct, _ = self.params[underlying]
        years = (datetime.combine(expiration, MARKET_CLOSE) - self.clock).total_seconds() / (365 * 86400)
        value, delta = black_scholes(kind, self.history[underlying][-1], strike, years, iv)
        half = max(0.01, value * spread_pct / 2)
        return max(round(value - half, 2), 0.0), max(round(value + half, 2), 0.01), delta

    def chain(self, symbol, kind, min_dte, max_dte, price):
        _, _, step, _, daily = self.params[symbol]
        today = self.clock.date()
        strikes = [k * step for k in range(int(price * 0.94 / step), int(price * 1.06 / step) + 1)]
        contracts = []
        for days in range(min_dte, max_dte + 1):
            expiration = today + timedelta(days=days)
            if expiration.weekday() >= 5 or (not daily and expiration.weekday() != 4):
                continue
            for strike in strikes:
                bid, ask, delta = self._quote(symbol, expiration, kind, strike)
                contracts.append(Contract(occ_symbol(symbol, expiration, kind, strike), symbol,
                                          expiration, kind, strike, bid, ask, delta))
        return contracts

    def quotes(self, symbols):
        out = {}
        for symbol in symbols:
            bid, ask, _ = self._quote(*parse_occ(symbol))
            out[symbol] = (bid, ask)
        return out

    def submit(self, bot, legs, qty, limit, opening):
        return qty, limit  # demo fills every limit order in full at its price

    def step(self, engine):
        if self.night_ticks:
            # Overnight: a short pause between trading days so the 3D city shows night.
            self.night_ticks -= 1
            if not self.night_ticks:
                day = self.clock.date() + timedelta(days=1)
                while day.weekday() >= 5:
                    day += timedelta(days=1)
                self.clock = datetime.combine(day, MARKET_OPEN)
            engine.market_open = False
            engine.status = "Market closed - simulated night"
            return
        self.clock += timedelta(minutes=1)
        if self.clock.time() >= MARKET_CLOSE:
            self.night_ticks = config.DEMO_NIGHT_TICKS
            if self.night_ticks:
                engine.market_open = False
                engine.status = "Market closed - simulated night"
                return
            self.night_ticks = 1  # no pause configured: jump straight to the next open
            return self.step(engine)
        self._tick_prices()
        engine.market_open = True
        engine.status = f"Simulated time {self.clock:%a %b %d  %I:%M %p}"
        engine.trade_all()


class AlpacaMarket:
    """Real option quotes and paper orders on Alpaca. Never touches real money."""

    name = "ALPACA PAPER TRADING - real option prices, fake money"
    interval = config.CHECK_INTERVAL_SECONDS
    state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_state.json")
    FINAL = {"filled", "canceled", "expired", "rejected", "done_for_day", "stopped", "suspended"}

    def __init__(self, key, secret, trading=None, stocks=None, options=None):
        # Paper keys start with "PK"; live-money keys start with "AK". Refuse live ones
        # outright so a pasted wrong key can never trade real money.
        if not key.startswith("PK"):
            raise ValueError("ALPACA_API_KEY is not a paper-trading key (paper keys start with PK). "
                             "Use the keys from the Paper Trading dashboard.")
        if trading is None:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.historical.option import OptionHistoricalDataClient
            from alpaca.trading.client import TradingClient
            trading = TradingClient(key, secret, paper=True)
            stocks = StockHistoricalDataClient(key, secret)
            options = OptionHistoricalDataClient(key, secret)
        self.trading = trading
        self.stocks = stocks
        self.options = options
        self._closes = {}

    def now(self):
        return datetime.now(ET).replace(tzinfo=None)

    def closes(self, symbol):
        return self._closes.get(symbol, [])

    def latest_closes(self, symbol, count=100 * config.SIGNAL_BAR_MINUTES):
        from alpaca.common.enums import Sort
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=datetime.now(ET) - timedelta(days=10),
            limit=count,
            sort=Sort.DESC,
            feed=DataFeed.IEX,  # the free stock data feed
        )
        bars = self.stocks.get_stock_bars(request).data.get(symbol, [])
        return [float(b.close) for b in reversed(bars)]

    def chain(self, symbol, kind, min_dte, max_dte, price):
        from alpaca.data.enums import OptionsFeed
        from alpaca.data.requests import OptionChainRequest
        from alpaca.trading.enums import ContractType

        today = self.now().date()
        snapshots = self.options.get_option_chain(OptionChainRequest(
            underlying_symbol=symbol,
            type=ContractType.CALL if kind == "call" else ContractType.PUT,
            expiration_date_gte=today + timedelta(days=min_dte),
            expiration_date_lte=today + timedelta(days=max_dte),
            strike_price_gte=round(price * 0.94, 2),
            strike_price_lte=round(price * 1.06, 2),
            feed=OptionsFeed.INDICATIVE,  # the free options data feed
        ))
        contracts = []
        for occ, snap in snapshots.items():
            quote = snap.latest_quote
            if not quote or not quote.bid_price or not quote.ask_price:
                continue
            underlying, expiration, kind_, strike = parse_occ(occ)
            if snap.greeks and snap.greeks.delta is not None:
                delta = snap.greeks.delta
            elif snap.implied_volatility:
                years = max((expiration - today).days, 1) / 365
                delta = black_scholes(kind_, price, strike, years, snap.implied_volatility)[1]
            else:
                continue
            contracts.append(Contract(occ, underlying, expiration, kind_, strike,
                                      float(quote.bid_price), float(quote.ask_price), float(delta)))
        return contracts

    def quotes(self, symbols):
        from alpaca.data.enums import OptionsFeed
        from alpaca.data.requests import OptionLatestQuoteRequest

        latest = self.options.get_option_latest_quote(
            OptionLatestQuoteRequest(symbol_or_symbols=symbols, feed=OptionsFeed.INDICATIVE))
        return {s: (float(q.bid_price), float(q.ask_price)) for s, q in latest.items()
                if q.bid_price is not None and q.ask_price}

    def submit(self, bot, legs, qty, limit, opening):
        """Place a limit order, wait for it, cancel what doesn't fill. Returns (filled qty, price per unit)."""
        from alpaca.trading.enums import OrderClass, OrderSide, PositionIntent, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest, OptionLegRequest

        def leg_order(side):
            buying = (side == "long") == opening
            if opening:
                intent = PositionIntent.BUY_TO_OPEN if buying else PositionIntent.SELL_TO_OPEN
            else:
                intent = PositionIntent.BUY_TO_CLOSE if buying else PositionIntent.SELL_TO_CLOSE
            return (OrderSide.BUY if buying else OrderSide.SELL), intent

        client_id = f"vws-{uuid.uuid4().hex[:20]}"
        if len(legs) == 1:
            side, intent = leg_order(legs[0][1])
            request = LimitOrderRequest(symbol=legs[0][0], qty=qty, side=side, position_intent=intent,
                                        limit_price=limit, time_in_force=TimeInForce.DAY,
                                        client_order_id=client_id)
        else:
            request = LimitOrderRequest(
                order_class=OrderClass.MLEG, qty=qty, time_in_force=TimeInForce.DAY,
                # Spread price: positive = we pay (debit, opening), negative = we receive (credit, closing)
                limit_price=limit if opening else -limit,
                legs=[OptionLegRequest(symbol=sym, ratio_qty=1, side=leg_order(side)[0],
                                       position_intent=leg_order(side)[1]) for sym, side in legs],
                client_order_id=client_id)
        order = self.trading.submit_order(request)
        deadline = time.monotonic() + config.FILL_WAIT_SECONDS
        while _value(order.status) not in self.FINAL and time.monotonic() < deadline:
            time.sleep(1)
            order = self.trading.get_order_by_id(order.id)
        if _value(order.status) not in self.FINAL:
            self.trading.cancel_order_by_id(order.id)
            for _ in range(10):
                order = self.trading.get_order_by_id(order.id)
                if _value(order.status) in self.FINAL:
                    break
                time.sleep(0.5)
        filled = int(float(order.filled_qty or 0))
        if not filled or not order.filled_avg_price:
            return 0, None
        return filled, abs(float(order.filled_avg_price))

    def step(self, engine):
        engine.equity = float(self.trading.get_account().equity)
        self._closes = {s: self.latest_closes(s) for s in {b.symbol for b in engine.bots}}
        clock = self.trading.get_clock()
        engine.market_open = bool(clock.is_open)
        if not clock.is_open:
            engine.status = f"Market closed - opens {clock.next_open:%a %b %d %I:%M %p} ET"
            for bot in engine.bots:
                bot.note = "market closed"
            return
        engine.status = f"Market open - checking every {self.interval}s"
        if engine.news:
            try:
                engine.news.refresh(self.now())
                engine.news_error = ""
            except Exception as e:  # a news problem shouldn't stop trading
                engine.news_error = f"News: {type(e).__name__}: {e}"[:140]
        engine.trade_all()


def _value(enum_or_str):
    return getattr(enum_or_str, "value", enum_or_str)
