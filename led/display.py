#!/usr/bin/env python
import time
from led.draw_lib import MatrixDraw
import data_process_2 as data_process
import constants

DEBUG_MODE = constants.DEBUG_MODE

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

def main(conn_recieve):
    draw = MatrixDraw()
    current_data = None
    
    fonts = {
        "tiny":  draw.loadFont("led/fonts/miniscule.bdf"),
        "small": draw.loadFont("led/fonts/tom-thumb.bdf"),
        "big":   draw.loadFont("led/fonts/5x8.bdf")
    }

    palette = {
        "red":     draw.newColor(255,   0,   0),
        "orange":  draw.newColor(255, 127,   0),
        "yellow":  draw.newColor(255, 255,   0),
        "lime":    draw.newColor(127, 255,   0),
        "green":   draw.newColor(  0, 255,   0),
        "seafoam": draw.newColor(  0, 255, 127),
        "cyan":    draw.newColor(  0, 255, 255),
        "ocean":   draw.newColor(  0, 127, 255),
        "blue":    draw.newColor(  0,   0, 255),
        "purple":  draw.newColor(127,   0, 255),
        "magenta": draw.newColor(255,   0, 255),
        "pink":    draw.newColor(255,   0, 127),

        "white":   draw.newColor(255, 255, 255),
        "gray":    draw.newColor(127, 127, 127),
        "dgray":   draw.newColor( 64,  64,  64),
        "black":   draw.newColor(  0,   0,   0)
    }

    selected_match = 0

    def debug_menu(draw: MatrixDraw):
        ui = UserInterface(draw, palette, fonts)

        action = ui.MenuSelect(
            "What would you like to do?",
            [
                "Modify Data Request"
            ]
        )

        if(action == 0):
            modification = ui.MenuSelect(
                "Modify what?",
                [
                    "Team Number",
                    "Event",
                    "Change Source",
                    "(return)"
                ]
            )
            if(modification == 0):
                ui.NumberEntry("Enter new team #:")

    def draw_main_area(draw: MatrixDraw, matches: list[data_process.Match]):
        nonlocal selected_match
        if(draw.key_just_pressed(4)):
            selected_match -= 1
        if(draw.key_just_pressed(6)):
            selected_match += 1

        if(not 0 <= selected_match < len(matches)):
            return
        current_match = matches[selected_match]

        # team numbers
        draw.rect(0, 0, 25, 10, palette["blue"])
        draw.rect(0, 11, 26, 10, palette["blue"])
        draw.rect(0, 22, 27, 10, palette["blue"])
        
        draw.print(str(current_match.blue_alliance.teams[0].team_number), 1, 7, palette["white"], fonts["big"])
        draw.print(str(current_match.blue_alliance.teams[1].team_number), 2, 18, palette["white"], fonts["big"])
        draw.print(str(current_match.blue_alliance.teams[2].team_number), 3, 29, palette["white"], fonts["big"])
        

        draw.rect(103, 0, 25, 10, palette["red"])
        draw.rect(102, 11, 26, 10, palette["red"])
        draw.rect(101, 22, 27, 10, palette["red"])

        draw.print(str(current_match.red_alliance.teams[0].team_number), 104, 7, palette["white"], fonts["big"])
        draw.print(str(current_match.red_alliance.teams[1].team_number), 103, 18, palette["white"], fonts["big"])
        draw.print(str(current_match.red_alliance.teams[2].team_number), 102, 29, palette["white"], fonts["big"])


        # time, match no, etc.
        draw.print("MATCH", 28, 4, palette["gray"], fonts["tiny"])
        draw.print(current_match.get_match_name(short=True), 29, 12, palette["white"], fonts["big"])
        
        draw.print("EST. START", 99, 4, palette["gray"], fonts["tiny"], align="r")
        draw.print(f"{(time.strftime('%I:%M', current_match.planned_start_time)).lower()}", 90, 12, palette["white"], fonts["big"], align="r")
        draw.print(f"{(time.strftime('%p', current_match.planned_start_time)).upper()}", 98, 13, palette["white"], fonts["tiny"], align="r")
        

    while not draw.aborted:
        try:
            draw.clear()
            if(DEBUG_MODE):
                draw.print("Keys Down:", 0, 0, palette["white"], fonts["small"])
                key_str = ""
                for i, is_pressed in enumerate(draw.keys_down):
                    if(is_pressed): key_str += f"{i} "
                draw.print(key_str, 0, 9, palette["white"], fonts["small"])
                
            else:
                if(current_data == None):
                    draw.print("No data yet.", 64, 15, palette["white"], fonts["small"], align="c")
                    draw.print("Attempting request...", 64, 21, palette["white"], fonts["small"], align="c")
                    draw_main_area(draw, [])
                else:
                    draw_main_area(draw, current_data)

            
            draw.flip()
            if(draw.key_just_pressed(0)):
                debug_menu(draw)
        except Exception as e:
            while True:
                draw.clear()
                draw.print(f"ERROR", 1, 8, palette["red"], fonts["small"])

                traceback_msg = "\n".join([str(e)[i:i+32] for i in range(0, len(str(e)), 32)])
                current_tb = e.__traceback__
                while current_tb:
                    traceback_msg += f"\non line {current_tb.tb_lineno}"
                    current_tb = current_tb.tb_next
                
                draw.print(traceback_msg, 1, 16, palette["white"], fonts["small"])


                draw.flip()
        
        if(conn_recieve.poll()):
            current_data = conn_recieve.recv()

if __name__ == "__main__":
    main(None)