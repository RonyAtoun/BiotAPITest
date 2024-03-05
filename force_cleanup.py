import os

from API_drivers import (
    login_with_credentials,
    get_patient_list, delete_patient,
    delete_device, get_device_list, get_device_alert_list, get_current_device_alert_list, delete_device_alert,
    delete_organization,
    delete_generic_entity, get_generic_entity_list,
    get_organization_list, get_all_templates, delete_template)


#############################################################################################
# Username and password have to be set in the environment in advance
#############################################################################################

def force_cleanup():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # get_device_alert_list_response = get_device_alert_list(admin_auth_token, "any")

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
    template_list_response = get_all_templates(admin_auth_token)
    assert template_list_response.status_code == 200
    for template in template_list_response.json()['data']:
        if "test" in template['name']:
            delete_template_response = delete_template(admin_auth_token, template['id'])
            if delete_template_response.status_code == 204:
                print("Template", template['name'])
            else:
                print("Failed to delete template in use", template['name'])


if __name__ == "__main__":
    force_cleanup()
