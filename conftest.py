import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()


ENDPOINT = os.getenv('ENDPOINT')
SIMULATOR_ENDPOINT = os.getenv('SIMULATOR_ENDPOINT')

headers = {'accept': 'application/json, text/plain, */*'}
payload = {}
url_start_simulator = SIMULATOR_ENDPOINT + "/start"
url_stop_simulator = SIMULATOR_ENDPOINT + "/stop"
url_simulator = ENDPOINT + "/simulator/"
url_simulator_healthcheck = ENDPOINT + "/simulator/system/healthCheck"
MAX_RETRIES = 15


def pytest_sessionstart(session):
    if not hasattr(session.config, 'workerinput'):
        start_simulator_response = requests.request("GET", url_start_simulator, headers=headers, data=payload)
        assert start_simulator_response.status_code == 200, f"{start_simulator_response.text}"
        # wait for simulator to be activated
        for attempt in range(MAX_RETRIES):
            simulator_started_response = requests.get(url_simulator, headers=headers)
            if simulator_started_response.status_code != 200:
                time.sleep(15)
            else:
                simulator_healthcheck_response = requests.get(url_simulator_healthcheck, headers=headers)
                print(f"Simulator is started, healthcheck status code: {simulator_healthcheck_response.status_code}")
                break
        else:
            raise Exception(f"Error: Number of {MAX_RETRIES} is used. Simulator hasn't started yet")


def pytest_sessionfinish(session):
    if not hasattr(session.config, 'workerinput'):
        stop_simulator_response = requests.request("GET", url_stop_simulator, headers=headers, data=payload)
        assert stop_simulator_response.status_code == 200, f"{stop_simulator_response.text}"
        for attempt in range(MAX_RETRIES):
            simulator_healthcheck_response = requests.get(url_simulator_healthcheck, headers=headers)
            if simulator_healthcheck_response.status_code == 200:
                time.sleep(5)
            else:
                print(f"Simulator is stopped, healthcheck status code: {simulator_healthcheck_response.status_code}")
                break
        else:
            raise Exception(f"Error: Number of {MAX_RETRIES} is used. Simulator hasn't stopped yet.")