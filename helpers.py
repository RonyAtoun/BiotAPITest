import json
import uuid
import pytest
import requests

ENDPOINT = "https://api.staging.biot-gen2.biot-med.com"


def login_with_with_credentials(username, password):
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
        "_phone": "+12345678901",
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
            "enabled": True,
            "expirationInMinutes": 1440
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
        "_phone": "+12345678901",
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
        "_additionalPhone": "+12345678901",
        "_nationalId": "123456789",
        "_ownerOrganization": {
            "id": organization_id
        },
        "_caregiver": {

        }
    }
    return requests.post(ENDPOINT + '/organization/v1/users/patients/templates/{templateName}'
                         .replace("{templateName}", template_name), headers=headers, data=json.dumps(payload))


def update_patient(auth_token, patient_id, organization_id, change_string):
    email = f'integ_test_{uuid.uuid4().hex}'[0:32]
    email = email + '_@biotmail.com'
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_name": {
            "firstName": "John",
            "lastName": "Smith"
        },
        "_description": change_string,
        "_email": email,
        "_phone": "+12345678901",
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
        "_additionalPhone": "+12345678901",
        "_nationalId": "123456789",
        "_ownerOrganization": {
            "id": organization_id
        },
    }
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
                         '/enabled-state/{state}'.replace('{state}', state))


def delete_patient(auth_token, user_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/organization/v1/users/patients/{id}'.replace("{id}", user_id),
                           headers=headers)


def reset_password(auth_token, user_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/ums/v2/users/{id}/password/generate'.replace('{id}', user_id), headers=headers)


def create_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                    test_reference_attrib_display_name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    payload = {
        "displayName": test_display_name,
        "name": test_name,
        "entityType": "generic-entity",
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

    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def delete_template(auth_token, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/settings/v1/templates/{templateId}'.replace("{templateId}", template_id),
                           headers=headers)


def create_generic_entity(auth_token, template_id, test_name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_ownerOrganization": {"id": "00000000-0000-0000-0000-000000000000"},
        "_name": test_name,
        "_templateId": template_id
    }
    return requests.post(ENDPOINT + '/generic-entity/v1/generic-entities', headers=headers, data=json.dumps(payload))


def delete_generic_entity(auth_token, entity_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/generic-entity/v1/generic-entities/{id}'.replace("{id}", entity_id),
                           headers=headers)


def create_organization(auth_token, template_id):
    email = f'integ_test_{uuid.uuid4().hex}'[0:32]
    email = email + '_@biotmail.com'
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
        "_phone": "+12345678901",
        "_timezone": "Europe/Oslo",
        "_locale": "en-us",
        "_primaryAdministrator": {
            "_name": {
                "firstName": "Test",
                "lastName": "User"
            },
            "_description": "Lorem Ipsum",
            "_email": email,
            "_phone": "+12345678901",
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
    #        {
    #        "filter": [
    #            {
    #                #"_id" : { "eq": organization_id}
    #
    #            }
    #        ],
    #    }
    #    #querystring = urllib.parse.urlencode(query_params)
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
        "_phone": "+12345678901",
        "_timezone": "Europe/Oslo",
        "_locale": "en-us"
    }
    return requests.patch(
        ENDPOINT + '/organization/v1/organizations/{id}'.replace('{id}', organization_id),
        headers=headers, data=json.dumps(payload))


def create_registration_code(auth_token, template_name, registration_code):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_code": registration_code,
        "_ownerOrganization": {
            "id": "00000000-0000-0000-0000-000000000000"
        }
    }
    return requests.post(ENDPOINT + '/organization/v1/registration-codes/templates/{templateName}'
                         .replace("{templateName}", template_name), headers=headers, data=json.dumps(payload))


def delete_registration_code(auth_token, code_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/organization/v1/registration-codes/{id}'.replace("{id}", code_id),
                           headers=headers)


def create_device(auth_token, template_name, device_id, registration_code_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_description": "integ_test_device",
        "_timezone": "Europe/Oslo",
        "_id": device_id,
        "_ownerOrganization": {
            "id": "00000000-0000-0000-0000-000000000000"
        },
        "_registrationCode": {
            "id": registration_code_id
        }
    }

    return requests.post(ENDPOINT + '/device/v2/devices/templates/{templateName}'
                         .replace('{templateName}', template_name), headers=headers, data=json.dumps(payload))


def delete_device(auth_token, device_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/device/v2/devices/{id}'.replace("{id}", device_id),
                           headers=headers)


def get_device(auth_token, device_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/device/v2/devices/{id}'.replace("{id}", device_id), headers=headers)


def identified_self_signup_with_registration_code(auth_token, test_name, email, registration_code, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_name": test_name,
        "_description": "Test Self-signup",
        "_email": email,
        "_phone": "+12345678901",
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
        "_additionalPhone": "+12345678901",
        "_nationalId": "123456789",
        "_username": email,
        "_password": "Ab12z456",
        "_deviceRegistrationCode": registration_code,
        "_ownerOrganization": {
            "id": organization_id
        }
    }
    return requests.post(ENDPOINT + '/api-gateway/v1/sign-up', headers=headers, data=json.dumps(payload))


def anonymous_self_signup_with_registration_code(auth_token, test_name, email, registration_code):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_username": email,
        "_password": "Aa123456",
        "_nickname": test_name,
        "_deviceRegistrationCode": registration_code
    }

    return requests.post(ENDPOINT + '/api-gateway/v1/sign-up/anonymous', headers=headers, data=json.dumps(payload))
