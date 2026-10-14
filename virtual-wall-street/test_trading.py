"""Run with:  python -m unittest test_trading.py"""

import json
import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest import mock

import config
from engine import AlpacaMarket, Bot, DemoMarket, Engine, make_bots
from news import ClaudeJudge, Headline, NewsWatcher
from options import Contract, black_scholes, occ_symbol, parse_occ, pick_single, pick_spread, round_price
from strategies import mean_reversion, momentum, rsi, sma_crossover

TODAY = date(2026, 10, 13)  # a Tuesday
EXP = TODAY + timedelta(days=17)
UP = [100 + i * 0.5 for i in range(60)]
DOWN = [130 - i * 0.5 for i in range(60)]
# Same shapes as one-minute closes, for the engine (which reads every 15th close)
UP_MIN = [100 + i * 0.5 / 15 for i in range(60 * 15)]
DOWN_MIN = [130 - i * 0.5 / 15 for i in range(60 * 15)]


class SignalTests(unittest.TestCase):
    def test_not_enough_data(self):
        for signal in (sma_crossover, momentum, mean_reversion):
            self.assertIsNone(signal([100.0] * 5))

    def test_directions(self):
        self.assertEqual(sma_crossover(UP), "call")
        self.assertEqual(sma_crossover(DOWN), "put")
        self.assertEqual(momentum(UP), "call")
        self.assertEqual(momentum(DOWN), "put")
        self.assertIsNone(momentum([100.0] * 30))
        self.assertLess(rsi(DOWN), 30)
        self.assertEqual(mean_reversion(DOWN), "call")  # bets on a bounce
        self.assertEqual(mean_reversion(UP), "put")


class OptionMathTests(unittest.TestCase):
    def test_occ_round_trip(self):
        symbol = occ_symbol("QQQ", date(2026, 10, 30), "call", 512.5)
        self.assertEqual(symbol, "QQQ261030C00512500")
        self.assertEqual(parse_occ(symbol), ("QQQ", date(2026, 10, 30), "call", 512.5))

    def test_black_scholes_sanity(self):
        call, call_delta = black_scholes("call", 100, 100, 30 / 365, 0.2)
        put, put_delta = black_scholes("put", 100, 100, 30 / 365, 0.2)
        self.assertAlmostEqual(call_delta, 0.54, places=1)
        self.assertAlmostEqual(put_delta, -0.46, places=1)
        self.assertGreater(call, put)  # put-call parity with positive rates

    def test_round_price(self):
        self.assertEqual(round_price(5.123, "QQQ"), 5.12)
        self.assertEqual(round_price(5.12, "AMD"), 5.10)
        self.assertEqual(round_price(2.123, "AMD"), 2.12)


def contract(strike, mid, delta, kind="call", exp=EXP, spread=0.10):
    return Contract(occ_symbol("QQQ", exp, kind, strike), "QQQ", exp, kind, strike,
                    mid - spread / 2, mid + spread / 2, delta)


CHAIN = [contract(495, 9.0, 0.62), contract(500, 6.0, 0.51), contract(502, 5.2, 0.47),
         contract(505, 4.0, 0.40), contract(510, 2.0, 0.25)]


class PickTests(unittest.TestCase):
    def test_single_prefers_half_delta(self):
        pick, why = pick_single(CHAIN, TODAY, 0.40, 0.60, 1000)
        self.assertEqual(pick.strike, 500)

    def test_single_too_expensive(self):
        pick, why = pick_single(CHAIN, TODAY, 0.40, 0.60, 300)
        self.assertIsNone(pick)
        self.assertIn("$400", why)

    def test_single_bent_rules_finds_cheap_contract(self):
        pick, _ = pick_single(CHAIN, TODAY, 0.20, 0.60, 300)
        self.assertEqual(pick.strike, 510)

    def test_spread_fits_small_budget(self):
        (long, short), why = pick_spread(CHAIN, TODAY, 0.40, 0.60, [5, 2], 250)
        self.assertEqual((long.strike, short.strike), (500, 505))  # $200 debit, max profit $300

    def test_spread_falls_back_to_narrower_width(self):
        (long, short), _ = pick_spread(CHAIN, TODAY, 0.40, 0.60, [5, 2], 100)
        self.assertEqual((long.strike, short.strike), (500, 502))  # $80 debit

    def test_put_spread_goes_down(self):
        puts = [contract(500, 6.0, -0.50, "put"), contract(495, 4.0, -0.38, "put")]
        (long, short), _ = pick_spread(puts, TODAY, 0.40, 0.60, [5], 300)
        self.assertEqual((long.strike, short.strike), (500, 495))


class FakeMarket:
    """Scripted market: you set the signal prices and option quotes."""

    name = "fake"
    interval = 0

    def __init__(self, closes, chain):
        self.closes_ = closes
        self.chain_ = chain
        self.clock = datetime(2026, 10, 13, 11, 0)
        self.orders = []
        self.fill = True

    def now(self):
        return self.clock

    def closes(self, symbol):
        return self.closes_

    def chain(self, symbol, kind, min_dte, max_dte, price):
        return [c for c in self.chain_ if c.kind == kind]

    def quotes(self, symbols):
        by_symbol = {c.symbol: (c.bid, c.ask) for c in self.chain_}
        return {s: by_symbol[s] for s in symbols if s in by_symbol}

    def submit(self, bot, legs, qty, limit, opening):
        self.orders.append((legs, qty, limit, opening))
        return (qty, limit) if self.fill else (0, None)

    def set_mid(self, strike, mid):
        for c in self.chain_:
            if c.strike == strike:
                c.bid, c.ask = mid - 0.05, mid + 0.05


def spread_bot(**extra):
    return Bot({"name": "T", "symbol": "QQQ", "signal": "momentum", "style": "spread",
                "widths": [5], "budget": 300, "risk_pct": 0.8, "max_loss_pct": 1.0, **extra})


class EngineRuleTests(unittest.TestCase):
    def setUp(self):
        self.market = FakeMarket(UP_MIN, [contract(c.strike, c.mid, c.delta) for c in CHAIN])
        self.bot = spread_bot()
        self.engine = Engine(self.market, [self.bot])

    def test_opens_spread_at_mid_with_limit(self):
        self.engine.trade_all()
        legs, qty, limit, opening = self.market.orders[0]
        self.assertTrue(opening)
        self.assertEqual([side for _, side in legs], ["long", "short"])
        self.assertEqual((qty, limit), (1, 2.0))
        self.assertEqual(self.bot.cash, 100)
        self.assertEqual(self.engine.events.get_nowait()[2], "call")

    def test_take_profit(self):
        self.engine.trade_all()
        self.market.set_mid(500, 8.0)  # spread worth 8 - 4 = 4.00, +100%
        self.engine.trade_all()
        self.assertIsNone(self.bot.position)
        self.assertAlmostEqual(self.bot.pnl, 200)
        self.assertEqual(self.bot.wins, 1)

    def test_stop_loss(self):
        self.engine.trade_all()
        self.market.set_mid(500, 5.0)  # spread worth 1.00, -50%
        self.engine.trade_all()
        self.assertIsNone(self.bot.position)
        self.assertAlmostEqual(self.bot.pnl, -100)

    def test_signal_flip_exits(self):
        self.engine.trade_all()
        self.market.closes_ = DOWN_MIN
        self.engine.trade_all()
        self.assertIsNotNone(self.bot.position, "one flip isn't enough")
        self.market.clock += timedelta(minutes=119)
        self.engine.trade_all()
        self.assertIsNotNone(self.bot.position)
        self.market.clock += timedelta(minutes=1)  # opposite signal held for 2 hours
        self.engine.trade_all()
        self.assertIsNone(self.bot.position)
        self.assertIn("SIGNAL FLIP", list(self.engine.events.queue)[-1][1])

    def test_cooldown_blocks_reentry(self):
        self.engine.trade_all()
        self.market.set_mid(500, 8.0)
        self.engine.trade_all()
        self.engine.trade_all()
        self.assertIsNone(self.bot.position)
        self.market.clock += timedelta(minutes=31)
        self.engine.trade_all()
        self.assertIsNotNone(self.bot.position)

    def test_unfilled_exit_gets_more_aggressive(self):
        self.engine.trade_all()
        self.market.set_mid(500, 8.0)
        self.market.fill = False
        self.engine.trade_all()
        self.engine.trade_all()
        first, second = self.market.orders[1][2], self.market.orders[2][2]
        self.assertLess(second, first)  # closer to the bid each retry
        self.assertIsNotNone(self.bot.position)

    def test_no_entries_right_after_open(self):
        self.market.clock = datetime(2026, 10, 13, 9, 35)
        self.engine.trade_all()
        self.assertEqual(self.market.orders, [])

    def test_time_stop_before_expiration(self):
        self.engine.trade_all()
        self.market.clock += timedelta(days=12)  # 5 days left
        self.engine.trade_all()
        self.assertIsNone(self.bot.position)

    def test_earnings_blackout_and_forced_exit(self):
        bot = spread_bot(earnings="2026-10-16", blackout_days=5)
        engine = Engine(self.market, [bot])
        engine.trade_all()
        self.assertIsNone(bot.position)
        self.assertEqual(bot.note, "earnings blackout")
        # Holding into the day before the report forces an exit.
        bot2 = spread_bot(earnings="2026-10-20", blackout_days=5)
        engine2 = Engine(self.market, [bot2])
        engine2.trade_all()
        self.assertIsNotNone(bot2.position)
        self.market.clock = datetime(2026, 10, 16, 11, 0)  # Friday before a Tuesday report: still holds
        engine2.trade_all()
        self.assertIsNotNone(bot2.position)
        self.market.clock = datetime(2026, 10, 19, 11, 0)  # Monday, the day before; 11 days to expiration
        engine2.trade_all()
        self.assertIsNone(bot2.position)
        self.assertIn("PRE-EARNINGS", list(engine2.events.queue)[-1][1])

    def test_loss_limit_caps_trade_size(self):
        bot = spread_bot(max_loss_pct=0.5)  # may lose at most $150
        self.market.chain_.append(contract(503, 4.6, 0.44))
        bot.spec["widths"] = [5, 3]
        Engine(self.market, [bot]).trade_all()
        self.assertLessEqual(bot.position["entry_cost"], 150)  # $200 spread skipped for a cheaper one

    def test_loss_limit_stops_bot_even_if_every_trade_goes_to_zero(self):
        bot = spread_bot(max_loss_pct=0.5, widths=[5, 2])
        engine = Engine(self.market, [bot])
        for _ in range(10):
            engine.trade_all()
            if bot.position:
                for c in self.market.chain_:
                    c.bid, c.ask = 0.0, 0.05  # wipe out: worth nothing
                engine.trade_all()
                self.market.chain_ = [contract(c.strike, c.mid, c.delta) for c in CHAIN]
                self.market.clock += timedelta(hours=1)
        self.assertGreaterEqual(bot.pnl, -150 - 1e-9)
        self.assertIsNone(bot.position)
        engine.trade_all()
        self.assertIsNone(bot.position, "no trade fits in the room left")

    def test_stopped_at_limit(self):
        bot = spread_bot(max_loss_pct=0.5)
        bot.cash = 150  # already lost $150 of $300
        Engine(self.market, [bot]).trade_all()
        self.assertIsNone(bot.position)
        self.assertIn("STOPPED", bot.note)

    def test_too_expensive_skips(self):
        bot = spread_bot(budget=50)
        Engine(self.market, [bot]).trade_all()
        self.assertIsNone(bot.position)
        self.assertIn("too pricey", bot.note)


class DemoTests(unittest.TestCase):
    def test_demo_has_a_night_after_the_close(self):
        bots = make_bots()
        market = DemoMarket(bots, seed=1, start=TODAY)
        engine = Engine(market, bots)
        market.step(engine)
        self.assertTrue(engine.market_open)
        for _ in range(389):
            market.step(engine)
        self.assertFalse(engine.market_open, "4:00 PM: market closed")
        events = engine.events.qsize()
        for _ in range(config.DEMO_NIGHT_TICKS - 1):
            market.step(engine)
            self.assertFalse(engine.market_open)
        self.assertEqual(engine.events.qsize(), events, "no trading at night")
        market.step(engine)  # night over: jumps to the next morning
        market.step(engine)
        self.assertTrue(engine.market_open)
        self.assertEqual(market.clock.date(), TODAY + timedelta(days=1))

    def test_demo_runs_a_simulated_week(self):
        bots = make_bots()
        market = DemoMarket(bots, seed=3, start=TODAY)
        engine = Engine(market, bots)
        for _ in range(390 * 5):
            market.step(engine)
        events = list(engine.events.queue)
        self.assertTrue(any(kind in ("call", "put") for _, _, kind in events), "bots should open trades")
        self.assertTrue(any(kind in ("profit", "loss") for _, _, kind in events), "bots should close trades")
        for bot in bots:
            self.assertGreaterEqual(bot.cash, -1e-9, f"{bot.name} spent money it doesn't have")
        rules = next(b for b in bots if b.name == "By the Rules")
        for _, text, kind in events:
            if _ is rules and kind in ("call", "put"):
                cost = float(text.split("-$")[1].replace(",", ""))
                self.assertLessEqual(cost, 50000 * 0.03 * 1.5)


class FakeAlpaca:
    """Stands in for the three Alpaca clients."""

    def __init__(self, today):
        self.today = today
        self.requests = []
        self.is_open = True
        exp = today + timedelta(days=17)
        self.snapshots = {}
        for strike, mid, delta in ((500, 6.0, 0.51), (505, 4.0, 0.40)):
            self.snapshots[occ_symbol("QQQ", exp, "call", strike)] = SimpleNamespace(
                latest_quote=SimpleNamespace(bid_price=mid - 0.05, ask_price=mid + 0.05),
                greeks=SimpleNamespace(delta=delta), implied_volatility=0.2)

    def get_account(self):
        return SimpleNamespace(equity="100000.00")

    def get_clock(self):
        return SimpleNamespace(is_open=self.is_open, next_open=datetime(2026, 10, 14, 9, 30))

    def get_stock_bars(self, request):
        bars = [SimpleNamespace(close=c) for c in reversed(UP_MIN)]
        return SimpleNamespace(data={request.symbol_or_symbols: bars})

    def get_option_chain(self, request):
        assert request.feed.value == "indicative"
        return self.snapshots if request.type.value == "call" else {}

    def get_option_latest_quote(self, request):
        return {s: self.snapshots[s].latest_quote for s in request.symbol_or_symbols}

    def submit_order(self, request):
        self.requests.append(request)
        return SimpleNamespace(id="1", status="filled", filled_qty=str(request.qty),
                               filled_avg_price=str(request.limit_price))


class AlpacaTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeAlpaca(TODAY)
        self.tmp = tempfile.TemporaryDirectory()
        patcher = mock.patch.object(AlpacaMarket, "state_path", os.path.join(self.tmp.name, "state.json"))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def make(self):
        market = AlpacaMarket("PKTEST", "secret", trading=self.fake, stocks=self.fake, options=self.fake)
        market.now = lambda: datetime(2026, 10, 13, 11, 0)
        bot = spread_bot()
        return market, bot, Engine(market, [bot])

    def test_refuses_live_keys(self):
        with self.assertRaises(ValueError):
            AlpacaMarket("AKLIVEKEY", "secret", trading=object())

    def test_spread_order_is_a_multileg_limit_debit(self):
        market, bot, engine = self.make()
        market.step(engine)
        request = self.fake.requests[0]
        self.assertEqual(request.order_class.value, "mleg")
        self.assertEqual(request.type.value, "limit")
        self.assertEqual(request.limit_price, 2.0)  # positive = debit
        self.assertEqual([(l.side.value, l.position_intent.value) for l in request.legs],
                         [("buy", "buy_to_open"), ("sell", "sell_to_open")])
        self.assertEqual(bot.cash, 100)

    def test_closing_is_a_credit_and_state_survives_restart(self):
        market, bot, engine = self.make()
        market.step(engine)
        engine.save()
        market2, bot2, engine2 = self.make()  # restart: loads bot_state.json
        self.assertEqual(bot2.position["label"], "500/505C 10/30")
        quote = self.fake.snapshots[bot2.position["legs"][0][0]].latest_quote
        quote.bid_price, quote.ask_price = 7.95, 8.05  # +100%
        market2.step(engine2)
        close = self.fake.requests[-1]
        self.assertEqual(close.limit_price, -4.0)  # negative = credit
        self.assertEqual([l.position_intent.value for l in close.legs], ["sell_to_close", "buy_to_close"])
        self.assertIsNone(bot2.position)

    def test_single_contract_order(self):
        market, _, _ = self.make()
        bot = Bot({"name": "S", "symbol": "QQQ", "signal": "momentum", "style": "single",
                   "budget": 50000, "risk_pct": 0.03})
        engine = Engine(market, [bot])
        market.step(engine)
        request = self.fake.requests[0]
        self.assertEqual((request.side.value, request.position_intent.value), ("buy", "buy_to_open"))
        self.assertEqual((request.qty, request.limit_price), (2, 6.0))  # 2 x $600 within $1,500

    def test_order_that_went_through_despite_a_timeout_is_recorded_once(self):
        market, bot, engine = self.make()
        placed = {}
        real_submit = self.fake.submit_order

        def flaky_submit(request):
            placed[request.client_order_id] = real_submit(request)
            raise TimeoutError("Read timed out")  # Alpaca got it, but the reply was lost

        self.fake.submit_order = flaky_submit
        self.fake.get_order_by_client_id = lambda cid: placed[cid]
        with mock.patch("engine.time.sleep"):
            market.step(engine)
        self.assertEqual(len(placed), 1)
        self.assertIsNotNone(bot.position)
        self.assertEqual(bot.cash, 100)

    def test_order_that_never_arrived_is_not_recorded(self):
        market, bot, engine = self.make()

        def failing_submit(request):
            raise TimeoutError("Read timed out")

        def not_found(cid):
            raise LookupError("order not found")

        self.fake.submit_order = failing_submit
        self.fake.get_order_by_client_id = not_found
        with mock.patch("engine.time.sleep"):
            with self.assertRaises(TimeoutError):
                market.step(engine)
        self.assertIsNone(bot.position)
        self.assertEqual(bot.cash, 300)

    def test_market_closed_places_no_orders(self):
        self.fake.is_open = False
        market, bot, engine = self.make()
        market.step(engine)
        self.assertEqual(self.fake.requests, [])
        self.assertIn("Market closed", engine.status)
        self.assertFalse(engine.market_open)


class FakeFeed:
    def __init__(self):
        self.items = []

    def fetch(self, symbols, since):
        return [i for i in self.items if i.published >= since]


class FakeClaude:
    """Stands in for anthropic.Anthropic(): answers with a scripted verdict."""

    def __init__(self, verdict=None, refuse=False):
        self.verdict = verdict or {"direction": "up", "strength": "notable", "reason": "Upgrade."}
        self.refuse = refuse
        self.requests = []
        self.messages = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(
            stop_reason="refusal" if self.refuse else "end_turn",
            content=[] if self.refuse else [SimpleNamespace(type="text", text=json.dumps(self.verdict))],
            usage=SimpleNamespace(input_tokens=300, output_tokens=200))


NOON = datetime(2026, 10, 13, 12, 0)


def headline(text, symbols=("AMD",), minutes_ago=10, id_="1"):
    return Headline(id_, text, "", list(symbols), NOON - timedelta(minutes=minutes_ago))


class NewsTests(unittest.TestCase):
    def watcher(self, **verdict):
        feed = FakeFeed()
        claude = FakeClaude({"direction": "up", "strength": "notable", "reason": "r", **verdict})
        return feed, claude, NewsWatcher(feed, ClaudeJudge(client=claude), ["AMD", "QQQ"])

    def test_judge_request_and_cost(self):
        feed, claude, watcher = self.watcher()
        feed.items = [headline("AMD wins big contract")]
        watcher.refresh(NOON)
        request = claude.requests[0]
        self.assertEqual(request["model"], "claude-haiku-5-5")
        self.assertEqual(request["output_config"]["effort"], "low")
        self.assertEqual(request["output_config"]["format"]["type"], "json_schema")
        self.assertIn("Ticker: AMD", request["messages"][0]["content"])
        self.assertAlmostEqual(watcher.judge.spent, 300 * 0.10 / 1e6 + 200 * 0.50 / 1e6)
        self.assertEqual(watcher.latest("AMD").direction, "up")

    def test_each_headline_judged_once_per_symbol(self):
        feed, claude, watcher = self.watcher()
        feed.items = [headline("Chip stocks rally", symbols=("AMD", "QQQ", "NVDA"))]
        watcher.refresh(NOON)
        watcher.refresh(NOON + timedelta(minutes=1))
        self.assertEqual(len(claude.requests), 2)  # AMD and QQQ, not NVDA, and not again

    def test_refusal_is_skipped(self):
        feed = FakeFeed()
        feed.items = [headline("Something")]
        watcher = NewsWatcher(feed, ClaudeJudge(client=FakeClaude(refuse=True)), ["AMD"])
        watcher.refresh(NOON)
        self.assertEqual(watcher.verdicts, [])

    def test_daily_cap(self):
        feed, claude, watcher = self.watcher()
        feed.items = [headline(f"h{i}", id_=str(i)) for i in range(5)]
        with mock.patch.dict(config.NEWS, max_headlines_per_day=3):
            watcher.refresh(NOON)
        self.assertEqual(len(claude.requests), 3)

    def test_signal_needs_price_confirmation(self):
        feed, _, watcher = self.watcher()
        feed.items = [headline("AMD upgraded")]
        watcher.refresh(NOON)
        self.assertEqual(watcher.signal("AMD", UP_MIN, NOON), "call")
        self.assertIsNone(watcher.signal("AMD", DOWN_MIN, NOON), "price moving against the news")
        self.assertIsNone(watcher.signal("AMD", UP_MIN, NOON + timedelta(minutes=61)), "headline too old")

    def test_minor_news_is_ignored(self):
        feed, _, watcher = self.watcher(strength="minor")
        feed.items = [headline("AMD mentioned in a roundup")]
        watcher.refresh(NOON)
        self.assertIsNone(watcher.signal("AMD", UP_MIN, NOON))
        self.assertIsNone(watcher.blocked("AMD", NOON))

    def test_major_news_blocks_other_bots_but_not_news_bot(self):
        feed, _, watcher = self.watcher(strength="major")
        feed.items = [headline("AMD guidance shock")]
        watcher.refresh(NOON)
        market = FakeMarket(UP_MIN, [contract(c.strike, c.mid, c.delta) for c in CHAIN])
        market.clock = NOON
        other = spread_bot(symbol="AMD")
        news_bot = Bot({"name": "News", "symbol": "AMD", "signal": "news", "style": "spread",
                        "widths": [5], "budget": 300, "risk_pct": 0.8, "max_loss_pct": 1.0})
        engine = Engine(market, [other, news_bot], watcher)
        engine.trade_all()
        self.assertIsNone(other.position)
        self.assertEqual(other.note, "major news, waiting")
        self.assertEqual(news_bot.position["kind"], "call")
        market.clock = NOON + timedelta(minutes=31)  # block over
        engine.trade_all()
        self.assertIsNotNone(other.position)

    def test_news_bot_idle_without_news(self):
        market = FakeMarket(UP_MIN, list(CHAIN))
        bot = Bot({"name": "News", "symbol": "AMD", "signal": "news", "style": "spread",
                   "widths": [5], "budget": 300, "risk_pct": 0.8})
        Engine(market, [bot]).trade_all()
        self.assertIsNone(bot.position)
        self.assertIn("news off", bot.note)

    def test_news_failure_does_not_stop_trading(self):
        fake = FakeAlpaca(TODAY)
        with mock.patch.object(AlpacaMarket, "state_path", None):
            market = AlpacaMarket("PKTEST", "secret", trading=fake, stocks=fake, options=fake)
            market.now = lambda: datetime(2026, 10, 13, 11, 0)
            broken = SimpleNamespace(refresh=mock.Mock(side_effect=RuntimeError("bad key")),
                                     blocked=lambda *a: None)
            bot = spread_bot()
            engine = Engine(market, [bot], broken)
            market.step(engine)
        self.assertIn("bad key", engine.news_error)
        self.assertIsNotNone(bot.position)


if __name__ == "__main__":
    unittest.main()
