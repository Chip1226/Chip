# Virtual Wall Street

A small pygame toy: five trading bots stand as buildings on screen. Every 1.5 seconds each bot makes a simulated trade (a random gain or loss between -$200 and +$200). The result floats up above the building, each bot's running P/L shows on top, and the combined total is at the top of the window.

The trades are random numbers — no real market data or money is involved.

## Run it

1. Install [Python 3](https://www.python.org/downloads/).
2. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   python main.py
   ```
3. Bots trade on their own. Press **A** to pause or resume auto trading, **Space** to force a trade right now. Close the window to quit.
