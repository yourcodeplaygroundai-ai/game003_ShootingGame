# JET DEFENDER - ENEMIES IN FRONT! (Copy & Run)
import pygame
import numpy as np
import sys
import random

# ========= INIT =========
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
screen = pygame.display.set_mode((1920, 1024))
pygame.display.set_caption("JET DEFENDER - ENEMIES VISIBLE & IN FRONT!")
clock = pygame.time.Clock()
FPS = 60

# ========= COLORS =========
WHITE, BLACK = (255,255,255), (0,0,0)
YELLOW, RED = (255,220,0), (255,50,50)
GREEN, TWILIGHT, SPACE = (100,220,100), (80,60,120), (10,5,30)

font = pygame.font.SysFont("Arial", 50, bold=True)
big_font = pygame.font.SysFont("Arial", 100, bold=True)

# ========= SOUNDS =========
def create_sound(freq=440, duration=0.1, volume=0.5, wave_type="sine"):
    rate = 44100
    samples = int(rate * duration)
    t = np.linspace(0, duration, samples, False)
    if wave_type == "laser":
        wave = np.sin(2 * np.pi * (800 + t*1000) * t) * np.exp(-t*8)
    elif wave_type == "hit":
        wave = np.random.randn(samples) * np.exp(-t*20)
    elif wave_type == "boom":
        wave = np.sin(2 * np.pi * 80 * t) * np.exp(-t*5) * 0.8
    elif wave_type == "gameover":
        notes = [200, 180, 150, 120, 100]
        wave = np.zeros(samples)
        seg = samples // len(notes)
        for i, f in enumerate(notes):
            start = i * seg
            end = (i+1) * seg
            wave[start:end] = np.sin(2 * np.pi * f * t[start:end]) * np.exp(-t[start:end]*3)
    else:
        wave = np.sin(2 * np.pi * freq * t)
    wave = (wave * 32767 * volume).astype(np.int16)
    stereo = np.column_stack((wave, wave))
    return pygame.sndarray.make_sound(stereo)

SHOOT = create_sound(wave_type="laser", duration=0.15, volume=0.6)
HIT = create_sound(wave_type="hit", duration=0.08, volume=0.7)
BOOM = create_sound(wave_type="boom", duration=0.4, volume=0.8)
GAMEOVER = create_sound(wave_type="gameover", duration=1.2, volume=0.6)

# ========= PLAYER =========
def draw_jet():
    s = pygame.Surface((100,100), pygame.SRCALPHA)
    pygame.draw.rect(s, (0,120,255), (30,20,40,50), border_radius=15)
    pygame.draw.rect(s, (0,180,255), (35,25,30,40), border_radius=10)
    pygame.draw.polygon(s, (0,100,200), [(20,40),(0,60),(15,40)])
    pygame.draw.polygon(s, (0,100,200), [(80,40),(100,60),(85,40)])
    pygame.draw.ellipse(s, (200,255,255), (40,30,20,25))
    pygame.draw.polygon(s, (255,150,0), [(40,70),(50,70),(45,85)])
    return s

player_img = draw_jet()
player_rect = player_img.get_rect(centerx=960, bottom=900)
player_speed = 8
base_speed = 8

# ========= BULLET =========
bullet_img = pygame.Surface((10,25), pygame.SRCALPHA)
pygame.draw.rect(bullet_img, YELLOW, (0,0,10,25), border_radius=5)
bullets = []
bullet_speed = 16

# ========= ENEMIES =========
def tiger():
    s = pygame.Surface((80,80), pygame.SRCALPHA)
    pygame.draw.circle(s, (255,150,0), (40,50), 30)
    pygame.draw.circle(s, (255,170,0), (40,30), 25)
    for y in range(20,60,8): pygame.draw.line(s, (200,80,0), (20,y), (60,y), 6)
    pygame.draw.circle(s, WHITE, (32,28), 8); pygame.draw.circle(s, BLACK, (34,28), 4)
    pygame.draw.circle(s, WHITE, (48,28), 8); pygame.draw.circle(s, BLACK, (50,28), 4)
    return s

def cat():
    s = pygame.Surface((70,80), pygame.SRCALPHA)
    pygame.draw.circle(s, (200,200,200), (35,50), 28)
    pygame.draw.circle(s, (180,180,180), (35,35), 20)
    pygame.draw.polygon(s, (200,200,200), [(20,20),(25,10),(35,18)])
    pygame.draw.polygon(s, (200,200,200), [(50,20),(45,10),(35,18)])
    pygame.draw.circle(s, (0,255,0), (28,35), 7)
    pygame.draw.circle(s, (0,255,0), (42,35), 7)
    return s

def spider():
    s = pygame.Surface((90,90), pygame.SRCALPHA)
    pygame.draw.circle(s, (120,0,180), (45,45), 25)
    for a in range(0,360,45):
        dx = int(30 * (1 if a%90==0 else 0.7) * (1 if a<180 else -1))
        dy = int(30 * (1 if a%90==0 else 0.7) * (1 if a in [0,90,270] else -1))
        pygame.draw.line(s, (80,0,120), (45,45), (45+dx,45+dy), 6)
    pygame.draw.circle(s, RED, (38,40), 7); pygame.draw.circle(s, RED, (52,40), 7)
    return s

enemies = []
enemy_imgs = [tiger(), cat(), spider()]
spawn_timer = 0

# ========= BACKGROUND =========
def draw_bg(name):
    if name == "clear":
        screen.fill(GREEN)
        pygame.draw.circle(screen, (255,230,0), (1600,200), 100)
        for x in range(200,1920,300):
            pygame.draw.ellipse(screen, WHITE, (x,100,200,60))
    elif name == "darker":
        screen.fill(TWILIGHT)
        pygame.draw.circle(screen, (220,220,180), (300,150), 70)
        for x in range(200,1920,350):
            pygame.draw.rect(screen, (40,30,20), (x,700,80,400))
            pygame.draw.circle(screen, (30,80,30), (x+40,680), 80)
    else:
        screen.fill(SPACE)
        for _ in range(300):
            pygame.draw.circle(screen, WHITE, (random.randint(0,1920), random.randint(0,1024)), 1)

bg = {
    "clear": lambda: draw_bg("clear"),
    "darker": lambda: draw_bg("darker"),
    "space": lambda: draw_bg("space")
}
current_bg = "clear"

# ========= GAME =========
score = 0
game_over = False

# ========= MAIN LOOP =========
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                b = bullet_img.get_rect(centerx=player_rect.centerx, bottom=player_rect.top)
                bullets.append(b)
                SHOOT.play()
            if event.key == pygame.K_r and game_over:
                score = 0
                player_rect.centerx = 960
                player_rect.bottom = 900
                player_speed = base_speed
                bullets.clear()
                enemies.clear()
                game_over = False
                current_bg = "clear"
                spawn_timer = 0

    if not game_over:
        # CONTROLS
        k = pygame.key.get_pressed()
        if k[pygame.K_LEFT]  and player_rect.left > 0:      player_rect.x -= player_speed
        if k[pygame.K_RIGHT] and player_rect.right < 1920:  player_rect.x += player_speed
        if k[pygame.K_UP]    and player_rect.top > 0:       player_rect.y -= player_speed
        if k[pygame.K_DOWN]  and player_rect.bottom < 1024: player_rect.y += player_speed

        # SPAWN ENEMIES (NOW VISIBLE!)
        spawn_timer += 1
        if spawn_timer > 60:  # Every second
            spawn_timer = 0
            img = random.choice(enemy_imgs)
            r = img.get_rect()
            side = random.choice(["top", "left", "right"])
            if side == "top":
                r.midbottom = (random.randint(200, 1720), -100)
                vx, vy = random.randint(-2, 2), random.randint(3, 6)
            elif side == "left":
                r.midright = (-100, random.randint(200, 800))
                vx, vy = random.randint(4, 7), random.randint(-2, 2)
            else:
                r.midleft = (1920 + 100, random.randint(200, 800))
                vx, vy = random.randint(-7, -4), random.randint(-2, 2)
            enemies.append({"img": img, "rect": r, "vx": vx, "vy": vy})

        # MOVE ENEMIES
        for e in enemies[:]:
            e["rect"].x += e["vx"]
            e["rect"].y += e["vy"]
            if e["rect"].left < -200 or e["rect"].right > 2120:
                e["vx"] *= -1
            if e["rect"].top < -200 or e["rect"].bottom > 1244:
                e["vy"] *= -1
            if e["rect"].top > 1100:
                enemies.remove(e)

        # BULLETS
        for b in bullets[:]:
            b.y -= bullet_speed
            if b.bottom < -50:
                bullets.remove(b)

        # COLLISIONS
        for b in bullets[:]:
            for e in enemies[:]:
                if b.colliderect(e["rect"]):
                    bullets.remove(b)
                    enemies.remove(e)
                    score += 1
                    HIT.play()
                    BOOM.play()
                    break
            else:
                continue
            break

        for e in enemies:
            if player_rect.colliderect(e["rect"]):
                game_over = True
                GAMEOVER.play()

        if score >= 5 and player_speed == base_speed:
            player_speed = 14

        current_bg = "clear" if score <= 2 else "darker" if score <= 4 else "space"

    # ========= DRAW: BACKGROUND FIRST! =========
    bg[current_bg]()  # Background drawn FIRST

    # THEN: Enemies, Player, Bullets ON TOP!
    for e in enemies:
        screen.blit(e["img"], e["rect"])
        # Optional: debug red box
        pygame.draw.rect(screen, RED, e["rect"], 2)

    screen.blit(player_img, player_rect)
    for b in bullets:
        screen.blit(bullet_img, b)

    # UI
    screen.blit(font.render(f"SCORE: {score}", True, WHITE), (50, 50))
    if player_speed > base_speed:
        screen.blit(font.render("TURBO!", True, YELLOW), (50, 110))

    # GAME OVER
    if game_over:
        overlay = pygame.Surface((1920, 1024))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        go = big_font.render("GAME OVER", True, RED)
        fs = font.render(f"Score: {score}", True, YELLOW)
        rs = font.render("Press R to Restart", True, WHITE)
        screen.blit(go, (960 - go.get_width()//2, 300))
        screen.blit(fs, (960 - fs.get_width()//2, 450))
        screen.blit(rs, (960 - rs.get_width()//2, 550))

    pygame.display.flip()

print("JET DEFENDER - ENEMIES NOW IN FRONT & VISIBLE!")
pygame.quit()
sys.exit()