from led.draw_lib import MatrixDraw
import constants

class UserInterface():
    def __init__(self, draw: MatrixDraw, palette: dict, fonts: dict):
        self.draw = draw
        self.palette = palette
        self.fonts = fonts

    def MenuSelect(self, header: str, options: list[str]):
        # fade in animation
        for box_position in range(self.draw.height, 0, -2):
            self.draw.rect(0, box_position, self.draw.width, self.draw.height - box_position, self.palette["black"])
            self.draw.print(header, 1, box_position+3, self.palette["white"], self.fonts["small"])
            self.draw.flip()

        selected_option = 0
        while not self.draw.key_just_pressed(constants.BUTTON_SELECT):
            self.draw.print(header, 1, 5, self.palette["white"], self.fonts["small"])
            for i, option in enumerate(options):
                self.draw.print(("> " if i == selected_option else "  ") + option, 7, 12 + i * 6, self.palette["white"], self.fonts["small"])


            if(self.draw.key_just_pressed(constants.BUTTON_UP)):
                selected_option = (selected_option - 1) % len(options)
            if(self.draw.key_just_pressed(constants.BUTTON_DOWN)):
                selected_option = (selected_option + 1) % len(options)
            self.draw.flip()

        return selected_option
    
    def TextEntryPrimitive(self, prompt: str, charset: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890 "):
        # fade in animation
        for box_position in range(self.draw.height, 0, -2):
            self.draw.rect(0, box_position, self.draw.width, self.draw.height - box_position, self.palette["black"])
            self.draw.print(prompt, 1, box_position+3, self.palette["white"], self.fonts["small"])
            self.draw.flip()

        cursor_pos = 0
        typed = ""
        framecount = 0
        repeat_timer = 0

        SPACING = 4
        MAX_OFFSET = ((self.draw.width // SPACING) - 1) // 2
        CENTER = (self.draw.width - SPACING) // 2
        CHAR_COUNT = len(charset)

        while True:
            self.draw.print(prompt, 1, 5, self.palette["white"], self.fonts["small"])
            self.draw.print(typed + ("" if framecount <= 30 else "|"), 1, 13, self.palette["white"], self.fonts["small"])
            for offset in range(-MAX_OFFSET, MAX_OFFSET + 1):
                self.draw.print(
                    charset[(cursor_pos + offset) % CHAR_COUNT],
                    CENTER + offset * SPACING, 20,
                    self.palette["white"] if offset == 0 else self.palette["gray"],
                    self.fonts["small"]
                )
            self.draw.print("^", CENTER, 26, self.palette["white"], self.fonts["small"])
            self.draw.print("[2] INSERT   [8] DELETE   [5] OK", 1, 30, self.palette["white"], self.fonts["small"])
            

            cursor_direction = (-1 if self.draw.is_key_pressed(constants.BUTTON_LEFT) else 0) + (1 if self.draw.is_key_pressed(constants.BUTTON_RIGHT) else 0)
            if(cursor_direction != 0):
                repeat_timer += 1
                if(repeat_timer == 1 or repeat_timer >= 20):
                    cursor_pos = (cursor_pos + cursor_direction) % CHAR_COUNT
            else:
                repeat_timer = 0
            if(self.draw.key_just_pressed(constants.BUTTON_UP)):
                typed += charset[cursor_pos]
            if(self.draw.key_just_pressed(constants.BUTTON_DOWN)):
                typed = typed[:-1]
            if(self.draw.key_just_pressed(constants.BUTTON_SELECT)):
                return typed

            framecount = ((framecount + 1) % 60)
            self.draw.flip()

    def NumberEntry(self, prompt: str):
        # fade in animation
        for box_position in range(self.draw.height, 0, -2):
            self.draw.rect(0, box_position, self.draw.width, self.draw.height - box_position, self.palette["black"])
            self.draw.print(prompt, 1, box_position+3, self.palette["white"], self.fonts["small"])
            self.draw.flip()

        cursor_pos = 0
        typed = ""
        framecount = 0
        repeat_timer = 0

        KEYBOARD = [13, 8, 9, 10, 4, 5, 6, 0, 1, 2]

        while True:
            self.draw.print(prompt, 1, 5, self.palette["white"], self.fonts["small"])
            self.draw.print(typed + ("" if framecount <= 30 else "|"), 1, 16, self.palette["white"], self.fonts["small"])
            self.draw.print("    [#] DELETE        [A] OK    ", 1, 30, self.palette["white"], self.fonts["small"])
            
            for n, key in enumerate(KEYBOARD):
                if(self.draw.key_just_pressed(key)): typed += str(n)
            if(self.draw.key_just_pressed(14)):
                typed = typed[:-1]
            if(self.draw.key_just_pressed(3)):
                return typed

            framecount = ((framecount + 1) % 60)
            self.draw.flip()