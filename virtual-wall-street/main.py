import os
import queue
import sys

import pygame

from engine import AlpacaMarket, DemoMarket, Engine, make_bots
from news import AlpacaNewsFeed, ClaudeJudge, NewsWatcher

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

# --- CONFIG ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1240, 640
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (60, 60, 60)
LIGHT_GRAY = (170, 170, 170)
YELLOW = (255, 255, 0)
CYAN = (0, 200, 255)
MAGENTA = (255, 0, 220)
# Buying a call = cyan, buying a put = magenta, closing at a profit = green, at a loss = red
SIGNAL_LABELS = {"momentum": "momentum", "sma_crossover": "crossover", "mean_reversion": "reversion",
                 "news": "news"}
EVENT_COLORS = {"call": CYAN, "put": MAGENTA, "profit": GREEN, "loss": RED, "info": YELLOW}

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Virtual Wall Street")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20, bold=True)
small_font = pygame.font.SysFont("Arial", 13)

# --- BUILDING (one per bot) ---
class Building:
    def __init__(self, x, y, bot):
        self.x = x
        self.y = y
        self.width = 80
        self.height = 150
        self.bot = bot
        self.floating_texts = []
        self.beams = []

    def draw(self, surface):
        # Beams go behind everything so they look like they shoot out of the roof
        for beam in self.beams:
            beam.draw(surface)
        # Draw building; windows light up in the trade's color while a position is open
        pygame.draw.rect(surface, GRAY, (self.x, self.y, self.width, self.height))
        position = self.bot.position
        window_color = EVENT_COLORS[position["kind"]] if position else DARK_GRAY
        for row in range(5):
            for col in range(3):
                pygame.draw.rect(surface, window_color, (self.x + 10 + col * 23, self.y + 12 + row * 27, 14, 16))
        # Draw bot name and details underneath
        center = self.x + self.width // 2
        name_text = font.render(self.bot.name, True, WHITE)
        surface.blit(name_text, (center - name_text.get_width() // 2, self.y + self.height + 5))
        lines = [
            (f"{self.bot.symbol} {self.bot.style} | {SIGNAL_LABELS[self.bot.signal_name]}", LIGHT_GRAY),
            (self.bot.note, YELLOW if position else LIGHT_GRAY),
            (f"cash ${self.bot.cash:,.0f} | {self.bot.wins}/{self.bot.trades} wins", LIGHT_GRAY),
        ]
        for i, (line, color) in enumerate(lines):
            text = small_font.render(line, True, color)
            surface.blit(text, (center - text.get_width() // 2, self.y + self.height + 30 + i * 17))
        # Draw P/L above building
        pnl = self.bot.pnl
        pnl_color = GREEN if pnl >= 0 else RED
        pnl_text = font.render(f"{pnl:+,.2f}", True, pnl_color)
        surface.blit(pnl_text, (center - pnl_text.get_width() // 2, self.y - 25))
        # Draw floating trade texts
        for ft in self.floating_texts:
            ft.draw(surface)

    def add_trade(self, text, color):
        self.floating_texts.append(FloatingText(text, self.x + self.width // 2, self.y - 50, color))
        self.beams.append(Beam(self.x + self.width // 2, self.y, color))

    def update(self):
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if not ft.is_expired()]
        for beam in self.beams:
            beam.update()
        self.beams = [beam for beam in self.beams if not beam.is_expired()]

# --- BEAM CLASS ---
class Beam:
    """A light beam that shoots up from a building's roof when it completes a trade."""

    DURATION = 60  # frames

    def __init__(self, x, roof_y, color):
        self.x = x
        self.roof_y = roof_y
        self.color = color
        self.age = 0

    def update(self):
        self.age += 1

    def draw(self, surface):
        progress = self.age / self.DURATION
        # Shoots up over the first quarter, then fades out
        top = self.roof_y - self.roof_y * min(progress * 4, 1)
        fade = 1 - max(0, progress - 0.25) / 0.75
        height = int(self.roof_y - top)
        if height <= 0:
            return
        glow = pygame.Surface((60, height), pygame.SRCALPHA)
        for width, alpha in ((60, 40), (34, 80), (16, 170)):
            pygame.draw.rect(glow, (*self.color, int(alpha * fade)), ((60 - width) // 2, 0, width, height))
        pygame.draw.rect(glow, (255, 255, 255, int(220 * fade)), (27, 0, 6, height))
        surface.blit(glow, (self.x - 30, top))
        # Flash on the roof where the beam starts
        flash = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(flash, (*self.color, int(150 * fade)), (45, 45), int(20 + 25 * progress))
        surface.blit(flash, (self.x - 45, self.roof_y - 45))

    def is_expired(self):
        return self.age >= self.DURATION

# --- FLOATING TEXT CLASS ---
class FloatingText:
    def __init__(self, text, x, y, color):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = 120  # frames

    def update(self):
        self.y -= 0.5
        self.lifetime -= 1

    def draw(self, surface):
        txt = font.render(self.text, True, self.color)
        surface.blit(txt, (self.x - txt.get_width() // 2, self.y))

    def is_expired(self):
        return self.lifetime <= 0

def draw_centered(text, used_font, color, y):
    rendered = used_font.render(text, True, color)
    screen.blit(rendered, (SCREEN_WIDTH // 2 - rendered.get_width() // 2, y))

# --- PICK A MARKET ---
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

engine = Engine(market, bots, news)
engine.start()

# --- CREATE BUILDINGS ---
buildings = {}
spacing = SCREEN_WIDTH // (len(bots) + 1)
for i, bot in enumerate(bots):
    buildings[bot.name] = Building(spacing * (i + 1) - 40, 300, bot)

# --- MAIN LOOP ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_a:
            # Pause/resume trading (prices and P/L keep updating)
            engine.paused = not engine.paused

    # Pick up trades the engine made since the last frame
    while True:
        try:
            bot, text, kind = engine.events.get_nowait()
        except queue.Empty:
            break
        buildings[bot.name].add_trade(text, EVENT_COLORS[kind])

    # Update
    for building in buildings.values():
        building.update()

    # Draw
    screen.fill(BLACK)
    draw_centered(market.name, small_font, CYAN, 15)
    total_pnl = sum(bot.pnl for bot in bots)
    total_color = GREEN if total_pnl >= 0 else RED
    draw_centered(f"TOTAL P/L: {total_pnl:+,.2f}", font, total_color, 40)
    status = engine.status
    if engine.equity is not None:
        status += f"   |   Paper account equity: ${engine.equity:,.2f}"
    draw_centered(status, small_font, LIGHT_GRAY, 70)
    trading_state = "TRADING PAUSED" if engine.paused else "AUTO TRADING: ON"
    draw_centered(f"{trading_state}  (A to toggle, ESC to quit)", font, YELLOW, 95)
    if news:
        lines = []
        for symbol in news.symbols:
            v = news.latest(symbol)
            if v:
                arrow = {"up": "UP", "down": "DOWN", "unclear": "?"}[v.direction]
                lines.append(f"{symbol} {arrow} ({v.strength}, {v.published:%I:%M %p}): {v.reason}")
        draw_centered(f"News: {news.judge.calls} headlines judged, Claude cost ${news.judge.spent:.4f}  |  "
                      + (lines[-1] if lines else "no notable headlines in the last hour"), small_font, WHITE, 125)
    if engine.error or engine.news_error:
        draw_centered(engine.error or engine.news_error, small_font, RED, 145)

    for building in buildings.values():
        building.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
