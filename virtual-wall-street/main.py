import pygame
import random
import sys

# --- CONFIG ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 600
FPS = 60
BOT_COUNT = 5
AUTO_TRADE_INTERVAL_MS = 1500  # how often bots trade on their own

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Virtual Wall Street")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20, bold=True)

# --- BOT CLASS ---
class TradingBot:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.width = 80
        self.height = 150
        self.name = name
        self.pnl = 0
        self.floating_texts = []

    def trade(self):
        # Simulate a trade result
        profit = round(random.uniform(-200, 200), 2)
        self.pnl += profit
        color = GREEN if profit >= 0 else RED
        self.floating_texts.append(FloatingText(f"{profit:+.2f}", self.x + self.width // 2, self.y - 50, color))

    def draw(self, surface):
        # Draw building
        pygame.draw.rect(surface, GRAY, (self.x, self.y, self.width, self.height))
        # Draw bot name
        name_text = font.render(self.name, True, WHITE)
        surface.blit(name_text, (self.x + (self.width - name_text.get_width()) // 2, self.y + self.height + 5))
        # Draw P/L above building
        pnl_color = GREEN if self.pnl >= 0 else RED
        pnl_text = font.render(f"{self.pnl:+.2f}", True, pnl_color)
        surface.blit(pnl_text, (self.x + (self.width - pnl_text.get_width()) // 2, self.y - 25))
        # Draw floating trade texts
        for ft in self.floating_texts:
            ft.draw(surface)

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
        self.lifetime = 60  # frames

    def update(self):
        self.y -= 0.5
        self.lifetime -= 1

    def draw(self, surface):
        txt = font.render(self.text, True, self.color)
        surface.blit(txt, (self.x - txt.get_width() // 2, self.y))

    def is_expired(self):
        return self.lifetime <= 0

# --- CREATE BOTS ---
bots = []
spacing = SCREEN_WIDTH // (BOT_COUNT + 1)
for i in range(BOT_COUNT):
    bots.append(TradingBot(spacing * (i + 1) - 40, SCREEN_HEIGHT // 2, f"Bot{i+1}"))

# --- AUTO TRADING ---
AUTO_TRADE_EVENT = pygame.USEREVENT + 1
auto_trading = True
pygame.time.set_timer(AUTO_TRADE_EVENT, AUTO_TRADE_INTERVAL_MS)

# --- MAIN LOOP ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Trigger trades for all bots
                for bot in bots:
                    bot.trade()
            elif event.key == pygame.K_a:
                # Toggle auto trading on/off
                auto_trading = not auto_trading
                pygame.time.set_timer(AUTO_TRADE_EVENT, AUTO_TRADE_INTERVAL_MS if auto_trading else 0)
        elif event.type == AUTO_TRADE_EVENT:
            for bot in bots:
                bot.trade()

    # Update
    for bot in bots:
        bot.update()

    # Draw
    screen.fill(BLACK)
    total_pnl = sum(bot.pnl for bot in bots)
    total_color = GREEN if total_pnl >= 0 else RED
    total_text = font.render(f"TOTAL P/L: {total_pnl:+.2f}", True, total_color)
    screen.blit(total_text, (SCREEN_WIDTH // 2 - total_text.get_width() // 2, 50))
    status = "AUTO TRADING: ON" if auto_trading else "AUTO TRADING: OFF"
    status_text = font.render(f"{status}  (A to toggle, SPACE to trade now)", True, YELLOW)
    screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, 85))

    for bot in bots:
        bot.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
