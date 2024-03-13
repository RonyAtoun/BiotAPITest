import json
import os
import uuid
import requests
from urllib.parse import urlencode

# from test_constants import *

forgot_password_landing_page = os.getenv('forgot_password_landing_page')
ENDPOINT = os.getenv('ENDPOINT')


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


def get_self_user_email(auth_token):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    payload = {}
    response = requests.get(ENDPOINT + '/organization/v1/users/self', headers=headers, data=json.dumps(payload))
    # assert response.status_code == 200
    return response.json()["_email"]


# Locales APIs  ######################################################
def get_available_locales(auth_token):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    return requests.get(ENDPOINT + '/settings/v1/locales/configuration', headers=headers)


def add_locale(auth_token, code):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    payload = {
        "code": code,
        "hidden": False,
        "translationFallbackTypes": None
    }
    return requests.post(ENDPOINT + '/settings/v1/locales', headers=headers, data=json.dumps(payload))


def delete_locale(auth_token, locale_id):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    return requests.delete(ENDPOINT + '/settings/v1/locales/{id)'.replace('{id', locale_id), headers=headers)


def update_locale(auth_token, code):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    payload = {
        "availableLocales": [
            {
                "code": code,
                "hidden": False,
                "translationFallbackTypes": None
            }
        ],
        "defaultLocaleCode": "en-us"
    }
    return requests.patch(ENDPOINT + '/settings/v1/locales/configuration', headers=headers, data=json.dumps(payload))


# Portal builder APIs   ################################################################################
def update_portal_views(auth_token, portal_type, view_id, payload):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    return requests.put(ENDPOINT + '/settings/v1/portal-builder/{portalType}/views/{viewId}'
                        .replace('{portalType}', portal_type).replace('{viewId}', view_id), data=json.dumps(payload),
                        headers=headers)


def view_full_portal_information(auth_token, portal_type, view_type, template_id):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    if template_id is None:
        return requests.get(ENDPOINT +
                            '/settings/v1/portal-builder/{portalType}/views-full-info/{'
                            'viewType}?entityTypeName=device'.replace('{portalType}', portal_type)
                            .replace('{viewType}', view_type), headers=headers)
    else:
        return requests.get(ENDPOINT +
                            '/settings/v1/portal-builder/{portalType}/views-full-info/{'
                            'viewType}?entityTypeName=device&templateId='.replace('{portalType}', portal_type)
                            .replace('{viewType}', view_type) + template_id, headers=headers)


# Analytics DB APIs  ###################################################################################

def deploy_adb(auth_token):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    return requests.post(ENDPOINT + '/dms/v1/analytics/db/deploy', headers=headers)


def undeploy_adb(auth_token):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    return requests.post(ENDPOINT + '/dms/v1/analytics/db/undeploy', headers=headers)


def start_init_adb(auth_token):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    return requests.post(ENDPOINT + '/dms/v1/analytics/db/initialization/start', headers=headers)


def stop_init_adb(auth_token):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    return requests.post(ENDPOINT + '/dms/v1/analytics/db/initialization/stop', headers=headers)


def stop_sync_adb(auth_token):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    return requests.post(ENDPOINT + '/dms/v1/analytics/db/synchronization/stop', headers=headers)


def get_adb_info(auth_token):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + auth_token
    }
    return requests.get(ENDPOINT + '/dms/v1/analytics/db/information', headers=headers)


# Organization user APIS ###############################################################################
def create_organization_user(auth_token, template_name, name, email, organization_id):
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
        "_employeeId": f'integ_test_{uuid.uuid4().hex}'[0:32],
        "_ownerOrganization": {
            "id": organization_id
        }
    }
    return requests.post(f"{ENDPOINT}/organization/v1/users/organizations/templates/{template_name}",
                         headers=headers, data=json.dumps(payload))


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
    }
    return requests.post(ENDPOINT + '/organization/v1/users/patients/templates/{templateName}'
                         .replace("{templateName}", template_name), headers=headers, data=json.dumps(payload))


def create_patient_with_phi(auth_token, name, email, template_name, organization_id):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "email-confirmation-landing-page": "https://example.com/en/landing-page",
        "Authorization": "Bearer " + auth_token
    }
    payload = {
        "_name": name,
        "_description": "Lorem Ipsum",
        "phitruelabel": "testphi",
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


def update_patient_without_caregiver(auth_token, patient_id, organization_id, change_string):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {"_description": change_string, "_ownerOrganization": {"id": organization_id}}

    return requests.patch(ENDPOINT + '/organization/v1/users/patients/{id}'.replace("{id}", patient_id),
                          headers=headers, data=json.dumps(payload))


def get_patient(auth_token, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/organization/v1/users/patients/{id}'.replace('{id}', patient_id),
                        headers=headers)


def get_patient_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {"limit": 200}
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


def set_password(auth_token, old_password, new_password):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "password": {
            "current": old_password,
            "new": new_password
        },
        "mfa": {
            "enabled": False,
        }
    }
    return requests.patch(ENDPOINT + '/ums/v2/users/self', data=json.dumps(payload), headers=headers)


def forgot_password(user_email):
    headers = {
        "Content-Type": "application/json",
        "forgot-password-landing-page": forgot_password_landing_page
    }
    payload = json.dumps({
        "username": user_email
    })
    response = requests.post(ENDPOINT + "/ums/v2/users/self/password/forgot", headers=headers, data=payload)
    assert response.status_code == 200, f"{response.text}"
    return response


def resend_invitation(auth_token, user_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/organization/v1/invitations/{userId}'.replace('{userId}', user_id),
                         headers=headers)


# Template APIs ################################################################################################
def create_generic_entity_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                                   test_reference_attrib_display_name, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    payload = get_generic_entity_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                                  test_reference_attrib_display_name, organization_id)

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


def create_device_alert_template(auth_token, device_template_id, alert_template_name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = json.dumps({
        "name": alert_template_name,
        "displayName": alert_template_name,
        "customAttributes": [],
        "builtInAttributes": [
            {
                "name": "_clearDateTime",
                "basePath": None,
                "displayName": "Clear Date Time",
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
                "name": "_clearNotes",
                "basePath": None,
                "displayName": "Clear Notes",
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
                "name": "_clearTrigger",
                "basePath": None,
                "displayName": "Clear Trigger",
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
                "name": "_clearedBy",
                "basePath": None,
                "displayName": "Cleared By",
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
                    "referencedSideAttributeName": f"{alert_template_name} Cleared By To Alert",
                    "referencedSideAttributeDisplayName": f"{alert_template_name} Cleared By To Alert",
                    "validTemplatesToReference": [],
                    "entityType": "organization-user"
                }
            },
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
                    "referencedSideAttributeName": f"{alert_template_name} Device to Alert",
                    "referencedSideAttributeDisplayName": f"{alert_template_name} Device to Alert",
                    "validTemplatesToReference": [
                        device_template_id
                    ],
                    "entityType": "device"
                }
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
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": f"{alert_template_name} Device Alert to Organization",
                    "referencedSideAttributeDisplayName": f"{alert_template_name} Device Alert to Organization",
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            },
            {
                "name": "_setDateTime",
                "basePath": None,
                "displayName": "Set Date Time",
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
                "name": "_severity",
                "basePath": None,
                "displayName": "Severity",
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
                "name": "_state",
                "basePath": None,
                "displayName": "State",
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
                "name": "_allowMultipleOpenAlerts",
                "basePath": None,
                "displayName": "Allow Multiple Open Alerts",
                "phi": False,
                "referenceConfiguration": None,
                "value": False,
                "organizationSelectionConfiguration": None
            }
        ],
        "entityType": "device-alert",
        "ownerOrganizationId": "",
        "parentTemplateId": device_template_id
    })
    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def create_patient_alert_template(auth_token, patient_template_id, alert_template_name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = json.dumps({
        "name": alert_template_name,
        "displayName": alert_template_name,
        "customAttributes": [],
        "builtInAttributes": [
            {
                "name": "_clearDateTime",
                "basePath": None,
                "displayName": "Clear Date Time",
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
                "name": "_clearNotes",
                "basePath": None,
                "displayName": "Clear Notes",
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
                "name": "_clearTrigger",
                "basePath": None,
                "displayName": "Clear Trigger",
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
                "name": "_clearedBy",
                "basePath": None,
                "displayName": "Cleared By",
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
                    "referencedSideAttributeName": f"{alert_template_name} Cleared By To Alert",
                    "referencedSideAttributeDisplayName": f"{alert_template_name} Cleared By To Alert",
                    "validTemplatesToReference": [],
                    "entityType": "caregiver"
                }
            },
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
                    "referencedSideAttributeName": f"{alert_template_name} Device to Alert",
                    "referencedSideAttributeDisplayName": f"{alert_template_name} Device to Alert",
                    "validTemplatesToReference": [
                        patient_template_id
                    ],
                    "entityType": "patient"
                }
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
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": f"{alert_template_name} Device Alert to Organization",
                    "referencedSideAttributeDisplayName": f"{alert_template_name} Device Alert to Organization",
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            },
            {
                "name": "_setDateTime",
                "basePath": None,
                "displayName": "Set Date Time",
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
                "name": "_severity",
                "basePath": None,
                "displayName": "Severity",
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
                "name": "_state",
                "basePath": None,
                "displayName": "State",
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
                "name": "_allowMultipleOpenAlerts",
                "basePath": None,
                "displayName": "Allow Multiple Open Alerts",
                "phi": False,
                "referenceConfiguration": None,
                "value": False,
                "organizationSelectionConfiguration": None
            }
        ],
        "entityType": "patient-alert",
        "ownerOrganizationId": "",
        "parentTemplateId": patient_template_id
    })
    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def create_usage_session_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                                  test_reference_attrib_display_name, organization_id, entity_type, parent_template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    payload = get_usage_session_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                                 test_reference_attrib_display_name, organization_id, entity_type,
                                                 parent_template_id)
    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def create_command_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                            test_reference_attrib_display_name, organization_id, entity_type, parent_template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    payload = get_command_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                           test_reference_attrib_display_name, organization_id, entity_type,
                                           parent_template_id)
    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def create_command_template_with_support_stop_true(auth_token, command_template_name, device_template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = json.dumps({
        "name": command_template_name,
        "displayName": command_template_name,
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
                    "referencedSideAttributeName": f"{command_template_name} Commands to Device",
                    "referencedSideAttributeDisplayName": f"{command_template_name} Commands to Device",
                    "validTemplatesToReference": [
                        device_template_id
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
                "name": "_errorMessage",
                "basePath": None,
                "displayName": "Error Message",
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
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": f"{command_template_name} Commands to Organization",
                    "referencedSideAttributeDisplayName": f"{command_template_name} Commands to Organization",
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
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
            }
        ],
        "templateAttributes": [
            {
                "name": "_supportStop",
                "basePath": None,
                "displayName": "Support Stop",
                "phi": False,
                "referenceConfiguration": None,
                "value": True,
                "organizationSelectionConfiguration": None
            },
            {
                "name": "_timeoutInSeconds",
                "basePath": None,
                "displayName": "Timeout In Seconds",
                "phi": False,
                "referenceConfiguration": None,
                "value": 10,
                "organizationSelectionConfiguration": None
            }
        ],
        "entityType": "command",
        "ownerOrganizationId": "",
        "parentTemplateId": device_template_id
    })
    response = requests.request("POST", ENDPOINT + '/settings/v1/templates', headers=headers, data=payload)
    return response


def get_template(auth_token, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/settings/v1/templates/{templateId}'.replace('{templateId}', template_id),
                        headers=headers)


def get_template_overview(auth_token, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/settings/v1/templates/{templateId}/overview'.replace('{templateId}', template_id),
                        headers=headers)


def get_all_templates(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/settings/v1/templates/minimized', data=json.dumps(query_params), headers=headers)


def delete_template(auth_token, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/settings/v1/templates/{templateId}'.replace("{templateId}", template_id),
                           headers=headers)


def update_template(auth_token, template_id, payload):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}

    return requests.put(ENDPOINT + '/settings/v1/templates/{templateId}'.replace('{templateId}', template_id),
                        headers=headers, data=json.dumps(payload))


def get_template_by_id(auth_token, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/settings/v1/templates/{template_id}'
                        .replace('{template_id}', template_id), headers=headers)


def get_templates_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/settings/v1/templates', headers=headers)


def get_template_by_parent_id(auth_token, parent_template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {}
    return requests.get(
        ENDPOINT + f'/settings/v1/templates?searchRequest=%7B%22filter%22%3A%7B%22parentTemplateId%22%3A%7B%22in%22%3A%5B%22{parent_template_id}%22%5D%7D%7D%7D',
        headers=headers, params=payload)


def create_generic_template(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    name = f"Generic_template_{uuid.uuid4().hex}"[0:32]
    payload = json.dumps({
        "name": name,
        "displayName": name,
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
                    "referencedSideAttributeName": name,
                    "referencedSideAttributeDisplayName": name,
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            }
        ],
        "templateAttributes": [],
        "entityType": "generic-entity",
        "ownerOrganizationId": ""
    })
    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def create_generic_template_with_phi_true(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    name = f"Generic_template_phi_{uuid.uuid4().hex}"[0:32]
    payload = json.dumps({
        "name": name,
        "displayName": name,
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
                "phi": True,
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
                    "referencedSideAttributeName": name,
                    "referencedSideAttributeDisplayName": name,
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            }
        ],
        "templateAttributes": [],
        "entityType": "generic-entity",
        "ownerOrganizationId": ""
    })
    return requests.post(ENDPOINT + '/settings/v1/templates', headers=headers, data=json.dumps(payload))


def update_patient_template(auth_token, template_id, payload):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.put(ENDPOINT + '/settings/v1/templates/{templateId}'.replace('{templateId}', template_id),
                        headers=headers, data=json.dumps(payload))


def create_registration_code_template(auth_token):
    name = f"registration_code_{uuid.uuid4().hex}"[0:32]
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = json.dumps({
        "name": name,
        "displayName": name,
        "customAttributes": [],
        "builtInAttributes": [
            {
                "name": "_code",
                "basePath": None,
                "displayName": "Code",
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
                    "referencedSideAttributeName": name,
                    "referencedSideAttributeDisplayName": name,
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            }
        ],
        "templateAttributes": [],
        "entityType": "registration-code",
        "ownerOrganizationId": ""
    })
    response = requests.request("POST", ENDPOINT + "/settings/v1/templates", headers=headers, data=payload)
    return response


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
    email = f'primary_admin_{uuid.uuid4().hex}'[0:32] + '_@biotmail.com'
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
                "firstName": "Primary",
                "lastName": "Admin"
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


def get_self_organization(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/organization/v1/users/organizations/self', headers=headers)


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
    if patient_id is None:
        payload = {"_description": change_string}
    else:
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


def create_device_without_registration_code(auth_token, template_name, organization_id):
    device_id = f"device_by_manu_admin{uuid.uuid4().hex}"[0:32]
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_description": "integ_test_device",
        "_timezone": "Europe/Oslo",
        "_id": device_id,
        "_ownerOrganization": {
            "id": organization_id
        }
    }
    return requests.post(ENDPOINT + '/device/v2/devices/templates/{templateName}'
                         .replace('{templateName}', template_name), headers=headers, data=json.dumps(payload))


def update_device_without_patient(auth_token, device_id):
    change_string = f'Updated device description {uuid.uuid4().hex}'[0:32]
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_description": change_string
    }
    return requests.patch(ENDPOINT + '/device/v2/devices/{id}'.replace('{id}', device_id),
                          headers=headers, data=json.dumps(payload)), change_string


def update_device_with_new_patient(auth_token, device_id, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_patient":
            {"id": patient_id}
    }
    return requests.patch(ENDPOINT + '/device/v2/devices/{id}'.replace('{id}', device_id),
                          headers=headers, data=json.dumps(payload))


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


# creates usage session without name which is considered to be phi=true
def create_usage_session_without_name(auth_token, device_id, patient_id, usage_session_template):
    headers = {
        'accept': 'application/json', "Authorization": "Bearer " + auth_token
    }
    payload = json.dumps({
        "_patient": {
            "id": patient_id
        },
        "_startTime": "2024-02-13T00:00:53.000Z",
        "_state": "ACTIVE",
        "_endTime": None,
        "_templateId": usage_session_template
    })

    response = requests.request("POST", ENDPOINT + f"/device/v1/devices/{device_id}/usage-sessions",
                                headers=headers, data=payload)
    return response


# creates usage session name which is considered to be phi=true
def create_usage_session_with_name(auth_token, device_id, patient_id, usage_session_template):
    headers = {
        'accept': 'application/json', "Authorization": "Bearer " + auth_token
    }
    payload = json.dumps({
        "_patient": {
            "id": patient_id
        },
        "_startTime": "2024-02-13T00:00:53.000Z",
        "_state": "ACTIVE",
        "_endTime": None,
        "_name": f"Name for Usage{uuid.uuid4().hex}"[0:32],
        "_templateId": usage_session_template
    })

    response = requests.request("POST", ENDPOINT + f"/device/v1/devices/{device_id}/usage-sessions",
                                headers=headers, data=payload)
    return response


def get_usage_session(auth_token, device_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/{id}'.replace('{deviceId}', device_id)
                        .replace('{id}', session_id), headers=headers)


def get_usage_session_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/device/v1/devices/usage-sessions', data=json.dumps(query_params), headers=headers)


def get_current_usage_sessions(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    query_params = {}
    return requests.get(ENDPOINT + '/device/v1/devices/current/usage-sessions', data=json.dumps(query_params),
                        headers=headers)


def update_usage_session(auth_token, device_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = json.dumps({
        "_state": "ACTIVE"
    })
    return requests.patch(
        ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/{id}'.replace('{deviceId}', device_id)
        .replace('{id}', session_id), headers=headers, data=payload)


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


def start_usage_session_without_name(auth_token, device_id, template_id, patient_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_templateId": template_id,
        "_patient": {
            "id": patient_id
        }
    }
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/remote-control/start'
                         .replace('{deviceId}', device_id), headers=headers, data=json.dumps(payload))


def stop_usage_session(auth_token, device_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/{id}/remote-control/stop'
                         .replace('{deviceId}', device_id).replace('{id}', session_id), headers=headers)


def pause_usage_session(auth_token, device_id, session_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {}
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/usage-sessions/{id}/remote-control/pause'
                         .replace('{deviceId}', device_id).replace('{id}', session_id), headers=headers, data=payload)


def resume_usage_session(auth_token, device_id, session_id):
    payload = {}
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    response = requests.request("POST", ENDPOINT + f"/device/v1/devices/{device_id}/usage-sessions"
                                                   f"/{session_id}/remote-control/resume", headers=headers,
                                data=payload)
    return response


def get_usage_session_by_id(auth_token, device_id, usage_session_id):
    payload = {}
    headers = {
        'accept': 'application/json', "Authorization": "Bearer " + auth_token
    }

    response = requests.request("GET", ENDPOINT + f"/device/v1/devices/{device_id}/usage-sessions/{usage_session_id}",
                                headers=headers, data=payload)
    # assert response.status_code == 200
    return response


def get_observation_attribute(username, password):
    auth_token = login_with_credentials(username, password)
    headers = {
        'accept': 'application/json', "Authorization": "Bearer " + auth_token
    }
    payload = {}
    response = requests.request("GET",
                                ENDPOINT + "/settings/v1/templates?searchRequest=%7B%22filter%22%3A%7B%22entityTypeName%22%3A%7B%22in%22%3A%5B%22patient%22%5D%7D%2C%22parentTemplateId%22%3A%7B%22isNull%22%3Atrue%7D%7D%2C%22page%22%3A0%2C%22limit%22%3A10%2C%22freeTextSearch%22%3A%22%22%7D",
                                headers=headers, data=payload)
    patient_template = response.json()["data"][0]
    patient_template_id = patient_template["id"]
    get_patient_template_response = get_template_by_id(auth_token, patient_template_id)
    observation_attribute = None
    custom_attributes = get_patient_template_response.json()["customAttributes"]
    for custom_attribute in custom_attributes:
        if custom_attribute["category"]["name"] == "MEASUREMENT":
            observation_attribute = custom_attribute
            break
    return observation_attribute


def start_simulation_with_existing_device(device_id, username, password):
    observation_attribute = get_observation_attribute(username, password)
    payload = json.dumps({
        "username": username,
        "password": password,
        "simulationLength": 60,
        "shouldFailSession": False,
        "devicesIds": [
            device_id
        ],
        "chosenMeasurementsAttributes": [
            observation_attribute
        ],
        "commandConfigurationRequest": {
            "commandsLengthInSeconds": 10,
            "shouldFailCommand": False,
            "shouldFailStop": False,
            "sendStatusAttributes": True,
            "sendSummaryAttributes": True,
            "errorMessage": "string"
        }
    })
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", ENDPOINT + "/simulator/v1/simulation/withExisting/start", headers=headers,
                                data=payload)
    # assert response.status_code == 200, f"{response.text}"
    return response


def get_simulation_status():
    payload = {}
    headers = {'accept': '*/*'}
    response = requests.request("GET", ENDPOINT + "/simulator/v1/simulation/status", headers=headers, data=payload)
    return response


def stop_simulation():
    payload = {}
    headers = {'accept': '*/*'}
    response = requests.request("GET", ENDPOINT + "/simulator/v1/simulation/stop", headers=headers, data=payload)
    return response


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


# command APIs
def start_command_by_template(auth_token, device_id, template_name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = json.dumps({
        "_name": 'Reboot'
    })
    return requests.post(ENDPOINT + "/device/v1/devices/{deviceId}/commands/{templateName}/start"
                         .replace('{deviceId}', device_id)
                         .replace('{templateName}', template_name), headers=headers, data=payload)


def start_command_by_id(auth_token, device_id, template_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = json.dumps({
        "_templateId": template_id,
        "_name": 'Reboot'
    })
    return requests.post(ENDPOINT + "/device/v1/devices/{deviceId}/commands/start"
                         .replace('{deviceId}', device_id), headers=headers, data=payload)


def stop_command(auth_token, device_id, command_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.post(ENDPOINT + '/device/v1/devices/{deviceId}/commands/{id}/stop'.replace('{deviceId}', device_id)
                         .replace('{id}', command_id), headers=headers)


def get_command(auth_token, device_id, command_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/device/v1/devices/{deviceId}/commands/{id}'.replace('{deviceId}', device_id)
                        .replace('{id}', command_id), headers=headers)


def search_commands(auth_token, command_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    search_request = {
        "searchRequest": json.dumps({
            "filter": {
                "_id": {
                    "like": command_id
                },
            }
        })
    }
    return requests.get(ENDPOINT + '/device/v1/devices/commands?', params=search_request, headers=headers)


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
                                                                                                        patient_id).replace(
        '{id}', alert_id), headers=headers)


def update_patient_alert(auth_token, patient_id, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_state": "ACTIVE",
        "_severity": "MAJOR",
        "_clearNotes": None,
        "_name": "test patient alert updated",
    }
    return requests.patch(ENDPOINT + '/organization/v1/users/patients/{patientId}/alerts/{id}'.replace('{patientId}',
                                                                                                       patient_id).replace(
        '{id}', alert_id), data=json.dumps(payload), headers=headers)


def get_patient_alert_list(auth_token, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    if alert_id is None:
        search_request = {}
    else:
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


def get_current_patient_alert_list(auth_token, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    search_request = {
        "searchRequest": json.dumps({
            "filter": {
                "_ownerOrganization.id": {
                    "eq": organization_id
                },
            }
        })
    }
    return requests.get(ENDPOINT + '/organization/v1/users/patients/current/alerts?', params=search_request,
                        headers=headers)


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
                                                                                          device_id).replace('{id}',
                                                                                                             alert_id),
                           headers=headers)


def update_device_alert(auth_token, device_id, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "_state": "ACTIVE",
        "_severity": "MAJOR",
        "_clearNotes": None,
        "_name": "test device alert updated",
    }
    return requests.patch(ENDPOINT + '/device/v1/devices/{deviceId}/alerts/{id}'.replace('{deviceId}',
                                                                                         device_id).replace('{id}',
                                                                                                            alert_id),
                          data=json.dumps(payload), headers=headers)


def get_device_alert(auth_token, device_id, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/device/v1/devices/{deviceId}/alerts/{id}'
                        .replace('{deviceId}', device_id).replace('{id}', alert_id), headers=headers)


def get_device_alert_list(auth_token, alert_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    if alert_id is None:
        search_request = {}
    else:
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


def get_current_device_alert_list(auth_token, organization_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    search_request = {
        "searchRequest": json.dumps({
            "filter": {
                "_ownerOrganization.id": {
                    "eq": organization_id
                },
            }
        })
    }
    return requests.get(ENDPOINT + '/device/v1/devices/current/alerts?', params=search_request, headers=headers)


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


# Get entities APIs ################################################################################################
def get_entities(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/settings/v2/entity-types', headers=headers)


# plugin APIs   ##############################################################################################
def create_plugin(auth_token, name):
    headers = {
        "Authorization": "Bearer " + auth_token
    }
    config_payload = {
        "name": name,
        "displayName": name,
        "version": 1,
        "runtime": "python3.10",
        "handler": "index.handler",
        "timeout": 900,
        "memorySize": 128,
        "environmentVariables": {
            "key": 'value'
        },
        "subscriptions": {
            "interceptionOrder": 1,
            "interceptions": [
                {
                    "type": "PRE_REQUEST",
                    "apiId": "string",
                    "entityTypeName": "generic-entity",
                    "order": 0
                }
            ],
            "notifications": [
                {
                    "entityTypeName": "generic-entity",
                    "actionName": "_create"
                }
            ]
        },
        "enabledState": "DISABLED",
        "endpointUrl": "string",
        "linkToConsole": "string",
        "lastModifiedTime": "2007-12-20T10:15:30Z",
        "creationTime": "2007-12-20T10:15:30Z"
    }
    deploy_payload = {
        'code': None,
        'configuration': json.dumps(config_payload)
    }
    return requests.post(ENDPOINT + '/settings/v2/plugins', files=deploy_payload, headers=headers)


def get_plugin(auth_token, name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/settings/v2/plugins/{name}'.replace('{name}', name), headers=headers)


def get_plugin_list(auth_token, name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    search_request = {
        "searchRequest": json.dumps({
            "filter": {
                "_ownerOrganization.id": {
                    "like": name
                },
            }
        })
    }
    return requests.get(ENDPOINT + '/settings/v2/plugins?', params=search_request, headers=headers)


def update_plugin(auth_token, name):
    headers = {
        "Authorization": "Bearer " + auth_token
    }
    config_payload = {
        "name": name,
        "displayName": name,
        "version": 1,
        "runtime": "python3.10",
        "handler": "index.handler",
        "timeout": 900,
        "memorySize": 128,
        "environmentVariables": {
            "key": 'value'
        },
        "subscriptions": {
            "interceptionOrder": 1,
            "interceptions": [
                {
                    "type": "PRE_REQUEST",
                    "apiId": "string",
                    "entityTypeName": "generic-entity",
                    "order": 0
                }
            ],
            "notifications": [
                {
                    "entityTypeName": "generic-entity",
                    "actionName": "_create"
                }
            ]
        },
        "enabledState": "DISABLED",
        "endpointUrl": "string",
        "linkToConsole": "string",
        "lastModifiedTime": "2007-12-20T10:15:30Z",
        "creationTime": "2007-12-20T10:15:30Z"
    }
    deploy_payload = {
        'code': None,
        'configuration': json.dumps(config_payload)
    }
    return requests.patch(ENDPOINT + '/settings/v2/plugins/{name}'.replace('{name}', name),
                          files=deploy_payload, headers=headers)


def delete_plugin(auth_token, name):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/settings/v2/plugins/{name}'.replace('{name}', name), headers=headers)


# DMS APIs  ##########################################################################################
def create_report(auth_token, output_metadata, queries):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {
        "queries": queries,
        "outputMetadata": output_metadata,
        "name": "BioT Devices Export"
    }
    return requests.post(ENDPOINT + '/dms/v1/data/reports/export', headers=headers, data=json.dumps(payload))


def delete_report(auth_token, report_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.delete(ENDPOINT + '/dms/v1/data/reports/{id}'.replace('{id}', report_id), headers=headers)


def get_report(auth_token, report_id):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    return requests.get(ENDPOINT + '/dms/v1/data/reports/{id}'.replace('{id}', report_id), headers=headers)


def get_report_list(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    payload = {

    }
    return requests.get(ENDPOINT + '/dms/v1/data/reports', headers=headers, data=json.dumps(payload))


# self signup APIs ##################################################################################
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
def get_generic_entity_template_payload(test_display_name, test_name, test_referenced_attrib_name,
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
                "name": "_bootTime",
                "basePath": "_status",
                "displayName": "Boot Time",
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
                "name": "_certificateStatus",
                "basePath": "_status",
                "displayName": "Certificate Status",
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
                "name": "_connected",
                "basePath": "_status._connection",
                "displayName": "Connected",
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
                "name": "_description",
                "basePath": None,
                "displayName": "Description",
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
                "name": "_fwVersion",
                "basePath": "_status",
                "displayName": "FW Version",
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
                "name": "_hwVersion",
                "basePath": "_status",
                "displayName": "HW Version",
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
                "name": "_ipAddress",
                "basePath": "_status._connection",
                "displayName": "IP Address",
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
                "name": "_lastConnectedTime",
                "basePath": "_status._connection",
                "displayName": "Last Connected Time",
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
                "name": "_message",
                "basePath": "_status._operational",
                "displayName": "Operational Message",
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
                "name": "_status",
                "basePath": "_status._operational",
                "displayName": "Operational Status",
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
            {
                "name": "_timezone",
                "basePath": None,
                "displayName": "Time Zone",
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
                "name": "_id",
                "basePath": None,
                "displayName": "Unique ID",
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
            }
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


def get_command_template_payload(test_display_name, test_name, test_referenced_attrib_name,
                                 test_reference_attrib_display_name, organization_id, entity_type,
                                 parent_template_id):
    referencedSideAttributeName = f'Template Device{uuid.uuid4()}'[0:30]
    command_to_device = f'Test command{uuid.uuid4()}'[0:30]
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
                    "referencedSideAttributeName": command_to_device,
                    "referencedSideAttributeDisplayName": command_to_device,
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
        ],
        "templateAttributes": [
            {
                "name": "_supportStop",
                "basePath": None,
                "displayName": 'Support Stop command',
                "phi": False,
                "referenceConfiguration": None,
                "value": True,
                "organizationSelectionConfiguration": None
            }
        ],
        "entityType": entity_type,
        "ownerOrganizationId": organization_id,
        "parentTemplateId": parent_template_id
    }


def create_caregiver_template(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    name = f"test_caregiver{uuid.uuid4().hex}"[0:35]
    payload = json.dumps({
        "name": name,
        "displayName": name,
        "customAttributes": [],
        "builtInAttributes": [
            {
                "name": "_address",
                "basePath": None,
                "displayName": "Address",
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
                "name": "_dateOfBirth",
                "basePath": None,
                "displayName": "Date of Birth",
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
                "name": "_degree",
                "basePath": None,
                "displayName": "Degree",
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
                "name": "_description",
                "basePath": None,
                "displayName": "Description",
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
                "name": "_email",
                "basePath": None,
                "displayName": "Email",
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
                "name": "_employeeId",
                "basePath": None,
                "displayName": "Employee ID",
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
                "name": "_enabled",
                "basePath": None,
                "displayName": "Enabled",
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
                "name": "_gender",
                "basePath": None,
                "displayName": "Gender",
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
                "name": "_locale",
                "basePath": None,
                "displayName": "Locale",
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
                "name": "enabled",
                "basePath": "_mfa",
                "displayName": "Login Using MFA",
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
                "name": "expirationInMinutes",
                "basePath": "_mfa",
                "displayName": "MFA Expiration Period",
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
                    "referencedSideAttributeName": f"{name} Caregivers",
                    "referencedSideAttributeDisplayName": f"{name} Caregivers",
                    "validTemplatesToReference": [],
                    "entityType": "organization"
                }
            },
            {
                "name": "_phone",
                "basePath": None,
                "displayName": "Phone",
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
        "templateAttributes": [],
        "entityType": "caregiver",
        "ownerOrganizationId": ""
    })
    response = requests.request("POST", ENDPOINT + "/settings/v1/templates", headers=headers, data=payload)
    # assert response.status_code == 201, f"{response.text}"
    # return response.json()["name"], response.json()["id"]
    return response


def create_org_user_template(auth_token):
    headers = {"content-type": "application/json", "Authorization": "Bearer " + auth_token}
    name = f"org_user{uuid.uuid4().hex}"[0:35]
    payload = json.dumps(
        {
            "name": name,
            "displayName": name,
            "customAttributes": [],
            "builtInAttributes": [
                {
                    "name": "_address",
                    "basePath": None,
                    "displayName": "Address",
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
                    "name": "_dateOfBirth",
                    "basePath": None,
                    "displayName": "Date of Birth",
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
                    "name": "_description",
                    "basePath": None,
                    "displayName": "Description",
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
                    "name": "_email",
                    "basePath": None,
                    "displayName": "Email",
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
                    "name": "_employeeId",
                    "basePath": None,
                    "displayName": "Employee ID",
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
                    "name": "_enabled",
                    "basePath": None,
                    "displayName": "Enabled",
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
                    "name": "_gender",
                    "basePath": None,
                    "displayName": "Gender",
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
                    "name": "_locale",
                    "basePath": None,
                    "displayName": "Locale",
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
                    "name": "enabled",
                    "basePath": "_mfa",
                    "displayName": "Login Using MFA",
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
                    "name": "expirationInMinutes",
                    "basePath": "_mfa",
                    "displayName": "MFA Expiration Period",
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
                        "referencedSideAttributeName": f"{name} Organizational Users",
                        "referencedSideAttributeDisplayName": f"{name} Organizational Users",
                        "validTemplatesToReference": [],
                        "entityType": "organization"
                    }
                },
                {
                    "name": "_phone",
                    "basePath": None,
                    "displayName": "Phone",
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
            "templateAttributes": [],
            "entityType": "organization-user",
            "ownerOrganizationId": ""
        })
    response = requests.request("POST", ENDPOINT + "/settings/v1/templates", headers=headers, data=payload)
    # assert response.status_code == 201, f"{response.text}"
    # return response.json()["name"], response.json()["id"]
    return response


def create_device_template_with_session(auth_token):
    name_device = f'device_templ_{uuid.uuid4().hex}'[0:32]
    name_usage = f'session_templ_{uuid.uuid4().hex}'[0:32]

    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': "Bearer " + auth_token}

    payload = json.dumps({
        "name": name_device,
        "displayName": name_device,
        "customAttributes": [],
        "builtInAttributes": [
            {
                "name": "_bootTime",
                "basePath": "_status",
                "displayName": "Boot Time",
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
                "name": "_certificateStatus",
                "basePath": "_status",
                "displayName": "Certificate Status",
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
                "name": "_connected",
                "basePath": "_status._connection",
                "displayName": "Connected",
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
                "name": "_description",
                "basePath": None,
                "displayName": "Description",
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
                "name": "_fwVersion",
                "basePath": "_status",
                "displayName": "FW Version",
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
                "name": "_hwVersion",
                "basePath": "_status",
                "displayName": "HW Version",
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
                "name": "_ipAddress",
                "basePath": "_status._connection",
                "displayName": "IP Address",
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
                "name": "_lastConnectedTime",
                "basePath": "_status._connection",
                "displayName": "Last Connected Time",
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
                "name": "_message",
                "basePath": "_status._operational",
                "displayName": "Operational Message",
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
                "name": "_status",
                "basePath": "_status._operational",
                "displayName": "Operational Status",
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
                    "mandatory": True,
                    "min": None,
                    "max": None,
                    "regex": None,
                    "defaultValue": None
                },
                "numericMetaData": None,
                "referenceConfiguration": {
                    "uniquely": False,
                    "referencedSideAttributeName": f"{name_device} Devices",
                    "referencedSideAttributeDisplayName": f"{name_device} Devices",
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
                    "referencedSideAttributeName": f"{name_device} Device",
                    "referencedSideAttributeDisplayName": f"{name_device} Device",
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
                    "referencedSideAttributeName": f"{name_device} Registration Code Devices",
                    "referencedSideAttributeDisplayName": f"{name_device} Registration Code Devices",
                    "validTemplatesToReference": [],
                    "entityType": "registration-code"
                }
            },
            {
                "name": "_timezone",
                "basePath": None,
                "displayName": "Time Zone",
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
                "name": "_id",
                "basePath": None,
                "displayName": "Unique ID",
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
            }
        ],
        "templateAttributes": [],
        "entityType": "device",
        "ownerOrganizationId": ""
    })

    response_device_template = requests.request("POST", ENDPOINT + '/settings/v1/templates', headers=headers,
                                                data=payload)
    assert response_device_template.status_code == 201, f"{response_device_template.status_code}, " \
                                                        f"{response_device_template.text}"
    device_template_id = response_device_template.json()["id"]
    payload_usage = json.dumps({
        "name": name_usage,
        "displayName": name_usage,
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
                    "referencedSideAttributeName": f"{name_usage} Usage Sessions to Device",
                    "referencedSideAttributeDisplayName": f"{name_usage} Usage Sessions to Device",
                    "validTemplatesToReference": [
                        device_template_id
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
                "phi": True,
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
                    "referencedSideAttributeName": f"{name_usage} Usage Sessions to Organization",
                    "referencedSideAttributeDisplayName": f"{name_usage} Usage Sessions to Organization",
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
                    "referencedSideAttributeName": f"{name_usage} Usage Sessions to Patient",
                    "referencedSideAttributeDisplayName": f"{name_usage} Usage Sessions to Patient",
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
        "entityType": "usage-session",
        "ownerOrganizationId": "",
        "parentTemplateId": device_template_id
    })

    response_usage_session_template = requests.request("POST", ENDPOINT + '/settings/v1/templates', headers=headers,
                                                       data=payload_usage)
    assert response_usage_session_template.status_code == 201, f"{response_usage_session_template.status_code}, " \
                                                               f"{response_usage_session_template.text}"
    return response_device_template
