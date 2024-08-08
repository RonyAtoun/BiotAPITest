import pytest
import requests
import time
import os
from dotenv import load_dotenv
from API_drivers import get_template, login_with_credentials, get_adb_info, stop_sync_adb
from api_test_helpers import map_template, update_template

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


@pytest.fixture(scope="session", autouse=True)
def adb_sync_off():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    adb_state = get_adb_info(admin_auth_token)
    adb_sync_state = adb_state.json()["activationState"]
    if adb_sync_state == "ACTIVE_AND_SYNC_ON":
        stop_sync_adb(admin_auth_token)
        adb_sync_state_new = get_adb_info(admin_auth_token)
        adb_state_new = adb_sync_state_new.json()["activationState"]
        assert adb_state_new == "ACTIVE_AND_SYNC_OFF", f"Actual ADB state is {adb_state_new}"
        print("ADB state changed to sync off")
    else:
        print("ADB state is sync off")


@pytest.fixture(scope="session", autouse=True)
def patient_template_prepare_on_fresh_install():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    patient_template_id = "a38f32d7-de6c-4252-9061-9bcdc253f6c9"
    get_template_response = get_template(admin_auth_token, patient_template_id)
    template_payload = map_template(get_template_response.json())
    for element in template_payload['customAttributes']:
        if element['validation']['mandatory']:
            element['validation']['mandatory'] = False
            element['validation']['defaultValue'] = None
        else:
            continue
    for element in template_payload['builtInAttributes']:
        if element['validation']['mandatory'] and element['validationMetadata']['mandatoryReadOnly'] is False:
            element['validation']['mandatory'] = False
            element['validation']['defaultValue'] = None
        else:
            continue
    for element in template_payload['templateAttributes']:
        element['value'] = ["SELF", "ANONYMOUS"]
        element['organizationSelectionConfiguration']['all'] = True
    for element in template_payload['customAttributes']:
        if element['phi']:
            element['phi'] = False
        else:
            continue
    for element in template_payload['builtInAttributes']:
        if element['phi']:
            element['phi'] = False
        else:
            continue
    update_template_response = update_template(admin_auth_token, patient_template_id, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"
    print("Patient Template updated")


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
