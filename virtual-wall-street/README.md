# Virtual Wall Street

Five trading bots stand as buildings on screen. Each one runs a different trading strategy, trades on its own, and shows its profit or loss above its building. A building's windows light up while that bot holds shares and go dark while it's sitting in cash.

| Bot | Strategy |
| --- | --- |
| Crossover | Buys when the 10-minute average price rises above the 30-minute average, sells when it falls below |
| Momentum | Buys when the price is higher than 20 minutes ago, sells when it's lower |
| Reversion | Buys after a sharp drop (RSI under 30), sells after a sharp rise (RSI over 70) |
| Breakout | Buys when the price beats its 20-minute high, sells when it drops below its 10-minute low |
| Buy&Hold | Buys once and never sells. **The benchmark:** a strategy that can't beat this isn't worth running |

All five trade SPY (an S&P 500 index fund) by default so you're comparing strategies on the same stock. Change symbols, strategies or trade size in `config.py`.

**None of this is guaranteed to make money.** These are well-known textbook strategies, which means plenty of professionals already trade against them. The point is to watch, with zero risk, which ones actually beat Buy&Hold.

## Two modes

- **Demo mode** (no setup): made-up prices that tick every half second. Good for seeing how the strategies behave.
- **Alpaca paper trading**: real live market prices and real orders placed on Alpaca, but with $100,000 of fake money. The game refuses to run with a live-money key.

## Run it

1. Install [Python 3](https://www.python.org/downloads/).
2. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   python main.py
   ```
3. With no keys set up it starts in demo mode. Press **A** to pause or resume trading, **Esc** to quit.

## Connect Alpaca paper trading

1. Sign up for free at [alpaca.markets](https://alpaca.markets). Paper trading only needs an email address. You don't have to fund anything or verify your identity.
2. In the dashboard, make sure you're on the **Paper Trading** account (top left), then find **API Keys** on the right side of the home page and click **Generate New Keys**.
3. Copy the **Key** (starts with `PK`) and the **Secret**. The secret is shown only once.
4. In this folder, copy `.env.example` to a new file named `.env` and paste the two values in:
   ```
   ALPACA_API_KEY=PK...
   ALPACA_SECRET_KEY=...
   ```
5. Run `python main.py` again. The top line now says **ALPACA PAPER TRADING**.

Keep `.env` private: don't paste the keys into chats, screenshots or commits. It's already git-ignored.

### What to expect

- Bots only trade while the US stock market is open (9:30am to 4pm Eastern, weekdays). Outside those hours the screen says when it opens next, and the P/L stays where it was.
- Bots check prices once a minute. Some strategies wait for a signal, so it can take a while before a trade happens.
- Each bot spends $1,000 (fake) per buy. Every order is tagged with the bot's name, so if you close the game and reopen it, each bot picks up its positions and P/L from your Alpaca order history.
- Prices come from Alpaca's free data feed (IEX), which can differ slightly from what you see on other sites.
- You can watch every order in the Alpaca dashboard under **Orders**.

## Tests

```
python -m unittest test_trading.py
```
