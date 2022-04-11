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
layout_target_grid = []

for count in range(100):
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
        self.start_image_array = 1
        self.end_image_array = 100
        self.previous_button_id = -1
        self.current_page = 1
        self.directory = 'img/tile/armour/renamed/'  # default''


    def idle(self):
        self.delta = self.clock.tick(self.fps)

    def quit(self):
        self.running = False



    def check_page_boundries(self, arraySize, startpos):
        """Checks that the startpos value does not exceed the size of the image array to prevent a index out of bounds exception
        @param arraySize The size of the image array
        @param startpos: he start position of the image_list array which we want to display images in the selection grid

        @returns: start_pos: The start position of the image_list array which we want to display images in the selection grid
        """

        # print("checking boundries current_page before:" + str(self.current_page))
        # print("checking boundries before arraySize:" + str(arraySize))

        if startpos > arraySize:
            self.current_page = 1
        return startpos

    def load_images(self, button_id):
        """Loads the images from the file system , based on the selected image type (button id)

        @param button_id: The selected button_id

        @returns: non_blank_images: The start position of the image_list array which we want to display images in the selection grid
        @returns: image_list: The image_list array filled in preparation to fill the selection grid
        @returns: button_id: The selected button_id
        """
        try:
            print("selected button_id" + str(button_id))
            if button_id == 3:
                self.directory = 'img/tile/armour/renamed/'
            elif button_id == 4:
                self.directory = 'img/tile/artifacts/renamed/'
            elif button_id == 5:
                self.directory = 'img/tile/backgrounds/renamed/'
            elif button_id == 6:
                self.directory = 'img/tile/humans/renamed/'
            elif button_id == 7:
                self.directory = 'img/tile/magical_items/renamed/'
            elif button_id == 8:
                self.directory = 'img/tile/monsters/renamed/'
            elif button_id == 9:
                self.directory = 'img/tile/potions/renamed/'
            elif button_id == 10:
                self.directory = 'img/tile/spellbooks/renamed/'
            elif button_id == 11:
                self.directory = 'img/tile/traps/renamed/'
            elif button_id == 12:
                self.directory = 'img/tile/weapons/renamed/'

            # pagination specify start and end position and return image array accordingly
            # page up 0, page down 1 button_id
            # Python program to split array and move first
            # part to end.

            image_list = []
            blank_image = pygame.image.load("img/tile/backgrounds/renamed/8.png")

            for count, filename in enumerate(os.listdir(self.directory)):
                img = pygame.image.load(f'{self.directory}/{filename}').convert_alpha()
                image_list.append(img)
            # print("image list size" + str(len(image_list)))
            non_blank_images = len(image_list)
            number_of_pages = int(len(image_list)/100) + 1
            nearest_hundred = ((number_of_pages) * 100)
            # get difference between array size and next number that is exactly divisible by 100
            # so 123, we would want 200-123=77 or 245, we would want 300-245=55 for example

            remaining_array_spaces = nearest_hundred - len(image_list) + 1
            # print("next 100 number" + str(nearest_hundred))
            # print("number_of_pages" + str(number_of_pages))
            # print("length of image list" + str(len(image_list)))
            # print("remaining_array_spaces" + str(remaining_array_spaces))
            for newcount in range(0, remaining_array_spaces):
                image_list.append(blank_image)
            # print("final length of array" + str(len(image_list)))
            return non_blank_images, image_list, button_id

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
        self.previous_button_id = -1
        self.current_page = 1

    def page_down(self):
        """set the current page value based on the page down'
        """
        self.current_page = self.current_page + 1
        print("page down")
        print("new current page" + str(self.current_page))

    def page_up(self):
        """set the current page value based on the page up'
        """
        self.current_page = self.current_page - 1
        print("page up")
        print("new current page" + str(self.current_page))

    def determine_grid_type(self):
        """Determine where we are in the grid and set the grid type to 'off_grid', 'selection', or 'layout'

        @returns: grid:  grid type to set 'off_grid', 'selection', or 'layout'
        """
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

            # print("selection_left_border_x" + str (selection_left_border_x))
            # print("selection_right_border_x" + str (selection_right_border_x))
            # print("selection_top_border_y" + str (selection_top_border_y))
            # print("selection_bottom_border_y" + str (selection_bottom_border_y))

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


    def display_selected(self, surface, images, layout_x, layout_y, grid, offset, startpos, drop_image=True):
        """Displays the selection grid

        @param surface: The surface used to blit images
        @param images: The images array
        @param layout_x: The layout_x x position where the selected image is going to be placed
        @param layout_y: The layout_y y position where the selected image is going to be placed
        @param grid: Has the value selection or layout based on where the mouse in clicked in which grid
        @param offset: The offset of from the start of the image array, so that we know which image to place in the layout grid
        @param startpos: The start position of the array that is displayed. Used when we change pages
        @param drop_image: A boolean flag to indicate, we wish to drop an image onto the layout grid
        """
        try:
            # print("selection_x calculating offset:" + str(selection_x))
            # print("selection_y calculating offset:" + str(selection_y))
            # x ranges 1 to 10 , y ranges 1 to 10
            # offset is the position in the image array and can be used to get the image array that will be used when generating level data
            # A dictionary of these offset values, can be kept for generating the level data in terms of x,y coords
            # print ("in display selected")
            cursorx = 700
            cursory = 700
            if grid == 'selection':
                a=1
                #print("selected image offset for selection:" + str(offset))
            elif grid == 'layout':
                # we dont need to change the offset value as it should point to the default or actual image we have
                # selected from the selection grid
                # print("current layout x" + str(layout_x))
                # print("current layout y" + str(layout_y))
                # calculate actual x y where selected object will be dropped
                cursorx, cursory = self.convert_grid_pos_into_xy_coords(layout_x, layout_y, grid)
                # print("selected image offset for layout same as selection:" + str(offset))

            pygame.display.update()

            if offset < len(images):
                if drop_image:
                    image_rect = images[offset + startpos - 1].get_rect()
                    image_rect.x = 700
                    image_rect.y = 700
                    # display the selected image in the selected item box
                    surface.blit(images[offset + startpos - 1], image_rect)
                    image_rect.x = cursorx
                    image_rect.y = cursory
                    # display the selected image at the current layout position if the mouse if over the layout grid
                    # if it is anywhere else it will be put over the existing,
                    # it will be displayed in the selected item box
                    surface.blit(images[offset + startpos + -1], image_rect)

                    pygame.display.update()

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in display_selected")

    def convert_grid_pos_into_xy_coords(self, layout_x, layout_y, grid):
        """Calculate the x and y position in pixels with the calculation different based on the grid i.e selection or layout

        @param layout_y: The y coordinate value 1 to 10
        @param layout_y: The x coordinate value 1 to 10
        """
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
        """Displays the selection grid and layout grid as two 10 x 10 empty grids
        """
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

    # def tile_image(self, surface, image):
    #     try:
    #         width, height = self.display_engine.rect.size
    #         i_width, i_height = image.get_size()
    #         camera_x = int(self.camera.x % i_width)
    #         camera_y = int(self.camera.y % i_height)
    #         for x in range(-camera_x, width, i_width):
    #             for y in range(-camera_y, height, i_height):
    #                 surface.blit(image, (x, y))
    #     except Exception as e:
    #         if hasattr(e, 'message'):
    #             print(e.message)
    #         else:
    #             print(e)
    #         print("An exception has taken place in tile_image")

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
        """Displays the selection grid

        @param surface: The file location of the spreadsheet
        @param button_id: The id of the selected button that has been pressed

        @returns: startpos: The start position at which we want to display images in the selection grid
        @returns: endpos: The endpos or end element image array. As we always display 100 images at a time in the selection grid
        """
        try:
            # we need to just clear the selection grid here
            self.display_empty_grids()
            count = 0
            
            # check whether the page up or page_down button has been pressed and change the current page if it has
            if button_id == 0:
              self.page_up()
            elif button_id == 1:
              self.page_down()

            # load the images based on the currently selected page and button id into the grid and return array size of the images that are selectable and the images array i.e non-blank images and the selected button_id
            non_blank_images, images, button_id = display_engine.load_images(button_id)
            endpos = len(images)-1
            startpos = 1

            #set the startpos to select the relevant portion of the image array that we want to display in the selection grid based on the current page number

            if self.current_page == 1:
               startpos = 1
            else:
               startpos = (self.current_page - 1) * 100

            # when checking the startpos, it must not be greater than the length of the array of non blank images. checks that we don't get an array out of bounds

            if startpos > non_blank_images:
                startpos = 1

            # print("display selection grid length images" + str(len(images)))
            # print("display selection grid startpos" + str(startpos))
            # print("display selection grid endpos" + str(endpos))

            # display selection grid
            for row in range(0, 10):
                for column in range(0, 10):
                    image_rect = images[count + startpos].get_rect(topleft=(100, 300))
                    image_rect.x = 10
                    image_rect.y = 20
                    image_rect = images[count + startpos].get_rect()
                    image_rect.x = column * 32
                    image_rect.y = (row + 1) * 32
                    surface.blit(images[count + startpos], image_rect)
                    pygame.display.update()
                    count += 1
            return startpos, endpos
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in display_selection_grid")

    def update_grid_data(self, offset , layout_x, layout_y):
        """Updates the array that will be used to generate the output data with the image id from filename

        @param offset: The image id taken from the filename
        @param layout_x: The x coordinate of the selected image in the layout 10 x 10 grid
        @param layout_y: The y coordinate of the selected image in the layout 10 x 10 grid
        """
        try:

            layout_offset = ((layout_y - 14) * 10) + layout_x
            layout_target_grid[layout_offset] = offset
            # print("layout_target_grid" + str(len(layout_target_grid)))
            # print("layoutx" + str(layout_x))
            # print("layouty" + str(layout_y))
            # print("layout_offset" + str(offset))
            # print("offset" + str (offset))
            # print("layout_target_grid[layout_offset] = selection_image_grid[offset]")

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            print("An exception has taken place in update_grid_data")

    def generate_level_data(self, layout_target_grid):
        """Generate the level data and write it to an output file

        @param layout_target_grid: array that contains the layout data
        """
        try:
            w, h = 10, 10
            my_array = [[0 for x in range(w)] for y in range(h)]
            print("Generating level data in output.csv")
            count =0
            for row in range(0, 10):
                print("\n")
                for column in range(0, 10):
                        my_array[row][column] = layout_target_grid[count]
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
        """main loop that displays the selection and layout grid, along with buttons to select
           the select image types, page up and down and generate the output test file, once updated using the selection grid
           to update the layout grid
         """
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


            button_id = 4  # default to display artefacts
            layout_x = 1
            layout_y = 1
            self.page_change = False
            # loop while we don't exit
            while self.display_engine.running:
                # get mouse position
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
                        break

                # set the button id, based on the selected button
                if page_images_up_button.draw(surface):
                    button_id = 0
                    rendered_selection = False
                    self.page_change = True
                if page_images_down_button.draw(surface):
                    button_id = 1
                    rendered_selection = False
                    self.page_change = True
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

                # if a button is selected that differs from the last button selected then reload the appropriate images
                # into the imoage selection grid. If page up or down is selected, change the currently selected page, and update the images
                # in the selection grid. If generate is selected then generate the output data based on the contents of the layout grid
                if button_id != self.previous_button_id:
                    print("displaying selection grid")
                    startpos, endpos = self.display_selection_grid(surface, button_id)

                    print("buttonid changed, reloading images" + str(button_id))
                    # non blank images holds the number of images loaded from the filesystem for the current image type
                    non_blank_images, images, button_id = display_engine.load_images(button_id)
                    rendered_selection = True
                    self.previous_button_id = button_id

                if event.type == pygame.MOUSEBUTTONDOWN:
                    grid = self.determine_grid_type()
                    pos = pygame.mouse.get_pos()
                    drop_image = True
                    # if we are selecting an image, then set values in preparation to blit copy it into the layout grid
                    if grid == 'selection':
                        # display all the images in the image array in the selection grid
                        selection_x = int(pos[0] / 32)
                        selection_y = int(pos[1] / 32)
                        offset = ((selection_y - 1) * 10) + selection_x + 1
                        print("display selected selection grid")
                        self.display_selected(surface, images, layout_x, layout_y, grid,
                                             offset, startpos, drop_image)
                    elif grid == 'layout':
                          # display the selected image at the correct location in the layout grid
                          layout_x = int(pos[0]/32)
                          layout_y = int(pos[1]/32)
                          pygame.draw.rect(self.display_engine.surface, pygame.Color(0, 0, 255, 255),
                                           (layout_x * 32, (layout_y * 32), 32, 32), 1)
                          print("display selected layout grid")
                          self.display_selected(surface, images, layout_x, layout_y, grid, offset,
                                        startpos, drop_image)
                          # update the array holding the layout data based on the last dropped item in the layout grid
                          self.update_grid_data(offset, layout_x, layout_y)
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
    #images = display_engine.load_images(INITIAL_IMAGES, False)
    scene = Scene(display_engine)
    scene.mainloop()
