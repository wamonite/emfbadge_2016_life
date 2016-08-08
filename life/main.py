### Author: @wamonite
### Description: Conway's Game of Life
### Category: uncategorised
### License: MIT
### Appname: life by wamonite
### Built-in: no

import pyb
import ugfx
import buttons
import onboard

PIXEL_WIDTH = 20
PIXEL_HEIGHT = 20
FRAME_DELAY = 100  # ms


def get_random(count):
    return pyb.rng() % count


class Cell(object):
    def __init__(self):
        self._alive = False
        self._alive_next = None

    @property
    def state(self):
        return self._alive

    @property
    def state_changed(self):
        return False if self._alive_next is None else (self._alive != self._alive_next)

    def set_state(self, state):
        self._alive = state
        self._alive_next = None

    def calculate_generation_state(self, neighbour_count):
        """Work out whether this cell will be alive at the next iteration."""

        if self._alive and (neighbour_count > 3 or neighbour_count < 2):
            self._alive_next = False
        elif not self._alive and neighbour_count == 3:
            self._alive_next = True
        else:
            self._alive_next = self._alive

    def next_generation_state(self):
        self._alive = self._alive_next


class Grid:

    COLOURS = (ugfx.RED, ugfx.GREEN, ugfx.BLUE)

    def __init__(self, width, height, pixel_width = PIXEL_WIDTH, pixel_height = PIXEL_HEIGHT):
        self.width = int(width / pixel_width)
        self.height = int(height / pixel_height)
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        self.cells = []
        self.colour = self.COLOURS[get_random(len(self.COLOURS))]

        for x in range(0, self.width):
            cell_row = []
            for y in range(0, self.height):
                cell = Cell()
                cell.set_state(get_random(2))
                cell_row.append(cell)

            self.cells.append(cell_row)

    def next_generation(self):
        cells = self.cells
        for x in range(0, self.width):
            if x == 0:
                x_down = self.width - 1
            else:
                x_down = x - 1

            if x == self.width - 1:
                x_up = 0
            else:
                x_up = x + 1

            for y in range(0, self.height):
                if y == 0:
                    y_down = self.height - 1
                else:
                    y_down = y - 1

                if y == self.height - 1:
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
                    neighbour_count += 1 if cells[neighbour[0]][neighbour[1]].state else 0

                cells[x][y].calculate_generation_state(neighbour_count)

        for cell_row in cells:
            for cell in cell_row:
                cell.next_generation_state()

    def display(self):
        for cell_row in self.cells:
            line = ""
            for cell in cell_row:
                line += "." if cell.state else "O"
            print(line)

    def badge(self):
        for y in range(self.height):
            for x in range(self.width):
                cell = self.cells[x][y]
                colour = self.colour if cell.state else ugfx.BLACK
                ugfx.area(
                    x * self.pixel_width,
                    y * self.pixel_height,
                    self.pixel_width,
                    self.pixel_height,
                    colour
                )


def do_circle_of_life():
    ugfx.init()
    buttons.init()
    buttons.disable_menu_reset()

    grid = None

    ugfx.area(0, 0, ugfx.width(), ugfx.height(), 0)
    while True:
        if grid is None:
            grid = Grid(ugfx.width(), ugfx.height())

        grid.next_generation()
        grid.badge()

        pyb.delay(FRAME_DELAY)

        pyb.wfi()
        if buttons.is_triggered("BTN_A") or buttons.is_triggered("BTN_B"):
            grid = None

        if buttons.is_triggered("BTN_MENU"):
            break


do_circle_of_life()
