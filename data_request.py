import requests, base64, json, time, os
import data_process_2 as data_process
import constants
from enum import Enum

class Action(Enum):
    BEGIN_REQUESTS = 0
    USE_CACHE = 1
    SEND_EVENT_LIST = 2

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

def make_request(source: str):
    # FRC path: https://frc-api.firstinspires.org/v3.0/{season}/schedule/{eventCode}?tournamentLevel={tournamentLevel}&teamNumber={teamNumber}&start={start}&end={end}
    # TBA path: https://www.thebluealliance.com/api/v3/event/{eventKey}/matches
    if source == "FRC":
        print("[HTTP] Attempting to make request to FRC servers...")
        print("[HTTP] Request Headers:", FRC_HEADERS)
        resp = requests.get(f"https://frc-api.firstinspires.org/v3.0/{FRC_REQUEST_PARAMS['season']}/schedule/{FRC_REQUEST_PARAMS['event_code']}?teamNumber={FRC_REQUEST_PARAMS['team_number']}", headers=FRC_HEADERS, params=FRC_REQUEST_PARAMS)
        print("[HTTP] Status code:", resp.status_code)
        print("[HTTP] Response Headers:", resp.headers)
        if(constants.SHOW_RESPONSE_BODY):
            print("[HTTP] Response Body:")
            print(resp.text)
        else:
            print("[HTTP] Response Body:", f"({len(resp.text)} characters)")

        try:
            if(constants.SAVE_RESPONSE):
                with open("request_output.txt", "w") as file:
                    file.write(resp.text)
                print("[HTTP] Data saved successfully to request_output.txt.")

            return data_process.get_matches(json.loads(resp.text), "FRC"), resp.status_code
        except json.decoder.JSONDecodeError as e:
            print(f"[HTTP] [ERROR] Error! Failed to decode JSON response, with error: {e}")
            print("[HTTP] Raw data:")
            print(resp.text)
            return None, resp.status_code

    elif source == "TBA":
        etag_value = ""
        if(os.path.isfile(constants.TBA_CACHE_FILEPATH)):
            with open(constants.TBA_CACHE_FILEPATH, "r") as cache:
                etag_value = cache.read()
        if(etag_value != ""): TBA_HEADERS["If-None-Match"] = etag_value

        print("[HTTP] Attempting to make request to TBA servers...")
        print("[HTTP] Request Headers:", TBA_HEADERS)
        resp = requests.get(f"https://www.thebluealliance.com/api/v3/event/{EVENT_KEY}/matches", headers=TBA_HEADERS)
        print("[HTTP] Status code:", resp.status_code)
        print("[HTTP] Response Headers:", resp.headers)
        if(constants.SHOW_RESPONSE_BODY):
            print("[HTTP] Response Body:")
            print(resp.text)
        else:
            print("[HTTP] Response Body:", f"({len(resp.text)} characters)")

        if(resp.status_code == 304): # Not Modified
            return None, resp.status_code

        with open(constants.TBA_CACHE_FILEPATH, "w") as cache:
            cache.write(resp.headers["ETag"])

        try:
            if(constants.SAVE_RESPONSE):
                with open("request_output_tba.txt" if constants.TBA_ADDITIONAL_DATA else "request_output.txt", "w") as file:
                    file.write(resp.text)
                print("[HTTP] Data saved successfully to request_output.txt.")

            return data_process.get_matches(json.loads(resp.text), "TBA"), resp.status_code
        except json.decoder.JSONDecodeError as e:
            print(f"[HTTP] [ERROR] Error! Failed to decode JSON response, with error: {e}")
            print("[HTTP] Raw data:")
            print(resp.text)
            return None, resp.status_code
        
    elif source == "NEXUS":

        print("[HTTP] Attempting to make request to Nexus servers...")
        print("[HTTP] Request Headers:", NEXUS_HEADERS)
        resp = requests.get(f"https://frc.nexus/api/v1/event/{EVENT_KEY}", headers=NEXUS_HEADERS, params=NEXUS_REQUEST_PARAMS)
        print("[HTTP] Status code:", resp.status_code)
        print("[HTTP] Response Headers:", resp.headers)
        if(constants.SHOW_RESPONSE_BODY):
            print("[HTTP] Response Body:")
            print(resp.text)
        else:
            print("[HTTP] Response Body:", f"({len(resp.text)} characters)")

        try:
            if(constants.SAVE_RESPONSE):
                with open("request_output.txt", "w") as file:
                    file.write(resp.text)
                print("[HTTP] Data saved successfully to request_output.txt.")

            return data_process.get_matches(json.loads(resp.text), "NEXUS"), resp.status_code
        except json.decoder.JSONDecodeError as e:
            print(f"[HTTP] [ERROR] Error! Failed to decode JSON response, with error: {e}")
            print("[HTTP] Raw data:")
            print(resp.text)
            return None, resp.status_code

    else:
        print(f"[HTTP] [CRITICAL] Illegal source {source}")

def attempt_request(source: str):    
    attempts = 0
    while attempts < constants.REQUEST_RETRY_LIMIT:
        try:
            result = make_request(source)
            print("[HTTP] Success!")
            return result
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
                if(constants.TBA_ADDITIONAL_DATA):
                    nexus_data, tba_data = [], []
                    with open("request_output.txt") as file: # NEXUS
                        nexus_data = data_process.get_matches(json.loads(file.read()), "NEXUS")
                    with open("request_output_tba.txt") as file: # TBA
                        tba_data = data_process.get_matches(json.loads(file.read()), "TBA")
                    display_pipe.send(data_process.merge(tba_data, nexus_data))
                    while True:
                        time.sleep(1000)
                else:
                    with open("request_output.txt") as file:
                        display_pipe.send(data_process.get_matches(json.loads(file.read()), "TBA"))
                    while True:
                        time.sleep(1000)
            elif(command == Action.BEGIN_REQUESTS):
                # Read a team key, and then use it [final]
                event_key = display_pipe.recv()
                if(isinstance(event_key, str)): EVENT_KEY = event_key
                break

        while True:
            print("[HTTP] Attempting request...")
            data, code = attempt_request(constants.REQUEST_SOURCE)
            print("[HTTP] Request successful.")

            if(code == 304): # Not Modified
                print("[HTTP] Data was not modified since the last request, and thus has not been sent to the display.")
            if(code == 400): # Bad Request
                print("[HTTP] [ERROR] Request could not be read by servers. Ensure settings are formatted properly.")
            elif(code == 200): # OK
                
                if(constants.TBA_ADDITIONAL_DATA):
                    print("[HTTP] Querying TBA for additional match results...")
                    tba_data, code = attempt_request("TBA")
                    if(code == 304): # Not Modified
                        print("[HTTP] Data was not modified since the last request.")
                        print("[HTTP] Attempting to merge data...")
                        data = data_process.merge(LAST_TBA_DATA, data)
                        print("[HTTP] Success!")
                    if(code == 400): # Bad Request
                        print("[HTTP] [ERROR] Request could not be read by servers. Ensure settings are formatted properly.")
                    elif(code == 200):
                        print("[HTTP] Successful! Attempting to merge data...")
                        data = data_process.merge(tba_data, data)
                        LAST_TBA_DATA = tba_data
                        print("[HTTP] Success!")
                else:
                    print("[HTTP] Request OK! Data sent to draw process.")
                
                display_pipe.send(data)



            print(f"[HTTP] Waiting {constants.REQUEST_TIMEOUT} seconds until next request...")
            time.sleep(constants.REQUEST_TIMEOUT)
        
    except BaseException as excpt:
        print("[HTTP] [CRITICAL] Request failed! Ensure Wi-Fi link is stable.")
        print("[HTTP] [CRITICAL] Exception details:", excpt)
        raise excpt

if __name__ == "__main__":
    attempt_request()