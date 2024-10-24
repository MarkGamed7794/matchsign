# hacked-together drawing library for the led matrices

if __name__ == "__main__":
    import os, sys, inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0, parentdir)

import constants

PYGAME_MODE = True
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
            GPIO.setmode(GPIO.BCM)
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
        if(PYGAME_MODE):
            return pygame.Color(r, g, b)
        else:
            return graphics.Color(r, g, b)
    
    @staticmethod
    def newFont(filepath):
        if(PYGAME_MODE):
            return bdf_reader.read_font(filepath)
        else:
            font = graphics.Font()
            font.LoadFont(filepath)
            return font

    def rect(self, x, y, w, h, col):
        if(PYGAME_MODE):
            if(self.scissor != None):
                x1, y1 = max(x, self.scissor[0]), max(y, self.scissor[1])
                pygame.draw.rect(self.screen, col, pygame.Rect(
                    x1 * 8,
                    y1 * 8,
                    (min(x + w, self.scissor[2] + 1) - x1) * 8,
                    (min(y + h, self.scissor[3] + 1) - y1) * 8
                ))
            else:
                pygame.draw.rect(self.screen, col, pygame.Rect(x * 8, y * 8, w * 8, h * 8))
        
        else:
            r, g, b = col.red, col.green, col.blue
            for y in range(y, y+h):
                for x in range(x, x+w):
                    self.alt_buffer.SetPixel(x, y, r, g, b)

    def setPixel(self, x, y, col):
        if(self.scissor != None):
            # Don't do anything if the pixel falls outside the scissor region
            if(not (self.scissor[0] <= x <= self.scissor[2] and self.scissor[1] <= y <= self.scissor[3])):
                return
        

        if(PYGAME_MODE):
            self.rect(x, y, 1, 1, col)
        else:
            self.alt_buffer.SetPixel(x, y, col.red, col.green, col.blue)

    def setScissor(self, left, top, right, bottom):
        self.scissor = (left, top, right, bottom)

    def disableScissor(self):
        self.scissor = None

    def print(self, text, x, y, col, font, align = "l"):
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
                            self.rect(draw_x + dx, draw_y + dy, 1, 1, col)

                draw_x += font["widths"][char]
        
        else:
            # TODO: handle newlines, as the built-in routine doesn't support them
            graphics.DrawText(self.alt_buffer, font, x - align_offset, y, col, text)

    def width_of_text(self, text, font):
        # only works on text without newlines

        if(PYGAME_MODE):
            return sum(font["widths"][char] for char in text) - 1

        else:
            return sum(font.CharacterWidth(char) for char in text) - 1

    def clear(self):
        if(PYGAME_MODE):
            self.screen.fill("black")
        else:
            self.alt_buffer.Clear()


    # --- I/O --- #
    def detect_keypresses(self):
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
                    pygame.K_KP7,
                    pygame.K_KP8,
                    pygame.K_KP9,
                    pygame.K_KP_DIVIDE,
                    pygame.K_KP4,
                    pygame.K_KP5,
                    pygame.K_KP6,
                    pygame.K_KP_MULTIPLY,
                    pygame.K_KP1,
                    pygame.K_KP2,
                    pygame.K_KP3,
                    pygame.K_KP_MINUS,
                    pygame.K_KP_PERIOD,
                    pygame.K_KP0,
                    pygame.K_KP_ENTER,
                    pygame.K_KP_PLUS,
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
        
    def key_just_pressed(self, id: int):
        return self.keys_down[id] and not self.keys_down_last[id]
    
    def is_key_pressed(self, id: int):
        return self.keys_down[id]
    
    # Draws all the changes
    def flip(self):
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
    "big":   MatrixDraw.newFont("led/fonts/5x8.bdf")
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