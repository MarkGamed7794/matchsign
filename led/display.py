#!/usr/bin/env python
import time, math
from led.draw_lib import MatrixDraw, Palette, Fonts
from led.ui import UserInterface
import data_process_2 as data_process
import constants

DEBUG_MODE = constants.DEBUG_MODE

def main(conn_recieve):
    draw: MatrixDraw = MatrixDraw()
    match_data: list[data_process.Match] = None
    current_data: dict = None

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

        if(match_data != None):

            scroll_adjusted = False
            # Select matches with left/right
            if(draw.key_just_pressed(4) and displayed_match > 0):
                displayed_match -= 1
                scroll_adjusted = True
            if(draw.key_just_pressed(6) and displayed_match < len(match_data) - 1):
                displayed_match += 1
                scroll_adjusted = True

            if(scroll_adjusted):
                # If a new match is selected and it's offscreen, scroll the list so that it is
                if(list_scroll > displayed_match):
                    list_scroll = displayed_match
                    list_scroll_frac = 0
                if(list_scroll + 3 < displayed_match):
                    list_scroll = displayed_match - 3
                    list_scroll_frac = 0

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
            if(list_scroll >= len(match_data) - 4 and list_scroll_frac > 0):
                list_scroll = len(match_data) - 4
                list_scroll_frac = 0
        

        if(draw.key_just_pressed(0)):
            debug_menu()

    def format_timediff(sec):
        hours = int(abs(sec)/3600) % 60
        minutes = int(abs(sec)/60) % 60
        seconds = int(abs(sec)) % 60
        if(abs(sec) > 3600):
            return f"{"-" if sec < 0 else ""}{hours}H{"0" if minutes < 10 else ""}{minutes}M"
        else: 
            return f"{"-" if sec < 0 else ""}{minutes}:{"0" if seconds < 10 else ""}{seconds}"
        
    # GRAPHICS #

    def draw_main_area():
        """
        Draw the main, upper panel.
        
        This includes the team numbers and detailed information about the currently selected match.
        """

        draw.rect(0, 0, 128, 32, Palette["black"])

        nonlocal displayed_match
        

        if(len(match_data) == 0):
            draw.print("Waiting for event to start...", 64, 30, Palette["white"], Fonts["small"], align="c")
            draw.print(f"as of {time.strftime("%I:%M %p", current_data['last_update'])} ({format_timediff(time.time() - time.mktime(current_data['last_update']))} ago)", 64, 38, Palette["gray"], Fonts["small"], align="c")
            return
        if(not 0 <= displayed_match < len(match_data)):
            return

        current_match = match_data[displayed_match]

        # team numbers
        for i, team in enumerate(current_match.red_alliance.teams):
            draw.rect(0, i * 11, 25 + i, 10, Palette["bgred"])
            col = Palette["yellow"] if (team.team_number == constants.TEAM_NUMBER) else Palette["white"]
            font = Fonts["big"] if team.team_number <= 9999 else Fonts["bigc"]
            draw.print(str(team.team_number), 24 + i, 7 + i * 11, col, font, align="r")
        
        for i, team in enumerate(current_match.blue_alliance.teams):
            draw.rect(103 - i, 11 * i, 25 + i, 10, Palette["bgblue"])
            col = Palette["yellow"] if (team.team_number == constants.TEAM_NUMBER) else Palette["white"]
            font = Fonts["big"] if team.team_number <= 9999 else Fonts["bigc"]
            draw.print(str(team.team_number), 104 - i, 7 + i * 11, col, font)


        # time, match no, etc.
        draw.print(current_match.get_match_name(include_extra=False), 64, 14, Palette["white"], Fonts["small"], align="c")
        draw.print(current_match.get_match_number_extra(), 64, 19, Palette["white"], Fonts["tiny"], align="c")
        
        est_time = current_match.planned_start_time
        est_label = "EST."
        if(current_match.status == "Queueing soon"):
            est_time = current_match.predicted_queue_time
            est_label = "QUEUE"
        elif(current_match.status == "Now queuing"):
            est_time = current_match.predicted_deck_time
            est_label = "ON DECK"
        elif(current_match.status == "On deck"):
            est_time = current_match.predicted_field_time
            est_label = "ON FIELD"
        elif(current_match.status == "On field"):
            est_time = current_match.predicted_start_time
            est_label = "START"

        status_timer = format_timediff(time.mktime(est_time) - time.time())
        
        draw.print(est_label, 29, 26, Palette["gray"], Fonts["tiny"], align="l")
        draw.print((time.strftime('%I:%M %p', est_time)).upper(), 29, 31, Palette["gray"], Fonts["tiny"], align="l")
        draw.print(status_timer, 99, 29, Palette["white"], Fonts["big"], align="r")

        # top banner
        banner_width = 30 # Distance from center to each side
        for y in range(7):
            draw.line(63 - banner_width + y, y, 65 + banner_width - y, y, Palette["dgray"])
        draw.print(current_match.status.upper(), 64, 5, Palette["white"], Fonts["small"], align="c")

    def draw_match_entry(match: data_process.Match, y: int, bg_color):
        draw.rect(0, y, draw.width, 7, bg_color)
        
        # Team positions

        for i, team in enumerate(match.red_alliance.teams):
            if(team.team_number == constants.TEAM_NUMBER): draw.rect(1 + i * 5, 1 + y, 5, 5, Palette["white"])
            draw.rect(2 + i * 5, 2 + y, 3, 3, Palette["red"])

        for i, team in enumerate(match.blue_alliance.teams):
            if(team.team_number == constants.TEAM_NUMBER): draw.rect(112 + i * 5, 1 + y, 5, 5, Palette["white"])
            draw.rect(113 + i * 5, 2 + y, 3, 3, Palette["blue"])

        # Match number
        draw.print(match.get_match_name(short=True), 18, y + 5, Palette["white"], Fonts["small"])

        # Time, if match is yet to be queued
        shown_time = match.status
        if(match.status == "Queuing soon"):
            shown_time = f"{(time.strftime('%I:%M %p', match.predicted_queue_time))}"

        draw.print(shown_time, 64, y + 5, Palette["white"], Fonts["small"], align='c')

    def draw_match_list():
        y_off = math.floor(list_scroll_frac * 7)
        for position, match in enumerate(match_data[list_scroll:list_scroll+5]):
            list_idx = position + list_scroll
            color = Palette["dgray"] if list_idx % 2 == 0 else Palette["black"] # default alternating list colour
            if(list_idx == displayed_match): color = Palette["dyellow"] # dark yellow if match is shown on upper half
            draw_match_entry(match, 34 - y_off + position * 7, color)

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
                    draw.print("Attempting request...", 64, 32, Palette["white"], Fonts["small"], align="c")
                else:
                    draw_match_list() # Draw this first so that it gets cut off by the main area
                    draw_main_area()

            draw.flip()
            update()
            
        except Exception as e:
            print(str(e)) # just in case
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
            match_data = current_data["matches"]

if __name__ == "__main__":
    main(None)