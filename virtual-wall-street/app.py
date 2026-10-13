"""Shared start-up for both views (main.py in 2D, city.py in 3D): pick the market, set up news."""

import os
import sys

from engine import AlpacaMarket, DemoMarket, Engine, make_bots
from news import AlpacaNewsFeed, ClaudeJudge, NewsWatcher


def build_engine():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    except ImportError:
        pass

    bots = make_bots()
    key, secret = os.getenv("ALPACA_API_KEY", ""), os.getenv("ALPACA_SECRET_KEY", "")
    if key and secret:
        try:
            market = AlpacaMarket(key, secret)
        except ValueError as e:
            print(e)
            sys.exit(1)
    else:
        market = DemoMarket(bots)

    # News needs real headlines (Alpaca mode) and a Claude API key to judge them
    news = None
    if isinstance(market, AlpacaMarket) and os.getenv("ANTHROPIC_API_KEY"):
        news = NewsWatcher(AlpacaNewsFeed(key, secret), ClaudeJudge(), [b.symbol for b in bots])

    return Engine(market, bots, news)
