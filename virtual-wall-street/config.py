"""Settings you can change without touching the rest of the code."""

# One building per bot. Each bot runs one strategy (see strategies.py) on one symbol.
# All five trade SPY by default so you compare strategies on the same stock;
# Buy & Hold is the benchmark the others need to beat.
BOTS = [
    {"name": "Crossover", "symbol": "SPY", "strategy": "sma_crossover"},
    {"name": "Momentum", "symbol": "SPY", "strategy": "momentum"},
    {"name": "Reversion", "symbol": "SPY", "strategy": "mean_reversion"},
    {"name": "Breakout", "symbol": "SPY", "strategy": "breakout"},
    {"name": "Buy&Hold", "symbol": "SPY", "strategy": "buy_and_hold"},
]

# Dollars each bot spends on one buy (fake money in paper trading).
TRADE_DOLLARS = 1000

# Alpaca mode: how often bots check prices and decide whether to trade.
# Strategies work on 1-minute bars, so checking more often than this adds nothing.
CHECK_INTERVAL_SECONDS = 60

# Demo mode (no Alpaca keys): seconds between simulated price ticks.
DEMO_TICK_SECONDS = 0.5
