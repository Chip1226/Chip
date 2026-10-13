"""Settings you can change without touching the rest of the code."""

# --- Rules every bot follows (from your notes) ---
RULES = {
    "min_dte": 14,          # buy 2-4 weeks of time; under ~7 days theta decay accelerates hard
    "max_dte": 28,
    "delta_min": 0.40,      # at the money or slightly in the money
    "delta_max": 0.60,
    "take_profit": 0.75,    # sell at +75% (inside the +50-100% range)
    "stop_loss": 0.45,      # cut a trade at -45% (inside the -40-50% range)
    # Hard limit per bot: the most it may ever lose, as a share of its budget.
    # Every trade's cost is capped at the room left above this line, so even a trade
    # that goes to zero can't push the bot past it. At the line the bot stops for good.
    "max_loss_pct": 0.50,
    "exit_dte": 5,          # never hold into the last days before expiration
    # "Clearly broken": the signal must point the other way this long before the bot exits on it.
    "flip_confirm_minutes": 120,
    "cooldown_minutes": 30, # wait after closing a trade before opening the next one
}

# --- One building per bot ---
# style:      "spread" = debit spread (buy ~0.50 delta, sell one `widths` dollars further out)
#             "single" = one call or put
# budget:     dollars this bot starts with (its own slice of the paper account)
# risk_pct:   most of its current cash one trade may cost (max loss of that trade),
#             further capped by the max_loss_pct hard limit above
# signal:     which direction signal picks calls vs puts (see strategies.py, or "news")
# earnings:   date of the next earnings report; the bot is flat that day and
#             opens nothing in the `blackout_days` before it (IV crush)
#
# The three QQQ bots share one signal so the only difference is how they trade it.
BOTS = [
    {"name": "QQQ Spread", "symbol": "QQQ", "signal": "momentum", "style": "spread",
     "widths": [5, 3, 2], "budget": 300, "risk_pct": 0.80},
    {"name": "By the Rules", "symbol": "QQQ", "signal": "momentum", "style": "single",
     "budget": 50000, "risk_pct": 0.03},
    {"name": "$300 Single", "symbol": "QQQ", "signal": "momentum", "style": "single",
     "budget": 300, "risk_pct": 1.00, "min_dte": 7, "delta_min": 0.20,  # bends the rules to fit $300
     "max_loss_pct": 1.00},  # may lose its whole $300, never more
    {"name": "SPY Spread", "symbol": "SPY", "signal": "sma_crossover", "style": "spread",
     "widths": [5, 3, 2], "budget": 300, "risk_pct": 0.80},
    {"name": "AMD Spread", "symbol": "AMD", "signal": "mean_reversion", "style": "spread",
     "widths": [5, 2.5], "budget": 300, "risk_pct": 0.80,
     "earnings": "2026-11-03", "blackout_days": 5},
    # Trades AMD news: buys when Claude rates a headline notable or major AND the price is
    # already moving that way. Needs ANTHROPIC_API_KEY and Alpaca mode (demo mode has no news).
    {"name": "News", "symbol": "AMD", "signal": "news", "style": "spread",
     "widths": [5, 2.5], "budget": 300, "risk_pct": 0.80,
     "earnings": "2026-11-03", "blackout_days": 5},
]

# --- News (Alpaca mode with ANTHROPIC_API_KEY set) ---
NEWS = {
    "model": "claude-haiku-5-5",   # cheapest Claude model, about $0.0001 per headline
    "lookback_minutes": 60,        # the News bot acts on headlines up to an hour old
    "block_minutes": 30,           # every other bot waits this long after a major headline
    "confirm_minutes": 30,         # the price must have moved the headline's way over this window
    "confirm_move": 0.002,         # ...by at least 0.2%
    "max_headlines_per_day": 300,  # spending cap: at most ~$0.05 a day
}

# No new trades in the first/last minutes of the session, when option quotes are wide and jumpy.
SKIP_OPEN_MINUTES = 15
SKIP_CLOSE_MINUTES = 15

# Signals read 15-minute bars, so a trade's reason lasts hours to days, not minutes.
# (With 1-minute bars the signals flip constantly and the bid/ask spread eats every trade.)
SIGNAL_BAR_MINUTES = 15

# Alpaca mode: how often bots check prices and manage open trades.
CHECK_INTERVAL_SECONDS = 60
# How long a limit order may sit unfilled before it's canceled and retried next check.
FILL_WAIT_SECONDS = 20

# Demo mode (no Alpaca keys): each tick is one simulated market minute.
DEMO_TICK_SECONDS = 0.2
# Made-up starting prices and volatility for the simulation (not real quotes).
DEMO_UNDERLYINGS = {
    # symbol: (start price, implied volatility, strike step, bid/ask spread as % of price, daily expirations)
    "QQQ": (500.0, 0.22, 1.0, 0.02, True),
    "SPY": (600.0, 0.16, 1.0, 0.02, True),
    "AMD": (160.0, 0.50, 2.5, 0.04, False),
}
