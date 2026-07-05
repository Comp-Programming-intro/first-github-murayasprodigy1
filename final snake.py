import os
import sys
import random
from datetime import datetime
import pygame

# ---------- CONFIGURATION & CONSTANTS ----------
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20
WIDTH = CELL_SIZE * GRID_WIDTH
HEIGHT = CELL_SIZE * GRID_HEIGHT

BASE_SPEED = 10.0      # Starting speed (FPS)
MAX_SPEED = 25.0       # Speed cap
SPEED_PER_FOOD = 0.3   # Incremental speed increase per food

HIGHSCORE_FILE = "highscore.txt"
HIGHSCORE_LOG_FILE = "highscore_log.txt"
LOG_ENTRIES_SHOWN = 5  

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (150, 150, 150)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 130, 0)
RED = (200, 30, 30)

IMAGE_SEARCH_DIRS = [".", "assets", "images"]


# ---------- DATA PERSISTENCE ----------
def load_highscore():
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, "r") as f:
                return int(f.read().strip() or 0)
    except Exception:
        pass
    return 0


def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))
    except Exception:
        pass


def log_score(score):
    try:
        with open(HIGHSCORE_LOG_FILE, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} score={score}\n")
    except Exception:
        pass


def load_recent_log_entries(n=LOG_ENTRIES_SHOWN):
    try:
        if not os.path.exists(HIGHSCORE_LOG_FILE):
            return []
        with open(HIGHSCORE_LOG_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        return lines[-n:][::-1]
    except Exception:
        return []


# ---------- ASSET MANAGEMENT ----------
def find_image_path(filename):
    for folder in IMAGE_SEARCH_DIRS:
        candidate = os.path.join(folder, filename)
        if os.path.exists(candidate):
            return candidate
    return None


def load_image_safe(filename, fallback_color, cell_size):
    path = find_image_path(filename)
    if path:
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (cell_size, cell_size))
        except pygame.error:
            pass
    surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    surf.fill(fallback_color)
    return surf


def rotated_for_direction(image, direction):
    if direction == (1, 0):
        return image
    elif direction == (-1, 0):
        return pygame.transform.rotate(image, 180)
    elif direction == (0, -1):
        return pygame.transform.rotate(image, 90)
    elif direction == (0, 1):
        return pygame.transform.rotate(image, -90)
    return image


# ---------- GAMEPLAY UTILITIES ----------
def random_food_position(snake_positions):
    available = [(x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT) if (x, y) not in snake_positions]
    if not available:
        return (0, 0)  # Edge case fallback for a perfect maximum length win
    return random.choice(available)


def draw_text(surface, font, text, x, y, center=False, topleft=False, color=WHITE):
    txt = font.render(text, True, color)
    rect = txt.get_rect()
    if center:
        rect.center = (x, y)
    elif topleft:
        rect.topleft = (x, y)
    else:
        rect.topright = (x, y)
    surface.blit(txt, rect)


# ---------- UI SCREENS ----------
def game_over_screen(screen, small_font, big_font, score, highscore, is_new_highscore):
    clock = pygame.time.Clock()
    recent = load_recent_log_entries()
    while True:
        screen.fill(BLACK)
        draw_text(screen, big_font, "GAME OVER", WIDTH // 2, 60, center=True)
        draw_text(screen, small_font, f"Score: {score}    Highscore: {highscore}", WIDTH // 2, 110, center=True)
        
        if is_new_highscore:
            draw_text(screen, small_font, "New high score!", WIDTH // 2, 135, center=True, color=GREEN)

        draw_text(screen, small_font, "Recent scores:", WIDTH // 2, 175, center=True, color=GREY)
        for i, entry in enumerate(recent):
            draw_text(screen, small_font, entry, WIDTH // 2, 200 + i * 22, center=True, color=GREY)

        draw_text(screen, small_font, "Press R to restart, Q or ESC to quit", WIDTH // 2, HEIGHT - 30, center=True)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
        clock.tick(15)


# ---------- MAIN GAME ARCHITECTURE ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Snake Architecture Variant")
    clock = pygame.time.Clock()

    # Asset Setup
    snake_head_img_base = load_image_safe("snake_head.png", DARK_GREEN, CELL_SIZE)
    if find_image_path("snake_head.png") is None:
        snake_head_img_base = load_image_safe("snake_body.png", DARK_GREEN, CELL_SIZE)
    snake_body_img = load_image_safe("snake_body.png", GREEN, CELL_SIZE)
    apple_img = load_image_safe("apple.png", RED, CELL_SIZE)

    small_font = pygame.font.SysFont("consolas", 18)
    big_font = pygame.font.SysFont("consolas", 48)
    highscore = load_highscore()

    def reset_game():
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        s = [(start_x - i, start_y) for i in range(3)]
        return s, (1, 0), random_food_position(s), 0, BASE_SPEED

    snake, current_direction, food, score, speed = reset_game()
    direction_queue = [] # Buffers swift inputs to prevent self-collision
    paused = False

    while True:
        # 1. Event & Input processing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_r:
                    # Allow instant recovery restart at any moment
                    snake, current_direction, food, score, speed = reset_game()
                    direction_queue.clear()
                    paused = False

                if not paused:
                    # Determine target vector from input
                    next_dir = None
                    if event.key in (pygame.K_UP, pygame.K_w):
                        next_dir = (0, -1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        next_dir = (0, 1)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        next_dir = (-1, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        next_dir = (1, 0)

                    if next_dir:
                        # Validate against the last item added to the queue, or current state
                        last_dir = direction_queue[-1] if direction_queue else current_direction
                        # Ensure input is not a 180-degree turnaround
                        if (next_dir[0] + last_dir[0] != 0 or next_dir[1] + last_dir[1] != 0):
                            if len(direction_queue) < 2: # Keep buffer minimal
                                direction_queue.append(next_dir)

        # 2. Pause Handling State
        if paused:
            screen.fill(BLACK)
            draw_text(screen, big_font, "PAUSED", WIDTH // 2, HEIGHT // 2 - 20, center=True)
            draw_text(screen, small_font, "Press P to resume", WIDTH // 2, HEIGHT // 2 + 20, center=True)
            pygame.display.flip()
            clock.tick(15)
            continue

        # 3. Game State Logic Step
        if direction_queue:
            current_direction = direction_queue.pop(0)

        head_x, head_y = snake[0]
        new_head = (head_x + current_direction[0], head_y + current_direction[1])

        # Boundary checks & Self-collision checks
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
            new_head[1] < 0 or new_head[1] >= GRID_HEIGHT or
            new_head in snake[:-1]): # Exclude tail end since it moves out of the way on safe frames
            
            is_new_high = score > highscore
            if is_new_high:
                highscore = score
                save_highscore(highscore)
            log_score(score)
            
            game_over_screen(screen, small_font, big_font, score, highscore, is_new_high)
            snake, current_direction, food, score, speed = reset_game()
            direction_queue.clear()
            continue

        snake.insert(0, new_head)

        # Scoring & Target generation
        if new_head == food:
            score += 1
            speed = min(speed + SPEED_PER_FOOD, MAX_SPEED)
            food = random_food_position(snake)
        else:
            snake.pop()

        # 4. Drawing Cycle
        screen.fill(BLACK)
        screen.blit(apple_img, (food[0] * CELL_SIZE, food[1] * CELL_SIZE))

        head_img = rotated_for_direction(snake_head_img_base, current_direction)
        for i, pos in enumerate(snake):
            x, y = pos[0] * CELL_SIZE, pos[1] * CELL_SIZE
            if i == 0:
                screen.blit(head_img, (x, y))
            else:
                screen.blit(snake_body_img, (x, y))

        # Interface Rendering
        draw_text(screen, small_font, f"Score: {score}", 8, 8, topleft=True)
        draw_text(screen, small_font, f"Highscore: {highscore}", WIDTH - 8, 8)
        draw_text(screen, small_font, "P = pause | R = manual restart", WIDTH // 2, HEIGHT - 18, center=True)

        pygame.display.flip()
        clock.tick(speed)


if __name__ == "__main__":
    main()