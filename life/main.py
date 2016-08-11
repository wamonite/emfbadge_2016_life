### Author: wamonite
### Description: Conway's Game of Life
### Category: uncategorised
### License: MIT
### Appname: life by wamonite
### Built-in: no

import array
try:
    import pyb
    import ugfx
    import buttons
    import onboard
    COLOUR_BACK = ugfx.BLACK
    COLOUR_LIST = [ugfx.RED, ugfx.GREEN, ugfx.BLUE]
    RUNNING_ON_BADGE = True

except ImportError:
    import random
    from time import sleep
    COLOUR_BACK = '0'
    COLOUR_LIST = ['.', ',']
    RUNNING_ON_BADGE = False

DEFAULT_WIDTH = 20
DEFAULT_HEIGHT = 20
PIXEL_WIDTH = 2
PIXEL_HEIGHT = 2
FRAME_DELAY = 100  # ms
HASH_COUNT_LIMIT = 20


def get_random(count):
    return pyb.rng() % count if RUNNING_ON_BADGE else random.randint(0, count - 1)


def get_colour(colour_current = None):
    while True:
        colour = COLOUR_LIST[get_random(len(COLOUR_LIST))]
        if colour != colour_current:
            return colour


class BitArray(object):

    def __init__(self, size):
        self._size = size
        self._size_elements = size >> 5
        if size & 32:
            self._size_elements += 1

        self._array = array.array('I', [0] * self._size_elements)
        assert self._array.itemsize == 4

    @property
    def size(self):
        return self._size

    @property
    def size_bytes(self):
        return self._size_elements * self._array.itemsize

    def test_bit(self, bit_index):
        element = bit_index >> 5
        offset = bit_index & 31
        mask = 1 << offset
        return bool(self._array[element] & mask)

    def set_bit(self, bit_index):
        element = bit_index >> 5
        offset = bit_index & 31
        mask = 1 << offset
        self._array[element] |= mask

    def clear_bit(self, bit_index):
        element = bit_index >> 5
        offset = bit_index & 31
        mask = ~(1 << offset)
        self._array[element] &= mask

    def randomise(self):
        if RUNNING_ON_BADGE:
            # TODO
            pass

        else:
            for idx in range(self._size_elements):
                self._array[idx] = random.getrandbits(32)

    def hash(self):
        # noddy xor hash
        val = 0
        for idx in range(self._size_elements):
            val = val ^ self._array[idx]
        return val


class Grid:

    def __init__(self, width, height, pixel_width = PIXEL_WIDTH, pixel_height = PIXEL_HEIGHT, colour_fore = None, colour_back = None):
        self._width = int(width / pixel_width)
        self._height = int(height / pixel_height)
        self._colour_fore = colour_fore
        self._colour_back = colour_back
        self._pixel_width = pixel_width
        self._pixel_height = pixel_height
        self._cells_display = BitArray(self._width * self._height)
        self._cells_next = BitArray(self._width * self._height)

    def get_cell(self, x, y, display_buffer = True):
        cells = self._cells_display if display_buffer else self._cells_next
        return cells.test_bit(x + y * self._width)

    def set_cell(self, x, y, display_buffer = False):
        cells = self._cells_display if display_buffer else self._cells_next
        cells.set_bit(x + y * self._width)

    def clear_cell(self, x, y, display_buffer = False):
        cells = self._cells_display if display_buffer else self._cells_next
        cells.clear_bit(x + y * self._width)

    def add_glider(self, x = None, y = None):
        if x is None:
            x = self._width / 2
        if y is None:
            y = self._height / 2

        self.set_cell(x + 2, y, display_buffer = True)
        self.set_cell(x, y + 1, display_buffer = True)
        self.set_cell(x + 2, y + 1, display_buffer = True)
        self.set_cell(x + 1, y + 2, display_buffer = True)
        self.set_cell(x + 2, y + 2, display_buffer = True)

    def randomise(self):
        self._cells_display.randomise()

    def hash(self):
        return self._cells_display.hash()

    def set_colour(self, colour):
        self._colour_fore = colour

    def swap_cell_buffers(self):
        temp_cells = self._cells_display
        self._cells_display = self._cells_next
        self._cells_next = temp_cells

    def next_generation(self):
        for x in range(0, self._width):
            if x == 0:
                x_down = self._width - 1
            else:
                x_down = x - 1

            if x == self._width - 1:
                x_up = 0
            else:
                x_up = x + 1

            for y in range(0, self._height):
                if y == 0:
                    y_down = self._height - 1
                else:
                    y_down = y - 1

                if y == self._height - 1:
                    y_up = 0
                else:
                    y_up = y + 1

                neighbour_count = 0
                for neighbour in [
                    (x_down, y_up),
                    (x, y_up),
                    (x_up, y_up),
                    (x_down, y),
                    (x_up, y),
                    (x_down, y_down),
                    (x, y_down),
                    (x_up, y_down),
                ]:
                    neighbour_count += 1 if self.get_cell(neighbour[0], neighbour[1]) else 0

                cell_alive = self.get_cell(x, y)
                if cell_alive and neighbour_count < 2 or neighbour_count > 3:
                    self.clear_cell(x, y)
                elif not cell_alive and neighbour_count == 3:
                    self.set_cell(x, y)
                elif cell_alive:
                    self.set_cell(x, y)
                else:
                    self.clear_cell(x, y)

    def display_text(self):
        idx = 0
        for y in range(self._height):
            line = ""
            for x in range(self._width):
                line += self._colour_fore if self._cells_display.test_bit(idx) else self._colour_back
                idx += 1
            print(line)

    # TODO
    # def display_badge(self):
    #     for y in range(self._height):
    #         for x in range(self._width):
    #             cell = self.cells[x][y]
    #             colour = self._colour_fore if cell.state else self._colour_back
    #             ugfx.area(
    #                 x * self._pixel_width,
    #                 y * self._pixel_height,
    #                 self._pixel_width,
    #                 self._pixel_height,
    #                 colour
    #             )


def do_circle_of_life():
    screen_width = DEFAULT_WIDTH
    screen_height = DEFAULT_HEIGHT

    if RUNNING_ON_BADGE:
        ugfx.init()
        buttons.init()
        buttons.disable_menu_reset()
        screen_width = ugfx.width()
        screen_height = ugfx.height()
        ugfx.clear(ugfx.BLACK)

    grid = None
    hash_count = 0
    hash_last = None
    hash_last_last = None
    colour = get_colour()

    while True:
        # initialise, if needed
        if grid is None:
            grid = Grid(screen_width, screen_height, colour_fore = colour, colour_back = COLOUR_BACK)
            grid.randomise()

        # display
        if RUNNING_ON_BADGE:
            grid.display_badge()

            pyb.delay(FRAME_DELAY)

            pyb.wfi()
            if buttons.is_triggered("BTN_A") or buttons.is_triggered("BTN_B"):
                grid = None

            if buttons.is_triggered("BTN_MENU"):
                break

        else:
            grid.display_text()

            sleep(float(FRAME_DELAY) / 1000.0)

        # randomise, if needed
        hash_val = grid.hash()
        if hash_val == hash_last_last:
            hash_count += 1

            if hash_count == HASH_COUNT_LIMIT:
                colour = get_colour(colour)
                grid.set_colour(colour)
                grid.randomise()
                hash_count = 0

        else:
            hash_count = 0

        hash_last_last = hash_last
        hash_last = hash_val

        # process next generation
        grid.next_generation()
        grid.swap_cell_buffers()

try:
    do_circle_of_life()

except KeyboardInterrupt:
    pass
