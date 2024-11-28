# hacked-together drawing library for the led matrices

if __name__ == "__main__":
    import os, sys, inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0, parentdir)

import constants
from constants import PYGAME_MODE


WIDTH_PIXELS = 128
HEIGHT_PIXELS = 64

FontCache = {}

if(PYGAME_MODE):
    import pygame
    import led.bdf_reader as bdf_reader
else:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics #type: ignore
    import RPi.GPIO as GPIO #type: ignore

class MatrixDraw():
    def __init__(self, matrix=None):
        if(PYGAME_MODE):
            pygame.init()
            self.screen = pygame.display.set_mode((WIDTH_PIXELS * 8, HEIGHT_PIXELS * 8))
            self.clock = pygame.time.Clock()
        else:
            # Configuration for the matrix
            options = RGBMatrixOptions()
            options.rows = 32
            options.cols = 64
            options.chain_length = 4
            options.pixel_mapper_config = "U-mapper" # Turns the 256x32 screen into a 128x64 one
            options.parallel = 1
            options.hardware_mapping = 'regular'
            options.gpio_slowdown = 4
            options.disable_hardware_pulsing = True

            matrix = RGBMatrix(options = options)

            self.matrix = matrix
            self.alt_buffer = matrix.CreateFrameCanvas()

            # input
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)
            for row_pin in constants.RPI_KEYPAD_ROWS:
                GPIO.setup(row_pin, GPIO.OUT)
            for col_pin in constants.RPI_KEYPAD_COLS:
                GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        self.keys_down = [False] * 16
        self.keys_down_last = [False] * 16

        self.width = WIDTH_PIXELS
        self.height = HEIGHT_PIXELS
        # Layout:
        # 0 1 2 3
        # 4 5 6 7
        # 8 9 A B
        # C D E F

        self.aborted = False
        self.scissor = None # If this is a 4-tuple (left, top, right, bottom), all drawing operations will be confined to that area

    @staticmethod
    def newColor(r: int, g: int, b: int):
        """
        Creates and returns a new Color.
        """

        if(PYGAME_MODE):
            return pygame.Color(r, g, b)
        else:
            return graphics.Color(r, g, b)
    
    @staticmethod
    def newFont(filepath: str):
        """
        Creates and returns a new Font.
        """

        if(PYGAME_MODE):
            return bdf_reader.read_font(filepath)
        else:
            font = graphics.Font()
            font.LoadFont(filepath)
            return font

    def rect(self, x: int, y: int, w: int, h: int, col):
        """
        Draws a rectangle at a specified position, with a specified size and colour.
        """

        x1, x2 = x, x+w
        y1, y2 = y, y+h
        if(self.scissor != None):
            x1, x2 = max(x, self.scissor[0]), min(x+w, self.scissor[2] + 1)
            y1, y2 = max(y, self.scissor[1]), min(y+h, self.scissor[3] + 1)

        if(PYGAME_MODE):
            pygame.draw.rect(self.screen, col, pygame.Rect(x1 * 8, y1 * 8, (x2-x1) * 8, (y2-y1) * 8))
        else:
            for dy in range(y1, y2):
                graphics.DrawLine(x1, dy, x2, dy, col)

    def line(self, x1: int, y1: int, x2: int, y2: int, col):
        # TODO: Make this work with the scissor

        if(PYGAME_MODE):
            # TODO
            if(x1 == x2):
                pygame.draw.rect(self.screen, col, pygame.Rect(x1 * 8, y1 * 8, 8, (y2-y1+1) * 8))
            elif(y1 == y2):
                pygame.draw.rect(self.screen, col, pygame.Rect(x1 * 8, y1 * 8, (x2-x1+1) * 8, 8))
            
        else:
            graphics.DrawLine(x1, y1, x2, y2, col)

    def setPixel(self, x: int, y: int, col):
        """
        Sets a pixel at a specified location to a given colour.
        """

        if(self.scissor != None):
            # Don't do anything if the pixel falls outside the scissor region
            if(not (self.scissor[0] <= x <= self.scissor[2] and self.scissor[1] <= y <= self.scissor[3])):
                return

        if(PYGAME_MODE):
            self.rect(x, y, 1, 1, col)
        else:
            self.alt_buffer.SetPixel(x, y, col.red, col.green, col.blue)

    def setScissor(self, left, top, right, bottom):
        """
        Sets the current scissor region to a given rectangle (left, top, right, bottom).

        If the scissor is currently active, all drawing operations will be confined to
        that specific region -- nothing will ever be drawn outside of it.

        The only exception is MatrixDraw.clear(), which will always clear the entire screen.
        """

        self.scissor = (left, top, right, bottom)

    def disableScissor(self):
        """
        Disables the current scissor. See MatrixDraw.setScissor() for details.
        """

        self.scissor = None

    def print(self, text: str, x: int, y: int, color, font, align = "l"):
        """
        Prints a specified string to the screen.

        The alignment parameter can take one of three possible values:

        - `l`: The given X position is the start of the text.
        - `c`: The given X position is the horizontal center of the text.
        - `r`: The given X position is the end of the text.
        """

        if(align == "l"): align_offset = 0
        if(align == "c"): align_offset = self.width_of_text(text, font) // 2
        if(align == "r"): align_offset = self.width_of_text(text, font)
        if(PYGAME_MODE):
            draw_x = x - align_offset
            draw_y = y - font["baseline"]
            for char in text:
                if(char == "\n"):
                    draw_x = x - align_offset
                    draw_y += 7
                    continue

                # bad but it works
                for dy, row in enumerate(font[char]):
                    for dx, pixel in enumerate(row):
                        if(pixel == 1):
                            self.rect(draw_x + dx, draw_y + dy, 1, 1, color)

                draw_x += font["widths"][char]
        
        else:
            # TODO: handle newlines, as the built-in routine doesn't support them
            graphics.DrawText(self.alt_buffer, font, x - align_offset, y, color, text)

    def width_of_text(self, text: str, font) -> int:
        """
        Returns the width of the specified string in a given font, such
        that if you were to print it, it would take up exactly that many
        pixels of horizontal space.

        This does not work on text with newlines.
        """
        # only works on text without newlines

        if(PYGAME_MODE):
            return sum(font["widths"][char] for char in text) - 1

        else:
            return sum(font.CharacterWidth(ord(char)) for char in text) - 1

    def clear(self):
        """
        Clears the entire screen to black.
        """
        
        if(PYGAME_MODE):
            self.screen.fill("black")
        else:
            self.alt_buffer.Clear()


    # --- I/O --- #
    def detect_keypresses(self):
        """
        Detects and updates all currently held down keys. This is
        automatically called every time the screen updates.
        """
        if(PYGAME_MODE):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.aborted = True
            pygame.event.pump()

            keys = pygame.key.get_pressed()
            self.keys_down_last = [v for v in self.keys_down]
            self.keys_down = [
                True if keys[code] else False
                for code in [
                    pygame.K_KP7,         # 0
                    pygame.K_KP8,         # 1
                    pygame.K_KP9,         # 2
                    pygame.K_KP_DIVIDE,   # 3
                    pygame.K_KP4,         # 4
                    pygame.K_KP5,         # 5
                    pygame.K_KP6,         # 6
                    pygame.K_KP_MULTIPLY, # 7
                    pygame.K_KP1,         # 8
                    pygame.K_KP2,         # 9
                    pygame.K_KP3,         # A
                    pygame.K_KP_MINUS,    # B
                    pygame.K_KP_PERIOD,   # C
                    pygame.K_KP0,         # D
                    pygame.K_KP_ENTER,    # E
                    pygame.K_KP_PLUS,     # F
                ]
            ]
        else:
            self.keys_down_last = [v for v in self.keys_down]
            self.keys_down = []
            # TODO: Actually test this
            for row_pin in constants.RPI_KEYPAD_ROWS:
                GPIO.output(row_pin, GPIO.HIGH)
                for col_pin in constants.RPI_KEYPAD_COLS:
                    self.keys_down.append(True if GPIO.input(col_pin) == 1 else False)
                GPIO.output(row_pin, GPIO.LOW)

            #raise NotImplementedError("TODO: Determine exactly how rpi GPIO works for the keypad")
        
    def key_just_pressed(self, id: int) -> bool:
        """
        For a given key ID, returns True if the key was just pressed this frame.
        """
        return self.keys_down[id] and not self.keys_down_last[id]
    
    def is_key_pressed(self, id: int) -> bool:
        """
        For a given key ID, returns True if the key is currently held down.
        """
        return self.keys_down[id]
    
    # Draws all the changes
    def flip(self):
        """
        Pushes the drawn screen to the display, and waits until the next frame (60 FPS).
        """
        if(PYGAME_MODE):
            pygame.display.flip()
            self.clock.tick(60)
        else:
            self.alt_buffer = self.matrix.SwapOnVSync(self.alt_buffer)

        self.detect_keypresses()
        self.clear()

# Colours, fonts, etc

Palette = {
    "red":     MatrixDraw.newColor(255,   0,   0),
    "orange":  MatrixDraw.newColor(255, 127,   0),
    "yellow":  MatrixDraw.newColor(255, 255,   0),
    "lime":    MatrixDraw.newColor(127, 255,   0),
    "green":   MatrixDraw.newColor(  0, 255,   0),
    "seafoam": MatrixDraw.newColor(  0, 255, 127),
    "cyan":    MatrixDraw.newColor(  0, 255, 255),
    "ocean":   MatrixDraw.newColor(  0, 127, 255),
    "blue":    MatrixDraw.newColor(  0,   0, 255),
    "purple":  MatrixDraw.newColor(127,   0, 255),
    "magenta": MatrixDraw.newColor(255,   0, 255),
    "pink":    MatrixDraw.newColor(255,   0, 127),

    "white":   MatrixDraw.newColor(255, 255, 255),
    "gray":    MatrixDraw.newColor(127, 127, 127),
    "dgray":   MatrixDraw.newColor( 64,  64,  64),
    "black":   MatrixDraw.newColor(  0,   0,   0),

    "dyellow": MatrixDraw.newColor( 80,  80,   0)
}

Fonts = {
    "tiny":  MatrixDraw.newFont("led/fonts/miniscule.bdf"),
    "small": MatrixDraw.newFont("led/fonts/tom-thumb.bdf"),
    "big":   MatrixDraw.newFont("led/fonts/5x8.bdf"),
    "bigc":  MatrixDraw.newFont("led/fonts/4x8.bdf")
}

if(__name__ == "__main__"):
    def wait():
        if(PYGAME_MODE):
            key_pressed = False
            while not key_pressed:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        key_pressed = True
                pygame.event.pump()
        
        else:
            input()

    # Graphical test suite
    artist = MatrixDraw()
    print("Graphical Test Suite v1")

    print("Color Test [press Enter to continue]")
    for y in range(HEIGHT_PIXELS):
        for x in range(WIDTH_PIXELS):
            u, v = x / (WIDTH_PIXELS-1), y / (HEIGHT_PIXELS-1)
            artist.setPixel(x, y, artist.newColor(int(u*255), int(v*255), 0))
    artist.flip()
    wait()

    print("Coordinates [press Enter to continue]")
    print("Red = (0, 0)")
    print("Green = (10, 0)")
    print("Blue = (0, 10)")
    print("Yellow = (10, 10)")
    print("White = (127, 31)")
    artist.setPixel(  0,  0, artist.newColor(255,   0,   0))
    artist.setPixel( 10,  0, artist.newColor(  0, 255,   0))
    artist.setPixel(  0, 10, artist.newColor(  0,   0, 255))
    artist.setPixel( 10, 10, artist.newColor(255, 255,   0))
    artist.setPixel(127, 31, artist.newColor(255, 255, 255))
    artist.flip()
    wait()

    print("Checkerboard [press Enter to continue]")
    for y in range(0, HEIGHT_PIXELS, 3):
        for x in range(0, WIDTH_PIXELS, 3):
            if(((x + y) // 3) % 2 == 0):
                artist.rect(x, y, 3, 3, artist.newColor(255, 255, 255))
    artist.flip()
    wait()

    print("Text Drawing [press Enter to continue]")
    font = artist.loadFont("led/fonts/tom-thumb.bdf")
    artist.print("#0,8 WHITE#", 0, 8, artist.newColor(255, 255, 255), font)
    artist.print("#64,16 RED#", 64, 16, artist.newColor(255, 0, 0), font)
    artist.print("#64,8 BLUE#", 64, 8, artist.newColor(0, 0, 255), font)
    artist.print("#0,16 GREEN#", 0, 16, artist.newColor(0, 255, 0), font)
    artist.flip()
    wait()
    
    print("Baseline Test [press Enter to continue]")
    font2 = artist.loadFont("led/fonts/5x8.bdf")
    artist.rect(0, 16, 128, 1, artist.newColor(128, 128, 128))
    artist.rect(0, 0, 1, 32, artist.newColor(128, 128, 128))
    artist.rect(64, 0, 1, 32, artist.newColor(128, 128, 128))
    artist.print("0, 16", 0, 16, artist.newColor(255, 255, 255), font)
    artist.print("64, 16", 64, 16, artist.newColor(255, 255, 255), font2)
    artist.flip()
    wait()