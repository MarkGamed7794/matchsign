import requests, base64, json, time, os
import data_process_2 as data_process
import constants
from enum import Enum

class Action(Enum):
    BEGIN_REQUESTS = 0
    USE_CACHE = 1
    SEND_EVENT_LIST = 2
    SEND_USED_SOURCES = 3

    RESTART = -9999

EVENT_KEY = constants.REQUEST_PARAMS["event_key"]

FRC_HEADERS = {
    "Authorization": "Basic " + base64.b64encode(constants.FRC_AUTH.encode("ascii")).decode("ascii")
}

TBA_LAST_ETAG_VALUE = None
TBA_HEADERS = {
    "X-TBA-Auth-Key": constants.TBA_AUTH
}
NEXUS_HEADERS = {
    "Nexus-Api-Key": constants.NEXUS_AUTH
}

FRC_REQUEST_PARAMS = {
    "tournament_level": constants.REQUEST_PARAMS["tournament_level"],
    "team_number": constants.REQUEST_PARAMS["team_number_frc"],
    "season": constants.CURRENT_SEASON,
    "event_code": constants.REQUEST_PARAMS["event_code_frc"]
}
TBA_REQUEST_PARAMS = {
    "team_key": constants.REQUEST_PARAMS["team_key_tba"]
}
NEXUS_REQUEST_PARAMS = {}

# Stores the full response text of each individual source, in case it returns Not Modified.
previous_responses = {
    "FRC": "",
    "TBA": "",
    "NEXUS": ""
}

used_sources = constants.USE_SOURCE

def make_request(source: str):
    global TBA_LAST_ETAG_VALUE
    # FRC path: https://frc-api.firstinspires.org/v3.0/{season}/schedule/{eventCode}?tournamentLevel={tournamentLevel}&teamNumber={teamNumber}&start={start}&end={end}
    # TBA path: https://www.thebluealliance.com/api/v3/event/{eventKey}/matches

    request_url = ""
    request_headers = None
    request_params = None

    if source == "FRC":
        request_url = f"https://frc-api.firstinspires.org/v3.0/{FRC_REQUEST_PARAMS['season']}/schedule/{FRC_REQUEST_PARAMS['event_code']}?teamNumber={FRC_REQUEST_PARAMS['team_number']}"
        request_headers = FRC_HEADERS
        request_params = FRC_REQUEST_PARAMS
    
    elif source == "TBA":
        if(TBA_LAST_ETAG_VALUE != ""): TBA_HEADERS["If-None-Match"] = TBA_LAST_ETAG_VALUE

        request_url = f"https://www.thebluealliance.com/api/v3/event/{EVENT_KEY}/matches"
        request_headers = TBA_HEADERS

    elif source == "NEXUS":
        request_url = f"https://frc.nexus/api/v1/event/{EVENT_KEY}"
        request_headers = NEXUS_HEADERS
        request_params = NEXUS_REQUEST_PARAMS

    print(f"[HTTP] Attempting to make request to {source}...")
    print("[HTTP] Request Headers:", request_headers)

    resp = requests.get(request_url, headers=request_headers, params=request_params)

    print("[HTTP] Status code:", resp.status_code)
    print("[HTTP] Response Headers:", resp.headers)
    if(constants.SHOW_RESPONSE_BODY):
        print("[HTTP] Response Body:")
        print(resp.text)
    else:
        print("[HTTP] Response Body:", f"({len(resp.text)} characters)")

    if(constants.SAVE_RESPONSE):
        with open(f"cache/{source}.txt", "w+") as file:
            file.write(resp.text)
        print("[HTTP] Data saved successfully to cache.")
    
    if source == "TBA":
        # Save TBA eTag value
        TBA_LAST_ETAG_VALUE = resp.headers["ETag"]

    return resp.text, resp.status_code

def attempt_request(source: str) -> tuple[str, int]:
    attempts = 0
    while attempts < constants.REQUEST_RETRY_LIMIT:
        try:
            data, code = make_request(source)
            print("[HTTP] Success!")

            if(code == 400):
                print("[HTTP] [ERROR] Request could not be read by servers. Ensure settings are formatted properly.")
                return "", 400

            elif(code == 304):
                print("[HTTP] Data was not modified since the last request. Using previously known data.")
                return previous_responses[source], 304

            elif(code == 200):
                # Save response for later
                previous_responses[source] = data
                return data, code

            raise RuntimeError(f"Unexpected HTTP code from request (code {code})")
        except requests.ConnectionError:
            print("[HTTP] [WARNING] Failed to connect. Ensure Wi-Fi link is stable.")

        attempts += 1
        print("[HTTP] Reattempting request in 5 seconds...")
        time.sleep(5)

    print(f"[HTTP] [CRITICAL]: Request failed {constants.REQUEST_RETRY_LIMIT} times in a row. Check connections and try again.")
    raise RuntimeError(f"Request failed {constants.REQUEST_RETRY_LIMIT} times in a row. Check connections and try again.")

LAST_TBA_DATA = "[]"

def main(display_pipe):
    # Wait until we recieve something from the pipe, which means the user selected what they want to happen.

    try:
        # Initial configuration
        global used_sources
        while True:
            command = display_pipe.recv()

            if(command == Action.SEND_EVENT_LIST):
                # Read in a team key, and send the list of current-year events
                print("[HTTP] Attempting to fetch event list from TBA...")
                resp = requests.get(f"https://www.thebluealliance.com/api/v3/team/{TBA_REQUEST_PARAMS['team_key']}/events/{constants.CURRENT_SEASON}", headers=TBA_HEADERS)
                print("[HTTP] Status code:", resp.status_code)
                print("[HTTP] Response Headers:", resp.headers)

                try:
                    events = json.loads(resp.text)
                    display_pipe.send([event["key"] for event in events])
                except json.JSONDecodeError as e:
                    print("[HTTP] Decoding error!", e.msg)
                    display_pipe.send([])
                
            elif(command == Action.USE_CACHE):
                # Use cache [final]
                print("[HTTP] Request module using cached data. No requests will be made.")
                used_sources = []
                with open("cache/used_sources.txt") as file:
                    used_sources = file.read().split(",")
                
                nexus_data, tba_data, frc_data = [], [], []

                if("NEXUS" in used_sources):
                    with open("cache/NEXUS.txt") as file: # NEXUS
                        nexus_data = data_process.get_matches(json.loads(file.read()), "NEXUS")
                    
                if("TBA" in used_sources):
                    with open("cache/TBA.txt") as file: # TBA
                        tba_data = data_process.get_matches(json.loads(file.read()), "TBA")

                if("FRC" in used_sources):
                    with open("cache/FRC.txt") as file: # FRC
                        tba_data = data_process.get_matches(json.loads(file.read()), "FRC")

                display_pipe.send(data_process.merge(frc_data, data_process.merge(tba_data, nexus_data)))
                while True:
                    time.sleep(3)
                    if(display_pipe.poll()):
                        if(display_pipe.recv() == Action.RESTART):
                            display_pipe.send(0) # Send a message to signal the setup process again
                            break

            elif(command == Action.SEND_USED_SOURCES):
                # Use a custom list of sources

                used_sources = display_pipe.recv()
            
            elif(command == Action.BEGIN_REQUESTS):
                # Read a team key, and then use it [final]
                global EVENT_KEY
                event_key = display_pipe.recv()
                if(isinstance(event_key, str)): EVENT_KEY = event_key

                if(constants.SAVE_RESPONSE):
                    source_list = []
                    for source in ["FRC", "TBA", "NEXUS"]:
                        if(used_sources[source]):
                            source_list.append(source)

                    with open("cache/used_sources.txt", "w+") as file:
                        file.write(",".join(source_list))

                while True:
                    print("[HTTP] Attempting request(s)...")

                    cumulative_data = []

                    for source in ["FRC", "TBA", "NEXUS"]:
                        if(used_sources[source]):
                            body, code = attempt_request(source)
                            if(code == 200 or code == 304):
                                provided_data = data_process.get_matches(json.loads(body), source)
                                cumulative_data = data_process.merge(cumulative_data, provided_data)
                        
                    display_pipe.send(cumulative_data)

                    print(f"[HTTP] Waiting {constants.REQUEST_TIMEOUT} seconds until next request batch...")
                    start = time.monotonic()
                    while(start + constants.REQUEST_TIMEOUT > time.monotonic()):
                        # Wait for however much time is left, but a maximum of 2 seconds
                        time.sleep(max(0, min((start + constants.REQUEST_TIMEOUT) - time.monotonic(), 2)))
                        if(display_pipe.poll()):
                            if(display_pipe.recv() == Action.RESTART):
                                display_pipe.send(0) # Send a message to signal the setup process again
                                break
        
    except BaseException as excpt:
        print("[HTTP] [CRITICAL] Request failed! Ensure Wi-Fi link is stable.")
        print("[HTTP] [CRITICAL] Exception details:", excpt)
        raise excpt

if __name__ == "__main__":
    attempt_request()