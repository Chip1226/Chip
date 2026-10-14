"""Option contracts: symbols, pricing math, and picking which contract to buy."""

import math
import re
from dataclasses import dataclass
from datetime import date, datetime

RISK_FREE_RATE = 0.04


@dataclass
class Contract:
    symbol: str
    underlying: str
    expiration: date
    kind: str  # "call" or "put"
    strike: float
    bid: float
    ask: float
    delta: float

    @property
    def mid(self):
        return (self.bid + self.ask) / 2

    def dte(self, today):
        return (self.expiration - today).days


# --- OCC option symbols, e.g. QQQ261030C00500000 = QQQ $500 call expiring 2026-10-30 ---

OCC = re.compile(r"^([A-Z.]+)(\d{6})([CP])(\d{8})$")


def occ_symbol(underlying, expiration, kind, strike):
    return f"{underlying}{expiration:%y%m%d}{'C' if kind == 'call' else 'P'}{round(strike * 1000):08d}"


def parse_occ(symbol):
    """Returns (underlying, expiration, kind, strike)."""
    root, ymd, cp, strike = OCC.match(symbol).groups()
    return root, datetime.strptime(ymd, "%y%m%d").date(), "call" if cp == "C" else "put", int(strike) / 1000


# --- Black-Scholes: used to price options in demo mode, and as a fallback delta ---

def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def black_scholes(kind, spot, strike, years, iv, rate=RISK_FREE_RATE):
    """Returns (price per share, delta)."""
    years = max(years, 1e-6)
    d1 = (math.log(spot / strike) + (rate + iv * iv / 2) * years) / (iv * math.sqrt(years))
    d2 = d1 - iv * math.sqrt(years)
    if kind == "call":
        return spot * _norm_cdf(d1) - strike * math.exp(-rate * years) * _norm_cdf(d2), _norm_cdf(d1)
    return strike * math.exp(-rate * years) * _norm_cdf(-d2) - spot * _norm_cdf(-d1), _norm_cdf(d1) - 1


# --- Prices and picking contracts ---

def round_price(price, underlying):
    """Round to a valid option price increment."""
    if underlying in ("SPY", "QQQ", "IWM") or price < 3:
        return round(price, 2)
    return round(round(price / 0.05) * 0.05, 2)


def _by_delta(chain, today, delta_min, delta_max, avoid=()):
    """Contracts with |delta| in range and a real two-sided quote, closest to 0.50 delta first."""
    usable = [c for c in chain if c.bid > 0 and c.ask >= c.bid and delta_min <= abs(c.delta) <= delta_max
              and c.symbol not in avoid]
    return sorted(usable, key=lambda c: (abs(abs(c.delta) - 0.5), c.dte(today)))


def pick_single(chain, today, delta_min, delta_max, max_cost, no_buy=()):
    """Best single contract costing at most `max_cost` dollars.

    Returns (contract, None) or (None, why_not) where why_not explains the skip.
    """
    candidates = _by_delta(chain, today, delta_min, delta_max, no_buy)
    if not candidates:
        return None, "no contract in delta range"
    for c in candidates:
        if c.mid * 100 <= max_cost:
            return c, None
    cheapest = min(c.mid * 100 for c in candidates)
    return None, f"too pricey (min ${cheapest:,.0f})"


def pick_spread(chain, today, delta_min, delta_max, widths, max_cost, no_buy=(), no_sell=()):
    """Best debit spread: buy a ~0.50 delta option, sell a further-out one, same expiration.

    `widths` are strike distances in dollars to try, widest (most profit potential) first.
    Returns ((long, short), None) or (None, why_not).
    """
    longs = _by_delta(chain, today, delta_min, delta_max, no_buy)
    if not longs:
        return None, "no contract in delta range"
    cheapest = None
    for long in longs:
        for width in widths:
            target = long.strike + width if long.kind == "call" else long.strike - width
            match = [c for c in chain if c.expiration == long.expiration and c.kind == long.kind
                     and abs(c.strike - target) < 1e-6 and c.bid > 0 and c.symbol not in no_sell]
            if not match:
                continue
            short = match[0]
            cost = (long.mid - short.mid) * 100
            if cost <= 0:
                continue
            if cost <= max_cost:
                return (long, short), None
            cheapest = cost if cheapest is None else min(cheapest, cost)
    if cheapest is None:
        return None, "no spread available"
    return None, f"too pricey (min ${cheapest:,.0f})"
