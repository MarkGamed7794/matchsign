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

    def WaitForRecieve(self, message, pipe):
        leftx = (self.draw.width - self.draw.width_of_text(message + "...", self.fonts["small"])) // 2
        y = (self.draw.height - 6) // 2
        dotsx = leftx + self.draw.width_of_text(message, self.fonts["small"]) + 2
        timer = 0
        while(not pipe.poll()):
            self.draw.print(message, leftx, y, self.palette["white"], self.fonts["small"])
            self.draw.print("".join([" " if (timer // 10) == i else "." for i in range(3)]), dotsx, y, self.palette["white"], self.fonts["small"])
            self.draw.flip()
            timer = (timer + 1) % 30
        return pipe.recv()


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
                selected = (i == selected_option)
                self.draw.print(("> " if selected else "  ") + option, 7, 12 + i * 6, self.palette["yellow" if selected else "white"], self.fonts["small"])


            if(self.draw.key_just_pressed(constants.BUTTON_UP)):
                selected_option = (selected_option - 1) % len(options)
            if(self.draw.key_just_pressed(constants.BUTTON_DOWN)):
                selected_option = (selected_option + 1) % len(options)
            self.draw.flip()

        return selected_option
    
    def CheckboxSelect(self, header: str, options: list[str], initial_states: list[bool]):
        self.FadeIn(header)

        states = list(initial_states) # copy
        selected_option = 0
        while True:
            self.draw.print(header, 1, 5, self.palette["white"], self.fonts["small"])
            for i, option in enumerate(options):
                selected = (i == selected_option)
                self.draw.print(f"{'>' if selected else ' '} {'[O]' if states[i] else '[ ]'} {option}", 7, 12 + i * 6, self.palette["yellow" if selected else "white"], self.fonts["small"])
            
            selected = (selected_option == len(options))
            self.draw.print(f"{'>' if selected else ' '} Confirm", 7, 12 + len(options) * 6, self.palette["yellow" if selected else "white"], self.fonts["small"])

            if(self.draw.key_just_pressed(constants.BUTTON_UP)):
                selected_option = (selected_option - 1) % (len(options) + 1)
            if(self.draw.key_just_pressed(constants.BUTTON_DOWN)):
                selected_option = (selected_option + 1) % (len(options) + 1)
            if(self.draw.key_just_pressed(constants.BUTTON_SELECT)):
                if(selected_option == len(options)):
                    return states
                else:
                    states[selected_option] = not states[selected_option]
            self.draw.flip()

    
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
            if(self.draw.key_just_pressed(constants.BUTTON_SELECT)):
                return typed

            framecount = ((framecount + 1) % 60)
            self.draw.flip()

    def TextEntry(self, prompt: str) -> str:
        self.FadeIn(prompt)

        keyboard = {
            False: [
                "1234567890-=",
                "qwertyuiop[]",
                "asdfghjkl;'`",
                "zxcvbnm,./\\"
            ],
            True: [
                "!@#$%^&*()_+",
                "QWERTYUIOP{}",
                "ASDFGHJKL:\"~",
                "ZXCVBNM<>?|"
            ]
        }

        shifted = False
        actions = ["BKSP", "SHIFT", "SPACE", "ENTER"]

        framecount = 0
        cursor = [0, 0]
        typed = ""

        while True:
            self.draw.print(prompt, 1, 5, self.palette["white"], self.fonts["small"])
            self.draw.print(typed + ("" if framecount <= 30 else "|"), 1, 13, self.palette["white"], self.fonts["small"])
            for y, row in enumerate(keyboard[shifted]):
                self.draw.print(
                    actions[y],
                    5, 32 + y * 7,
                    self.palette["yellow"] if [0, y] == cursor else self.palette["gray"],
                    self.fonts["small"]
                )
                for x, char in enumerate(row):
                    self.draw.print(
                        char,
                        27 + x * 8 + y * 2, 32 + y * 7,
                        self.palette["yellow"] if [x+1, y] == cursor else self.palette["gray"],
                        self.fonts["small"]
                    )
            
            if(self.draw.key_just_pressed(constants.BUTTON_LEFT)):   cursor[0] = max(cursor[0] - 1, 0)
            if(self.draw.key_just_pressed(constants.BUTTON_RIGHT)):  cursor[0] = min(cursor[0] + 1, len(keyboard[shifted][cursor[1]]))
            if(self.draw.key_just_pressed(constants.BUTTON_UP)):     cursor[1] = max(cursor[1] - 1, 0)
            if(self.draw.key_just_pressed(constants.BUTTON_DOWN)):
                cursor[1] = min(cursor[1] + 1, len(keyboard[shifted]) - 1)
                cursor[0] = max(cursor[0], len(keyboard[shifted][cursor[1]])) # Edge case for fourth row
            
            if(self.draw.key_just_pressed(constants.BUTTON_SELECT)):
                if(cursor[0] == 0):
                    if(cursor[1] == 0): # BKSP
                        typed = typed[:-1]
                    elif(cursor[1] == 1): # CAPS
                        shifted = not shifted
                    elif(cursor[1] == 2): # SPACE
                        typed += " "
                    elif(cursor[1] == 3): # ENTER
                        return typed
                else:
                    typed += keyboard[shifted][cursor[1]][cursor[0] - 1]

            framecount = ((framecount + 1) % 60)

            self.draw.print("  [ARROWS] MOVE     [A] SELECT  ", 1, 63, self.palette["white"], self.fonts["small"])
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
        
    def Notification(self, prompt: str) -> None:
        self.FadeIn(prompt)

        while True:
            self.draw.print("             [A] OK            ", 1, 63, self.palette["white"], self.fonts["small"])
            if(self.draw.key_just_pressed(constants.BUTTON_SELECT)):
                break
            self.draw.flip()

        return None