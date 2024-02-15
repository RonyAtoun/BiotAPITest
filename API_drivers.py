import json
import uuid
import requests
from urllib.parse import urlencode

ENDPOINT = "https://api.staging.biot-gen2.biot-med.com"


def login_with_credentials(username, password):
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    payload = {
        "username": username,
        "password": password
    }

    response = requests.post(ENDPOINT + '/ums/v2/users/login', headers=headers, data=json.dumps(payload))
    assert response.status_code == 200
    return response.json()["accessJwt"]["token"]


# Organization user APIs ###############################################################################################
def create_organization_user(auth_token, template_name, name, email, employee_id):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "email-confirmation-landing-page": "https://example.com/en/landing-page",
        "Authorization": "Bearer " + auth_token
    }
    payload = {
        "_name": {
            "firstName": name["firstName"],
            "lastName": name["lastName"]
        },
        "_description": "Lorem Ipsum",
        "_email": email,
        "_phone": None,
        "_locale": "en-us",
        "_gender": "FEMALE",
        "_dateOfBirth": "2007-12-20",
        "_address": {
            "countryCode": "US",
            "state": "Massachusetts",
            "city": "Boston",
            "zipCode": "02101",
            "address1": "11 Main St.",
            "address2": "Entry B, Apartment 1"
        },
        "_mfa": {
            "enabled": False,
            "expirationInMinutes": None
        },
        "_employeeId": employee_id,
        "_ownerOrganization": {
            "id": '00000000-0000-0000-0000-000000000000'
        }
    }
    return requests.post(ENDPOINT + '/organization/v1/users/organizations/templates/{templateName}'
                         .replace("{templateName}", template_name), headers=headers, data=json.dumps(payload))


def delete_organization_user(auth_token, user_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/organization/v1/users/organizations/{id}'.replace("{id}", user_id),
                           headers=headers)


def update_organization_user(auth_token, user_id, organization_id, change_string):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_description": change_string,
        "_ownerOrganization": {
            "id": organization_id
        },
    }
    return requests.patch(ENDPOINT + '/organization/v1/users/organizations/{id}'.replace("{id}", user_id),
                          headers=headers, data=json.dumps(payload))


def get_organization_user(auth_token, user_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/organization/v1/users/organizations/{id}'.replace('{id}', user_id),
                        headers=headers)


def get_organization_user_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/organization/v1/users/organizations', data=json.dumps(query_params),
                        headers=headers)


def change_organization_user_state(auth_token, user_id, state):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/organization/v1/users/organizations/{id}'.replace("{id}", user_id) +
                         '/enabled-state/{state}'.replace('{state}', state), headers=headers)


# Patient APIs ################################################################################################
def create_patient(auth_token, name, email, template_name, organization_id):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "email-confirmation-landing-page": "https://example.com/en/landing-page",
        "Authorization": "Bearer " + auth_token
    }
    payload = {
        "_name": name,
        "_description": "Lorem Ipsum",
        "_email": email,
        # "_phone": "+12345678901",
        "_locale": "en-us",
        "_gender": "FEMALE",
        "_dateOfBirth": "2007-12-20",
        "_address": {
            "countryCode": "US",
            "state": "Massachusetts",
            "city": "Boston",
            "zipCode": "02101",
            "address1": "11 Main St.",
            "address2": "Entry B, Apartment 1"
        },
        "_mfa": {
            "enabled": False,

        },
        # "_additionalPhone": "+12345678901",
        "_nationalId": "123456789",
        "_ownerOrganization": {
            "id": organization_id
        },
        "_caregiver": {

        }
    }
    return requests.post(ENDPOINT + '/organization/v1/users/patients/templates/{templateName}'
                         .replace("{templateName}", template_name), headers=headers, data=json.dumps(payload))


def update_patient(auth_token, patient_id, organization_id, change_string, caregiver_id, data):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    if data is not None:
        payload = data
    else:
        payload = {"_description": change_string, "_ownerOrganization": {"id": organization_id}} \
            if (caregiver_id is None) else {"_description": change_string,
                                            "_ownerOrganization": {"id": organization_id},
                                            "_caregiver": {"id": caregiver_id}}

    return requests.patch(ENDPOINT + '/organization/v1/users/patients/{id}'.replace("{id}", patient_id),
                          headers=headers, data=json.dumps(payload))


def get_patient(auth_token, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/organization/v1/users/patients/{id}'.replace('{id}', patient_id),
                        headers=headers)


def get_patient_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/organization/v1/users/patients', data=json.dumps(query_params), headers=headers)


def change_patient_state(auth_token, patient_id, state):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/organization/v1/users/patients/{id}'.replace("{id}", patient_id) +
                         '/enabled-state/{state}'.replace('{state}', state), headers=headers)


def delete_patient(auth_token, user_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/organization/v1/users/patients/{id}'.replace("{id}", user_id),
                           headers=headers)


# Caregiver APIs ################################################################################################
def create_caregiver(auth_token, name, email, template_name, organization_id):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "email-confirmation-landing-page": "https://example.com/en/landing-page",
        "Authorization": "Bearer " + auth_token
    }
    payload = {
        "_name": name,
        "_description": "test care giver",
        "_email": email,
        "_employeeId": f'integ_test_{uuid.uuid4().hex}'[0:32],
        "_ownerOrganization": {
            "id": organization_id
        }
    }
    return requests.post(ENDPOINT + '/organization/v1/users/caregivers/templates/{templateName}'
                         .replace("{templateName}", template_name), headers=headers, data=json.dumps(payload))


def update_caregiver(auth_token, caregiver_id, organization_id, change_string):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_description": change_string,
        "_ownerOrganization": {
            "id": organization_id
        },
    }
    return requests.patch(ENDPOINT + '/organization/v1/users/caregivers/{id}'.replace("{id}", caregiver_id),
                          headers=headers, data=json.dumps(payload))


def delete_caregiver(auth_token, user_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/organization/v1/users/caregivers/{id}'.replace("{id}", user_id),
                           headers=headers)


def change_caregiver_state(auth_token, caregiver_id, state):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/organization/v1/users/caregivers/{id}'.replace("{id}", caregiver_id) +
                         '/enabled-state/{state}'.replace('{state}', state), headers=headers)


def get_caregiver(auth_token, caregiver_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/organization/v1/users/caregivers/{id}'.replace('{id}', caregiver_id),
                        headers=headers)


def get_caregiver_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/organization/v1/users/caregivers', data=json.dumps(query_params), headers=headers)


# Misc user APIs ################################################################################################
def reset_password(auth_token, user_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/ums/v2/users/{id}/password/generate'.replace('{id}', user_id), headers=headers)


def resend_invitation(auth_token, user_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/organization/v1/invitations/{userId}'.replace('{userId}', user_id),
                         headers=headers)


# Template APIs ################################################################################################
def create_organization_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                                 test_reference_attrib_display_name, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    payload = get_organization_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                                test_reference_attrib_display_name, organization_id)

    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def create_patient_template(auth_token, test_display_name, test_name, organization_id, entity_type):
    pass
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    payload = get_patient_template_payload(test_display_name, test_name, organization_id, entity_type)

    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def create_device_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                           test_reference_attrib_display_name, organization_id, entity_type, parent_template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    payload = get_device_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                          test_reference_attrib_display_name, organization_id, entity_type,
                                          parent_template_id)

    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def create_alert_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                          test_reference_attrib_display_name, organization_id, entity_type, parent_template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    if entity_type == "patient-alert":
        payload = get_patient_alert_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                                     test_reference_attrib_display_name, organization_id, entity_type,
                                                     parent_template_id)
    else:
        payload = get_device_alert_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                                    test_reference_attrib_display_name, organization_id, entity_type,
                                                    parent_template_id)
    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def create_usage_session_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                                  test_reference_attrib_display_name, organization_id, entity_type, parent_template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    payload = get_usage_session_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                                 test_reference_attrib_display_name, organization_id, entity_type,
                                                 parent_template_id)
    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def get_template(auth_token, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/settings/v1/templates/{templateId}'.replace('{templateId}', template_id),
                        headers=headers)


def delete_template(auth_token, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/settings/v1/templates/{templateId}'.replace("{templateId}", template_id),
                           headers=headers)


def update_template(auth_token, template_id, device_template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "parentTemplateId": template_id
    }
    return requests.put(ENDPOINT + '/settings/v1/templates/{templateId})'.replace('{templateId}', device_template_id),
                        headers=headers, data=json.dumps(payload))


def update_patient_template(auth_token, template_id, payload):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.put(ENDPOINT + '/settings/v1/templates/{templateId}'.replace('{templateId}', template_id),
                        headers=headers, data=json.dumps(payload))


# Generic Entity APIs ################################################################################################
def create_generic_entity(auth_token, template_id, test_name, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_ownerOrganization": {"id": organization_id},
        "_name": test_name,
        "_templateId": template_id
    }
    return requests.post(ENDPOINT + '/generic-entity/v1/generic-entities', headers=headers, data=json.dumps(payload))


def delete_generic_entity(auth_token, entity_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/generic-entity/v1/generic-entities/{id}'.replace("{id}", entity_id),
                           headers=headers)


def update_generic_entity(auth_token, entity_id, change_string):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_name": change_string,
    }
    return requests.patch(ENDPOINT + '/generic-entity/v1/generic-entities/{id}'.replace('{id}', entity_id),
                          headers=headers, data=json.dumps(payload))


def get_generic_entity(auth_token, entity_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/generic-entity/v1/generic-entities/{id}'.replace('{id}', entity_id),
                        headers=headers)


def get_generic_entity_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/generic-entity/v1/generic-entities', data=json.dumps(query_params),
                        headers=headers)


# Organization APIs ################################################################################################
def create_organization(auth_token, template_id):
    email = f'integ_test_{uuid.uuid4().hex}'[0:32] + '_@biotmail.com'
    organization_name = f'Test Org_{uuid.uuid4().hex}'[0:32]
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "email-confirmation-landing-page": "https://example.com/en/landing-page",
        "Authorization": "Bearer " + auth_token
    }
    payload = {
        "_name": organization_name,
        "_description": "Lorem Ipsum",
        "_headquarters": {
            "countryCode": "US",
            "state": "Massachusetts",
            "city": "Boston",
            "zipCode": "02101",
            "address1": "11 Main St.",
            "address2": "Entry B, Apartment 1"
        },
        # "_phone": "+12345678901",
        "_timezone": "Europe/Oslo",
        "_locale": "en-us",
        "_primaryAdministrator": {
            "_name": {
                "firstName": "Test",
                "lastName": "User"
            },
            "_description": "Lorem Ipsum",
            "_email": email,
            # "_phone": "+12345678901",
            "_locale": "en-us",
            "_gender": "FEMALE",
            "_dateOfBirth": "2007-12-20",
            "_address": {
                "countryCode": "US",
                "state": "Massachusetts",
                "city": "Boston",
                "zipCode": "02101",
                "address1": "11 Main St.",
                "address2": "Entry B, Apartment 1"
            },
            "_mfa": {
                "enabled": False,
                "expirationInMinutes": None
            },
            "_employeeId": f'{uuid.uuid4().hex}'
        },
        "_templateId": template_id
    }

    return requests.post(ENDPOINT + '/organization/v1/organizations', headers=headers, data=json.dumps(payload))


def get_organization(auth_token, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/organization/v1/organizations/{id}'.replace('{id}', organization_id),
                        headers=headers)


def get_organization_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/organization/v1/organizations', data=json.dumps(query_params), headers=headers)


def delete_organization(auth_token, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/organization/v1/organizations/{id}'.replace('{id}', organization_id),
                           headers=headers)


def update_organization(auth_token, organization_id, change_string):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_name": change_string,
        "_description": "Lorem Ipsum",
        "_headquarters": {
            "countryCode": "US",
            "state": "Massachusetts",
            "city": "Boston",
            "zipCode": "02101",
            "address1": "11 Main St.",
            "address2": "Entry B, Apartment 1"
        },
        # "_phone": "+12345678901",
        "_timezone": "Europe/Oslo",
        "_locale": "en-us"
    }
    return requests.patch(
        ENDPOINT + '/organization/v1/organizations/{id}'.replace('{id}', organization_id),
        headers=headers, data=json.dumps(payload))


# Registration codes APIs ##############################################################################################
def create_registration_code(auth_token, template_name, registration_code, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_code": registration_code,
        "_ownerOrganization": {
            "id": organization_id
        }
    }
    return requests.post(ENDPOINT + '/organization/v1/registration-codes/templates/{templateName}'
                         .replace("{templateName}", template_name), headers=headers, data=json.dumps(payload))


def delete_registration_code(auth_token, code_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/organization/v1/registration-codes/{id}'.replace("{id}", code_id),
                           headers=headers)


def update_registration_code(auth_token, registration_code_id, change_string):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_code": change_string,
    }
    return requests.patch(ENDPOINT + '/organization/v1/registration-codes/{id}'.replace('{id}', registration_code_id),
                          headers=headers, data=json.dumps(payload))


def get_registration_code(auth_token, registration_code_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/organization/v1/registration-codes/{id}'.replace("{id}", registration_code_id),
                        headers=headers)


def get_registration_code_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/organization/v1/registration-codes', data=json.dumps(query_params),
                        headers=headers)


# Device APIs ################################################################################################
def create_device(auth_token, template_name, device_id, registration_code_id, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_description": "integ_test_device",
        "_timezone": "Europe/Oslo",
        "_id": device_id,
        "_ownerOrganization": {
            "id": organization_id
        },
        "_registrationCode": {
            "id": registration_code_id
        }
    }

    return requests.post(ENDPOINT + '/device/v2/devices/templates/{templateName}'
                         .replace('{templateName}', template_name), headers=headers, data=json.dumps(payload))


def update_device(auth_token, device_id, change_string, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_description": change_string,
        "_patient": {
            "id": patient_id,
        },
    }
    return requests.patch(ENDPOINT + '/device/v2/devices/{id}'.replace('{id}', device_id),
                          headers=headers, data=json.dumps(payload))


def delete_device(auth_token, device_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/device/v2/devices/{id}'.replace("{id}", device_id),
                           headers=headers)


def get_device(auth_token, device_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/device/v2/devices/{id}'.replace("{id}", device_id), headers=headers)


def get_device_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/device/v2/devices', data=json.dumps(query_params), headers=headers)


def get_device_credentials(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/device/v2/credentials/organization', headers=headers)


# Usage session APIs ################################################################################################
def create_usage_session_by_usage_type(auth_token, device_id, usage_type):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_startTime": "2023-12-20T10:15:30Z",
        "_state": "PAUSED",
    }
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/usage-type/{usageType}'
                         .replace('{deviceId}', device_id).replace('{usageType}', usage_type),
                         data=json.dumps(payload), headers=headers)


def create_usage_session(auth_token, device_id, template_id):  ##### doesn't work
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_startTime": "2023-12-20T10:15:30Z",
        "_state": "PAUSED",
        "_templateId": template_id
    }
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions'
                         .replace('{deviceId}', device_id), data=json.dumps(payload), headers=headers)


def get_usage_session(auth_token, device_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/{id}'.replace('{deviceId}', device_id)
                        .replace('{id}', session_id), headers=headers)


def get_usage_session_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/device/v1/devices/usage-sessions', data=json.dumps(query_params), headers=headers)


def update_usage_session(auth_token, device_id, session_id, state):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    if state == "DONE":
        payload = {
            "_startTime": "2023-12-20T10:15:30Z",
            "_state": "DONE",
            "_summary": {
                "_stopReasonCode": "COMPLETION",
                "_stopReason": "Manual stop"
            },
            "_endTime": "2023-12-25T10:15:30Z",
        }
    else:
        payload = {
            "_startTime": "2023-12-20T10:15:30Z",
            "_state": "ACTIVE",
            "_summary": {
                "_stopReasonCode": None,
                "_stopReason": None
            },
            "_endTime": None,
        }
    return requests.patch(
        ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/{id}'.replace('{deviceId}', device_id)
        .replace('{id}', session_id), headers=headers, data=json.dumps(payload))


def delete_usage_session(auth_token, device_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/{id}'.replace("{deviceId}",
                                                                                                  device_id).replace(
        '{id}', session_id), headers=headers)


def start_usage_session(auth_token, device_id, template_id, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_templateId": template_id,
        "_name": "test start session",
        "_patient": {
            "id": patient_id
        }
    }
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/remote-control/start'
                         .replace('{deviceId}', device_id), headers=headers, data=json.dumps(payload))


def stop_usage_session(auth_token, device_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/v1/devices/{deviceId}/usage-sessions/{id}/remote-control/stop'
                         .replace('{deviceId}', device_id).replace('{id}', session_id), headers=headers)


def pause_usage_session(auth_token, device_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/{id}/remote-control/pause'
                         .replace('{deviceId}', device_id).replace('{id}', session_id), headers=headers)


def resume_usage_session():
    pass


# Measurement APIs ################################################################################################
def create_measurement(auth_token, device_id, patient_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "metadata": {
            "timestamp": "2023-12-20T10:15:30Z",
            "deviceId": device_id,
            "patientId": patient_id,
            "sessionId": session_id
        },
        "data": {
            "test_hr": 70
        }
    }
    return requests.post(ENDPOINT + '/measurement/v1/measurements', data=json.dumps(payload), headers=headers)


def create_bulk_measurement(auth_token, device_id, patient_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "metadata": {
            "timestamp": "2023-10-20T10:15:30Z",
            "deviceId": device_id,
            "patientId": patient_id,
            "sessionId": session_id
        },
        "data": {
            "test_hr": 70,
        }
    }
    return requests.post(ENDPOINT + '/measurement/v1/measurements/bulk', data=json.dumps(payload), headers=headers)


def get_raw_measurements(auth_token, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {
        "attributes": "test_hr",
        "patientId": patient_id,
        "startTime": "2023-12-30T10:15:30Z",
        "endTime": "2024-01-30T08:15:30Z"
    }
    encoded_params = urlencode(query_params)
    return requests.get(ENDPOINT + "/measurement/v1/measurements/raw?" + encoded_params, headers=headers)


def get_aggregated_measurements(auth_token, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {
        "attributes": "test_hr",
        "patientId": patient_id,
        "startTime": "2023-12-30T10:15:30Z",
        "endTime": "2024-01-30T08:15:30Z",
        "binIntervalSeconds": 120
    }
    encoded_params = urlencode(query_params)
    return requests.get(ENDPOINT + "/measurement/v1/measurements/aggregated?" + encoded_params, headers=headers)


def get_v2_raw_measurements(auth_token, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    search_request = {
        "searchRequest": json.dumps({
            "filter": {
                "_patient.id": {
                    "eq": patient_id
                },
                "test_hr": {
                    "gt": 25,
                    "gte": 25,
                },
                "timestamp": {
                    "from": "2023-12-30T10:15:30Z",
                    "to": "2023-12-30T10:15:35Z",
                }
            }
        })
    }
    return requests.get(ENDPOINT + "/measurement/v2/measurements/raw?", params=search_request, headers=headers)


def get_v2_aggregated_measurements(auth_token, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    search_request = {
        "searchRequest": json.dumps({
            "filter": {
                "_patient.id": {
                    "eq": patient_id
                },
                "test_hr": {
                    "gt": 25,
                    "gte": 25,
                },
                "timestamp": {
                    "from": "2023-12-30T10:15:30Z",
                    "to": "2023-12-30T10:15:35Z",
                },
                "binIntervalSeconds": {
                    "eq": 120
                }
            }
        })
    }
    return requests.get(ENDPOINT + "/measurement/v2/measurements/aggregated?", params=search_request, headers=headers)


# Alert APIs (patient & device)########################################################################################
def create_patient_alert_by_id(auth_token, patient_id, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_state": "ACTIVE",
        "_severity": "MAJOR",
        "_clearNotes": None,
        "_name": "test patient alert",
        "_templateId": template_id
    }
    return requests.post(ENDPOINT + '/organization/v1/users/patients/{patientId}/alerts'
                         .replace('{patientId}', patient_id), data=json.dumps(payload), headers=headers)


def create_patient_alert_by_name(auth_token, patient_id, template_name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_state": "ACTIVE",
        "_severity": "MAJOR",
        "_clearNotes": None,
        "_name": "test patient alert",
    }
    return requests.post(ENDPOINT + '/organization/v1/users/patients/{patientId}/alerts/{templateName}'
                         .replace('{patientId}', patient_id).replace('{templateName}', template_name),
                         data=json.dumps(payload), headers=headers)


def get_patient_alert(auth_token, patient_id, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/organization/v1/users/patients/{patientId}/alerts/{id}'
                        .replace('{patientId}', patient_id).replace('{id}', alert_id), headers=headers)


def delete_patient_alert(auth_token, patient_id, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/organization/v1/users/patients/{patientId}/alerts/{id}'.replace('{patientId}',
                           patient_id).replace('{id}', alert_id), headers=headers)


def update_patient_alert(auth_token, patient_id, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_state": "ACTIVE",
        "_severity": "MAJOR",
        "_clearNotes": None,
        "_name": "test patient alert",
    }
    return requests.patch(ENDPOINT + '/organization/v1/users/patients/{patientId}/alerts/{id}'.replace('{patientId}',
                          patient_id).replace('{id}', alert_id), data=json.dumps(payload), headers=headers)


def get_patient_alert_list(auth_token, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    search_request = {
        "searchRequest": json.dumps({
            "filter": {
                "_id": {
                    "like": alert_id
                },
            }
        })
    }
    return requests.get(ENDPOINT + '/organization/v1/users/patients/alerts?', params=search_request, headers=headers)


def create_device_alert_by_id(auth_token, device_id, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_state": "ACTIVE",
        "_severity": "MAJOR",
        "_clearNotes": None,
        "_name": "test device alert",
        "_templateId": template_id
    }
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/alerts'
                         .replace('{deviceId}', device_id), data=json.dumps(payload), headers=headers)


def create_device_alert_by_name(auth_token, device_id, template_name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_state": "ACTIVE",
        "_severity": "MAJOR",
        "_clearNotes": None,
        "_name": "test patient alert",
    }
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/alerts/{templateName}'
                         .replace('{deviceId}', device_id).replace('{templateName}', template_name),
                         data=json.dumps(payload), headers=headers)


def delete_device_alert(auth_token, device_id, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/device/v1/devices/{deviceId}/alerts/{id}'.replace('{deviceId}',
                           device_id).replace('{id}', alert_id), headers=headers)


def update_device_alert(auth_token, device_id, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_state": "ACTIVE",
        "_severity": "MAJOR",
        "_clearNotes": None,
        "_name": "test patient alert",
    }
    return requests.patch(ENDPOINT + '/device/v1/devices/{deviceId}/alerts/{id}'.replace('{deviceId}',
                          device_id).replace('{id}', alert_id), data=json.dumps(payload), headers=headers)


def get_device_alert(auth_token, device_id, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/device/v1/devices/{deviceId}/alerts/{id}'
                        .replace('{deviceId}', device_id).replace('{id}', alert_id), headers=headers)


def get_device_alert_list(auth_token, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    search_request = {
        "searchRequest": json.dumps({
            "filter": {
                "_id": {
                    "like": alert_id
                },
            }
        })
    }
    return requests.get(ENDPOINT + '/device/v1/devices/alerts?', params=search_request, headers=headers)


# File APIs ################################################################################################
def create_file(auth_token, name, mime_type):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        'name': name,
        'mimeType': mime_type
    }
    return requests.post(ENDPOINT + '/file/v1/files/upload', data=json.dumps(payload), headers=headers)


def get_file(auth_token, file_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/file/v1/files/{id}/download'.replace('{id}', file_id), headers=headers)


# Get entities PIs ################################################################################################
def get_entities(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/settings/v2/entity-types', headers=headers)


def identified_self_signup_with_registration_code(auth_token, test_name, email, registration_code, organization_id):
    headers = {"content-type": "application/json"}
    payload = {
        "_name": test_name,
        "_description": "Test Self-signup",
        "_email": email,
        "_locale": "en-us",
        "_gender": "FEMALE",
        "_dateOfBirth": "2007-12-20",
        "_address": {
            "countryCode": "US",
            "state": "Massachusetts",
            "city": "Boston",
            "zipCode": "02101",
            "address1": "11 Main St.",
            "address2": "Entry B, Apartment 1"
        },
        "_mfa": {
            "enabled": False,
        },
        # "_additionalPhone": "+12345678901",
        "_nationalId": "123456789",
        "_username": email,
        "_password": "Q2207819w@",
        "_deviceRegistrationCode": registration_code,
        "_ownerOrganization": {
            "id": organization_id
        }
    }
    return requests.post(ENDPOINT + '/api-gateway/v1/sign-up', headers=headers, data=json.dumps(payload))


def anonymous_self_signup_with_registration_code(auth_token, test_name, email, registration_code):
    headers = {"content-type": "application/json"}
    payload = {
        "_username": email,
        "_password": "Q2207819w@",
        "_nickname": test_name,
        "_deviceRegistrationCode": registration_code
    }

    return requests.post(ENDPOINT + '/api-gateway/v1/sign-up/anonymous', headers=headers, data=json.dumps(payload))


# Payloads for template APIs # #######################################################################################
def get_organization_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                      test_reference_attrib_display_name, organization_id):
    return {
        "displayName": test_display_name,
        "name": test_name,
        "entityType": "generic-entity",
        "ownerOrganizationId": organization_id,
        "builtInAttributes": [
            {
                "name": "_ownerOrganization",
                "basePath": None,
                "displayName": "Org",
                "phi": False,
                "referenceConfiguration": {
                    "uniquely": True,
                    "referencedSideAttributeName": test_referenced_attrib_name,
                    "referencedSideAttributeDisplayName": test_reference_attrib_display_name,
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                },
                "validation": {"mandatory": True}
            }
        ]
    }


def get_device_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                test_reference_attrib_display_name, organization_id, entity_type, parent_template_id):
    referencedSideAttributeName = f'Template Device{uuid.uuid4()}'[0:16]
    return {
        "name": test_name,
        "displayName": test_display_name,
        "customAttributes": [],
        "builtInAttributes": [
            {
                "name": "_ownerOrganization",
                "basePath": None,
                "displayName": "Owner Organization",
                "phi": False,
                "validation": {
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": test_referenced_attrib_name,
                    "referencedSideAttributeDisplayName": test_reference_attrib_display_name,
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            },
            {
                "name": "_patient",
                "basePath": None,
                "displayName": "Patient",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": referencedSideAttributeName,
                    "referencedSideAttributeDisplayName": referencedSideAttributeName,
                    "validTemplatesToReference": [],
                    "entityType": "patient"
                }
            },
            {
                "name": "_registrationCode",
                "basePath": None,
                "displayName": "Registration Code",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": True,
                    "referencedSideAttributeName": referencedSideAttributeName,
                    "referencedSideAttributeDisplayName": referencedSideAttributeName,
                    "validTemplatesToReference": [],
                    "entityType": "registration-code"
                }
            },
        ],
        "templateAttributes": [],
        "entityType": entity_type,
        "parentTemplateId": parent_template_id,
        "ownerOrganizationId": organization_id
    }


def get_patient_alert_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                       test_reference_attrib_display_name, organization_id, entity_type,
                                       parent_template_id):
    referencedSideAttributeName = f'Template Alert{uuid.uuid4()}'[0:16]
    return {
        "name": test_name,
        "displayName": test_display_name,
        "customAttributes": [],
        "builtInAttributes": [
            {
                "name": "_ownerOrganization",
                "basePath": None,
                "displayName": "Owner Organization",
                "phi": False,
                "validation": {
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": test_referenced_attrib_name,
                    "referencedSideAttributeDisplayName": test_reference_attrib_display_name,
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            },
            {
                "name": "_patient",
                "basePath": None,
                "displayName": "Patient",
                "phi": False,
                "validation": {
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": referencedSideAttributeName,
                    "referencedSideAttributeDisplayName": referencedSideAttributeName,
                    "validTemplatesToReference": [],
                    "entityType": "patient"
                }
            },
            {
                "name": "_clearedBy",
                "basePath": None,
                "displayName": "clearedBy",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": referencedSideAttributeName,
                    "referencedSideAttributeDisplayName": referencedSideAttributeName,
                    "validTemplatesToReference": [],
                    "entityType": "caregiver"
                }
            },
        ],
        "templateAttributes": [],
        "entityType": entity_type,
        "parentTemplateId": parent_template_id,
        "ownerOrganizationId": organization_id
    }


def get_device_alert_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                      test_reference_attrib_display_name, organization_id, entity_type,
                                      parent_template_id):
    referencedSideAttributeName = f'Template Alert{uuid.uuid4()}'[0:16]
    return {
        "name": test_name,
        "displayName": test_display_name,
        "customAttributes": [],
        "builtInAttributes": [
            {
                "name": "_ownerOrganization",
                "basePath": None,
                "displayName": "Owner Organization",
                "phi": False,
                "validation": {
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": test_referenced_attrib_name,
                    "referencedSideAttributeDisplayName": test_reference_attrib_display_name,
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            },
            {
                "name": "_device",
                "basePath": None,
                "displayName": "Device",
                "phi": False,
                "validation": {
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": referencedSideAttributeName,
                    "referencedSideAttributeDisplayName": referencedSideAttributeName,
                    "validTemplatesToReference": [],
                    "entityType": "device"
                }
            },
            {
                "name": "_clearedBy",
                "basePath": None,
                "displayName": "clearedBy",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": referencedSideAttributeName,
                    "referencedSideAttributeDisplayName": referencedSideAttributeName,
                    "validTemplatesToReference": [],
                    "entityType": "caregiver"
                }
            },
        ],
        "templateAttributes": [],
        "entityType": entity_type,
        "parentTemplateId": parent_template_id,
        "ownerOrganizationId": organization_id
    }


def get_usage_session_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                       test_reference_attrib_display_name, organization_id, entity_type,
                                       parent_template_id):
    referencedSideAttributeName = f'Template Device{uuid.uuid4()}'[0:30]
    usage_session_to_device = f'Test us-session{uuid.uuid4()}'[0:30]
    return {
        "name": test_name,
        "displayName": test_display_name,
        "customAttributes": [],
        "builtInAttributes": [
            {
                "name": "_creationTime",
                "basePath": None,
                "displayName": "Creation Time",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": None
            },
            {
                "name": "_device",
                "basePath": None,
                "displayName": "Device",
                "phi": False,
                "validation": {
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": usage_session_to_device,
                    "referencedSideAttributeDisplayName": usage_session_to_device,
                    "validTemplatesToReference": [
                        parent_template_id
                    ],
                    "entityType": "device"
                }
            },
            {
                "name": "_endTime",
                "basePath": None,
                "displayName": "End Time",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": None
            },
            {
                "name": "_lastModifiedTime",
                "basePath": None,
                "displayName": "Last Modified Time",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": None
            },
            {
                "name": "_name",
                "basePath": None,
                "displayName": "Name",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": None
            },
            {
                "name": "_ownerOrganization",
                "basePath": None,
                "displayName": "Owner Organization",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": test_referenced_attrib_name,
                    "referencedSideAttributeDisplayName": test_reference_attrib_display_name,
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            },
            {
                "name": "_patient",
                "basePath": None,
                "displayName": "Patient",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": referencedSideAttributeName,
                    "referencedSideAttributeDisplayName": referencedSideAttributeName,
                    "validTemplatesToReference": [],
                    "entityType": "patient"
                }
            },
            {
                "name": "_initiator",
                "basePath": None,
                "displayName": "Session Initiator",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": None
            },
            {
                "name": "_startTime",
                "basePath": None,
                "displayName": "Start Time",
                "phi": False,
                "validation": {
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": None
            },
            {
                "name": "_state",
                "basePath": None,
                "displayName": "State",
                "phi": False,
                "validation": {
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": None
            },
            {
                "name": "_stopReason",
                "basePath": "_summary",
                "displayName": "Stop Reason",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": None
            },
            {
                "name": "_stopReasonCode",
                "basePath": "_summary",
                "displayName": "Stop Reason Code",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": None
            }
        ],
        "templateAttributes": [
            {
                "name": "_requiredMeasurementIntervalMilliseconds",
                "basePath": None,
                "displayName": "Required Measurement Interval",
                "phi": False,
                "referenceConfiguration": None,
                "value": 1000,
                "organizationSelectionConfiguration": None
            }
        ],
        "entityType": entity_type,
        "ownerOrganizationId": organization_id,
        "parentTemplateId": parent_template_id
    }


def get_patient_template_payload(test_display_name, test_name, organization_id, entity_type):
    return {
        "displayName": test_display_name,
        "name": test_name,
        "description": "Patient template",
        "entityType": entity_type,
        "ownerOrganizationId": None,
        "parentTemplateId": None,
        "forceUpdate": False,
        "customAttributes": [
            {
                "name": "uploadFile",
                "type": "FILE",
                "displayName": "uploadFile",
                "phi": False,
                "validation": {
                    "mandatory": False,
                    "min": None,
                    "max": 20971520,
                    "regex": None,
                    "defaultValue": None
                },
                "id": "2885fbe6-1f26-4ac7-92cf-206d1a60e813",
                "selectableValues": [],
                "category": "REGULAR",
                "numericMetaData": None,
                "referenceConfiguration": None,
                "linkConfiguration": None
            }
        ],
    }
