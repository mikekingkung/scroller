"""
Defender-style arcade game.

A horizontally-wrapping planet: fly over the terrain, shoot down Landers
before they abduct your Humans, rescue any Human that gets dropped in
mid-air, and clear each wave. Losing every Human on a wave turns the
remaining Landers into fast, aggressive Mutants. Swarmers - small, fast,
erratic enemies - spawn in loose bursts throughout every wave.

Controls:
    LEFT / RIGHT  - horizontal thrust (also sets which way you're facing)
    UP / DOWN     - vertical thrust
    SPACE         - fire laser (in the direction you're facing)
    B             - smart bomb (destroys every enemy on screen)
    H             - hyperspace (random teleport, brief invulnerability)
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
WORLD_WIDTH = 4800

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (80, 220, 255)
MAGENTA = (230, 60, 200)
GREEN = (80, 255, 120)
YELLOW = (255, 220, 80)
RED = (255, 70, 70)
ORANGE = (255, 150, 40)

TOP_MARGIN = 90
GROUND_BASE = 650

FONT_NAME = 'Futura'


# ---------------------------------------------------------------------------
# world-wrap helpers
# ---------------------------------------------------------------------------
def wrapped_dx(a, b):
    """shortest signed delta from b to a on a world that wraps at WORLD_WIDTH"""
    d = (a - b + WORLD_WIDTH / 2) % WORLD_WIDTH - WORLD_WIDTH / 2
    return d


def screen_positions(world_x, cam_x, margin=80):
    """candidate on-screen x positions for a world_x, handling the wrap seam"""
    raw = (world_x - cam_x) % WORLD_WIDTH
    candidates = [raw, raw - WORLD_WIDTH]
    return [c for c in candidates if -margin <= c <= SCREEN_WIDTH + margin]


def terrain_height(world_x):
    """procedurally generated ground height at a given world x, built from
    three stacked sine waves (coarse hills + medium + fine detail)"""
    x = world_x % WORLD_WIDTH
    frac = x / WORLD_WIDTH
    h = GROUND_BASE
    h -= 70 * math.sin(2 * math.pi * frac * 3)
    h -= 35 * math.sin(2 * math.pi * frac * 7 + 1.3)
    h -= 18 * math.sin(2 * math.pi * frac * 13 + 2.1)
    return h


def tint_surface(surf, color):
    """recolor a grayscale/white sprite by multiplying it with a solid color,
    used to derive lander/mutant/swarmer variants from the same source art"""
    tinted = surf.copy()
    overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, 255))
    tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


# ---------------------------------------------------------------------------
# assets
# ---------------------------------------------------------------------------
display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Defender')
clock = pygame.time.Clock()

def make_laser_image(length, color):
    """a long, thin glowing beam - a soft outer glow behind a bright core"""
    surf = pygame.Surface((length, 12), pygame.SRCALPHA)
    pygame.draw.rect(surf, (*color, 90), (0, 2, length, 8), border_radius=4)
    pygame.draw.rect(surf, (*color, 255), (0, 5, length, 2), border_radius=1)
    return surf


player_bullet_img = make_laser_image(58, GREEN)
enemy_bullet_img = make_laser_image(36, RED)


def load_numbered_images(folder, count, size):
    """load up to `count` images from `folder`, sorted numerically by filename
    (e.g. '1.png', '2.png', ...), scaled to `size`"""
    images = []
    files = sorted(os.listdir(folder), key=lambda f: int(f.split('.')[0]))
    for f in files[:count]:
        img = pygame.image.load(os.path.join(folder, f)).convert_alpha()
        img = pygame.transform.scale(img, size)
        images.append(img)
    return images


LANDER_COLOR = (200, 120, 255)
MUTANT_COLOR = (255, 90, 90)
SWARMER_COLOR = (255, 220, 60)

human_images = load_numbered_images('img/tile/humans/renamed', 8, (22, 30))
monster_images = load_numbered_images('img/tile/monsters/renamed', 10, (40, 40))
lander_images = [tint_surface(img, LANDER_COLOR) for img in monster_images]
mutant_images = [tint_surface(img, MUTANT_COLOR) for img in monster_images]
swarmer_images = [
    tint_surface(pygame.transform.scale(img, (22, 22)), SWARMER_COLOR)
    for img in monster_images
]

laser_sound = mixer.Sound('sounds/laser.wav')
laser_sound.set_volume(0.3)
explosion_sound = mixer.Sound('sounds/explosion.wav')
explosion_sound.set_volume(0.5)
hyperspace_sound = mixer.Sound('sounds/hyperspace.wav')
hyperspace_sound.set_volume(0.5)
rescue_sound = mixer.Sound('sounds/rescue.wav')
rescue_sound.set_volume(0.5)
bomb_sound = mixer.Sound('sounds/bomb.wav')
bomb_sound.set_volume(0.6)
thrust_sound = mixer.Sound('sounds/thrust.wav')
thrust_sound.set_volume(0.35)

# channel 0 is reserved exclusively for the looping thrust sound so it
# doesn't get cut off by (or steal) the channel auto-picked for one-shot
# sounds like the laser or explosions
mixer.set_reserved(1)
thrust_channel = mixer.Channel(0)

mixer.music.load('sounds/alien_theme.wav')
mixer.music.set_volume(0.3)
mixer.music.play(loops=-1)


# ---------------------------------------------------------------------------
# entities
# ---------------------------------------------------------------------------
STAR_COLORS = [
    WHITE, WHITE,
    CYAN,
    YELLOW,
    (255, 170, 210),  # pink
    (170, 180, 255),  # pale blue
    (170, 255, 210),  # pale green
]


class Star:
    """background starfield particle; drawn at a fraction of camera speed
    (parallax) so it appears to sit farther away than the terrain/entities"""

    def __init__(self):
        self.x = random.uniform(0, WORLD_WIDTH)
        self.y = random.uniform(20, TOP_MARGIN + 380)
        self.size = random.choice([1, 1, 2])
        self.parallax = random.uniform(0.2, 0.5)
        self.color = random.choice(STAR_COLORS)

    def draw(self, surface, cam_x):
        for sx in screen_positions(self.x, cam_x * self.parallax):
            pygame.draw.rect(surface, self.color, (sx, self.y, self.size, self.size))


class Bullet:
    """a straight-line laser shot, fired either by the player or an enemy"""
    speed = 20

    def __init__(self, x, y, direction, hostile=False):
        self.x = x
        self.y = y
        self.vx = direction * self.speed
        self.hostile = hostile
        self.radius = 5
        self.life = 110  # frames until the bullet expires even if it hits nothing
        self.image = enemy_bullet_img if hostile else player_bullet_img
        if direction < 0:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self):
        self.x = (self.x + self.vx) % WORLD_WIDTH  # wrap around the cylindrical world
        self.life -= 1

    def dead(self):
        return self.life <= 0

    def draw(self, surface, cam_x):
        for sx in screen_positions(self.x, cam_x):
            rect = self.image.get_rect(center=(sx, self.y))
            surface.blit(self.image, rect)


class Explosion:
    """brief expanding/fading 3-layer fireball used for normal enemy/ship kills"""
    duration = 320

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.spawn_time = pygame.time.get_ticks()

    def dead(self):
        return pygame.time.get_ticks() - self.spawn_time > self.duration

    def draw(self, surface, cam_x):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        progress = elapsed / self.duration
        alpha = int(255 * (1 - progress))
        max_radius = 34
        for sx in screen_positions(self.x, cam_x):
            for i, color in enumerate(((255, 255, 120), (255, 140, 40), (200, 40, 20))):
                radius = max(1, int((6 + progress * (max_radius - 6)) - i * 7))
                halo = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(halo, (*color, alpha), (radius, radius), radius)
                surface.blit(halo, (sx - radius, self.y - radius))


class Disintegration:
    """smart-bomb kill effect: the target breaks apart into fading pixel debris"""
    duration = 500

    def __init__(self, x, y, color, particle_count=16):
        self.x = x
        self.y = y
        self.color = color
        self.spawn_time = pygame.time.get_ticks()
        self.particles = []
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 5.5)
            self.particles.append({
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'size': random.randint(2, 5),
            })

    def dead(self):
        return pygame.time.get_ticks() - self.spawn_time > self.duration

    def draw(self, surface, cam_x):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        progress = elapsed / self.duration
        alpha = max(0, int(255 * (1 - progress)))
        for sx in screen_positions(self.x, cam_x):
            for p in self.particles:
                px = sx + p['dx'] * elapsed * 0.07
                py = self.y + p['dy'] * elapsed * 0.07
                size = max(1, int(p['size'] * (1 - progress)))
                particle = pygame.Surface((size, size), pygame.SRCALPHA)
                particle.fill((*self.color, alpha))
                surface.blit(particle, (px - size / 2, py - size / 2))


class Human:
    """a rescuable civilian on the ground. State machine:
    walking -> claimed (a lander is approaching) -> captured (being carried
    up) -> falling (lander destroyed mid-carry, drops and re-lands) -> back
    to walking, or lost entirely if the lander reaches the top of the screen"""

    def __init__(self, x):
        self.x = x
        self.y = terrain_height(x)
        self.state = 'walking'  # walking, claimed, captured, falling, rescued
        self.dir = random.choice([-1, 1])
        self.image = random.choice(human_images)
        self.radius = 12
        self.vy = 0.0

    def update(self):
        if self.state == 'walking':
            self.y = terrain_height(self.x)
            if random.random() < 0.01:
                self.dir *= -1  # occasionally wander the other way
            self.x = (self.x + self.dir * 0.6) % WORLD_WIDTH
        elif self.state == 'falling':
            # simple gravity fall back down to the terrain after being dropped
            self.vy += 0.4
            self.y += self.vy
            ground = terrain_height(self.x)
            if self.y >= ground:
                self.y = ground
                self.state = 'walking'
                self.vy = 0.0

    def draw(self, surface, cam_x):
        if self.state == 'captured':
            return
        for sx in screen_positions(self.x, cam_x):
            rect = self.image.get_rect(midbottom=(sx, self.y))
            surface.blit(self.image, rect)


class Lander:
    """enemy that hunts down a Human, carries it upward, and escapes off the
    top of the screen; if it reaches the top it turns into a Mutant"""
    speed = 1.6
    score_value = 150

    def __init__(self, x, game):
        self.x = x
        self.y = random.uniform(TOP_MARGIN + 20, GROUND_BASE - 220)
        self.target = None
        self.image = random.choice(lander_images)
        self.radius = 18
        self.game = game

    def pick_target(self, humans):
        """claim the nearest free-walking human as this lander's abduction target"""
        available = [h for h in humans if h.state == 'walking']
        if not available:
            self.target = None
            return
        nearest = min(available, key=lambda h: abs(wrapped_dx(h.x, self.x)))
        nearest.state = 'claimed'
        self.target = nearest

    def update(self, humans):
        # re-pick a target if we lost the current one (killed, rescued, etc.)
        if self.target is None or self.target.state not in ('claimed', 'captured'):
            self.pick_target(humans)

        if self.target is None:
            # nothing left to abduct - roam gently
            self.x = (self.x + math.sin(pygame.time.get_ticks() * 0.001 + self.radius) * 0.8) % WORLD_WIDTH
            return

        if self.target.state == 'claimed':
            # fly toward the target human
            dx = wrapped_dx(self.target.x, self.x)
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist < 14:
                self.target.state = 'captured'
            else:
                self.x = (self.x + (dx / dist) * self.speed) % WORLD_WIDTH
                self.y += (dy / dist) * self.speed
        elif self.target.state == 'captured':
            # carry the human straight up; escaping past the top loses them
            self.target.x = self.x
            self.target.y = self.y + 14
            self.y -= self.speed * 1.3
            if self.y <= TOP_MARGIN:
                self.game.on_human_lost(self)

    def draw(self, surface, cam_x):
        for sx in screen_positions(self.x, cam_x):
            rect = self.image.get_rect(center=(sx, self.y))
            surface.blit(self.image, rect)


class Mutant:
    """aggressive enemy created when a lander escapes with a human, or when
    all humans on a wave are gone - faster than a Lander and shoots back"""
    speed = 3.2
    fire_interval = 90  # frames between shots, once in range
    score_value = 150

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = random.choice(mutant_images)
        self.radius = 18
        # randomize the initial cooldown so multiple mutants don't all fire in sync
        self.fire_cooldown = random.randint(0, self.fire_interval)

    def update(self, player, bullets):
        # steer directly toward the player, using the shortest wrapped path
        dx = wrapped_dx(player.x, self.x)
        dy = player.y - self.y
        dist = math.hypot(dx, dy) or 1  # avoid div-by-zero if exactly on top of the player
        self.x = (self.x + (dx / dist) * self.speed) % WORLD_WIDTH
        self.y += (dy / dist) * self.speed
        # clamp vertical position so mutants stay above the ground and below the ceiling
        self.y = max(TOP_MARGIN, min(self.y, terrain_height(self.x) - 10))

        self.fire_cooldown -= 1
        if self.fire_cooldown <= 0 and abs(dx) < 700:  # only fire when the player is within range
            self.fire_cooldown = self.fire_interval
            direction = 1 if dx > 0 else -1  # aim the bullet toward the player's side
            bullets.append(Bullet(self.x, self.y, direction, hostile=True))

    def draw(self, surface, cam_x):
        for sx in screen_positions(self.x, cam_x):
            rect = self.image.get_rect(center=(sx, self.y))
            surface.blit(self.image, rect)


class Swarmer:
    """small, fast, erratic enemy that darts around in loose homing bursts"""
    speed = 4.5
    score_value = 60

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = random.choice(swarmer_images)
        self.radius = 10
        self.vx = 0.0
        self.vy = 0.0
        self.retarget_at = 0

    def update(self, player):
        now = pygame.time.get_ticks()
        # only recompute heading periodically (every 200-500ms) rather than every
        # frame - this is what gives swarmers their darting, erratic motion
        # instead of smooth homing
        if now >= self.retarget_at:
            self.retarget_at = now + random.randint(200, 500)
            dx = wrapped_dx(player.x, self.x)
            dy = player.y - self.y
            dist = math.hypot(dx, dy) or 1
            # blend a random jitter direction with a pull toward the player:
            # homing_weight controls how much of each new heading is "toward
            # the player" (0.35) vs. pure random noise (0.65)
            jitter_angle = random.uniform(0, 2 * math.pi)
            homing_weight = 0.35
            jx, jy = math.cos(jitter_angle), math.sin(jitter_angle)
            vx = jx * (1 - homing_weight) + (dx / dist) * homing_weight
            vy = jy * (1 - homing_weight) + (dy / dist) * homing_weight
            norm = math.hypot(vx, vy) or 1
            self.vx = vx / norm  # normalize to a unit vector so `speed` fully controls velocity
            self.vy = vy / norm

        self.x = (self.x + self.vx * self.speed) % WORLD_WIDTH
        self.y += self.vy * self.speed
        self.y = max(TOP_MARGIN, min(self.y, terrain_height(self.x) - 10))

    def draw(self, surface, cam_x):
        for sx in screen_positions(self.x, cam_x):
            rect = self.image.get_rect(center=(sx, self.y))
            surface.blit(self.image, rect)


class Ship:
    """the player-controlled ship: momentum-based flight (thrust + drag),
    a forward-facing laser, and a hyperspace panic button"""
    accel = 0.6
    drag = 0.95   # velocity is multiplied by this each frame, so the ship coasts to a stop
    max_speed = 9

    def __init__(self):
        self.x = WORLD_WIDTH / 2
        self.y = (TOP_MARGIN + GROUND_BASE) / 2
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1  # 1 = facing right, -1 = facing left; also the shot direction
        self.radius = 15
        self.fire_cooldown = 0
        self.invulnerable_until = pygame.time.get_ticks() + 2000  # brief spawn/respawn grace period
        self.thrusting = False

    def invulnerable(self):
        return pygame.time.get_ticks() < self.invulnerable_until

    def update(self, keys):
        # read held-down movement keys into a thrust direction for this frame
        thrust_x = 0
        thrust_y = 0
        if keys[pygame.K_LEFT]:
            thrust_x -= 1
            self.facing = -1
        if keys[pygame.K_RIGHT]:
            thrust_x += 1
            self.facing = 1
        if keys[pygame.K_UP]:
            thrust_y -= 1
        if keys[pygame.K_DOWN]:
            thrust_y += 1

        # start/stop the looping thrust sound only on state transitions,
        # not every frame, so it doesn't restart while a key is held
        was_thrusting = self.thrusting
        self.thrusting = bool(thrust_x or thrust_y)
        if self.thrusting and not was_thrusting:
            thrust_channel.play(thrust_sound, loops=-1)
        elif was_thrusting and not self.thrusting:
            thrust_channel.stop()

        # apply thrust as acceleration, then drag, then clamp to max speed -
        # this is what makes the ship feel like it has inertia/momentum
        # instead of moving at a fixed speed
        self.vx = (self.vx + thrust_x * self.accel) * self.drag
        self.vy = (self.vy + thrust_y * self.accel) * self.drag
        self.vx = max(-self.max_speed, min(self.max_speed, self.vx))
        self.vy = max(-self.max_speed, min(self.max_speed, self.vy))

        self.x = (self.x + self.vx) % WORLD_WIDTH  # wrap around the world
        self.y += self.vy
        self.y = max(TOP_MARGIN, min(self.y, terrain_height(self.x) - 4))  # stay between sky ceiling and ground

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def shoot(self, bullets):
        """fire one shot in the direction the ship is currently facing,
        gated by a cooldown so holding SPACE doesn't spam infinite bullets"""
        if self.fire_cooldown == 0:
            self.fire_cooldown = 10
            bullets.append(Bullet(self.x, self.y, self.facing, hostile=False))
            laser_sound.play()

    def hyperspace(self):
        """emergency escape: teleport to a random point on the map, reset
        velocity, and grant a short window of invulnerability"""
        self.x = random.uniform(0, WORLD_WIDTH)
        self.y = random.uniform(TOP_MARGIN + 20, GROUND_BASE - 150)
        self.vx = 0
        self.vy = 0
        self.invulnerable_until = pygame.time.get_ticks() + 1200
        hyperspace_sound.play()

    def draw(self, surface, cam_x):
        # blink (skip every other ~120ms) while invulnerable, as a visual cue
        if self.invulnerable() and (pygame.time.get_ticks() // 120) % 2 == 0:
            return
        for sx in screen_positions(self.x, cam_x):
            # a simple arrow-shaped triangle/notch, mirrored based on facing direction
            nose = self.facing * 16
            points = [
                (sx + nose, self.y),
                (sx - self.facing * 12, self.y - 10),
                (sx - self.facing * 6, self.y),
                (sx - self.facing * 12, self.y + 10),
            ]
            pygame.draw.polygon(surface, CYAN, points)
            pygame.draw.circle(surface, WHITE, (int(sx - self.facing * 2), int(self.y)), 3)
            if self.thrusting:
                # flickering exhaust flame trailing behind the ship, opposite facing direction
                flame_len = random.randint(8, 16)
                flame = [
                    (sx - self.facing * 12, self.y - 5),
                    (sx - self.facing * (12 + flame_len), self.y),
                    (sx - self.facing * 12, self.y + 5),
                ]
                pygame.draw.polygon(surface, ORANGE, flame)


# ---------------------------------------------------------------------------
# game
# ---------------------------------------------------------------------------
class Game:
    """top-level game state and orchestration: owns every entity list, the
    frame loop (input -> update -> draw), scoring, wave progression, and the
    win/loss state machine ('playing' -> 'game_over')"""

    def __init__(self):
        # stars are created once and persist across resets/waves (background only)
        self.stars = [Star() for _ in range(140)]
        self.reset()

    def reset(self):
        """(re)initialize a fresh run: clear all entities/score/lives and start wave 1"""
        self.ship = Ship()
        self.humans = []
        self.landers = []
        self.mutants = []
        self.swarmers = []
        self.bullets = []
        self.explosions = []
        self.score = 0
        self.lives = 3
        self.bombs = 3
        self.wave = 0
        self.state = 'playing'
        self.banner_text = ''
        self.banner_until = 0
        self.last_hyperspace = 0
        self.no_humans_left = False
        self.last_swarm_spawn = pygame.time.get_ticks()
        self.swarm_interval = random.randint(9000, 15000)
        self.start_wave()

    def start_wave(self):
        """advance to the next wave: keep any surviving humans, top them up to
        the wave's target count, and spawn a fresh batch of landers"""
        self.wave += 1
        self.no_humans_left = False

        # carry over humans who survived the previous wave, then spawn new
        # ones (at random locations) until we reach this wave's target count
        # (waves get progressively more humans, capped at 8)
        survivors = [h for h in self.humans if h.state == 'walking']
        target_humans = min(8, 4 + self.wave)
        while len(survivors) < target_humans:
            survivors.append(Human(random.uniform(0, WORLD_WIDTH)))
        self.humans = survivors

        # each wave adds more landers, capped at 12; mutants don't carry over
        lander_count = min(12, 3 + self.wave)
        self.landers = [Lander(random.uniform(0, WORLD_WIDTH), self) for _ in range(lander_count)]
        self.mutants = []
        self.bombs = min(5, self.bombs + 1)  # award a bonus bomb per wave, capped at 5
        self.banner_text = f'WAVE {self.wave}'
        self.banner_until = pygame.time.get_ticks() + 2000

    def on_human_lost(self, lander):
        """called by a Lander when it escapes off the top of the screen with
        a captured human - the human is gone for good, and the lander that
        carried it is replaced by a (spawned-at-the-top) Mutant"""
        human = lander.target
        if human in self.humans:
            self.humans.remove(human)
        if lander in self.landers:
            self.landers.remove(lander)
        self.mutants.append(Mutant(lander.x, TOP_MARGIN + 10))
        self.check_no_humans_left()

    def destroy_lander(self, lander):
        """remove a lander and free whatever human it had claimed/captured:
        a captured human drops (starts falling back to the ground), while a
        merely claimed human just resumes walking"""
        if lander in self.landers:
            self.landers.remove(lander)
        if lander.target:
            if lander.target.state == 'captured':
                lander.target.state = 'falling'
                lander.target.vy = 0
            elif lander.target.state == 'claimed':
                lander.target.state = 'walking'

    def check_no_humans_left(self):
        """once every human is gone (abducted, none ever spawned to survive,
        etc.), the wave's threat escalates: any remaining landers - who have
        nothing left to abduct - instantly convert into aggressive Mutants.
        Guarded by no_humans_left so this only fires once per wave."""
        if self.no_humans_left:
            return
        if not any(h.state in ('walking', 'claimed', 'captured', 'falling') for h in self.humans):
            self.no_humans_left = True
            for lander in self.landers:
                self.mutants.append(Mutant(lander.x, lander.y))
            self.landers = []

    def spawn_swarm(self):
        """spawn a loose cluster (6-9) of Swarmers at one random location,
        scattered slightly so they don't all start in exactly the same spot"""
        sx = random.uniform(0, WORLD_WIDTH)
        sy = random.uniform(TOP_MARGIN + 20, GROUND_BASE - 150)
        for _ in range(random.randint(6, 9)):
            self.swarmers.append(Swarmer(sx + random.uniform(-30, 30), sy + random.uniform(-30, 30)))

    def smart_bomb(self):
        """consume one bomb charge (if any) to instantly destroy every enemy
        currently near the player's screen (not the whole world)"""
        if self.bombs <= 0 or self.state != 'playing':
            return
        self.bombs -= 1
        killed = False
        groups = (
            (self.landers, True, LANDER_COLOR),
            (self.mutants, False, MUTANT_COLOR),
            (self.swarmers, False, SWARMER_COLOR),
        )
        for group, is_lander_group, color in groups:
            for enemy in list(group):  # iterate a copy since we mutate the list mid-loop
                # only kill enemies within roughly one screen-width of the ship
                # (using wrapped distance so it also works across the world seam)
                if abs(wrapped_dx(enemy.x, self.ship.x)) < SCREEN_WIDTH / 2 + 60:
                    self.explosions.append(Disintegration(enemy.x, enemy.y, color))
                    self.score += enemy.score_value
                    if is_lander_group:
                        self.destroy_lander(enemy)  # also frees any human it was carrying
                    else:
                        group.remove(enemy)
                    killed = True
        if killed:
            bomb_sound.play()
        self.check_no_humans_left()

    def handle_input(self, keys, events):
        """process discrete key-press events (quit, bomb, hyperspace, restart)
        plus continuously-held keys (movement, firing) each frame"""
        for event in events:
            if event.type == pygame.QUIT:
                self.quit = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    self.smart_bomb()
                if event.key == pygame.K_h and self.state == 'playing':
                    # hyperspace has its own 2-second cooldown, separate from
                    # the ship's fire cooldown, to prevent spamming teleports
                    now = pygame.time.get_ticks()
                    if now - self.last_hyperspace > 2000:
                        self.last_hyperspace = now
                        self.ship.hyperspace()
                if event.key == pygame.K_RETURN and self.state == 'game_over':
                    self.reset()

        if self.state != 'playing':
            return
        self.ship.update(keys)
        if keys[pygame.K_SPACE]:
            self.ship.shoot(self.bullets)

    def update(self):
        """advance the simulation by one frame: spawn timers, entity
        movement, collisions, and wave progression. Skipped (except for
        letting explosions finish) whenever the game isn't actively playing."""
        if self.state != 'playing':
            # even on the game-over screen, let in-flight explosion animations finish
            for explosion in list(self.explosions):
                if explosion.dead():
                    self.explosions.remove(explosion)
            return

        # periodically spawn a new swarm burst, capped so swarmers can't pile
        # up unboundedly; interval is re-randomized after each spawn
        now = pygame.time.get_ticks()
        if now - self.last_swarm_spawn > self.swarm_interval and len(self.swarmers) < 24:
            self.last_swarm_spawn = now
            self.swarm_interval = random.randint(9000, 15000)
            self.spawn_swarm()

        for human in self.humans:
            human.update()
        for lander in list(self.landers):  # copy: update() may remove/replace entries via on_human_lost
            lander.update(self.humans)
        for mutant in self.mutants:
            mutant.update(self.ship, self.bullets)
        for swarmer in self.swarmers:
            swarmer.update(self.ship)
        for bullet in list(self.bullets):
            bullet.update()
            if bullet.dead():
                self.bullets.remove(bullet)

        self.resolve_collisions()

        # a wave ends once every lander/mutant threat is cleared (humans
        # left over just carry into the next wave)
        if not self.landers and not self.mutants:
            self.start_wave()

        for explosion in list(self.explosions):
            if explosion.dead():
                self.explosions.remove(explosion)

    def resolve_collisions(self):
        """check every pair of interacting entities for this frame: player
        shots vs. enemies, human rescues, and everything that can hurt the
        player (enemy shots, enemy contact, terrain collision)"""

        # player bullets vs landers/mutants/swarmers - axis-aligned "box"
        # check (not true circular) against each enemy's radius, using
        # wrapped_dx so hits register correctly across the world seam
        for bullet in list(self.bullets):
            if bullet.hostile or bullet not in self.bullets:
                continue
            hit = False
            for group, is_lander_group in ((self.landers, True), (self.mutants, False), (self.swarmers, False)):
                for enemy in list(group):
                    if abs(wrapped_dx(bullet.x, enemy.x)) < enemy.radius and abs(bullet.y - enemy.y) < enemy.radius:
                        if is_lander_group:
                            self.destroy_lander(enemy)  # also frees any human it was carrying
                        else:
                            group.remove(enemy)
                        self.bullets.remove(bullet)
                        self.explosions.append(Explosion(enemy.x, enemy.y))
                        explosion_sound.play()
                        self.score += enemy.score_value
                        self.check_no_humans_left()
                        hit = True
                        break  # one bullet can only hit one enemy
                if hit:
                    break

        # falling humans (dropped by a destroyed lander) are rescued simply
        # by the ship touching them - snaps them to the ship's position and
        # returns them to 'walking' on the ground below
        for human in self.humans:
            if human.state == 'falling':
                dx = wrapped_dx(human.x, self.ship.x)
                if abs(dx) < 24 and abs(human.y - self.ship.y) < 24:
                    human.state = 'walking'
                    human.x = self.ship.x
                    self.score += 500
                    rescue_sound.play()

        # nothing below this point can hurt the ship while it's invulnerable
        # (spawn grace period or right after a hyperspace jump)
        if self.ship.invulnerable():
            return

        # enemy bullets vs player
        for bullet in list(self.bullets):
            if not bullet.hostile:
                continue
            if abs(wrapped_dx(bullet.x, self.ship.x)) < self.ship.radius and abs(bullet.y - self.ship.y) < self.ship.radius:
                self.bullets.remove(bullet)
                self.ship_hit()
                return  # stop checking further collisions - the ship (and possibly the run) just ended

        # landers/mutants/swarmers ramming the player (true circular distance check)
        for group, is_lander_group in ((self.landers, True), (self.mutants, False), (self.swarmers, False)):
            for enemy in list(group):
                dx = wrapped_dx(enemy.x, self.ship.x)
                dy = enemy.y - self.ship.y
                if math.hypot(dx, dy) < enemy.radius + self.ship.radius:
                    if is_lander_group:
                        self.destroy_lander(enemy)
                    else:
                        group.remove(enemy)
                    self.explosions.append(Explosion(enemy.x, enemy.y))
                    explosion_sound.play()
                    self.ship_hit()
                    return

        # crashing into the terrain (ship flew low enough to clip the ground)
        if self.ship.y >= terrain_height(self.ship.x) - 6:
            self.ship_hit()

    def ship_hit(self):
        """the ship took damage: play the death fx, spend a life, and either
        respawn a fresh Ship (with its own invulnerability window) or end the game"""
        thrust_channel.stop()
        self.explosions.append(Explosion(self.ship.x, self.ship.y))
        explosion_sound.play()
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.state = 'game_over'
        else:
            self.ship = Ship()  # fresh ship at world center, with a new invulnerability grace period

    # ---------------------------------------------------------------- draw
    def draw(self):
        """render one full frame, back to front: starfield -> terrain ->
        world entities -> ship -> HUD/overlays. `cam_x` is the camera's
        world-space x position, kept centered on the ship, and is what lets
        every entity convert its own world coordinate into a screen coordinate."""
        display.fill(BLACK)
        cam_x = (self.ship.x - SCREEN_WIDTH / 2) % WORLD_WIDTH

        for star in self.stars:
            star.draw(display, cam_x)

        self.draw_terrain(cam_x)

        for human in self.humans:
            human.draw(display, cam_x)
        for lander in self.landers:
            lander.draw(display, cam_x)
        for mutant in self.mutants:
            mutant.draw(display, cam_x)
        for swarmer in self.swarmers:
            swarmer.draw(display, cam_x)
        for bullet in self.bullets:
            bullet.draw(display, cam_x)
        for explosion in self.explosions:
            explosion.draw(display, cam_x)

        if self.state == 'playing':
            self.ship.draw(display, cam_x)  # don't draw the ship on the game-over screen

        self.draw_hud(cam_x)
        self.draw_mutant_radar()

        # temporary "WAVE n" banner, faded out automatically once banner_until passes
        if self.banner_text and pygame.time.get_ticks() < self.banner_until:
            font = pygame.font.SysFont(FONT_NAME, 50)
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

    def draw_terrain(self, cam_x):
        """sample terrain_height across the visible screen width (every 8px)
        to build a silhouette polygon, filled solid and outlined"""
        points = [(sx, terrain_height(cam_x + sx)) for sx in range(0, SCREEN_WIDTH + 1, 8)]
        # close the polygon down to the bottom corners so the fill covers
        # everything below the ridge line, not just a thin outline
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        points.append((0, SCREEN_HEIGHT))
        pygame.draw.polygon(display, (40, 10, 40), points)
        pygame.draw.lines(display, MAGENTA, False, points[:-2], 3)  # outline just the ridge, not the bottom corners

    def draw_hud(self, cam_x):
        """draw score/wave/lives/bombs/humans-remaining text, plus a
        world-spanning minimap strip along the top of the screen"""
        font = pygame.font.SysFont(FONT_NAME, 26)
        display.blit(font.render(f'Score: {self.score}', True, WHITE), (14, 55))
        display.blit(font.render(f'Wave: {self.wave}', True, WHITE), (14, 82))

        lives_surf = font.render(f'Lives: {self.lives}', True, WHITE)
        display.blit(lives_surf, lives_surf.get_rect(topright=(SCREEN_WIDTH - 14, 55)))
        bombs_surf = font.render(f'Bombs: {self.bombs}', True, ORANGE)
        display.blit(bombs_surf, bombs_surf.get_rect(topright=(SCREEN_WIDTH - 14, 82)))
        humans_left = sum(1 for h in self.humans if h.state in ('walking', 'claimed', 'falling'))
        humans_surf = font.render(f'Humans: {humans_left}', True, GREEN)
        display.blit(humans_surf, humans_surf.get_rect(midtop=(SCREEN_WIDTH // 2, 55)))

        # minimap: a thin strip representing the entire WORLD_WIDTH compressed
        # into SCREEN_WIDTH pixels, with a box showing the camera's current viewport
        map_rect = pygame.Rect(0, 8, SCREEN_WIDTH, 36)
        pygame.draw.rect(display, (15, 15, 25), map_rect)
        pygame.draw.rect(display, (60, 60, 80), map_rect, 1)

        def map_x(world_x):
            """convert a world x-coordinate to its position along the minimap strip"""
            return (world_x % WORLD_WIDTH) / WORLD_WIDTH * SCREEN_WIDTH

        view_left = map_x(cam_x)
        view_width = SCREEN_WIDTH / WORLD_WIDTH * SCREEN_WIDTH
        pygame.draw.rect(display, (90, 90, 120), (view_left, 8, view_width, 36), 1)

        # plot every relevant entity as a colored dot along the minimap
        for human in self.humans:
            if human.state in ('walking', 'claimed', 'falling'):
                pygame.draw.circle(display, GREEN, (int(map_x(human.x)), 26), 2)
        for lander in self.landers:
            pygame.draw.circle(display, MAGENTA, (int(map_x(lander.x)), 26), 2)
        for mutant in self.mutants:
            pygame.draw.circle(display, RED, (int(map_x(mutant.x)), 26), 2)
        for swarmer in self.swarmers:
            pygame.draw.circle(display, YELLOW, (int(map_x(swarmer.x)), 26), 1)
        pygame.draw.circle(display, WHITE, (int(map_x(self.ship.x)), 26), 3)

    def draw_mutant_radar(self):
        """small fixed panel showing every enemy's position across the whole
        world (not just the visible screen) and vertically by altitude - lets
        the player see threats approaching from off-screen"""
        panel_w, panel_h = 170, 90
        panel_x = SCREEN_WIDTH - panel_w - 14
        panel_y = 135
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        pygame.draw.rect(display, (15, 15, 25), panel)
        pygame.draw.rect(display, RED, panel, 1)

        font = pygame.font.SysFont(FONT_NAME, 16)
        display.blit(font.render('THREATS', True, RED), (panel_x + 4, panel_y - 18))

        def to_panel(world_x, world_y):
            """map a world position onto a point inside the radar panel:
            x wraps around the full world width, y is scaled from the
            sky-ceiling/ground band and clamped so dots stay inside the panel"""
            px = panel_x + (world_x % WORLD_WIDTH) / WORLD_WIDTH * panel_w
            py = panel_y + 8 + (world_y - TOP_MARGIN) / (GROUND_BASE - TOP_MARGIN) * (panel_h - 16)
            py = max(panel_y + 4, min(panel_y + panel_h - 4, py))
            return px, py

        # Landers (not yet mutated), true Mutants, and Swarmers all read as
        # "the aliens chasing me" to a player, so the radar tracks all three
        threats = [(l, MAGENTA) for l in self.landers] + \
                  [(m, RED) for m in self.mutants] + \
                  [(s, YELLOW) for s in self.swarmers]

        if threats:
            # dot size pulses between 3 and 4px every 200ms for a "blip" effect
            pulse = 3 + (pygame.time.get_ticks() // 200) % 2
            for enemy, color in threats:
                ex, ey = to_panel(enemy.x, enemy.y)
                pygame.draw.circle(display, color, (int(ex), int(ey)), pulse)
        else:
            empty_surf = font.render('none nearby', True, (140, 140, 140))
            display.blit(empty_surf, empty_surf.get_rect(center=panel.center))

        sx, sy = to_panel(self.ship.x, self.ship.y)
        pygame.draw.circle(display, WHITE, (int(sx), int(sy)), 3)

    def run(self):
        """the main game loop: poll input, advance simulation, render, and
        cap the frame rate at 60 FPS, until the window is closed"""
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
