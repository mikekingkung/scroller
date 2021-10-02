import os
import pygame
from pygame import mixer
import csv

mixer.init()
pygame.init()

# define colours
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)


# define game variables
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
start_intro = False


# define player action variables
moving_left = False
moving_right = False

shoot = False
grenade = False
grenade_thrown = False




# store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)


# create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# pick up boxes
surface = pygame.display.set_mode((600, 600), 0)
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
arion_box_img = pygame.image.load('img/tiles2/13.png').convert_alpha()
item_boxes = {
    'Health': health_box_img,
    'Ammo': ammo_box_img,
    'Grenade': grenade_box_img,
    'Arion': arion_box_img
}


# function to reset level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)

    return data


class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class DisplayEngine:
    @staticmethod
    def center_screen():
        os.environ['SDL_VIDEO_CENTERED'] = '1'

    def __init__(self, caption, width, height, flags=0):

        pygame.display.set_caption(caption)
        self.surface = pygame.display.set_mode((width, height), flags)
        self.rect = self.surface.get_rect()
        self.clock = pygame.time.Clock()
        self.running = False
        self.delta = 0
        self.fps = 60

    def idle(self):
        self.delta = self.clock.tick(self.fps)

    def quit(self):
        self.running = False

class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        #update with new health
        self.health = health
        #calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(display_engine.surface, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(display_engine.surface, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(display_engine.surface, GREEN, (self.x, self.y, 150 * ratio, 20))

class World():
    def __init__(self):
        self.obstacle_list = []

    def draw(self, bg):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            bg.blit(tile[0], tile[1])

    def process_data(self, data):
        self.level_length = len(data[0])
        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    # elif tile >= 11 and tile <= 14:
                    #     decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                    #     decoration_group.add(decoration)
                    elif tile == 15:# create player
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20, 5, display_engine)
                        # player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20, 5, display_engine)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:# create enemies
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 20, 0, display_engine)
                        enemy_group.add(enemy)
                    elif tile == 17:# create ammo box
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:# create grenade box
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:# create health box
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:# create exit
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)

        return player, health_bar


class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll



class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


    def update(self):
        #scroll
        self.rect.x += screen_scroll
        # #check if the player has picked up the box
        # if pygame.sprite.collide_rect(self, player):
        # 	#check what kind of box it was
        # 	if self.item_type == 'Health':
        # 		player.health += 25
        # 		if player.health > player.max_health:
        # 			player.health = player.max_health
        # 	elif self.item_type == 'Ammo':
        # 		player.ammo += 15
        # 	elif self.item_type == 'Grenade':
        # 		player.grenades += 3
        # 	#delete the item box
        # 	self.kill()


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades, display_engine):
        self.display_engine = display_engine
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.shoot_cooldown = 0
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = False
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        # ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        # load all images for the players
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            # reset temporary list of images
            temp_list = []
            # count number of files in the folder
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        # reset movement variables
        screen_scroll = 0
        dx = 0
        dy = 0

        # assign movement variables if moving left or right
        if moving_left:
            print("moving the player left")
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            print("moving the player right")
            dx = self.speed
            self.flip = False
            self.direction = 1

        # jump
        if self.jump == True and self.in_air == False:
            self.vel_y = -11
            self.jump = False
            self.in_air = True

        # check for collision with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # check if fallen off the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        # check if going off the edges of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        # update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        # update scroll based on player position
        if self.char_type == 'player':
           # world.level_length
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (
                     1 * TILE_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete

    def update_animation(self):
        # update animation
        ANIMATION_COOLDOWN = 100
        # update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]
        print("self.action" + str(self.action))
        print("self.frame.index" + str(self.frame_index))
        # check if enough time has passed since the last update
        print("pygame.time.get_ticks()" + str(pygame.time.get_ticks()))
        print("self.update.time" + str(self.update_time))
        print("pygame.time.get_ticks() - self.update_time" + str(pygame.time.get_ticks() - self.update_time))
        print("ANIMATION_COOLDOWN" + str(ANIMATION_COOLDOWN))
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            print("frame index" + str(self.frame_index))
        # if the animation has run out the reset back to the start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                print("resetting frame index")
                self.frame_index = 0

    def update_action(self, new_action):
        # check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        print("drawing value of self.flip" + str(self.flip))
        self.display_engine.surface.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class Scene:

    def __init__(self, display_engine, moving_left, moving_right):
        self.display_engine = display_engine
        self.bg = pygame.Surface((800, 800))
        self.bg.fill(pygame.Color('gray5'))
        self.moving_left = moving_left
        self.moving_right = moving_right
        pygame.draw.line(self.bg, pygame.Color('dodgerblue'), (0, 10), (800, 10))
        pygame.draw.line(self.bg, pygame.Color('dodgerblue'), (0, 400), (800, 400), 2)
        pygame.draw.line(self.bg, pygame.Color('dodgerblue'), (0, 750), (800, 750))
        pygame.draw.line(self.bg, pygame.Color('firebrick'), (20, 0), (20, 800), 3)
        pygame.draw.line(self.bg, pygame.Color('firebrick'), (300, 0), (300, 800))

        self.camera = pygame.Vector2()
        self.camera_speed = 140 / 1000

    # Area you are looking for.
    def tile_image(self, surface, image):
        width, height = self.display_engine.rect.size
        i_width, i_height = image.get_size()
        camera_x = int(self.camera.x % i_width)
        camera_y = int(self.camera.y % i_height)
        for x in range(-camera_x, width, i_width):
            for y in range(-camera_y, height, i_height):
                surface.blit(image, (x, y))

    def draw_text(self, text1, text2, xcord, ycord, surface, font, text_col, x, y):
        img = font.render(text1 + ":" + str(xcord) + " " + text2 + ":" + str(ycord), True, text_col)
        surface.blit(img, (x, y))

    def mainloop(self, player):
        # define player action variables

        self.display_engine.running = True
        while self.display_engine.running:

            print("moving left" + str(self.moving_left))
            print("moving right" + str(self.moving_right))

            surface = self.display_engine.surface
            surface.fill(pygame.Color("black"))
            # # draw world map
            world.draw(self.bg)

            self.tile_image(surface, self.bg)
            # define font
            font = pygame.font.SysFont('Futura', 30)
            self.draw_text("x", "y", self.camera.x, self.camera.y,  surface, font, WHITE, 10, 60)



            player.update()
            player.draw()


            # update and draw groups
            bullet_group.update()
            grenade_group.update()
            explosion_group.update()
            item_box_group.update()
            decoration_group.update()
            water_group.update()
            exit_group.update()
            bullet_group.draw(surface)
            grenade_group.draw(surface)
            explosion_group.draw(surface)
            item_box_group.draw(surface)
            decoration_group.draw(surface)
            water_group.draw(surface)
            exit_group.draw(surface)


            # update player actions
            print("moving left" + str(self.moving_left))
            print("moving right" + str(self.moving_right))
            print("player.alive" + str(player.alive))
            if player.alive:
                if player.in_air:
                    print("player in the air")
                    print("updating action to 2 - jump")
                    player.update_action(2)  # 2: jump
                elif self.moving_left or self.moving_right:
                    print("updating action to 1 - run")
                    player.update_action(1)  # 1: run
                else:
                    print("updating action to 0 - idle")
                    player.update_action(0)  # 0: idle
            print("moving the player")
            screen_scroll, level_complete = player.move(self.moving_left, self.moving_right)
            # bg_scroll -= screen_scroll

            pygame.display.flip()
            self.display_engine.idle()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.display_engine.quit()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                self.camera.y -= self.camera_speed * self.display_engine.delta

            if keys[pygame.K_s]:
                self.camera.y += self.camera_speed * self.display_engine.delta

            if keys[pygame.K_a]:
                self.moving_left = True
                self.camera.x -= self.camera_speed * self.display_engine.delta


            if keys[pygame.K_d]:
                self.moving_right = True
                self.camera.x += self.camera_speed * self.display_engine.delta


            # keyboard button released
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    self.moving_left = False
                if event.key == pygame.K_d:
                    self.moving_right = False

            pygame.display.update()

if __name__ == '__main__':
    DisplayEngine.center_screen()
    display_engine = DisplayEngine("Moving Background", 600, 600)
    scene = Scene(display_engine, moving_left, moving_right)
    # create empty tile list
    world_data = []
    for row in range(ROWS):
        r = [-1] * COLS
        world_data.append(r)
    # load in level data and create world
    with open(f'level{level}_data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for x, row in enumerate(reader):
            for y, tile in enumerate(row):
                world_data[x][y] = int(tile)
    world = World()
    # player = Soldier('player', 10 * TILE_SIZE, 10 * TILE_SIZE, 1.65, 5, 20, 5, display_engine)
    player, health_bar = world.process_data(world_data)
    scene.mainloop(player)