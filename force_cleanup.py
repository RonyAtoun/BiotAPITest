import os

from dotenv import load_dotenv, find_dotenv

from API_drivers import (
    login_with_credentials,
    get_patient_list, delete_patient,
    delete_device, get_device_list,
    delete_organization,
    delete_generic_entity, get_generic_entity_list,
    get_organization_list)


#############################################################################################
# Username and password have to be set in the environment in advance
#############################################################################################

def force_cleanup():
    #load_dotenv()
    #print(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
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
            delete_organization_response = delete_organization(admin_auth_token, org['_id'])
            assert delete_organization_response.status_code == 204


if __name__ == "__main__":
    force_cleanup()
