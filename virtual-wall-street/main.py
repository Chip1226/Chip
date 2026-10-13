import os
import queue
import sys

import pygame

from engine import AlpacaMarket, DemoMarket, Engine, make_bots

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

# --- CONFIG ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 600
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
EVENT_COLORS = {"buy": CYAN, "profit": GREEN, "loss": RED, "info": YELLOW}

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Virtual Wall Street")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20, bold=True)
small_font = pygame.font.SysFont("Arial", 14)

# --- BUILDING (one per bot) ---
class Building:
    def __init__(self, x, y, bot):
        self.x = x
        self.y = y
        self.width = 80
        self.height = 150
        self.bot = bot
        self.floating_texts = []

    def draw(self, surface):
        # Draw building; windows light up while the bot holds shares
        pygame.draw.rect(surface, GRAY, (self.x, self.y, self.width, self.height))
        window_color = YELLOW if self.bot.holding else DARK_GRAY
        for row in range(5):
            for col in range(3):
                pygame.draw.rect(surface, window_color, (self.x + 10 + col * 23, self.y + 12 + row * 27, 14, 16))
        # Draw bot name, symbol and strategy
        name_text = font.render(self.bot.name, True, WHITE)
        surface.blit(name_text, (self.x + (self.width - name_text.get_width()) // 2, self.y + self.height + 5))
        detail = "%s  %s" % (self.bot.symbol, "HOLDING" if self.bot.holding else "CASH")
        detail_text = small_font.render(detail, True, LIGHT_GRAY)
        surface.blit(detail_text, (self.x + (self.width - detail_text.get_width()) // 2, self.y + self.height + 30))
        # Draw P/L above building
        pnl = self.bot.pnl
        pnl_color = GREEN if pnl >= 0 else RED
        pnl_text = font.render(f"{pnl:+.2f}", True, pnl_color)
        surface.blit(pnl_text, (self.x + (self.width - pnl_text.get_width()) // 2, self.y - 25))
        # Draw floating trade texts
        for ft in self.floating_texts:
            ft.draw(surface)

    def add_trade(self, text, color):
        self.floating_texts.append(FloatingText(text, self.x + self.width // 2, self.y - 50, color))

    def update(self):
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if not ft.is_expired()]

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

engine = Engine(market, bots)
engine.start()

# --- CREATE BUILDINGS ---
buildings = {}
spacing = SCREEN_WIDTH // (len(bots) + 1)
for i, bot in enumerate(bots):
    buildings[bot.name] = Building(spacing * (i + 1) - 40, SCREEN_HEIGHT // 2, bot)

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
    draw_centered(f"TOTAL P/L: {total_pnl:+.2f}", font, total_color, 40)
    status = engine.status
    if engine.equity is not None:
        status += f"   |   Account equity: ${engine.equity:,.2f}"
    draw_centered(status, small_font, LIGHT_GRAY, 70)
    trading_state = "TRADING PAUSED" if engine.paused else "AUTO TRADING: ON"
    draw_centered(f"{trading_state}  (A to toggle, ESC to quit)", font, YELLOW, 95)
    if engine.error:
        draw_centered(engine.error, small_font, RED, 125)

    for building in buildings.values():
        building.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
