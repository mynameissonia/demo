"""
Snowman Run
A "Chrome Dino" style endless runner where a snowman jumps over obstacles
(rocks, trees, icicles) that scroll toward him.

Controls:
    SPACE / UP ARROW  -> Jump
    R                 -> Restart after Game Over
    ESC               -> Quit

Requires: pygame  (pip install pygame)
Run:      python snowman_run.py
"""

import random
import sys
import pygame

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
GROUND_Y = 320

FPS = 60

WHITE = (255, 255, 255)
SKY_TOP = (135, 206, 250)
SKY_BOTTOM = (225, 245, 255)
GROUND_COLOR = (240, 240, 245)
GROUND_LINE = (200, 210, 220)
BLACK = (30, 30, 30)
GRAY = (120, 120, 130)
DARK_GRAY = (70, 70, 80)
GREEN = (60, 130, 80)
BROWN = (110, 75, 50)
RED = (200, 50, 50)
ORANGE = (255, 150, 40)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snowman Run")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("arial", 48, bold=True)
font_med = pygame.font.SysFont("arial", 28, bold=True)
font_small = pygame.font.SysFont("arial", 20)

# ---------------------------------------------------------------------------
# Physics constants
# ---------------------------------------------------------------------------
GRAVITY = 0.9
JUMP_STRENGTH = -15.5
BASE_SPEED = 6.0
MAX_SPEED = 16.0
SPEED_INCREASE_RATE = 0.0015  # per frame, scaled by dt-ish

SNOWMAN_X = 90
SNOWMAN_WIDTH = 44
SNOWMAN_HEIGHT = 62
DUCK_HEIGHT = 40  # crouch height if ducking under a low obstacle (icicle)


class Snowman:
    def __init__(self):
        self.width = SNOWMAN_WIDTH
        self.height = SNOWMAN_HEIGHT
        self.x = SNOWMAN_X
        self.y = GROUND_Y - self.height
        self.vel_y = 0.0
        self.on_ground = True
        self.ducking = False
        self.bob_timer = 0.0

    def rect(self):
        h = DUCK_HEIGHT if self.ducking and self.on_ground else self.height
        y = GROUND_Y - h
        return pygame.Rect(self.x, y, self.width, h)

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

    def update(self, ducking_input):
        self.ducking = ducking_input and self.on_ground

        if not self.on_ground:
            self.vel_y += GRAVITY
            self.y += self.vel_y
            if self.y >= GROUND_Y - self.height:
                self.y = GROUND_Y - self.height
                self.vel_y = 0
                self.on_ground = True
        else:
            self.y = GROUND_Y - self.height
            self.bob_timer += 0.25

    def draw(self, surface):
        r = self.rect()
        cx = r.x + r.width // 2

        if self.ducking:
            # Squashed "duck" snowman: two stacked ellipses, low profile
            base_y = r.bottom
            pygame.draw.ellipse(surface, WHITE, (r.x, base_y - 22, r.width, 22))
            pygame.draw.ellipse(surface, WHITE, (r.x + 6, base_y - 36, r.width - 12, 20))
            pygame.draw.circle(surface, BLACK, (cx + 10, base_y - 30), 2)
            pygame.draw.polygon(
                surface, ORANGE,
                [(cx + 16, base_y - 28), (cx + 26, base_y - 26), (cx + 16, base_y - 24)]
            )
            return

        bob = 0
        if self.on_ground:
            bob = int(2 * abs((self.bob_timer % 2) - 1))

        base_y = r.bottom - bob
        # bottom ball
        bottom_r = 20
        bottom_cy = base_y - bottom_r
        pygame.draw.circle(surface, WHITE, (cx, bottom_cy), bottom_r)
        # middle ball
        mid_r = 15
        mid_cy = bottom_cy - bottom_r - mid_r + 6
        pygame.draw.circle(surface, WHITE, (cx, mid_cy), mid_r)
        # head
        head_r = 11
        head_cy = mid_cy - mid_r - head_r + 6
        pygame.draw.circle(surface, WHITE, (cx, head_cy), head_r)

        # outlines for definition
        pygame.draw.circle(surface, (210, 215, 225), (cx, bottom_cy), bottom_r, 1)
        pygame.draw.circle(surface, (210, 215, 225), (cx, mid_cy), mid_r, 1)
        pygame.draw.circle(surface, (210, 215, 225), (cx, head_cy), head_r, 1)

        # buttons
        for i, dy in enumerate((-4, 4, 12)):
            pygame.draw.circle(surface, BLACK, (cx, mid_cy - 2 + dy), 2)

        # eyes
        pygame.draw.circle(surface, BLACK, (cx - 4, head_cy - 2), 2)
        pygame.draw.circle(surface, BLACK, (cx + 4, head_cy - 2), 2)

        # carrot nose (points in running direction)
        pygame.draw.polygon(
            surface, ORANGE,
            [(cx + head_r - 2, head_cy), (cx + head_r + 10, head_cy + 2), (cx + head_r - 2, head_cy + 4)]
        )

        # twig arms
        arm_swing = 6 if self.on_ground and not self.ducking else 0
        pygame.draw.line(surface, BROWN, (cx - mid_r + 3, mid_cy), (cx - mid_r - 8, mid_cy - 8 + arm_swing), 3)
        pygame.draw.line(surface, BROWN, (cx + mid_r - 3, mid_cy), (cx + mid_r + 8, mid_cy - 8 - arm_swing), 3)

        # little hat
        hat_w = 20
        pygame.draw.rect(surface, DARK_GRAY, (cx - hat_w // 2, head_cy - head_r - 10, hat_w, 8))
        pygame.draw.rect(surface, DARK_GRAY, (cx - hat_w // 2 - 4, head_cy - head_r - 2, hat_w + 8, 4))


class Obstacle:
    """Base scrolling obstacle."""

    def __init__(self, x, kind):
        self.kind = kind
        self.x = float(x)
        self.passed = False

        if kind == "rock_small":
            self.w, self.h = 26, 26
        elif kind == "rock_big":
            self.w, self.h = 38, 38
        elif kind == "tree":
            self.w, self.h = 30, 55
        elif kind == "icicle":  # hangs from the "sky" -> must duck
            self.w, self.h = 22, 40
        else:
            self.w, self.h = 26, 26

        if kind == "icicle":
            self.y = GROUND_Y - 70  # floating, requires ducking to pass under
        else:
            self.y = GROUND_Y - self.h

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, speed):
        self.x -= speed

    def offscreen(self):
        return self.x + self.w < 0

    def draw(self, surface):
        r = self.rect()
        if self.kind in ("rock_small", "rock_big"):
            pygame.draw.ellipse(surface, GRAY, r)
            pygame.draw.ellipse(surface, DARK_GRAY, r, 2)
        elif self.kind == "tree":
            trunk = pygame.Rect(r.x + r.width // 2 - 3, r.bottom - 14, 6, 14)
            pygame.draw.rect(surface, BROWN, trunk)
            pygame.draw.polygon(
                surface, GREEN,
                [(r.x + r.width // 2, r.y), (r.x, r.y + 34), (r.x + r.width, r.y + 34)]
            )
            pygame.draw.polygon(
                surface, GREEN,
                [(r.x + r.width // 2, r.y + 14), (r.x - 3, r.y + r.height - 14), (r.x + r.width + 3, r.y + r.height - 14)]
            )
        elif self.kind == "icicle":
            pygame.draw.polygon(
                surface, (150, 210, 235),
                [(r.x, r.y), (r.x + r.width, r.y), (r.x + r.width // 2, r.bottom)]
            )
            pygame.draw.line(surface, (100, 170, 200), (r.x + r.width // 2, r.y), (r.x + r.width // 2, r.bottom), 1)


class Snowflake:
    def __init__(self):
        self.x = random.uniform(0, SCREEN_WIDTH)
        self.y = random.uniform(-SCREEN_HEIGHT, 0)
        self.speed = random.uniform(0.6, 2.2)
        self.size = random.uniform(1.5, 3.5)

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = random.uniform(-20, 0)
            self.x = random.uniform(0, SCREEN_WIDTH)

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), int(self.size))


def draw_sky_gradient(surface):
    for i in range(GROUND_Y):
        t = i / GROUND_Y
        color = tuple(
            int(SKY_TOP[c] + (SKY_BOTTOM[c] - SKY_TOP[c]) * t) for c in range(3)
        )
        pygame.draw.line(surface, color, (0, i), (SCREEN_WIDTH, i))


def draw_ground(surface, offset):
    pygame.draw.rect(surface, GROUND_COLOR, (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
    dash_w = 18
    gap = 14
    total = dash_w + gap
    start = -int(offset) % total
    x = -total + start
    while x < SCREEN_WIDTH:
        pygame.draw.line(surface, GROUND_LINE, (x, GROUND_Y + 4), (x + dash_w, GROUND_Y + 4), 3)
        x += total


def spawn_obstacle(x):
    kind = random.choices(
        ["rock_small", "rock_big", "tree", "icicle"],
        weights=[30, 25, 25, 20],
        k=1,
    )[0]
    return Obstacle(x, kind)


def main():
    snowman = Snowman()
    obstacles = []
    snowflakes = [Snowflake() for _ in range(60)]

    speed = BASE_SPEED
    ground_offset = 0.0
    score = 0.0
    high_score = 0
    next_spawn_x = SCREEN_WIDTH + 100

    game_over = False
    running = True

    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    if game_over:
                        # restart
                        snowman = Snowman()
                        obstacles = []
                        speed = BASE_SPEED
                        score = 0.0
                        next_spawn_x = SCREEN_WIDTH + 100
                        game_over = False
                    else:
                        snowman.jump()
                elif event.key == pygame.K_r and game_over:
                    snowman = Snowman()
                    obstacles = []
                    speed = BASE_SPEED
                    score = 0.0
                    next_spawn_x = SCREEN_WIDTH + 100
                    game_over = False

        keys = pygame.key.get_pressed()
        ducking_input = keys[pygame.K_DOWN] or keys[pygame.K_s]

        if not game_over:
            snowman.update(ducking_input)

            speed = min(MAX_SPEED, speed + SPEED_INCREASE_RATE * dt)
            ground_offset += speed

            for obs in obstacles:
                obs.update(speed)
            obstacles = [o for o in obstacles if not o.offscreen()]

            if not obstacles or obstacles[-1].x < SCREEN_WIDTH - 260:
                if len(obstacles) == 0 or SCREEN_WIDTH - obstacles[-1].x > random.randint(220, 380):
                    obstacles.append(spawn_obstacle(SCREEN_WIDTH + 20))

            snow_rect = snowman.rect()
            for obs in obstacles:
                if snow_rect.colliderect(obs.rect()):
                    game_over = True
                    high_score = max(high_score, int(score))

            score += speed * 0.05

        for flake in snowflakes:
            flake.update()

        # ---- Draw ----
        draw_sky_gradient(screen)
        for flake in snowflakes:
            flake.draw(screen)
        draw_ground(screen, ground_offset)

        for obs in obstacles:
            obs.draw(screen)
        snowman.draw(screen)

        score_surf = font_small.render(f"Score: {int(score)}", True, BLACK)
        screen.blit(score_surf, (SCREEN_WIDTH - score_surf.get_width() - 20, 16))
        best_surf = font_small.render(f"Best: {int(high_score)}", True, GRAY)
        screen.blit(best_surf, (SCREEN_WIDTH - best_surf.get_width() - 20, 38))

        if game_over:
            high_score = max(high_score, int(score))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 140))
            screen.blit(overlay, (0, 0))

            title = font_big.render("Game Over", True, RED)
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)))

            sub = font_med.render(f"Score: {int(score)}", True, BLACK)
            screen.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 15)))

            hint = font_small.render("Press SPACE or R to restart  |  ESC to quit", True, DARK_GRAY)
            screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 55)))
        elif int(score) == 0:
            hint = font_small.render("Press SPACE / UP to jump, DOWN to duck under icicles", True, DARK_GRAY)
            screen.blit(hint, (20, 16))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
