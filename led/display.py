#!/usr/bin/env python
import time, math
from led.draw_lib import MatrixDraw, Palette, Fonts
from led.ui import UserInterface
import data_process_2 as data_process
import constants

DEBUG_MODE = constants.DEBUG_MODE

def main(conn_recieve):
    draw: MatrixDraw = MatrixDraw()
    current_data: list[data_process.Match] = None

    displayed_match: int = 0

    # These are seperate variables solely for convenience; the latter is really only for visuals.
    list_scroll: int = 0 # The amount of full entries scrolled down.
    list_scroll_frac: float = 0 # Between 0 and 1, represents how much of the way the list is to being scrolled to the next entry.


    def debug_menu():
        ui = UserInterface(draw, Palette, Fonts)

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

    def update():
        nonlocal displayed_match, list_scroll, list_scroll_frac

        if(current_data != None):

            # Select matches with left/right
            if(draw.key_just_pressed(4)):
                displayed_match -= 1
            if(draw.key_just_pressed(6)):
                displayed_match += 1

            # Scroll list with up/down
            if(draw.keys_down[1]):
                list_scroll_frac -= 1/10
            if(draw.keys_down[9]):
                list_scroll_frac += 1/10

            # Clamp scroll between list boundaries
            if(not (0 <= list_scroll_frac < 1)):
                list_scroll += math.floor(list_scroll_frac)
                list_scroll_frac %= 1
            if(list_scroll < 0):
                list_scroll = 0
                list_scroll_frac = 0
            if(list_scroll >= len(current_data) - 4 and list_scroll_frac > 0):
                list_scroll = len(current_data) - 4
                list_scroll_frac = 0
        

        if(draw.key_just_pressed(0)):
            debug_menu()

    def draw_main_area():
        nonlocal displayed_match

        if(not 0 <= displayed_match < len(current_data)):
            return
        current_match = current_data[displayed_match]

        # team numbers
        for i, team in enumerate(current_match.red_alliance.teams):
            draw.rect(0, i * 11, 25 + i, 10, Palette["red"])
            draw.print(str(team.team_number), 1 + i, 7 + i * 11, Palette["yellow"] if (team.team_number == constants.TEAM_NUMBER) else Palette["white"], Fonts["big"])
        
        for i, team in enumerate(current_match.blue_alliance.teams):
            draw.rect(103 - i, 11 * i, 25 + i, 10, Palette["blue"])
            draw.print(str(team.team_number), 104 - i, 7 + i * 11, Palette["yellow"] if (team.team_number == constants.TEAM_NUMBER) else Palette["white"], Fonts["big"])


        # time, match no, etc.
        draw.print(current_match.get_match_name(include_extra=False), 64, 12, Palette["white"], Fonts["small"], align="c")
        draw.print(current_match.get_match_number_extra(), 64, 18, Palette["white"], Fonts["tiny"], align="c")
        
        draw.print("EST.", 29, 28, Palette["gray"], Fonts["tiny"], align="l")
        draw.print(f"{(time.strftime('%I:%M', current_match.planned_start_time)).lower()}", 91, 29, Palette["white"], Fonts["big"], align="r")
        draw.print(f"{(time.strftime('%p', current_match.planned_start_time)).upper()}", 99, 29, Palette["white"], Fonts["tiny"], align="r")

    def draw_match_entry(match: data_process.Match, y: int, bg_color):
        draw.rect(0, y, draw.width, y+7, bg_color)
        
        # Team positions

        for i, team in enumerate(match.red_alliance.teams):
            if(team.team_number == constants.TEAM_NUMBER): draw.rect(1 + i * 5, 1 + y, 5, 5, Palette["white"])
            draw.rect(2 + i * 5, 2 + y, 3, 3, Palette["red"])

        for i, team in enumerate(match.blue_alliance.teams):
            if(team.team_number == constants.TEAM_NUMBER): draw.rect(112 + i * 5, 1 + y, 5, 5, Palette["white"])
            draw.rect(113 + i * 5, 2 + y, 3, 3, Palette["blue"])

        # Alliance numbers, if present
        # TODO: Data doesn't seem to provide alliance numbers. Is this intentional?

        # Match number
        draw.print(match.get_match_name(short=True), 18, y + 5, Palette["white"], Fonts["small"])

        # Time, if match is yet to be played
        draw.print(f"{(time.strftime('%I:%M %p', match.planned_start_time))}", 64, y + 5, Palette["white"], Fonts["small"], align='c')

        

    def draw_match_list():
        y_off = math.floor(list_scroll_frac * 7)
        draw.setScissor(0, 34, 127, 63)
        for position, match in enumerate(current_data[list_scroll:list_scroll+5]):
            list_idx = position + list_scroll
            color = Palette["dgray"] if list_idx % 2 == 0 else Palette["black"] # default alternating list colour
            if(list_idx == displayed_match): color = Palette["dyellow"] # dark yellow if match is shown on upper half
            draw_match_entry(match, 34 - y_off + position * 7, color)
        draw.disableScissor()
        
        

    while not draw.aborted:
        try:
            draw.clear()
            if(DEBUG_MODE):
                draw.print("Keys Down:", 0, 0, Palette["white"], Fonts["small"])
                key_str = ""
                for i, is_pressed in enumerate(draw.keys_down):
                    if(is_pressed): key_str += f"{i} "
                draw.print(key_str, 0, 9, Palette["white"], Fonts["small"])
                
            else:
                if(current_data == None):
                    draw.print("No data yet.", 64, 47, Palette["white"], Fonts["small"], align="c")
                    draw.print("Attempting request...", 64, 53, Palette["white"], Fonts["small"], align="c")
                else:
                    draw_main_area()
                    draw_match_list()

            draw.flip()
            update()
            
        except Exception as e:
            draw.disableScissor()
            while True:
                draw.clear()
                draw.print(f"ERROR", 1, 8, Palette["red"], Fonts["small"])

                traceback_msg = "\n".join([str(e)[i:i+32] for i in range(0, len(str(e)), 32)])
                current_tb = e.__traceback__
                while current_tb:
                    traceback_msg += f"\non line {current_tb.tb_lineno}"
                    current_tb = current_tb.tb_next
                
                draw.print(traceback_msg, 1, 16, Palette["white"], Fonts["small"])
                draw.flip()
        
        if(conn_recieve.poll()):
            current_data = conn_recieve.recv()

if __name__ == "__main__":
    main(None)