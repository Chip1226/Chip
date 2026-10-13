"""Direction signals.

Each signal looks at recent closing prices of the stock (oldest first) and says
which way it expects the price to go: "call" (up), "put" (down), or None (no view).
The bot buys calls on "call" and puts on "put". If the signal flips the other way
while a trade is open, the reason for the trade is broken and the bot exits.
"""


def sma(prices, n):
    return sum(prices[-n:]) / n


def sma_crossover(prices, fast=10, slow=30):
    """Up when the short-term average is above the long-term one, down when below."""
    if len(prices) < slow:
        return None
    fast_avg, slow_avg = sma(prices, fast), sma(prices, slow)
    if fast_avg > slow_avg:
        return "call"
    if fast_avg < slow_avg:
        return "put"
    return None


def momentum(prices, lookback=20, min_move=0.002):
    """Up if the price rose more than 0.2% over the last `lookback` bars, down if it fell more."""
    if len(prices) <= lookback:
        return None
    change = prices[-1] / prices[-1 - lookback] - 1
    if change > min_move:
        return "call"
    if change < -min_move:
        return "put"
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
    return 100 - 100 / (1 + gains / losses)


def mean_reversion(prices, n=14, oversold=30, overbought=70):
    """Bets on a bounce: up after a sharp drop (RSI oversold), down after a sharp rise (RSI overbought)."""
    if len(prices) <= n:
        return None
    value = rsi(prices, n)
    if value < oversold:
        return "call"
    if value > overbought:
        return "put"
    return None


SIGNALS = {
    "sma_crossover": sma_crossover,
    "momentum": momentum,
    "mean_reversion": mean_reversion,
}
