"""3D city view. Run:  python city.py

Starts the same trading engine as main.py, then serves the 3D city (web/) on
http://localhost:8765 and opens it in your browser. The server only listens on
this computer; nothing is reachable from other machines.
"""

import argparse
import json
import os
import queue
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app import build_engine

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
SIGNAL_LABELS = {"momentum": "momentum", "sma_crossover": "crossover", "mean_reversion": "reversion",
                 "news": "news"}


class EventLog:
    """Numbers each trade event so the browser can ask for "everything after #N"."""

    def __init__(self, engine, keep=200):
        self.engine = engine
        self.keep = keep
        self.items = []
        self.next_id = 1
        self.lock = threading.Lock()

    def since(self, last_id):
        with self.lock:
            while True:
                try:
                    bot, text, kind = self.engine.events.get_nowait()
                except queue.Empty:
                    break
                self.items.append({"id": self.next_id, "bot": bot.name, "text": text, "kind": kind})
                self.next_id += 1
            del self.items[:-self.keep]
            return [e for e in self.items if e["id"] > last_id], self.next_id - 1


def snapshot(engine, log, since):
    events, last_id = log.since(since)
    bots = []
    for b in engine.bots:
        pos = b.position
        bots.append({
            "name": b.name, "symbol": b.symbol, "style": b.style,
            "signal": SIGNAL_LABELS.get(b.signal_name, b.signal_name),
            "pnl": round(b.pnl, 2), "pnl_pct": b.pnl / b.budget if b.budget else 0,
            "cash": round(b.cash, 2), "budget": b.budget, "note": b.note,
            "wins": b.wins, "trades": b.trades,
            "position": {"kind": pos["kind"], "label": pos["label"]} if pos else None,
        })
    news = None
    if engine.news:
        latest = [engine.news.latest(s) for s in engine.news.symbols]
        news = {
            "calls": engine.news.judge.calls, "spent": engine.news.judge.spent,
            "latest": [{"symbol": v.symbol, "direction": v.direction, "strength": v.strength,
                        "reason": v.reason, "time": v.published.strftime("%I:%M %p")}
                       for v in latest if v],
        }
    return {
        "mode": engine.market.name, "status": engine.status, "paused": engine.paused,
        "market_open": engine.market_open,
        "error": engine.error or engine.news_error, "equity": engine.equity,
        "total_pnl": round(sum(b.pnl for b in engine.bots), 2),
        "bots": bots, "news": news, "events": events, "last_event_id": last_id,
    }


class Handler(SimpleHTTPRequestHandler):
    # Some Windows setups map .js to text/plain, which browsers refuse to run as a module.
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript"}

    def __init__(self, *args, engine, log, **kwargs):
        self.engine = engine
        self.log = log
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/state":
            since = int(parse_qs(url.query).get("since", ["0"])[0])
            self.send_json(snapshot(self.engine, self.log, since))
        else:
            super().do_GET()

    def do_POST(self):
        # The custom header keeps other websites open in your browser from pressing these:
        # browsers won't send it cross-site without permission, which this server never gives.
        path = urlparse(self.path).path
        if self.headers.get("X-VWS") != "1":
            self.send_error(403)
        elif path == "/api/pause":
            self.engine.paused = not self.engine.paused
            self.send_json({"paused": self.engine.paused})
        elif path == "/api/quit":
            self.send_json({"stopping": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send_error(404)

    def end_headers(self):
        if not self.path.startswith("/vendor/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # keep the terminal quiet


def main():
    parser = argparse.ArgumentParser(description="Virtual Wall Street in 3D")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="don't open a browser tab")
    args = parser.parse_args()

    url = f"http://localhost:{args.port}"
    engine = build_engine()
    log = EventLog(engine)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, engine=engine, log=log))
    except OSError:
        # Already running: never start a second set of bots on the same account.
        print(f"Virtual Wall Street is already running. Opening {url}")
        if not args.no_browser:
            webbrowser.open(url)
        return
    engine.start()
    print(f"Virtual Wall Street 3D is running at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    print("\nStopping: letting the bots finish what they're doing...")
    engine.stop()
    print("Stopped.")


if __name__ == "__main__":
    main()
