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
PIXEL_WIDTH = 5
PIXEL_HEIGHT = 5
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

        self._array = None
        self.clear()

    @property
    def size(self):
        return self._size

    @property
    def size_bytes(self):
        return self._size_elements

    def clear(self):
        self._array = None
        self._array = bytearray([0] * self._size_elements)

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

    @micropython.viper
    def randomise(self):
        array = ptr8(self._array)
        idx = int(self._size_elements)
        while idx:
            val = int(pyb.rng()) & 0xff
            array[idx] = val
            idx -= 1

    @micropython.viper
    def hash(self) -> int:
        # noddy xor hash
        val = 0
        array = ptr8(self._array)
        idx = int(self._size_elements)
        while idx:
            val = val ^ array[idx]
            idx -= 1
        return val

    @micropython.viper
    def get_block(self, block_index: int) -> int:
        array = ptr8(self._array)
        return array[block_index]


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

    @micropython.native
    def display_badge(self):
        x = 0
        y = 0
        x_pixel = 0
        y_pixel = 0
        block_idx = 0
        block_idx_limit = self._cells_display.size_bytes
        cells = self._cells_display
        width = self._width
        colour_fore = self._colour_fore
        colour_back = self._colour_back
        pixel_width = self._pixel_width
        pixel_height = self._pixel_height
        hash_val = 0
        while block_idx < block_idx_limit:
            cell_block = cells.get_block(block_idx)
            hash_val ^= cell_block
            mask = 1
            mask_idx = 0
            while mask_idx < 8:
                cell_alive = mask & cell_block
                colour = colour_fore if cell_alive else colour_back
                ugfx.area(
                    x_pixel,
                    y_pixel,
                    pixel_width,
                    pixel_height,
                    colour
                )

                mask <<= 1
                mask_idx += 1

                x += 1
                x_pixel += pixel_width
                if x == width:
                    x = 0
                    x_pixel = 0
                    y += 1
                    y_pixel += pixel_height

            block_idx += 1

        return hash_val


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
        hash_val = grid.display_badge()

        # randomise, if needed
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

        # buttons
        pyb.wfi()
        if buttons.is_triggered("BTN_A") or buttons.is_triggered("BTN_B"):
            colour = get_colour(colour)
            grid.set_colour(colour)
            grid.randomise()

        if buttons.is_triggered("BTN_MENU"):
            break


do_circle_of_life()
