#!/usr/bin/env python
import time, math
from led.draw_lib import MatrixDraw, Palette, Fonts
from led.ui import UserInterface
import data_process_2 as data_process
from data_request import Action
import constants

DEBUG_MODE = constants.DEBUG_MODE
def main(request_pipe):
    draw: MatrixDraw = MatrixDraw()
    ui: UserInterface = UserInterface(draw, Palette, Fonts)
    match_data: list[data_process.Match] = None
    current_data: dict = None

    displayed_match: int = 0

    # These are seperate variables solely for convenience; the latter is really only for visuals.
    list_scroll: int = 0 # The amount of full entries scrolled down.
    list_scroll_frac: float = 0 # Between 0 and 1, represents how much of the way the list is to being scrolled to the next entry.

    # Filtering and its respective popup.
    filter_popup_text: str = ""
    filter_popup_timer: int = 0

    filter_mode: int = 0 # Which filtering mode to use.
    # 0: Show all matches
    # 1: Show all matches that haven't happened yet
    # 2: Show all matching in which the current team is playing
    # 3: Show all matches that haven't happened yet in which the current team is playing

    def initial_setup():
        while True:
            selection = ui.MenuSelect("Use cache or live data?", ["Cache", "Live Data"], help=True)

            if(selection == -1):
                ui.Notification("Match Sign\nprogrammed by Mark M\nSee ~/README.txt for details")
            if(selection == 0):
                request_pipe.send(Action.USE_CACHE)
                return
            if(selection == 1): break
        
        sources = ["FRC", "TBA", "NEXUS"]
        source_str = '+'.join([source for source in sources if constants.USE_SOURCE[source]])
        if(ui.MenuSelect("Use which sources?", [f"Default ({source_str})", "Custom"]) == 1):
            source_states = ui.CheckboxSelect("Pick sources to use:", sources, [constants.USE_SOURCE[source] for source in sources])

            use_source = {}
            use_source["FRC"] = source_states[0]
            use_source["TBA"] = source_states[1]
            use_source["NEXUS"] = source_states[2]

            request_pipe.send(Action.SEND_USED_SOURCES)
            request_pipe.send(use_source)
        
        # Attempt to grab list of event keys from The Blue Alliance
        team_key = constants.REQUEST_PARAMS["team_key_tba"]
        request_pipe.send(Action.SEND_EVENT_LIST)
        event_list = ui.WaitForRecieve("Fetching events", request_pipe)
        
        selected_key = ui.MenuSelect(f"Use which event key?", ["[Enter manually...]"] + event_list)
        if(selected_key == 0):
            event_key = ui.TextEntry("Enter new event key:")
        else:
            event_key = event_list[selected_key - 1]
        
        request_pipe.send(Action.BEGIN_REQUESTS)
        request_pipe.send(event_key)

    def debug_menu():
        action = ui.MenuSelect(
            "What would you like to do?",
            [
                "Modify Data Request",
                "Modify Display Settings"
            ]
        )

        if(action == 0):
            modification = ui.MenuSelect(
                "Modify what?",
                [
                    "Team Number",
                    "Request Interval",
                    "Restart Setup",
                    "(return)"
                ]
            )
            if(modification == 0):
                entered = ui.NumberEntry("Enter new team #:")
                if(entered <= 0 or entered == None):
                    ui.Notification("Illegal team number.")
                else:
                    constants.TEAM_NUMBER = entered

            elif(modification == 1):
                interval = ui.NumberChange("How many seconds between\neach request?", 10, 600, 10, constants.REQUEST_TIMEOUT)
                request_pipe.send(Action.CHANGE_TIMEOUT)
                request_pipe.send(interval)
            
            elif(modification == 2):
                request_pipe.send(Action.RESTART)
                nonlocal current_data, match_data
                current_data, match_data = None, None
                ui.WaitForRecieve("Halting requests", request_pipe)
                initial_setup()

        elif(action == 1):

            modification = ui.MenuSelect(
                "Modify what?",
                [
                    "Panel Brightness"
                ]
            )

            if(modification == 0):
                draw.setBrightness(ui.NumberChange("Set new brightness:", initial_value=draw.getBrightness()))

    def update():
        nonlocal displayed_match, list_scroll, list_scroll_frac

        if(match_data != None):

            scroll_adjusted = False
            # Select matches with left/right
            if(draw.key_just_pressed(constants.BUTTON_LEFT) and displayed_match > 0):
                displayed_match -= 1
                scroll_adjusted = True
            if(draw.key_just_pressed(constants.BUTTON_RIGHT) and displayed_match < len(match_data) - 1):
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
            if(draw.keys_down[constants.BUTTON_DOWN]):
                list_scroll_frac += 1/10
            if(draw.keys_down[constants.BUTTON_UP]):
                list_scroll_frac -= 1/10

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

            # Use 1 to cycle through filters
            nonlocal filter_mode, filter_popup_timer, filter_popup_text
            if(draw.key_just_pressed(1)):
                filter_mode = (filter_mode + 1) % 4
                displayed_match = 0
                list_scroll = 0
                list_scroll_frac = 0
                match filter_mode:
                    case 0:
                        filter_popup_text = "Showing all matches"
                    case 1:
                        filter_popup_text = "Showing future matches"
                    case 2:
                        filter_popup_text = f"Showing {constants.TEAM_NUMBER}'s matches"
                    case 3:
                        filter_popup_text = f"Showing {constants.TEAM_NUMBER}'s future matches"
                filter_popup_timer = 120
        

        if(draw.key_just_pressed(0)):
            debug_menu()

    def format_timediff(sec):
        hours = int(abs(sec)/3600)
        minutes = int(abs(sec)/60) % 60
        seconds = int(abs(sec)) % 60
        if(abs(sec) > 3600):
            return f"{'-' if sec < 0 else ''}{hours}H{'0' if minutes < 10 else ''}{minutes}M"
        else: 
            return f"{'-' if sec < 0 else ''}{minutes}:{'0' if seconds < 10 else ''}{seconds}"
        
    def draw_filter_popup():
        # filter popup
        nonlocal filter_popup_timer
        if(filter_popup_timer > 0):
            y = min(filter_popup_timer, 8) - 8
            draw.rect(0, y, 128, 8, Palette["black"])
            draw.print(filter_popup_text, 1, y + 5, Palette["white"], Fonts["small"])
            filter_popup_timer -= 1
    
    # GRAPHICS #

    def draw_main_area():
        """
        Draw the main, upper panel.
        
        This includes the team numbers and detailed information about the currently selected match.
        """

        draw.rect(0, 0, 128, 34, Palette["black"])

        nonlocal displayed_match

        if(len(match_data) == 0):
            draw.print("No matches found!", 64, 22, Palette["white"], Fonts["small"], align="c")
            draw.print(f"Either the event has not started", 64, 34, Palette["gray"], Fonts["small"], align="c")
            draw.print(f"or nothing matches your filter.", 64, 41, Palette["gray"], Fonts["small"], align="c")
            
            draw_filter_popup()
            return
        if(not 0 <= displayed_match < len(match_data)):
            return

        current_match = match_data[displayed_match]

        # team numbers
        if(current_match.red_alliance.is_unknown):
            for i in range(3):
                draw.rect(0, i * 11, 25 + i, 10, Palette["dgray"])
                draw.print("----", 24 + i, 7 + i * 11, Palette["gray"], Fonts["big"], align="r")
        else:
            for i, team in enumerate(current_match.red_alliance.teams):
                if(team.is_unknown):
                    draw.rect(0, i * 11, 25 + i, 10, Palette["dgray"])
                    draw.print("----", 24 + i, 7 + i * 11, Palette["gray"], Fonts["big"], align="r")
                else:
                    draw.rect(0, i * 11, 25 + i, 10, Palette["bgred"])
                    col = Palette["yellow"] if (team.team_number == constants.TEAM_NUMBER) else Palette["white"]
                    font = Fonts["big"] if team.team_number <= 9999 else Fonts["bigc"]
                    draw.print(str(team.team_number), 24 + i, 7 + i * 11, col, font, align="r")
        
        if(current_match.blue_alliance.is_unknown):
            for i in range(3):
                draw.rect(103 - i, 11 * i, 25 + i, 10, Palette["dgray"])
                draw.print("----", 104 - i, 7 + i * 11, Palette["gray"], Fonts["big"])
        else:
            for i, team in enumerate(current_match.blue_alliance.teams):
                if(team.is_unknown):
                    draw.rect(103 - i, 11 * i, 25 + i, 10, Palette["dgray"])
                    draw.print("----", 104 - i, 7 + i * 11, Palette["gray"], Fonts["big"])
                else:
                    draw.rect(103 - i, 11 * i, 25 + i, 10, Palette["bgblue"])
                    col = Palette["yellow"] if (team.team_number == constants.TEAM_NUMBER) else Palette["white"]
                    font = Fonts["big"] if team.team_number <= 9999 else Fonts["bigc"]
                    draw.print(str(team.team_number), 104 - i, 7 + i * 11, col, font)


        # time, match no, etc.
        draw.print(current_match.get_match_name(include_extra=False), 64, 14, Palette["white"], Fonts["small"], align="c")
        draw.print(current_match.get_match_number_extra(), 64, 19, Palette["white"], Fonts["tiny"], align="c")
        
        status = current_match.get_status()
        if(status not in ["Playing", "Finished"]):
            est_time = current_match.planned_start_time
            est_label = "EST."
            if(status == "Queuing soon"):
                est_time = current_match.predicted_queue_time
                est_label = "QUEUES"
            elif(status == "Now queuing"):
                est_time = current_match.predicted_deck_time
                est_label = "ON DECK"
            elif(status == "On deck"):
                est_time = current_match.predicted_field_time
                est_label = "ON FIELD"
            elif(status == "On field"):
                est_time = current_match.predicted_start_time
                est_label = "STARTS"

            if(est_time != None):
                seconds_left = max(time.mktime(est_time) - time.time(), 0)
                status_timer = format_timediff(seconds_left)

                color = Palette["white"]
                if(status == "Queuing soon"):
                    # Alert if we need to queue
                    if(seconds_left < constants.TIMER_FLASH):
                        if(seconds_left % 1 < 0.5): color = Palette["red"]
                    elif(seconds_left < constants.TIMER_WARN):
                        color = Palette["yellow"]
                
                draw.print(est_label, 30, 27, Palette["gray"], Fonts["tiny"], align="l")
                draw.print((time.strftime('%I:%M %p', est_time)).upper(), 30, 32, Palette["gray"], Fonts["tiny"], align="l")
                draw.print(status_timer, 98, 30, color, Fonts["big"], align="r")
        else:
            draw.print("STARTED", 30, 29, Palette["gray"], Fonts["tiny"], align="l")
            if(current_match.predicted_start_time != None):
                draw.print(time.strftime('%I:%M', current_match.predicted_start_time), 90, 30, Palette["white"], Fonts["big"], align="r")
                draw.print(time.strftime('%p', current_match.predicted_start_time), 98, 30, Palette["gray"], Fonts["tiny"], align="r")
            

        # top banner
        banner_width = 30 # Distance from center to each side
        banner_col = Palette["dgray"]
        if(current_match.winning_alliance == data_process.TeamColor.RED):
            banner_col = Palette["bgred"]
            banner_width += 5
        if(current_match.winning_alliance == data_process.TeamColor.BLUE):
            banner_col = Palette["bgblue"]
            banner_width += 5
        
        for y in range(7):
            draw.line(63 - banner_width + y, y, 65 + banner_width - y, y, banner_col)

        if(current_match.winning_alliance != None):
            draw.print(current_match.get_final_result(long=True), 64, 5, Palette["white"], Fonts["small"], align="c")
        else:
            draw.print(current_match.get_status().upper(), 64, 5, Palette["white"], Fonts["small"], align="c")

        draw_filter_popup()

    def draw_match_entry(match: data_process.Match, y: int, bg_color):
        draw.rect(0, y, draw.width, 7, bg_color)
        
        # Team positions
        if(match.red_alliance.is_unknown):
            for i in range(3):
                draw.rect(2 + i * 5, 2 + y, 3, 3, Palette["gray"])
        else:
            for i, team in enumerate(match.red_alliance.teams):
                if(team.team_number == constants.TEAM_NUMBER): draw.rect(1 + i * 5, 1 + y, 5, 5, Palette["white"])
                draw.rect(2 + i * 5, 2 + y, 3, 3, Palette["red"])

        if(match.blue_alliance.is_unknown):
            for i in range(3):
                draw.rect(113 + i * 5, 2 + y, 3, 3, Palette["gray"])
        else:
            for i, team in enumerate(match.blue_alliance.teams):
                if(team.team_number == constants.TEAM_NUMBER): draw.rect(112 + i * 5, 1 + y, 5, 5, Palette["white"])
                draw.rect(113 + i * 5, 2 + y, 3, 3, Palette["blue"])

        # Match number
        draw.print(match.get_match_name(short=True), 18, y + 5, Palette["white"], Fonts["small"])

        # Time, if match is yet to be queued
        shown_time = match.get_status() or "MATCH"
        if(match.get_status() == "Queuing soon"):
            if(match.predicted_queue_time != None):
                shown_time = f"{(time.strftime('%I:%M %p', match.predicted_queue_time))}"
            else:
                shown_time = "Queuing soon"
        if(match.winning_alliance != None):
            shown_time = match.get_final_result()

        draw.print(shown_time, 64, y + 5, Palette["white"], Fonts["small"], align='c')

    def draw_match_list():
        y_off = math.floor(list_scroll_frac * 7)
        for position, match in enumerate(match_data[list_scroll:list_scroll+5]):
            list_idx = position + list_scroll
            
            state = "waiting"
            if(match.winning_alliance != None):
                if(match.winning_alliance == data_process.TeamColor.RED): state = "red_win"
                if(match.winning_alliance == data_process.TeamColor.BLUE): state = "blue_win"
                if(match.winning_alliance == data_process.TeamColor.TIE): state = "finished"
            elif(match.get_status() == "Finished"):
                state = "finished"
            elif(match.get_status() != "Queuing soon"):
                state = "queueing"

            if(list_idx == displayed_match): state = "selected"
            draw_match_entry(match, 34 - y_off + position * 7, Palette[state][(list_idx + 1) % 2])

    initial_setup()
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
                    current_data = ui.WaitForRecieve("Attempting request", request_pipe)
                else:
                    match_data = [match for match in current_data if match.matches_filter(filter_mode)]
                    
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
        
        if(request_pipe.poll()):
            current_data = request_pipe.recv()

if __name__ == "__main__":
    main(None)