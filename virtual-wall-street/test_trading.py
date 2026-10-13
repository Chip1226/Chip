"""Run with:  python -m unittest test_trading.py"""

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import config
from engine import AlpacaMarket, Bot, DemoMarket, Engine, make_bots
from strategies import breakout, buy_and_hold, mean_reversion, momentum, rsi, sma_crossover


class StrategyTests(unittest.TestCase):
    def test_not_enough_data_does_nothing(self):
        for strategy in (sma_crossover, momentum, mean_reversion, breakout):
            self.assertIsNone(strategy([100.0] * 5, False))

    def test_sma_crossover(self):
        rising = [100 + i for i in range(40)]
        falling = [140 - i for i in range(40)]
        self.assertEqual(sma_crossover(rising, False), "buy")
        self.assertIsNone(sma_crossover(rising, True))
        self.assertEqual(sma_crossover(falling, True), "sell")

    def test_momentum(self):
        self.assertEqual(momentum([100 + i for i in range(30)], False), "buy")
        self.assertEqual(momentum([130 - i for i in range(30)], True), "sell")

    def test_mean_reversion(self):
        self.assertLess(rsi([100 - i for i in range(20)]), 30)
        self.assertEqual(mean_reversion([100 - i for i in range(20)], False), "buy")
        self.assertEqual(mean_reversion([100 + i for i in range(20)], True), "sell")

    def test_breakout(self):
        self.assertEqual(breakout([100.0] * 25 + [101.0], False), "buy")
        self.assertEqual(breakout([100.0] * 25 + [99.0], True), "sell")

    def test_buy_and_hold_never_sells(self):
        self.assertEqual(buy_and_hold([100.0], False), "buy")
        self.assertIsNone(buy_and_hold([1.0], True))


class BotTests(unittest.TestCase):
    def test_round_trip_profit(self):
        bot = Bot("Test", "SPY", "momentum")
        self.assertIsNone(bot.record_fill("buy", 10, 100))
        bot.price = 110
        self.assertAlmostEqual(bot.pnl, 100)
        self.assertAlmostEqual(bot.record_fill("sell", 10, 110), 100)
        self.assertFalse(bot.holding)
        self.assertAlmostEqual(bot.pnl, 100)

    def test_partial_sell_keeps_cost_basis_proportional(self):
        bot = Bot("Test", "SPY", "momentum")
        bot.record_fill("buy", 10, 100)
        self.assertAlmostEqual(bot.record_fill("sell", 4, 90), -40)
        self.assertAlmostEqual(bot.cost_basis, 600)


class DemoMarketTests(unittest.TestCase):
    def test_runs_and_pnl_matches_trades(self):
        bots = make_bots()
        market = DemoMarket(bots, seed=1)
        engine = Engine(market, bots)
        for _ in range(500):
            market.step(engine)
        self.assertFalse(engine.events.empty(), "bots should have traded")
        for bot in bots:
            self.assertIsNotNone(bot.price)
        buy_and_hold_bot = next(b for b in bots if b.strategy_name == "buy_and_hold")
        self.assertTrue(buy_and_hold_bot.holding)

    def test_paused_does_not_trade(self):
        bots = make_bots()
        market = DemoMarket(bots, seed=1)
        engine = Engine(market, bots)
        engine.paused = True
        for _ in range(100):
            market.step(engine)
        self.assertTrue(engine.events.empty())


class FakeAlpaca:
    """Stands in for both Alpaca clients. Fills every market order instantly."""

    def __init__(self, closes, is_open=True):
        self.closes = closes
        self.is_open = is_open
        self.orders = []
        self.requests = []

    def get_account(self):
        return SimpleNamespace(equity="100000.00")

    def get_clock(self):
        return SimpleNamespace(is_open=self.is_open, next_open=datetime(2026, 10, 14, 9, 30))

    def get_stock_bars(self, request):
        assert request.sort.value == "desc" and request.feed.value == "iex"
        bars = [SimpleNamespace(close=c) for c in reversed(self.closes)]
        return SimpleNamespace(data={request.symbol_or_symbols: bars})

    def get_orders(self, request):
        return sorted(self.orders, key=lambda o: o.submitted_at, reverse=True)[:request.limit]

    def submit_order(self, request):
        self.requests.append(request)
        price = self.closes[-1]
        qty = request.notional / price if request.notional else request.qty
        order = SimpleNamespace(
            id=str(len(self.orders)), client_order_id=request.client_order_id, status="filled",
            side=request.side, filled_qty=str(qty), filled_avg_price=str(price),
            submitted_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=len(self.orders)))
        self.orders.append(order)
        return order


class AlpacaMarketTests(unittest.TestCase):
    def setUp(self):
        self.bots = [Bot("Buy&Hold", "SPY", "buy_and_hold"), Bot("Momentum", "SPY", "momentum")]

    def make(self, fake):
        market = AlpacaMarket("PKTEST", "secret", trading=fake, data=fake)
        return market, Engine(market, self.bots)

    def test_refuses_live_keys(self):
        with self.assertRaises(ValueError):
            AlpacaMarket("AKLIVEKEY", "secret", trading=object(), data=object())

    def test_buys_with_notional_and_tags_orders(self):
        fake = FakeAlpaca([100 + i for i in range(100)])
        market, engine = self.make(fake)
        market.step(engine)
        self.assertEqual(len(fake.requests), 2)
        for request, bot in zip(fake.requests, self.bots):
            self.assertEqual(request.notional, config.TRADE_DOLLARS)
            self.assertTrue(request.client_order_id.startswith(bot.order_prefix))
            self.assertTrue(bot.holding)
        self.assertEqual(engine.equity, 100000.0)

    def test_restart_rebuilds_positions_from_order_history(self):
        fake = FakeAlpaca([100 + i for i in range(100)])
        market, engine = self.make(fake)
        market.step(engine)
        # Prices drop: momentum sells, buy & hold keeps its shares.
        fake.closes = [300 - i for i in range(100)]
        fresh_bots = [Bot(b.name, b.symbol, b.strategy_name) for b in self.bots]
        market2 = AlpacaMarket("PKTEST", "secret", trading=fake, data=fake)
        engine2 = Engine(market2, fresh_bots)
        market2.step(engine2)
        hold, mom = fresh_bots
        self.assertTrue(hold.holding)
        self.assertFalse(mom.holding)
        self.assertEqual(fake.requests[-1].side.value, "sell")
        self.assertLessEqual(fake.requests[-1].qty, 1000 / 199)
        self.assertEqual(len(fake.requests), 3, "buy & hold must not buy twice after a restart")

    def test_market_closed_places_no_orders(self):
        fake = FakeAlpaca([100 + i for i in range(100)], is_open=False)
        market, engine = self.make(fake)
        market.step(engine)
        self.assertEqual(fake.requests, [])
        self.assertIn("Market closed", engine.status)


if __name__ == "__main__":
    unittest.main()
