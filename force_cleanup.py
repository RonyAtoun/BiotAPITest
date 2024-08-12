import os
from API_drivers import *
from dotenv import load_dotenv
from api_test_helpers import map_template

load_dotenv()


#############################################################################################
# Username and password have to be set in the environment in advance
#############################################################################################

def force_cleanup():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    get_registration_code_list_response = get_registration_code_list(admin_auth_token)
    assert get_registration_code_list_response.status_code == 200
    for reg_code in get_registration_code_list_response.json()['data']:
        print(f"reg_code_id: {reg_code['_id']}")
        delete_reg_response = delete_registration_code(admin_auth_token, reg_code['_id'])
        assert delete_reg_response.status_code == 204
    get_org_users_list_response = get_organization_user_list(admin_auth_token)
    assert get_org_users_list_response.status_code == 200
    for user in get_org_users_list_response.json()['data']:
        if 'test' in user['_name']['firstName']:
            print(f"org user name: {user['_name']}")
            delete_org_user_response = delete_organization_user(admin_auth_token, user['_id'])
            #assert delete_org_user_response.status_code == 204

    get_device_alert_list_response = get_device_alert_list(admin_auth_token, None)
    if os.getenv('ENDPOINT') == 'https://api.staging.biot-gen2.biot-med.com':
        assert get_device_alert_list_response.status_code == 200
        for alert in get_device_alert_list_response.json()['data']:
            if 'test' in alert['_name'] and 'device' in alert:
                print("deviceAlertId", alert['_id'])
                device_id = alert['_device']['id']
                delete_alert_response = delete_device_alert(admin_auth_token, device_id, alert['_id'])
                #assert delete_alert_response.status_code == 204

        get_patient_alert_list_response = get_patient_alert_list(admin_auth_token, None)
        assert get_patient_alert_list_response.status_code == 200
        if get_patient_alert_list_response.json()['data'] is not None:
            for alert in get_patient_alert_list_response.json()['data']:
                if alert['_name'] is not None and 'test' in alert['_name'] and 'patient' in alert:
                    print("patientAlertId", alert['_id'])
                    patient_id = alert['_patient']['id']
                    delete_alert_response = delete_patient_alert(admin_auth_token, patient_id, alert['_id'])
                    #assert delete_alert_response.status_code == 204

    get_device_list_response = get_device_list(admin_auth_token)
    assert get_device_list_response.status_code == 200
    for device in get_device_list_response.json()['data']:
        if 'test' in device['_id'] or 'device_by_manu_admin' in device['_id'] or '343' in device['_id']:
            delete_device_response = delete_device(admin_auth_token, device['_id'])
            #assert delete_device_response.status_code == 204
            print("deviceId", device['_id'])
    get_patient_list_response = get_patient_list(admin_auth_token)
    assert get_patient_list_response.status_code == 200
    for patient in get_patient_list_response.json()['data']:
        if '_name' in patient and "test" in patient['_name']['firstName']:
            print("patient", patient['_name'])
            patient_delete_response = delete_patient(admin_auth_token, patient['_id'])
            #assert patient_delete_response.status_code == 204
    get_caregiver_list_response = get_caregiver_list(admin_auth_token)
    assert get_caregiver_list_response.status_code == 200
    for caregiver in get_caregiver_list_response.json()['data']:
        if "test" in caregiver['_name']['firstName']:
            print("caregiver", caregiver['_name'])
            caregiver_delete_response = delete_caregiver(admin_auth_token, caregiver['_id'])
            #assert caregiver_delete_response.status_code == 204

    get_organization_list_response = get_organization_list(admin_auth_token)
    assert get_organization_list_response.status_code == 200

    for org in get_organization_list_response.json()['data']:
        if "Test Org_" in org['_name']:
            print(org['_name'], org['_id'])
            get_generic_entity_list_response = get_generic_entity_list(admin_auth_token)
            assert get_generic_entity_list_response.status_code == 200
            for generic_entity in get_generic_entity_list_response.json()['data']:
                print('generic entity', generic_entity['_id'])
                delete_generic_entity_response = delete_generic_entity(admin_auth_token, generic_entity['_id'])
                #assert delete_generic_entity_response.status_code == 204
            delete_organization_response = delete_organization(admin_auth_token, org['_id'])
            #assert delete_organization_response.status_code == 204
    template_list_response = get_all_templates(admin_auth_token)
    assert template_list_response.status_code == 200
    for template in template_list_response.json()['data']:
        if "test" in template['name']:
            delete_template_response = delete_template(admin_auth_token, template['id'])
            if delete_template_response.status_code == 204:
                print("Template", template['name'])
            else:
                print("Failed to delete template in use", template['name'])

    # revert changes in Patient Template
    patient_template_id = "a38f32d7-de6c-4252-9061-9bcdc253f6c9"
    get_template_response = get_template(admin_auth_token, patient_template_id)
    template_payload = map_template(get_template_response.json())
    index = 0
    for element in template_payload['customAttributes']:
        if "test_integ_dec_int" in element['name']:
            del template_payload['customAttributes'][index]
            print(f'Attribute removed {element["name"]}')
            continue
        elif "test_integ_waveform" in element['name']:
            del template_payload['customAttributes'][index]
            print(f'Attribute removed {element["name"]}')
            continue
        elif "file_attr_integ_test" in element['name']:
            del template_payload['customAttributes'][index]
            print(f'Attribute removed {element["name"]}')
            continue
        elif "test_phi_object_patient" in element['name']:
            del template_payload['customAttributes'][index]
            print(f'Attribute removed {element["name"]}')
            continue
        else:
            index += 1
    update_template_response = update_template(admin_auth_token, patient_template_id, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    stop_simulation()


if __name__ == "__main__":
    force_cleanup()
