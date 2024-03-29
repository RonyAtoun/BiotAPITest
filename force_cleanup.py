import os

from API_drivers import *


#############################################################################################
# Username and password have to be set in the environment in advance
#############################################################################################

def force_cleanup():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    get_device_alert_list_response = get_device_alert_list(admin_auth_token, None)
    assert get_device_alert_list_response.status_code == 200
    for alert in get_device_alert_list_response.json()['data']:
        if 'test' in alert['_name'] and 'device' in alert:
            print("deviceAlertId", alert['_id'])
            device_id = alert['_device']['id']
            delete_alert_response = delete_device_alert(admin_auth_token, device_id, alert['_id'])
            assert delete_alert_response.status_code == 204

    get_patient_alert_list_response = get_patient_alert_list(admin_auth_token, None)
    assert get_patient_alert_list_response.status_code == 200
    if get_patient_alert_list_response.json()['data'] is not None:
        for alert in get_patient_alert_list_response.json()['data']:
            if alert['_name'] is not None and 'test' in alert['_name'] and 'patient' in alert:
                print("patientAlertId", alert['_id'])
                patient_id = alert['_patient']['id']
                delete_alert_response = delete_patient_alert(admin_auth_token, patient_id, alert['_id'])
                assert delete_alert_response.status_code == 204

    get_device_list_response = get_device_list(admin_auth_token)
    assert get_device_list_response.status_code == 200
    for device in get_device_list_response.json()['data']:
        print("deviceId", device['_id'])
        if 'test' in device['_id'] or 'device_by_manu_admin' in device['_id'] or '343' in device['_id']:
            delete_device_response = delete_device(admin_auth_token, device['_id'])
            assert delete_device_response.status_code == 204
    get_patient_list_response = get_patient_list(admin_auth_token)
    assert get_patient_list_response.status_code == 200
    for patient in get_patient_list_response.json()['data']:
        if "test" in patient['_name']['firstName']:
            print("patient", patient['_name'])
            patient_delete_response = delete_patient(admin_auth_token, patient['_id'])
            assert patient_delete_response.status_code == 204
    get_caregiver_list_response = get_caregiver_list(admin_auth_token)
    assert get_caregiver_list_response.status_code == 200
    for caregiver in get_caregiver_list_response.json()['data']:
        if "test" in caregiver['_name']['firstName']:
            print("caregiver", caregiver['_name'])
            caregiver_delete_response = delete_caregiver(admin_auth_token, caregiver['_id'])
            assert caregiver_delete_response.status_code == 204

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

    stop_simulation()

if __name__ == "__main__":
    force_cleanup()
