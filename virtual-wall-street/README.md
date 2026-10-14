# Virtual Wall Street

Six trading bots stand as buildings on screen. Each one trades short-term **options** (calls and puts) on its own and shows its profit or loss above its building.

- When a bot completes a trade, a beam shoots out of its roof: **cyan** = bought a call, **magenta** = bought a put, **green** = closed at a profit, **red** = closed at a loss.
- While a trade is open, the building's windows glow cyan (call) or magenta (put).
- Under each building: the stock and style, what the bot is doing right now, its cash, and its win count.

## The six bots

The three QQQ bots all use the same signal, so the only difference between them is *how* they trade it. That's the comparison to watch.

| Bot | Trades | Budget | How |
| --- | --- | --- | --- |
| QQQ Spread | QQQ | $300 | Debit spreads: buy a ~0.50 delta option, sell one $2-5 further out. Fixed max loss, capped profit |
| By the Rules | QQQ | $50,000 (paper) | Single calls/puts, exactly by the rules below, each trade at most 3% of its cash |
| $300 Single | QQQ | $300 | Single calls/puts that fit $300. **Bends the rules:** allows delta down to 0.20 and 7 days to expiration |
| SPY Spread | SPY | $300 | Debit spreads, average-crossover signal |
| AMD Spread | AMD | $300 | Debit spreads, buy-the-dip / sell-the-rip signal. Out before the Nov 3 earnings report |
| News | AMD | $300 | Debit spreads on news: buys when Claude rates a headline notable or major *and* the price is already moving that way. Same earnings rules. See "News" below |

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
- **Per bot, hard limit:** a bot may lose at most **50% of its budget** ($150 of a $300 bot). The exception is $300 Single, whose limit is 100%: it can lose its whole $300, but never more. Each trade's cost is capped at the room left above that line, so even a trade that goes to zero can't take the bot past it. At the line, the bot stops trading for good.

Change any of these in `config.py` (`RULES` for everything, `BOTS` for one bot).

**None of this makes the bots profitable.** Most retail traders who buy short-dated options lose money over time, mainly to time decay and IV crush. The point is to watch, with fake money, whether any of these approaches holds up.

## News

With an Anthropic API key, the game reads real headlines about QQQ, SPY and AMD from Alpaca's free news feed and has Claude Haiku (Anthropic's cheapest model) rate each one: up, down or unclear, and minor, notable or major.

- **Protection for every bot:** after a **major** headline about a stock (earnings surprise, big deal, regulatory action, surprise Fed decision), the other bots open no new trades in it for 30 minutes, while prices and option quotes settle. Open trades keep their normal exit rules.
- **The News bot:** opens a trade when the latest notable or major headline (from the last hour) and the price agree, meaning the price has moved at least 0.2% the headline's way over the last 30 minutes. A good headline with a falling price is skipped: the market may already have priced it in, or disagrees.
- **On screen:** the line under "AUTO TRADING" shows how many headlines Claude has judged, what that cost, and the latest notable verdict with its one-line reason.

**Cost:** about $0.0001 per headline, so typically well under $1 a month. There's a hard cap of 300 headlines a day (about $0.05). Set a monthly spending limit in the Anthropic console too.

**To turn it on:**
1. Create an account at [console.anthropic.com](https://console.anthropic.com), add a little credit (for example $5), and create an API key. This is billed separately from a Claude.ai subscription.
2. Add it to your `.env` file: `ANTHROPIC_API_KEY=sk-ant-...`
3. Run the game with your Alpaca keys too. News only works in Alpaca mode; demo mode has no real headlines, so the News bot shows "news off".

If the key is wrong or Claude can't be reached, the error shows in red and every other bot keeps trading without the news filter.

**Keep expectations low:** professional traders read the same headlines by computer within milliseconds. By the time the News bot reacts, much of the move has usually happened. The price-confirmation rule avoids fighting the market, but it also means buying after the move has started. Watch whether this bot beats the others before trusting it.

## Make it a Mac app (no Terminal needed)

Run this once, in Terminal, from this folder:

```
bash make_app.sh
```

It creates **Virtual Wall Street** in your Applications folder, with its own icon. From then on:

- **Open it** like any app: double-click it in Applications, find it in Launchpad, or press Cmd+Space and type "Virtual". Drag it to your Dock to keep it one click away. The game starts in the background and the 3D city opens in your browser.
- **Closing the browser tab doesn't stop the bots.** They keep trading in the background while your Mac is awake. Open the app again to see the city.
- **To stop the game,** click **Stop game** in the top-left panel of the city.
- Opening the app while the game is already running just opens the city again. It never starts a second set of bots.
- If you move the game folder or install a different Python, run `bash make_app.sh` again.
- If the game won't start, the app shows the error. The full log is in `city.log` in this folder.

## 3D city

```
python city.py
```

This opens the same game as a 3D night city in your web browser (Chrome, Edge, Safari or Firefox). The trading is identical; it's only a different view. Keep the terminal window open while you play; closing it (or Ctrl+C) stops the bots.

- **The Exchange**, the tall tower in the middle, shows every bot's P/L, its open position and the combined total on a big screen on each side. The ring floating around it glows green when the bots are up overall and red when they're down. The six light columns on the plaza point at each bot's tower: taller = bigger gain or loss for its budget.
- **Bot towers** stand in a ring around it. Each one's windows glow cyan while holding a call, magenta for a put, and warm white in cash. The band around the roof turns green or red with the bot's P/L, and a label above shows its numbers.
- **Trades** fire a beam of light from the roof, with a flash and a shockwave: cyan for a call, magenta for a put, green for a profitable close, red for a loss.
- **Day and night follow the market.** While the market is open it's daytime, with the sun out. When it closes, the sun sets, the sky darkens, the stars come out, the moon rises and the city lights up. It turns back to day when the market opens. In demo mode each night lasts 30 seconds (`DEMO_NIGHT_TICKS` in `config.py`). Press **N** to preview: always day, always night, then back to following the market.

**Moving around:**

| Key | Does |
| --- | --- |
| ↑ / ↓ | Walk forward / back, staying at the same height |
| ← / → | Turn left / right |
| Click the city | Look around with the mouse (Esc gets the cursor back). You can also drag with the mouse button held |
| W A S D | Fly forward, left, back, right, in the direction you're looking (including up or down) |
| Space or E / Q or C | Fly up / down |
| Shift | Fly faster |
| 1-6 | Fly to that bot's tower |
| 0 | Fly to the Exchange |
| Tab | Fly to the next building |
| R | Circle around the building you're at, to see it from behind |
| P | Pause / resume trading |
| N | Preview day / night (press again to cycle back to following the market) |
| H | Hide / show the key legend at the bottom of the screen |

The arrow keys alone are enough to get around; the legend along the bottom of the screen lists every key. You can also click a building in the list at the top right to fly there. Buildings are solid, so you can't fly through walls.

The 3D view runs on `http://localhost:8765` and only your own computer can reach it. Three.js (the 3D library, MIT license) is included in `web/vendor`, so nothing extra needs installing or downloading. The 2D window (`python main.py`) still works too; it needs one extra library: `pip install -r requirements-2d.txt`.

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
4. For the 3D city instead, run `python city.py` (see "3D city" above).

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

To turn on news reading, also add `ANTHROPIC_API_KEY` (see "News" above).

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
