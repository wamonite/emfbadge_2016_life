### Author: wamonite
### Description: Conway's Game of Life
### Category: uncategorised
### License: MIT
### Appname: life

import pyb
import ugfx
import buttons
import onboard

COLOUR_BACK = ugfx.BLACK
COLOUR_LIST = [ugfx.RED, ugfx.GREEN, ugfx.BLUE]
PIXEL_WIDTH = 4
PIXEL_HEIGHT = 4
FRAME_DELAY = 100  # ms
HASH_COUNT_LIMIT = 20


def get_random(count):
    return pyb.rng() % count


def get_colour(colour_current = None):
    while True:
        colour = COLOUR_LIST[get_random(len(COLOUR_LIST))]
        if colour != colour_current:
            return colour


class BitArray(object):

    def __init__(self, size):
        self._size = size
        self._size_elements = size >> 3
        if size % 8:
            self._size_elements += 1

        self._array = bytearray([0] * self._size_elements)

    @property
    def size(self):
        return self._size

    @property
    def size_bytes(self):
        return self._size_elements

    def test_bit(self, bit_index):
        element = bit_index >> 3
        offset = bit_index % 8
        mask = 1 << offset
        return bool(self._array[element] & mask)

    def set_bit(self, bit_index):
        element = bit_index >> 3
        offset = bit_index % 8
        mask = 1 << offset
        self._array[element] |= mask

    def clear_bit(self, bit_index):
        element = bit_index >> 3
        offset = bit_index % 8
        mask = ~(1 << offset)
        self._array[element] &= mask

    def randomise(self):
        for idx in range(self._size_elements):
            self._array[idx] = pyb.rng() & 0xff

    def hash(self):
        # noddy xor hash
        val = 0
        for idx in range(self._size_elements):
            val = val ^ self._array[idx]
        return val


class Grid:

    def __init__(self, width, height, pixel_width = PIXEL_WIDTH, pixel_height = PIXEL_HEIGHT, colour_fore = None, colour_back = None):
        self._width = width // pixel_width
        self._height = height // pixel_height
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
            x = self._width // 2
        if y is None:
            y = self._height // 2

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
                line += '.' if self._cells_display.test_bit(idx) else '0'
                idx += 1
            print(line)

    def display_badge(self):
        for y in range(self._height):
            for x in range(self._width):
                cell_alive = self.get_cell(x, y)
                colour = self._colour_fore if cell_alive else self._colour_back
                ugfx.area(
                    x * self._pixel_width,
                    y * self._pixel_height,
                    self._pixel_width,
                    self._pixel_height,
                    colour
                )


def do_circle_of_life():
    ugfx.init()
    buttons.init()
    buttons.disable_menu_reset()

    colour = get_colour()
    grid = Grid(ugfx.width(), ugfx.height(), colour_fore = colour, colour_back = COLOUR_BACK)
    grid.randomise()

    ugfx.clear(COLOUR_BACK)

    hash_count = 0
    hash_last = None
    hash_last_last = None
    while True:
        # display
        grid.display_badge()
        # grid.display_text()

        # pyb.delay(FRAME_DELAY)

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

        pyb.wfi()
        if buttons.is_triggered("BTN_A") or buttons.is_triggered("BTN_B"):
            colour = get_colour(colour)
            grid.set_colour(colour)
            grid.randomise()

        if buttons.is_triggered("BTN_MENU"):
            break


do_circle_of_life()
