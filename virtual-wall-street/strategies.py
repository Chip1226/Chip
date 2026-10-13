"""Trading strategies.

Each strategy looks at a list of recent closing prices (oldest first) and
whether the bot currently holds shares, and returns "buy", "sell" or None.
Bots only ever go long: they buy, hold, then sell back to cash. No shorting.
"""


def sma(prices, n):
    return sum(prices[-n:]) / n


def sma_crossover(prices, holding, fast=10, slow=30):
    """Buy when the short average rises above the long one, sell when it drops below."""
    if len(prices) < slow:
        return None
    fast_avg, slow_avg = sma(prices, fast), sma(prices, slow)
    if not holding and fast_avg > slow_avg:
        return "buy"
    if holding and fast_avg < slow_avg:
        return "sell"
    return None


def momentum(prices, holding, lookback=20):
    """Buy when price is higher than `lookback` bars ago, sell when it's lower."""
    if len(prices) <= lookback:
        return None
    change = prices[-1] - prices[-1 - lookback]
    if not holding and change > 0:
        return "buy"
    if holding and change < 0:
        return "sell"
    return None


def rsi(prices, n=14):
    gains = losses = 0.0
    for prev, cur in zip(prices[-n - 1:-1], prices[-n:]):
        diff = cur - prev
        if diff > 0:
            gains += diff
        else:
            losses -= diff
    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100 - 100 / (1 + rs)


def mean_reversion(prices, holding, n=14, oversold=30, overbought=70):
    """Buy after a sharp drop (RSI oversold), sell after a sharp rise (RSI overbought)."""
    if len(prices) <= n:
        return None
    value = rsi(prices, n)
    if not holding and value < oversold:
        return "buy"
    if holding and value > overbought:
        return "sell"
    return None


def breakout(prices, holding, entry=20, exit=10):
    """Buy when price beats its recent high, sell when it falls below its recent low."""
    if len(prices) <= entry:
        return None
    price = prices[-1]
    if not holding and price > max(prices[-1 - entry:-1]):
        return "buy"
    if holding and price < min(prices[-1 - exit:-1]):
        return "sell"
    return None


def buy_and_hold(prices, holding):
    """Buy once and never sell. The benchmark every other bot has to beat."""
    if not holding and prices:
        return "buy"
    return None


STRATEGIES = {
    "sma_crossover": sma_crossover,
    "momentum": momentum,
    "mean_reversion": mean_reversion,
    "breakout": breakout,
    "buy_and_hold": buy_and_hold,
}
