# Virtual Wall Street

Five trading bots stand as buildings on screen. Each one trades short-term **options** (calls and puts) on its own and shows its profit or loss above its building.

- When a bot completes a trade, a beam shoots out of its roof: **cyan** = bought a call, **magenta** = bought a put, **green** = closed at a profit, **red** = closed at a loss.
- While a trade is open, the building's windows glow cyan (call) or magenta (put).
- Under each building: the stock and style, what the bot is doing right now, its cash, and its win count.

## The five bots

The three QQQ bots all use the same signal, so the only difference between them is *how* they trade it. That's the comparison to watch.

| Bot | Trades | Budget | How |
| --- | --- | --- | --- |
| QQQ Spread | QQQ | $300 | Debit spreads: buy a ~0.50 delta option, sell one $2-5 further out. Fixed max loss, capped profit |
| By the Rules | QQQ | $50,000 (paper) | Single calls/puts, exactly by the rules below, each trade at most 3% of its cash |
| $300 Single | QQQ | $300 | Single calls/puts that fit $300. **Bends the rules:** allows delta down to 0.20 and 7 days to expiration |
| SPY Spread | SPY | $300 | Debit spreads, average-crossover signal |
| AMD Spread | AMD | $300 | Debit spreads, buy-the-dip / sell-the-rip signal. Out before the Nov 3 earnings report |

**Signals** pick the direction, reading 15-minute bars: *momentum* (price up/down over the last ~5 hours), *average crossover* (short-term average above/below the long-term one), *mean reversion* (bets on a bounce after a sharp move).

## Rules every bot follows

- **Expiration** 14-28 days out (the $300 Single bot: 7-28).
- **Strike** around 0.40-0.60 delta, closest to 0.50.
- **Limit orders at the mid** of the bid/ask, never market orders. Unfilled orders are canceled and retried. Exits step toward the bid each retry so they can't get stuck.
- **Exits:** take profit at +75%, stop loss at -45%, close when the signal flips the other way, and close with 5 days left (time decay accelerates).
- **Earnings (AMD):** no new trades in the 5 days before the report, and any open trade is closed the trading day before.
- **No trades** in the first and last 15 minutes of the day, or for 30 minutes after closing a trade.

## How much can I lose?

- **Never more than you put in.** The bots only *buy* options. A single call or put can lose at most what it cost. In a debit spread, the option sold is covered by the one bought, so the spread can lose at most what you paid for it. There's no short selling and nothing with unlimited loss.
- **Per trade:** each trade is closed at -45%. A sudden overnight gap can blow past that, but a trade still can't lose more than its cost.
- **Per bot, hard limit:** a bot may lose at most **50% of its budget** ($150 of a $300 bot). Each trade's cost is capped at the room left above that line, so even a trade that goes to zero can't take the bot past it. At the line, the bot stops trading for good.

Change any of these in `config.py` (`RULES` for everything, `BOTS` for one bot).

**None of this makes the bots profitable.** Most retail traders who buy short-dated options lose money over time, mainly to time decay and IV crush. The point is to watch, with fake money, whether any of these approaches holds up.

## Two modes

- **Demo mode** (no setup): simulated prices and options. Each tick is one market minute, so a trading day passes in about 80 seconds, and you can see time decay eat positions that go nowhere. The simulated market has no trend built in, so demo results are luck: don't read anything into them.
- **Alpaca paper trading**: real option prices and real orders on Alpaca, with fake money. The game refuses to run with a live-money key.

## Run it

1. Install [Python 3](https://www.python.org/downloads/).
2. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   python main.py
   ```
3. With no keys set up it starts in demo mode. Press **A** to pause or resume trading, **Esc** to quit.

## Connect Alpaca paper trading

1. Sign up for free at [alpaca.markets](https://alpaca.markets). Paper trading only needs an email address.
2. In the dashboard, switch to the **Paper Trading** account (top left) and generate API keys.
3. Copy the **Key** (starts with `PK`) and the **Secret**. The secret is shown only once.
4. In this folder, copy `.env.example` to a new file named `.env` and paste both values in:
   ```
   ALPACA_API_KEY=PK...
   ALPACA_SECRET_KEY=...
   ```
5. Run `python main.py` again. The top line now says **ALPACA PAPER TRADING**.

Keep `.env` private: don't paste the keys into chats, screenshots or commits. It's already git-ignored.

### What to expect with Alpaca

- The paper account starts with $100,000. Each bot only uses its own budget from `config.py`. The "By the Rules" bot's $50,000 is half of it.
- Paper accounts normally have options trading (including spreads) turned on. If orders are rejected for options permissions, check **Account > Configure** in the paper dashboard.
- Bots only trade while the US market is open (9:30am-4pm Eastern, weekdays) and check once a minute.
- Each bot's cash and open trade are saved in `bot_state.json` in this folder, so closing and reopening the game picks up where it left off. To start the bots fresh, close any open option positions in the Alpaca dashboard, then delete `bot_state.json`.
- Option prices come from Alpaca's free "indicative" feed, which can differ slightly from the real market. Fills at the mid are not guaranteed.
- Watch every order in the Alpaca dashboard under **Orders**.

## Tests

```
python -m unittest test_trading.py
```
