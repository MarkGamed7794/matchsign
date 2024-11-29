# Unified Team Layout datastructures

from enum import Enum
import time

class DataFlavor(Enum):
    FRC = 0
    TBA = 1
    NEXUS = 2

# ------------------ UTILITY ------------------ #

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

    def inherit(self, data: dict, data_flavor: DataFlavor):
        if(data_flavor == DataFlavor.FRC):
            # TODO: this
            pass
        elif(data_flavor == DataFlavor.TBA):
            for team_n in range(3):
                # TODO: All the key matching and stuff
                self.teams[team_n].team_number = int(data["team_keys"][team_n][3:])
        elif(data_flavor == DataFlavor.NEXUS):
            if(data == None): return
            for team_n in range(3):
                self.teams[team_n].team_number = int(data[team_n])
            

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
    # Nexus exclusive properties
    predicted_queue_time: time.struct_time
    predicted_deck_time:  time.struct_time
    predicted_field_time: time.struct_time
    status: str

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
    
    def inherit(self, data: dict, flavor: DataFlavor):
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
        elif(flavor == DataFlavor.NEXUS):
            # Nexus returns timestamps in milliseconds, not seconds
            self.predicted_queue_time = time.localtime(data["times"]["estimatedQueueTime"] / 1000)
            self.predicted_deck_time  = time.localtime(data["times"]["estimatedOnDeckTime"] / 1000)
            self.predicted_field_time = time.localtime(data["times"]["estimatedOnFieldTime"] / 1000)
            self.predicted_start_time = time.localtime(data["times"]["estimatedStartTime"] / 1000)
            self.planned_start_time = self.predicted_start_time
            self.status = data["status"]

            # Nexus only returns a human-readable match name. So...
            [match_level, match_number] = data["label"].split(" ")

            if(match_level == "Practice"):      self.tournament_level = TournamentLevel.PRACTICE
            if(match_level == "Qualification"): self.tournament_level = TournamentLevel.QUALIFICATION
            if(match_level == "Playoff"):       self.tournament_level = TournamentLevel.SEMIFINAL
            if(match_level == "Final"):         self.tournament_level = TournamentLevel.FINAL
            
            if(self.tournament_level == TournamentLevel.FINAL):
                self.set_number = 1
                self.match_number = int(match_number)
            elif(self.tournament_level == TournamentLevel.QUALIFICATION):
                self.match_number = int(match_number)
                self.set_number = 1
            else:
                self.match_number = int(match_number)
                if(data["label"].endswith("Replay") == "Replay"):
                    self.match_number = 2
                else:
                    self.match_number = 1

            self.red_alliance.inherit(data["redTeams"], DataFlavor.NEXUS)
            self.blue_alliance.inherit(data["blueTeams"], DataFlavor.NEXUS)
        
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
    
    def get_match_number_extra(self):
        if(self.set_number and self.match_number):
            if(self.tournament_level == TournamentLevel.QUALIFICATION):
                return ""
            elif(self.tournament_level.value < TournamentLevel.FINAL.value):
                if(self.match_number > 1):
                    return f"PLAY {self.match_number}"
                else:
                    return ""
            elif(self.tournament_level == TournamentLevel.FINAL):
                return f"ROUND {self.match_number}"
        
        return ""
    
    def get_match_name(self, short = False, include_extra = True):
        if(self.set_number and self.tournament_level.value > TournamentLevel.QUALIFICATION.value):
            out = f"{self.get_tournament_level_name(short)}{'' if short else ' '}{self.set_number}"
            if(include_extra and not (self.tournament_level.value < TournamentLevel.FINAL.value and self.match_number == 1)):
                out += f"-{self.match_number}"
            return out
        elif(self.match_number):
            return f"{self.get_tournament_level_name(short)}{'' if short else ' '}{self.match_number}"
        else:
            return f"[invalid match]"
        

def get_matches(data, flavor: str) -> dict:
    # TODO: Properly use inheritance
    if(flavor == "TBA"):
        # TBA flavor
        matches = [Match().inherit(match_json, DataFlavor.TBA) for match_json in data]
        matches.sort()
        return {
            "matches": matches
        }
    elif(flavor == "FRC"):
        # FRC flavor
        matches = [Match().inherit(match_json, DataFlavor.FRC) for match_json in data["Schedule"]]
        matches.sort()
        return {
            "matches": matches,
        }
    elif(flavor == "NEXUS"):
        matches = [Match().inherit(match_json, DataFlavor.NEXUS) for match_json in data["matches"]]
        matches.sort()
        return {
            "matches": matches,
            "announcements": [{"data": announcement["announcement"], "time": time.localtime(announcement["postedTime"])} for announcement in data["announcements"]],
            "last_update": time.localtime(data["dataAsOfTime"] / 1000)
        }
    else:
        raise ValueError(f"Illegal data flavor {flavor}")
            