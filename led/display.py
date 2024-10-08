#!/usr/bin/env python
import time
from led.draw_lib import MatrixDraw, Palette, Fonts
from led.ui import UserInterface
import data_process_2 as data_process
import constants

DEBUG_MODE = constants.DEBUG_MODE

def main(conn_recieve):
    draw = MatrixDraw()
    current_data = None

    selected_match = 0

    def debug_menu(draw: MatrixDraw):
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
        draw.rect(0, 0, 25, 10, Palette["blue"])
        draw.rect(0, 11, 26, 10, Palette["blue"])
        draw.rect(0, 22, 27, 10, Palette["blue"])
        
        draw.print(str(current_match.blue_alliance.teams[0].team_number), 1, 7, Palette["white"], Fonts["big"])
        draw.print(str(current_match.blue_alliance.teams[1].team_number), 2, 18, Palette["white"], Fonts["big"])
        draw.print(str(current_match.blue_alliance.teams[2].team_number), 3, 29, Palette["white"], Fonts["big"])
        

        draw.rect(103, 0, 25, 10, Palette["red"])
        draw.rect(102, 11, 26, 10, Palette["red"])
        draw.rect(101, 22, 27, 10, Palette["red"])

        draw.print(str(current_match.red_alliance.teams[0].team_number), 104, 7, Palette["white"], Fonts["big"])
        draw.print(str(current_match.red_alliance.teams[1].team_number), 103, 18, Palette["white"], Fonts["big"])
        draw.print(str(current_match.red_alliance.teams[2].team_number), 102, 29, Palette["white"], Fonts["big"])


        # time, match no, etc.
        draw.print(current_match.get_match_name(include_extra=False), 64, 12, Palette["white"], Fonts["small"], align="c")
        draw.print(current_match.get_match_number_extra(), 64, 18, Palette["white"], Fonts["tiny"], align="c")
        
        draw.print("EST.", 29, 28, Palette["gray"], Fonts["tiny"], align="l")
        draw.print(f"{(time.strftime('%I:%M', current_match.planned_start_time)).lower()}", 91, 29, Palette["white"], Fonts["big"], align="r")
        draw.print(f"{(time.strftime('%p', current_match.planned_start_time)).upper()}", 99, 29, Palette["white"], Fonts["tiny"], align="r")
        

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
                    draw.print("No data yet.", 64, 15, Palette["white"], Fonts["small"], align="c")
                    draw.print("Attempting request...", 64, 21, Palette["white"], Fonts["small"], align="c")
                    draw_main_area(draw, [])
                else:
                    draw_main_area(draw, current_data)

            
            draw.flip()
            if(draw.key_just_pressed(0)):
                debug_menu(draw)
        except Exception as e:
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