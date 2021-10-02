import os
import pygame
import button
import csv


pygame.init()

# define colours
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

SCREEN_WIDTH = 1034
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
CURSOR_YOFFSET = 14
INITIAL_IMAGES = 4  # initial button id means artifact images loaded first

selection_x = 1
selection_y = 1
layout_x = 1
layout_y = 1
offset = 0
selection_image_grid = []
layout_target_grid = []
for count in range(100):
    selection_image_grid.append("A")
    layout_target_grid.append("-1")



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

    def load_images(self, button_id):
        try:
            directory = 'img/tile/armour/renamed/'  # default
            if button_id == 3:
                directory = 'img/tile/armour/renamed/'
            elif button_id == 4:
                directory = 'img/tile/artifacts/renamed/'
            elif button_id == 5:
                directory = 'img/tile/backgrounds/renamed/'
            elif button_id == 6:
                directory = 'img/tile/humans/renamed/'
            elif button_id == 7:
                directory = 'img/tile/magical_items/renamed/'
            elif button_id == 8:
                directory = 'img/tile/monsters/renamed/'
            elif button_id == 9:
                directory = 'img/tile/potions/renamed/'
            elif button_id == 10:
                directory = 'img/tile/spellbooks/renamed/'
            elif button_id == 11:
                directory = 'img/tile/traps/renamed/'
            elif button_id == 12:
                directory = 'img/tile/weapons/renamed/'

            # print("loading images")
            image_list = []
            for count, filename in enumerate(os.listdir(directory)):
                img = pygame.image.load(f'{directory}/{filename}').convert_alpha()
                selection_image_grid.append(filename) # needs to be without .png
                image_list.append(img)
            return image_list

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in load_images")

class Scene:

    def __init__(self, display_engine):
        self.display_engine = display_engine
        self.bg = pygame.Surface((1024, 1024))
        self.bg.fill(pygame.Color('gray5'))
        self.display_empty_grids()


    def determine_grid_type(self):
        try:
            SELECTION_GRID_YOFFSET = 1
            LAYOUT_GRID_YOFFSET = 14

            ROWS = 10
            COLS = 10
            pos = pygame.mouse.get_pos()
            # print("pos:" +str(pos))
            #print("pos[0]:" + str(pos[0]))
            #print("pos[1]:" + str(pos[1]))
            current_x = pos[0]
            current_y = pos[1]

            selection_left_border_x = 0
            selection_right_border_x = COLS * 32
            selection_top_border_y = SELECTION_GRID_YOFFSET * 32
            selection_bottom_border_y = (SELECTION_GRID_YOFFSET * 32) + (ROWS * 32)

            #print("selection_left_border_x" + str (selection_left_border_x))
            #print("selection_right_border_x" + str (selection_right_border_x))
            #print("selection_top_border_y" + str (selection_top_border_y))
            #print("selection_bottom_border_y" + str (selection_bottom_border_y))

            layout_left_border_x = 0
            layout_right_border_x = COLS * 32
            layout_top_border_y = LAYOUT_GRID_YOFFSET * 32
            layout_bottom_border_y = LAYOUT_GRID_YOFFSET * 32 + (ROWS * 32)

            # print("layout_left_border_x" + str (layout_left_border_x))
            # print("layout_right_border_x" + str (layout_right_border_x))
            # print("layout_top_border_y" + str (layout_top_border_y))
            # print("layout_bottom_border_y" + str (layout_bottom_border_y))
            #
            # print ("x check selection left border" + str(current_x >= selection_left_border_x))
            # print ("x check selection right border" + str(current_x <= selection_right_border_x))
            # print ("y check selection top border"+ str(current_y) + ">=" + str(selection_top_border_y))
            # print ("y check selection bottom border" + str(current_y <= selection_bottom_border_y))

            grid = 'offgrid'
            if (current_x >= selection_left_border_x) and (current_x <= selection_right_border_x) and (
                    current_y >= selection_top_border_y) and (current_y <= selection_bottom_border_y):
                grid = 'selection'

            if (current_x >= layout_left_border_x) and (current_x <= layout_right_border_x) and (
                    current_y >= layout_top_border_y) and (current_y <= layout_bottom_border_y):
                grid = 'layout'
            return grid
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in determine_grid_type")


    def display_selected(self, surface, images, layout_x, layout_y, selection_x, selection_y, grid, offset, drop_image=True):
        try:
            # print("selection_x calculating offset:" + str(selection_x))
            # print("selection_y calculating offset:" + str(selection_y))
            # x ranges 1 to 10 , y ranges 1 to 10
            # offset is the position in the image array and can be used to get the image array that will be used when generating level data
            # A dictionary of these offset values, can be kept for generating the level data in terms of x,y coords
            cursorx = 700
            cursory = 700
            if grid == 'selection':
                a=1
                #print("selected image offset for selection:" + str(offset))
            elif grid == 'layout':
                # we dont need to change the offset value as it should point to the default or actual image we have
                # selected from the selection grid
                #print("current layout x" + str(layout_x))
                #print("current layout y" + str(layout_y))
                # calculate actual x y where selected object will be dropped
                cursorx, cursory = self.convert_grid_pos_into_xy_coords(layout_x, layout_y, grid)
                #print("selected image offset for layout same as selection:" + str(offset))

            pygame.display.update()
            if offset < len(images):
                if drop_image:
                    image_rect = images[offset].get_rect()
                    image_rect.x = 700
                    image_rect.y = 700
                    # display the selected image in the selected item box
                    surface.blit(images[offset], image_rect)
                    image_rect.x = cursorx
                    image_rect.y = cursory
                    # display the selected image at the current layout position if the mouse if over the layout grid
                    # if it is anywhere else it will be put over the existing,
                    # it will be displayed in the selected item box
                    surface.blit(images[offset], image_rect)

                    pygame.display.update()

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in display_selected")

    def convert_grid_pos_into_xy_coords(self, layout_x, layout_y, grid):
        try:
            CURSOR_YOFFSET = 14
            if grid == 'selection':
                cursorx = 32 * (layout_x - 1)  # actual x position of layout_x in pixels
                cursory = (CURSOR_YOFFSET * 32) + (32 * (layout_y - 1))  # actual y position of layout_y in pixels
            elif grid == 'layout':
                cursorx = 32 * (layout_x)  # actual x position of layout_x in pixels
                cursory = (32 * (layout_y))  # actual y position of layout_y in pixels
            # print("layout_x:" +str(layout_x))
            # print("layout_y:" +str(layout_y))
            # print("cursorx:" + str(cursorx))
            # ("cursory:" + str(cursory))

            return cursorx, cursory
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place convert_grid_pos_into_xy_coords")

    def display_empty_grids(self):
        try:
            # draw grid left 20 lots of 32 by 20 lots of 32
            ROWS = 10
            COLS = 10

            YOFFSET = 2  # so we should see a 5* 32 pixel gap between the top grid and the bottom one
            for row in range(ROWS):
                for col in range(COLS):
                    pygame.draw.line(self.display_engine.surface, pygame.Color('firebrick'), (0, (YOFFSET + row) * 32),
                                     (COLS * 32, (YOFFSET + row) * 32))
                    pygame.draw.line(self.display_engine.surface, pygame.Color('firebrick'), (col * 32, (YOFFSET * 32)),
                                     (col * 32, (row + YOFFSET) * 32))
                    pygame.draw.line(self.display_engine.surface, pygame.Color('firebrick'),
                                     ((col + 1) * 32, (YOFFSET * 32)), ((col + 1) * 32, (row + YOFFSET) * 32))

            ROWS = 11
            COLS = 10

            YOFFSET = 14  # so we should see a 5* 32 pixel gap between the top grid and the bottom one
            for row in range(ROWS):
                for col in range(COLS):
                    pygame.draw.line(self.display_engine.surface, pygame.Color('firebrick'), (0, (YOFFSET + row) * 32),
                                     (COLS * 32, (YOFFSET + row) * 32))
                    pygame.draw.line(self.display_engine.surface, pygame.Color('firebrick'), (col * 32, (YOFFSET * 32)),
                                     (col * 32, (row + YOFFSET) * 32))
                    pygame.draw.line(self.display_engine.surface, pygame.Color('firebrick'),
                                     ((col + 1) * 32, (YOFFSET * 32)), ((col + 1) * 32, (row + YOFFSET) * 32))
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place display_empty_grids")

        # Area you are looking for.

    def tile_image(self, surface, image):
        try:
            width, height = self.display_engine.rect.size
            i_width, i_height = image.get_size()
            camera_x = int(self.camera.x % i_width)
            camera_y = int(self.camera.y % i_height)
            for x in range(-camera_x, width, i_width):
                for y in range(-camera_y, height, i_height):
                    surface.blit(image, (x, y))
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in tile_image")

    # draw text1 and text2 on the sceen at coordinates x and y, with font and text color set as parameters passed in
    def draw_text(self, text1, text2, xcord, ycord, surface, font, text_col, x, y):
        try:
            img = font.render(text1 + ":" + str(xcord) + " " + text2 + ":" + str(ycord), True, text_col)
            surface.blit(img, (x, y))
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in draw_text")

    def display_selection_grid(self, surface, button_id):
        # define start position  in place of count = 1 as we page up and down the array.
        # page down, we would add 100 to the count, page up subtract 100, assuming a 10 by 10 grid
        try:
            # we need to just clear the selection grid here and refill it
            # when we change selection types
            # surface.fill(pygame.Color("black"))
            # surface.fill((0, 0, 0))  # clear screen
            # print("displaying selection grid")
            self.display_empty_grids()
            count = 1
            images = display_engine.load_images(button_id)
            for row in range(0, 10):
                for column in range(0, 10):
                    image_rect = images[count].get_rect(topleft=(100, 300))
                    image_rect.x = 10
                    image_rect.y = 20
                    image_rect = images[count].get_rect()
                    image_rect.x = column * 32
                    image_rect.y = (row + 1) * 32
                    surface.blit(images[count], image_rect)
                    pygame.display.update()
                    count += 1
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in display_selection_grid")

    def update_grid_data(self, offset ,selection_image_grid, layout_x, layout_y):
        try:
            #print("layout_target_grid" + str(len(layout_target_grid)))
            #print("selection_image_grid" + str(len(selection_image_grid)))
            print("layoutx" + str(layout_x))
            print("layouty" + str(layout_y))
            layout_offset = ((layout_y - 14) * 10) + layout_x
            print("layout_offset" + str(offset))
            print("offset" + str (offset))
            print("layout_target_grid[layout_offset] = selection_image_grid[offset]")
            layout_target_grid[layout_offset] = offset
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in update_grid_data")

    def generate_level_data(self, layout_target_grid):
        try:
            w, h = 10, 10
            my_array = [[0 for x in range(w)] for y in range(h)]
            print("in generate level data")
            count =0
            for row in range(0, 10):
                print("\n")
                for column in range(0, 10):
                        print(str(layout_target_grid[count]) + ",")
                        my_array[row][column] = layout_target_grid[count]
                        print("column:" + str(column))
                        print("row:" + str(row))
                        print("1")
                        print ("my_array: " + str(my_array[row][column]))
                        print("2")
                        count = count + 1


            with open("output.csv", "w") as f:
                writer = csv.writer(f)
                writer.writerows(my_array)

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in generate_level_data")

    def mainloop(self):
        try:
            # define player action variables
            self.display_engine.running = True
            page_images_up_button = pygame.image.load('img/page_images_up_button.png').convert_alpha()
            page_images_down_button = pygame.image.load('img/page_images_down_button.png').convert_alpha()
            generate_level_data_button = pygame.image.load('img/generate_level_data_button.png').convert_alpha()
            armour_button = pygame.image.load('img/armour.png').convert_alpha()
            artifacts_button = pygame.image.load('img/artifacts.png').convert_alpha()
            backgrounds_button = pygame.image.load('img/backgrounds.png').convert_alpha()
            humans_button = pygame.image.load('img/humans.png').convert_alpha()
            magical_items_button = pygame.image.load('img/magical_items.png').convert_alpha()
            monsters_button = pygame.image.load('img/monsters.png').convert_alpha()
            potions_button = pygame.image.load('img/potions.png').convert_alpha()
            spell_books_button = pygame.image.load('img/spell_books.png').convert_alpha()
            traps_button = pygame.image.load('img/traps.png').convert_alpha()
            weapons_button = pygame.image.load('img/weapons.png').convert_alpha()

            # create buttons
            page_images_up_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 750,
                                                  page_images_up_button,
                                                  1)
            page_images_down_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 700,
                                                    page_images_down_button, 1)
            generate_level_data_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 650,
                                                       generate_level_data_button, 1)

            armour_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 550, armour_button, 1)
            artifacts_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 500, artifacts_button, 1)
            backgrounds_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 450, backgrounds_button, 1)
            humans_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 400, humans_button, 1)
            magical_items_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 350, magical_items_button,
                                                 1)
            monsters_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 300, monsters_button, 1)
            potions_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 250, potions_button, 1)
            spell_books_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 200, spell_books_button, 1)
            traps_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 150, traps_button, 1)
            weapons_button = button.Button(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 1 - 100, weapons_button, 1)

            rendered_selection = False
            surface = self.display_engine.surface
            # surface.fill(pygame.Color("black"))
            # surface.fill((0, 0, 0))  # clear screen

            button_id = 4  # artefacts
            layout_x = 1
            layout_y = 1
            while self.display_engine.running:
                pos = pygame.mouse.get_pos()
                # print("pos:" +str(pos))
                # print("pos[0]:" + str(pos[0]))
                # print("pos[1]:" + str(pos[1]))
                selection_x = int(pos[0] / 32) + 1
                selection_y = int(pos[1] / 32) + 1
                # print("selection_x" + str(selection_x))
                # print("selection_y" + str(selection_y))

                # define font
                #font = pygame.font.SysFont('Futura', 30)
                #self.draw_text("x", "y", selection_x, selection_y, surface, font, WHITE, 10, 10)

                # check key presses w,a,s,d
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.display_engine.quit()

                if page_images_up_button.draw(surface):
                    button_id = 0
                if page_images_down_button.draw(surface):
                    button_id = 1
                if generate_level_data_button.draw(surface):
                    button_id = 2
                    self.generate_level_data(layout_target_grid)
                    self.display_engine.quit()

                if armour_button.draw(surface):
                    button_id = 3
                    rendered_selection = False
                if artifacts_button.draw(surface):
                    button_id = 4
                    rendered_selection = False
                if backgrounds_button.draw(surface):
                    button_id = 5
                    rendered_selection = False
                if humans_button.draw(surface):
                    button_id = 6
                    rendered_selection = False
                if magical_items_button.draw(surface):
                    button_id = 7
                    rendered_selection = False
                if monsters_button.draw(surface):
                    button_id = 8
                    rendered_selection = False
                if potions_button.draw(surface):
                    button_id = 9
                    rendered_selection = False
                if spell_books_button.draw(surface):
                    button_id = 10
                    rendered_selection = False
                if traps_button.draw(surface):
                    button_id = 11
                    rendered_selection = False
                if weapons_button.draw(surface):
                    button_id = 12
                    rendered_selection = False

                if not rendered_selection:
                    self.display_selection_grid(surface, button_id)
                    images = display_engine.load_images(button_id)
                    rendered_selection = True

                keys = pygame.key.get_pressed()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    grid = self.determine_grid_type()
                    #print("grid:" + grid)
                    pos = pygame.mouse.get_pos()
                    #print("pos[0]:" + str(pos[0]))
                    #print("pos[1]:" + str(pos[1]))
                    drop_image = True
                    if grid == 'selection':
                        selection_x = int(pos[0] / 32)
                        selection_y = int(pos[1] / 32)
                        offset = ((selection_y - 1) * 10) + selection_x + 1
                        self.display_selected(surface, images, layout_x, layout_y, selection_x, selection_y, grid,
                                              offset, drop_image)
                    elif grid == 'layout':
                          layout_x = int(pos[0]/32)
                          layout_y = int(pos[1]/32)
                          pygame.draw.rect(self.display_engine.surface, pygame.Color(0, 0, 255, 255),
                                           (layout_x * 32, (layout_y * 32), 32, 32), 1)
                          self.display_selected(surface, images, layout_x, layout_y, selection_x, selection_y, grid, offset,
                                        drop_image)
                          self.update_grid_data(offset, selection_image_grid, layout_x, layout_y)
                    MousePressed = True
                    MouseDown = True
                    pygame.display.update()
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in mainloop")


if __name__ == '__main__':
    DisplayEngine.center_screen()
    display_engine = DisplayEngine("Level Designer", 1024, 1024)
    images = display_engine.load_images(INITIAL_IMAGES)
    scene = Scene(display_engine)
    scene.mainloop()
