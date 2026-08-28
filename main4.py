"""
Robotron-style twin-stick arena shooter.

A single fixed-screen arena swarming with enemies. Rescue Humans by
touching them, avoid the electrified Electrodes, and clear each wave.

Controls:
    ARROW KEYS    - move (8-directional)
    W / A / S / D - fire (8-directional, independent of movement)
    ENTER         - restart after Game Over
"""
import math
import os
import random

import pygame
from pygame import mixer

pygame.init()
mixer.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

ARENA_LEFT = 24
ARENA_TOP = 90
ARENA_RIGHT = SCREEN_WIDTH - 24
ARENA_BOTTOM = SCREEN_HEIGHT - 24

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (80, 220, 255)
MAGENTA = (230, 60, 200)
GREEN = (80, 255, 120)
YELLOW = (255, 220, 80)
RED = (255, 70, 70)
ORANGE = (255, 150, 40)
ELECTRIC_BLUE = (120, 200, 255)

FONT_NAME = 'Futura'


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def tint_surface(surf, color):
    tinted = surf.copy()
    overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, 255))
    tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


def load_numbered_images(folder, count, size):
    images = []
    files = sorted(os.listdir(folder), key=lambda f: int(f.split('.')[0]))
    for f in files[:count]:
        img = pygame.image.load(os.path.join(folder, f)).convert_alpha()
        img = pygame.transform.scale(img, size)
        images.append(img)
    return images


# ---------------------------------------------------------------------------
# assets
# ---------------------------------------------------------------------------
display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Robotron')
clock = pygame.time.Clock()

human_images = load_numbered_images('img/tile/humans/renamed', 8, (22, 30))
monster_images = load_numbered_images('img/tile/monsters/renamed', 10, (36, 36))

GRUNT_COLOR = (255, 120, 60)
HULK_COLOR = (170, 170, 190)
BRAIN_COLOR = (255, 120, 220)
ENFORCER_COLOR = (120, 200, 255)
PROG_COLOR = (200, 40, 40)

grunt_images = [tint_surface(img, GRUNT_COLOR) for img in monster_images]
hulk_images = [tint_surface(pygame.transform.scale(img, (54, 54)), HULK_COLOR) for img in monster_images]
brain_images = [tint_surface(pygame.transform.scale(img, (30, 30)), BRAIN_COLOR) for img in monster_images]
enforcer_images = [tint_surface(pygame.transform.scale(img, (34, 34)), ENFORCER_COLOR) for img in monster_images]
prog_images = [tint_surface(img, PROG_COLOR) for img in human_images]

shoot_sound = mixer.Sound('sounds/robotron_shoot.wav')
shoot_sound.set_volume(0.25)
hit_sound = mixer.Sound('sounds/robotron_hit.wav')
hit_sound.set_volume(0.45)
explosion_sound = mixer.Sound('sounds/explosion.wav')
explosion_sound.set_volume(0.5)
bomb_sound = mixer.Sound('sounds/bomb.wav')
bomb_sound.set_volume(0.6)
rescue_sound = mixer.Sound('sounds/rescue.wav')
rescue_sound.set_volume(0.5)
brain_zap_sound = mixer.Sound('sounds/brain_zap.wav')
brain_zap_sound.set_volume(0.5)
extra_life_sound = mixer.Sound('sounds/extra_life.wav')
extra_life_sound.set_volume(0.55)

mixer.music.load('sounds/robotron_theme.wav')
mixer.music.set_volume(0.3)
mixer.music.play(loops=-1)


# ---------------------------------------------------------------------------
# effects
# ---------------------------------------------------------------------------
class Burst:
    """small fading particle burst for a kill"""
    duration = 260

    def __init__(self, x, y, color, particle_count=10):
        self.x = x
        self.y = y
        self.color = color
        self.spawn_time = pygame.time.get_ticks()
        self.particles = []
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.2, 4.0)
            self.particles.append({
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'size': random.randint(2, 4),
            })

    def dead(self):
        return pygame.time.get_ticks() - self.spawn_time > self.duration

    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        progress = elapsed / self.duration
        alpha = max(0, int(255 * (1 - progress)))
        for p in self.particles:
            px = self.x + p['dx'] * elapsed * 0.08
            py = self.y + p['dy'] * elapsed * 0.08
            size = max(1, int(p['size'] * (1 - progress)))
            part = pygame.Surface((size, size), pygame.SRCALPHA)
            part.fill((*self.color, alpha))
            surface.blit(part, (px - size / 2, py - size / 2))


# ---------------------------------------------------------------------------
# entities
# ---------------------------------------------------------------------------
class Human:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = 'walking'  # walking, claimed, captured
        self.image = random.choice(human_images)
        self.radius = 11
        self.dir_x = random.choice([-1, 0, 1])
        self.dir_y = random.choice([-1, 0, 1])

    def update(self):
        if self.state != 'walking':
            return
        if random.random() < 0.02:
            self.dir_x = random.choice([-1, 0, 1])
            self.dir_y = random.choice([-1, 0, 1])
        self.x = clamp(self.x + self.dir_x * 0.8, ARENA_LEFT, ARENA_RIGHT)
        self.y = clamp(self.y + self.dir_y * 0.8, ARENA_TOP, ARENA_BOTTOM)

    def draw(self, surface):
        if self.state == 'captured':
            return
        rect = self.image.get_rect(center=(self.x, self.y))
        surface.blit(self.image, rect)


class Grunt:
    speed = 2.3
    score_value = 100
    burst_color = GRUNT_COLOR

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 1
        self.image = random.choice(grunt_images)
        self.radius = 15

    def update(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy) or 1
        self.x = clamp(self.x + dx / dist * self.speed, ARENA_LEFT, ARENA_RIGHT)
        self.y = clamp(self.y + dy / dist * self.speed, ARENA_TOP, ARENA_BOTTOM)

    def draw(self, surface):
        rect = self.image.get_rect(center=(self.x, self.y))
        surface.blit(self.image, rect)


class Hulk:
    speed = 1.1
    score_value = 250
    burst_color = HULK_COLOR

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 6
        self.image = random.choice(hulk_images)
        self.radius = 26

    def update(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy) or 1
        self.x = clamp(self.x + dx / dist * self.speed, ARENA_LEFT, ARENA_RIGHT)
        self.y = clamp(self.y + dy / dist * self.speed, ARENA_TOP, ARENA_BOTTOM)

    def draw(self, surface):
        rect = self.image.get_rect(center=(self.x, self.y))
        surface.blit(self.image, rect)


class Brain:
    speed = 1.8
    score_value = 150
    burst_color = BRAIN_COLOR

    def __init__(self, x, y, game):
        self.x = x
        self.y = y
        self.hp = 1
        self.image = random.choice(brain_images)
        self.radius = 14
        self.target = None
        self.game = game

    def pick_target(self, humans):
        available = [h for h in humans if h.state == 'walking']
        if not available:
            self.target = None
            return
        nearest = min(available, key=lambda h: math.hypot(h.x - self.x, h.y - self.y))
        nearest.state = 'claimed'
        self.target = nearest

    def update(self, humans):
        if self.target is None or self.target.state != 'claimed':
            self.pick_target(humans)

        if self.target is None:
            self.x = clamp(self.x + math.sin(pygame.time.get_ticks() * 0.001 + self.radius) * 0.6,
                            ARENA_LEFT, ARENA_RIGHT)
            self.y = clamp(self.y + math.cos(pygame.time.get_ticks() * 0.0013 + self.radius) * 0.6,
                            ARENA_TOP, ARENA_BOTTOM)
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < 14:
            self.target.state = 'captured'
            self.game.on_human_captured(self.target)
            self.target = None
        else:
            self.x = clamp(self.x + dx / dist * self.speed, ARENA_LEFT, ARENA_RIGHT)
            self.y = clamp(self.y + dy / dist * self.speed, ARENA_TOP, ARENA_BOTTOM)

    def draw(self, surface):
        rect = self.image.get_rect(center=(self.x, self.y))
        surface.blit(self.image, rect)


class Prog:
    """a captured human, reprogrammed into a fast homing killer"""
    speed = 3.4
    score_value = 200
    burst_color = PROG_COLOR

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 1
        self.image = random.choice(prog_images)
        self.radius = 12

    def update(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy) or 1
        self.x = clamp(self.x + dx / dist * self.speed, ARENA_LEFT, ARENA_RIGHT)
        self.y = clamp(self.y + dy / dist * self.speed, ARENA_TOP, ARENA_BOTTOM)

    def draw(self, surface):
        rect = self.image.get_rect(center=(self.x, self.y))
        surface.blit(self.image, rect)


class Electrode:
    """static hazard - deadly to touch, cannot be destroyed"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 13

    def draw(self, surface):
        pulse = 3 + int(2 * math.sin(pygame.time.get_ticks() * 0.01 + self.x))
        pygame.draw.circle(surface, ELECTRIC_BLUE, (int(self.x), int(self.y)), 9 + pulse, 2)
        pygame.draw.line(surface, WHITE, (self.x - 9, self.y), (self.x + 9, self.y), 2)
        pygame.draw.line(surface, WHITE, (self.x, self.y - 9), (self.x, self.y + 9), 2)


class Bullet:
    speed = 14
    life = 55

    def __init__(self, x, y, dx, dy, hostile=False):
        self.x = x
        self.y = y
        self.vx = dx * self.speed
        self.vy = dy * self.speed
        self.hostile = hostile
        self.radius = 4
        self.age = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.age += 1

    def dead(self):
        if self.age > self.life:
            return True
        return not (ARENA_LEFT - 20 <= self.x <= ARENA_RIGHT + 20 and ARENA_TOP - 20 <= self.y <= ARENA_BOTTOM + 20)

    def draw(self, surface):
        color = RED if self.hostile else CYAN
        size = 5 if self.hostile else 6
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(surface, color, rect)


class Enforcer:
    speed = 1.4
    fire_interval = 100
    score_value = 175
    burst_color = ENFORCER_COLOR

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 1
        self.image = random.choice(enforcer_images)
        self.radius = 16
        self.fire_cooldown = random.randint(0, self.fire_interval)
        self.wander_angle = random.uniform(0, 2 * math.pi)

    def update(self, player, bullets):
        self.wander_angle += random.uniform(-0.15, 0.15)
        dist_to_player = math.hypot(player.x - self.x, player.y - self.y)
        if dist_to_player < 260:
            self.x = clamp(self.x - (player.x - self.x) / (dist_to_player or 1) * self.speed,
                            ARENA_LEFT, ARENA_RIGHT)
            self.y = clamp(self.y - (player.y - self.y) / (dist_to_player or 1) * self.speed,
                            ARENA_TOP, ARENA_BOTTOM)
        else:
            self.x = clamp(self.x + math.cos(self.wander_angle) * self.speed, ARENA_LEFT, ARENA_RIGHT)
            self.y = clamp(self.y + math.sin(self.wander_angle) * self.speed, ARENA_TOP, ARENA_BOTTOM)

        self.fire_cooldown -= 1
        if self.fire_cooldown <= 0:
            self.fire_cooldown = self.fire_interval
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.hypot(dx, dy) or 1
            bullets.append(Bullet(self.x, self.y, dx / dist, dy / dist, hostile=True))

    def draw(self, surface):
        rect = self.image.get_rect(center=(self.x, self.y))
        surface.blit(self.image, rect)


class Player:
    speed = 5.5
    fire_cooldown_max = 6

    def __init__(self):
        self.x = SCREEN_WIDTH / 2
        self.y = (ARENA_TOP + ARENA_BOTTOM) / 2
        self.radius = 14
        self.facing = (1, 0)
        self.fire_cooldown = 0
        self.invulnerable_until = pygame.time.get_ticks() + 1800

    def invulnerable(self):
        return pygame.time.get_ticks() < self.invulnerable_until

    def update(self, keys):
        mx = 0
        my = 0
        if keys[pygame.K_LEFT]:
            mx -= 1
        if keys[pygame.K_RIGHT]:
            mx += 1
        if keys[pygame.K_UP]:
            my -= 1
        if keys[pygame.K_DOWN]:
            my += 1
        if mx or my:
            norm = math.hypot(mx, my)
            self.x = clamp(self.x + mx / norm * self.speed, ARENA_LEFT, ARENA_RIGHT)
            self.y = clamp(self.y + my / norm * self.speed, ARENA_TOP, ARENA_BOTTOM)

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def aim_direction(self, keys):
        fx = 0
        fy = 0
        if keys[pygame.K_a]:
            fx -= 1
        if keys[pygame.K_d]:
            fx += 1
        if keys[pygame.K_w]:
            fy -= 1
        if keys[pygame.K_s]:
            fy += 1
        if fx or fy:
            norm = math.hypot(fx, fy)
            return fx / norm, fy / norm
        return None

    def shoot(self, direction, bullets):
        if self.fire_cooldown == 0:
            self.fire_cooldown = self.fire_cooldown_max
            self.facing = direction
            bullets.append(Bullet(self.x, self.y, direction[0], direction[1], hostile=False))
            shoot_sound.play()

    def draw(self, surface):
        if self.invulnerable() and (pygame.time.get_ticks() // 100) % 2 == 0:
            return
        pygame.draw.circle(surface, CYAN, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)
        bx = self.x + self.facing[0] * (self.radius + 10)
        by = self.y + self.facing[1] * (self.radius + 10)
        pygame.draw.line(surface, WHITE, (self.x, self.y), (bx, by), 3)


# ---------------------------------------------------------------------------
# game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player = Player()
        self.humans = []
        self.grunts = []
        self.hulks = []
        self.brains = []
        self.progs = []
        self.enforcers = []
        self.electrodes = []
        self.bullets = []
        self.bursts = []
        self.score = 0
        self.lives = 3
        self.wave = 0
        self.state = 'playing'
        self.banner_text = ''
        self.banner_until = 0
        self.next_extra_life = 10000
        self.start_wave()

    def start_wave(self):
        self.wave += 1
        survivors = [h for h in self.humans if h.state == 'walking']
        target_humans = min(6, 2 + self.wave)
        while len(survivors) < target_humans:
            survivors.append(Human(random.uniform(ARENA_LEFT + 40, ARENA_RIGHT - 40),
                                    random.uniform(ARENA_TOP + 40, ARENA_BOTTOM - 40)))
        self.humans = survivors

        def spawn_point():
            while True:
                x = random.uniform(ARENA_LEFT + 20, ARENA_RIGHT - 20)
                y = random.uniform(ARENA_TOP + 20, ARENA_BOTTOM - 20)
                if math.hypot(x - self.player.x, y - self.player.y) > 220:
                    return x, y

        grunt_count = min(24, 4 + self.wave * 2)
        self.grunts = [Grunt(*spawn_point()) for _ in range(grunt_count)]

        hulk_count = min(6, 1 + self.wave // 2)
        self.hulks = [Hulk(*spawn_point()) for _ in range(hulk_count)]

        brain_count = min(5, 1 + self.wave // 3)
        self.brains = [Brain(*spawn_point(), self) for _ in range(brain_count)]

        enforcer_count = min(4, self.wave // 2)
        self.enforcers = [Enforcer(*spawn_point()) for _ in range(enforcer_count)]

        electrode_count = min(16, 6 + self.wave)
        self.electrodes = [Electrode(*spawn_point()) for _ in range(electrode_count)]

        self.banner_text = f'WAVE {self.wave}'
        self.banner_until = pygame.time.get_ticks() + 2000

    def on_human_captured(self, human):
        self.progs.append(Prog(human.x, human.y))
        brain_zap_sound.play()

    def enemy_groups(self):
        return (
            (self.grunts, hit_sound),
            (self.hulks, explosion_sound),
            (self.brains, hit_sound),
            (self.progs, hit_sound),
            (self.enforcers, hit_sound),
        )

    def award_score(self, amount):
        self.score += amount
        if self.score >= self.next_extra_life:
            self.next_extra_life += 10000
            self.lives = min(9, self.lives + 1)
            extra_life_sound.play()
            self.banner_text = 'EXTRA LIFE'
            self.banner_until = pygame.time.get_ticks() + 1500

    def handle_input(self, keys, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.quit = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.state == 'game_over':
                    self.reset()

        if self.state != 'playing':
            return
        self.player.update(keys)
        aim = self.player.aim_direction(keys)
        if aim:
            self.player.shoot(aim, self.bullets)

    def update(self):
        if self.state != 'playing':
            for burst in list(self.bursts):
                if burst.dead():
                    self.bursts.remove(burst)
            return

        for human in self.humans:
            human.update()
        for grunt in self.grunts:
            grunt.update(self.player)
        for hulk in self.hulks:
            hulk.update(self.player)
        for brain in list(self.brains):
            brain.update(self.humans)
        for prog in self.progs:
            prog.update(self.player)
        for enforcer in self.enforcers:
            enforcer.update(self.player, self.bullets)
        for bullet in list(self.bullets):
            bullet.update()
            if bullet.dead():
                self.bullets.remove(bullet)

        self.resolve_collisions()

        if not (self.grunts or self.hulks or self.brains or self.progs or self.enforcers):
            self.start_wave()

        for burst in list(self.bursts):
            if burst.dead():
                self.bursts.remove(burst)

    def resolve_collisions(self):
        # player bullets vs enemies
        for bullet in list(self.bullets):
            if bullet.hostile or bullet not in self.bullets:
                continue
            hit = False
            for group, sound in self.enemy_groups():
                for enemy in list(group):
                    if math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) < enemy.radius:
                        enemy.hp -= 1
                        self.bullets.remove(bullet)
                        if enemy.hp <= 0:
                            group.remove(enemy)
                            color = getattr(enemy, 'burst_color', WHITE)
                            self.bursts.append(Burst(enemy.x, enemy.y, color))
                            sound.play()
                            self.award_score(enemy.score_value)
                        hit = True
                        break
                if hit:
                    break

        # player rescuing humans
        for human in list(self.humans):
            if human.state == 'walking' and math.hypot(human.x - self.player.x, human.y - self.player.y) < \
                    human.radius + self.player.radius:
                self.humans.remove(human)
                self.award_score(500)
                rescue_sound.play()

        if self.player.invulnerable():
            return

        # enemy bullets vs player
        for bullet in list(self.bullets):
            if not bullet.hostile:
                continue
            if math.hypot(bullet.x - self.player.x, bullet.y - self.player.y) < bullet.radius + self.player.radius:
                self.bullets.remove(bullet)
                self.player_hit()
                return

        # enemies/electrodes touching the player
        for group, _ in self.enemy_groups():
            for enemy in group:
                if math.hypot(enemy.x - self.player.x, enemy.y - self.player.y) < enemy.radius + self.player.radius:
                    self.player_hit()
                    return
        for electrode in self.electrodes:
            if math.hypot(electrode.x - self.player.x, electrode.y - self.player.y) < \
                    electrode.radius + self.player.radius:
                self.player_hit()
                return

    def player_hit(self):
        self.bursts.append(Burst(self.player.x, self.player.y, CYAN, particle_count=20))
        bomb_sound.play()
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.state = 'game_over'
        else:
            self.player = Player()

    # ---------------------------------------------------------------- draw
    def draw(self):
        display.fill(BLACK)
        self.draw_arena()

        for electrode in self.electrodes:
            electrode.draw(display)
        for human in self.humans:
            human.draw(display)
        for brain in self.brains:
            brain.draw(display)
        for grunt in self.grunts:
            grunt.draw(display)
        for hulk in self.hulks:
            hulk.draw(display)
        for prog in self.progs:
            prog.draw(display)
        for enforcer in self.enforcers:
            enforcer.draw(display)
        for bullet in self.bullets:
            bullet.draw(display)
        for burst in self.bursts:
            burst.draw(display)

        if self.state == 'playing':
            self.player.draw(display)

        self.draw_hud()

        if self.banner_text and pygame.time.get_ticks() < self.banner_until:
            font = pygame.font.SysFont(FONT_NAME, 46)
            surf = font.render(self.banner_text, True, YELLOW)
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
            display.blit(surf, rect)

        if self.state == 'game_over':
            font = pygame.font.SysFont(FONT_NAME, 90)
            surf = font.render('GAME OVER', True, RED)
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            display.blit(surf, rect)
            font2 = pygame.font.SysFont(FONT_NAME, 30)
            surf2 = font2.render('Press ENTER to restart', True, WHITE)
            rect2 = surf2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
            display.blit(surf2, rect2)

        pygame.display.flip()

    def draw_arena(self):
        rect = pygame.Rect(ARENA_LEFT - 4, ARENA_TOP - 4, ARENA_RIGHT - ARENA_LEFT + 8, ARENA_BOTTOM - ARENA_TOP + 8)
        pygame.draw.rect(display, MAGENTA, rect, 3)

    def draw_hud(self):
        font = pygame.font.SysFont(FONT_NAME, 26)
        display.blit(font.render(f'Score: {self.score}', True, WHITE), (14, 14))
        display.blit(font.render(f'Wave: {self.wave}', True, WHITE), (14, 42))

        lives_surf = font.render(f'Lives: {self.lives}', True, WHITE)
        display.blit(lives_surf, lives_surf.get_rect(topright=(SCREEN_WIDTH - 14, 14)))

        enemies_left = len(self.grunts) + len(self.hulks) + len(self.brains) + len(self.progs) + len(self.enforcers)
        enemies_surf = font.render(f'Enemies: {enemies_left}', True, RED)
        display.blit(enemies_surf, enemies_surf.get_rect(topright=(SCREEN_WIDTH - 14, 42)))

        humans_left = sum(1 for h in self.humans if h.state != 'captured')
        humans_surf = font.render(f'Humans: {humans_left}', True, GREEN)
        display.blit(humans_surf, humans_surf.get_rect(midtop=(SCREEN_WIDTH // 2, 14)))

    def run(self):
        self.quit = False
        while not self.quit:
            events = pygame.event.get()
            keys = pygame.key.get_pressed()
            self.handle_input(keys, events)
            self.update()
            self.draw()
            clock.tick(60)
        pygame.quit()


if __name__ == '__main__':
    Game().run()
