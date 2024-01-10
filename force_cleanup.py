import os

import pytest

from API_drivers import (
    login_with_with_credentials,
    create_registration_code, update_registration_code, delete_registration_code, get_registration_code,
    get_registration_code_list,
    identified_self_signup_with_registration_code,
    create_patient, update_patient, get_patient, get_patient_list, change_patient_state,
    delete_patient,
    create_device, get_device, delete_device, update_device, get_device_list,
    create_organization_template, create_device_template, delete_template,
    create_organization, delete_organization,
    create_organization_user, delete_organization_user, update_organization_user,
    change_organization_user_state, get_organization_user, get_organization_user_list,
    create_generic_entity, delete_generic_entity, update_generic_entity, get_generic_entity,
    get_generic_entity_list,
    update_organization, get_organization, get_organization_list,
    create_caregiver, update_caregiver, delete_caregiver, change_caregiver_state, get_caregiver,
    get_caregiver_list, resend_invitation)


#############################################################################################
# Username and password have to be set in the environment in advance
#############################################################################################

def cleanup_generic_entities():
    admin_auth_token = login_with_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    get_organization_list_response = get_organization_list(admin_auth_token)
    assert get_organization_list_response.status_code == 200
    for org in get_organization_list_response.json()['data']:
        if "Test Org_" in org['_name']:
            print(org['_name'], org['_id'])
            get_generic_entity_list_response = get_generic_entity_list(admin_auth_token)
            assert get_generic_entity_list_response.status_code == 200
            for generic_entity in get_generic_entity_list_response.json()['data']:
                print('generic entity', generic_entity['_name'])
                delete_generic_entity_response = delete_generic_entity(admin_auth_token, generic_entity['_id'])
                assert delete_generic_entity_response.status_code == 204

    get_device_list_response = get_device_list(admin_auth_token)
    assert get_device_list_response.status_code == 200
    for device in get_device_list_response.json()['data']:
        print("deviceId", device['_id'])
        if 'test' in device['_id']:
            delete_device_response = delete_device(admin_auth_token, device['_id'])
            assert delete_device_response.status_code == 204
    get_patient_list_response = get_patient_list(admin_auth_token)
    assert get_patient_list_response.status_code == 200
    for patient in get_patient_list_response.json()['data']:
        if "test" in patient['_name']['firstName']:
            print("patient", patient['_name'])
            patient_delete_response = delete_patient(admin_auth_token, patient['_id'])
            assert patient_delete_response.status_code == 204


if __name__ == "__main__":
    cleanup_generic_entities()
