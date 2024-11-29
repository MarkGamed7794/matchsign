from led.draw_lib import MatrixDraw
import constants

class UserInterface():
    draw:    MatrixDraw
    palette: dict
    fonts:   dict

    def __init__(self, draw: MatrixDraw, palette: dict, fonts: dict):
        self.draw = draw
        self.palette = palette
        self.fonts = fonts

    def FadeIn(self, header: str = ""):
        # fade in animation
        for box_position in range(self.draw.height, 0, -2):
            self.draw.rect(0, box_position, self.draw.width, self.draw.height - box_position, self.palette["black"])
            self.draw.print(header, 1, box_position+3, self.palette["white"], self.fonts["small"])
            self.draw.flip()

    def NumberChange(self, header, min_val: int = 0, max_val: int = 100, step: int = 1, initial_value: int = 0):
        self.FadeIn(header)

        current_val = initial_value
        while not self.draw.key_just_pressed(constants.BUTTON_SELECT):
            self.draw.print(header, 1, 5, self.palette["white"], self.fonts["small"])
            self.draw.print("             [A] OK            ", 1, 63, self.palette["white"], self.fonts["small"])
            
            n_width = self.draw.width_of_text(str(current_val), self.fonts["big"])
            self.draw.print(str(current_val), 64, 36, self.palette["white"], self.fonts["big"], align="c")
            self.draw.print("<", 53 - n_width, 35, self.palette["white"], self.fonts["small"])
            self.draw.print(">", 72 + n_width, 35, self.palette["white"], self.fonts["small"])


            cursor_direction = (-1 if self.draw.is_key_pressed(constants.BUTTON_LEFT) else 0) + (1 if self.draw.is_key_pressed(constants.BUTTON_RIGHT) else 0)
            if(cursor_direction != 0):
                repeat_timer += 1
                if(repeat_timer == 1 or (repeat_timer >= 30 and repeat_timer % 2 == 0)):
                    current_val = max(min_val, min((current_val + cursor_direction * step), max_val))
            else:
                repeat_timer = 0
            
            self.draw.flip()
        
        return current_val

    def MenuSelect(self, header: str, options: list[str]) -> int:
        self.FadeIn(header)

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
    
    def TextEntryPrimitive(self, prompt: str, charset: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890 ") -> str:
        self.FadeIn(prompt)

        cursor_pos: int = 0
        typed: str = ""
        framecount: int = 0
        repeat_timer: int = 0

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
            self.draw.print("[^] INSERT   [v] DELETE   [A] OK", 1, 30, self.palette["white"], self.fonts["small"])
            

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
            if(self.draw.key_just_pressed(15)):
                return typed

            framecount = ((framecount + 1) % 60)
            self.draw.flip()

    def NumberEntry(self, prompt: str) -> int|None:
        self.FadeIn(prompt)

        typed: str = ""
        framecount: int = 0

        while True:
            self.draw.print(prompt, 1, 5, self.palette["white"], self.fonts["small"])
            self.draw.print(typed + ("" if framecount <= 30 else "|"), 1, 36, self.palette["white"], self.fonts["big"])
            self.draw.print("    [B] DELETE        [A] OK    ", 1, 63, self.palette["white"], self.fonts["small"])
            
            for key in range(10):
                if(self.draw.key_just_pressed(key)): typed += str(key)
            if(self.draw.key_just_pressed(constants.BUTTON_CANCEL)):
                typed = typed[:-1]
            if(self.draw.key_just_pressed(constants.BUTTON_SELECT)):
                break

            framecount = ((framecount + 1) % 60)
            self.draw.flip()

        try:
            return int(typed)
        except:
            return None