# Unified Team Layout datastructures

from enum import Enum
import json
import time

class DataFlavor(Enum):
    FRC = 0
    TBA = 1

# ------------------ SCORING ------------------ #


# ------------------ TEAMS AND ALLIANCES ------------------ #

class TeamColor(Enum):
    RED = 1
    BLUE = 2

class Team():
    team_number: int

    # General Info
    color:        TeamColor
    disqualified: bool
    station:      int
    surrogate:    bool


class Alliance():
    teams: list[Team]
    color: TeamColor

    def __init__(self):
        self.teams = [Team(), Team(), Team()]

    def inherit(self, data, data_flavor):
        if(data_flavor == DataFlavor.FRC):
            # TODO: this
            pass
        elif(data_flavor == DataFlavor.TBA):
            for team_n in range(3):
                # TODO: All the key matching and stuff
                self.teams[team_n].team_number = int(data["team_keys"][team_n][3:])
                pass
            

# ------------------ MATCH ------------------ #
    
class TournamentLevel(Enum):
    NONE = 1
    PRACTICE = 2
    QUALIFICATION = 3
    PLAYOFF = 4
    QUARTERFINAL = 5
    SEMIFINAL = 6
    FINAL = 7

class Match():
    planned_start_time:   time.struct_time
    predicted_start_time: time.struct_time
    actual_start_time:    time.struct_time
    result_posted_time:   time.struct_time

    tournament_level:  TournamentLevel
    set_number:        int
    match_number:      int
    played_number:     int

    field: str

    red_alliance:  Alliance
    blue_alliance: Alliance

    winning_alliance: TeamColor

    def __init__(self):
        self.red_alliance = Alliance()
        self.blue_alliance = Alliance()

    def __gt__(self, other):
        return self.planned_start_time > other.planned_start_time
    
    def __lt__ (self, other):
        return self.planned_start_time < other.planned_start_time
    
    def inherit(self, data, flavor: DataFlavor):
        if(flavor == DataFlavor.FRC):
            # TODO: Pretty sure this returns UTC, and it needs to be converted to local time.
            self.planned_start_time = time.strptime(str.split(data["startTime"], ".")[0], "%Y-%m-%dT%H:%M:%S")
            
            tournament_level = data["tournamentLevel"]
            if(tournament_level == "Practice"):
                self.tournament_level = TournamentLevel.PRACTICE
            elif(tournament_level == "Qualification"):
                self.tournament_level = TournamentLevel.QUALIFICATION
            elif(tournament_level == "Playoff"):
                self.tournament_level = TournamentLevel.PLAYOFF
            else:
                self.tournament_level = TournamentLevel.NONE

            self.played_number = data["matchNumber"]
            self.field = data["field"]

            for team in data["teams"]:
                # TODO: this
                pass
        
        elif(flavor == DataFlavor.TBA):
            self.planned_start_time = time.localtime(data["time"])
            self.actual_start_time = time.localtime(data["actual_time"])
            self.predicted_start_time = time.localtime(data["predicted_time"])
            self.result_posted_time = time.localtime(data["post_result_time"])

            tournament_level = data["comp_level"]
            if(tournament_level == "p"):
                self.tournament_level = TournamentLevel.PRACTICE
            elif(tournament_level == "qm"):
                self.tournament_level = TournamentLevel.QUALIFICATION
            elif(tournament_level == "qf"):
                self.tournament_level = TournamentLevel.QUARTERFINAL
            elif(tournament_level == "sf"):
                self.tournament_level = TournamentLevel.SEMIFINAL
            elif(tournament_level == "f"):
                self.tournament_level = TournamentLevel.FINAL
            else:
                self.tournament_level = TournamentLevel.NONE

            self.match_number = data["match_number"]
            self.set_number = data["set_number"]

            self.red_alliance.inherit(
                data["alliances"]["red"],
                DataFlavor.TBA
            )
            self.blue_alliance.inherit(
                data["alliances"]["blue"],
                DataFlavor.TBA
            )

            # TODO: score breakdown (?)
        
        return self
    
    def get_tournament_level_name(self, short = False):
        tournament_level_names = {
            TournamentLevel.NONE:          "M"  if short else "Match",
            TournamentLevel.PRACTICE:      "P"  if short else "Practice",
            TournamentLevel.QUALIFICATION: "Q"  if short else "Qualification",
            TournamentLevel.QUARTERFINAL:  "QF" if short else "Quarterfinal",
            TournamentLevel.SEMIFINAL:     "SF" if short else "Semifinal",
            TournamentLevel.FINAL:         "F"  if short else "Final"
        }

        if(self.tournament_level in tournament_level_names):
            return tournament_level_names[self.tournament_level]
        return "[invalid TL]"
        
    
    def get_match_name(self, short = False):
        if(self.set_number and self.tournament_level.value > TournamentLevel.QUALIFICATION.value):
            return f"{self.get_tournament_level_name(short)}{"" if short else " "}{self.set_number}-{self.match_number}"
        elif(self.match_number):
            return f"{self.get_tournament_level_name(short)}{"" if short else " "}{self.match_number}"
        else:
            return f"[invalid match]"
        

def get_matches(data, flavor: str):
    # TODO: Properly use inheritance
    if(flavor == "TBA"):
        # TBA flavor
        matches = [Match().inherit(match_json, DataFlavor.TBA) for match_json in data]
    elif(flavor == "FRC"):
        # FRC flavor
        matches = [Match().inherit(match_json, DataFlavor.FRC) for match_json in data["Schedule"]]
    else:
        raise ValueError(f"Illegal data flavor {flavor}")
    
    matches.sort()
    return matches
            