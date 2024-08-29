from API_drivers import *
from api_test_helpers import *


def main():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    get_minimized_response = get_all_templates(admin_auth_token)
    assert get_minimized_response.status_code == 200, f"{get_minimized_response.text}"
    for record in get_minimized_response.json()['data']:
        if record['entityTypeName'] == 'device':
            device_template_name = record['name']
            break

    patient1_auth_token, patient1_id, registration_code1_id, device1_id = create_single_patient_self_signup(
        admin_auth_token, "00000000-0000-0000-0000-000000000000", device_template_name)

    get_patient_response = get_patient(admin_auth_token, patient1_id)
    assert get_patient_response.status_code == 200, f"{get_patient_response.text}"

    template_id = get_patient_response.json()['_template']['id']
    get_template_response = get_template(admin_auth_token, template_id)
    assert get_template_response.status_code == 200, f"{get_template_response.text}"
    template_payload = map_template(get_template_response.json())

    # clean up validation errors
    for element in template_payload['builtInAttributes']:
        if element['referenceConfiguration'] is not None:
            if (element['referenceConfiguration']['referencedSideAttributeName'] !=
                    element['referenceConfiguration']['referencedSideAttributeDisplayName']):
                element['referenceConfiguration']['referencedSideAttributeDisplayName'] = (
                    element)['referenceConfiguration']['referencedSideAttributeName']

    for element in template_payload['customAttributes']:
        if element['referenceConfiguration'] is not None:
            if (element['referenceConfiguration']['referencedSideAttributeName'] !=
                    element['referenceConfiguration']['referencedSideAttributeDisplayName']):
                element['referenceConfiguration']['referencedSideAttributeDisplayName'] = (
                    element)['referenceConfiguration']['referencedSideAttributeName']

    for element in template_payload['customAttributes']:
        if element['referenceConfiguration'] is not None:
            if element['type'] != 'MULTI_SELECT' and element['type'] != 'SINGLE_SELECT':
                del element['selectableValues']
        if element['name'] == 'customtimezone':
            del element['selectableValues']

    # add phi to template
    phi_object = {
        "name": "test_phi_object",
        "id": str(uuid.uuid4()),
        "basePath": None,
        "displayName": "test_phi_object",
        "phi": True,
        "type": "LABEL",
        "validation": {
            "mandatory": True,
            "min": None,
            "max": None,
            "regex": None,
            "defaultValue": "test_phi_object"
        },
        "numericMetaData": None,
        "referenceConfiguration": None
    }
    (template_payload['customAttributes']).append(phi_object)

    update_template_response = update_template(admin_auth_token, template_id, template_payload)
    assert update_template_response.status_code == 200

    # and check
    get_template_response = get_template(admin_auth_token, template_id)
    assert get_template_response.status_code == 200, f"{get_template_response.text}"
    # revert
    template_payload = map_template(get_template_response.json())
    index = 0
    for element in template_payload['customAttributes']:
        if element['name'] == "test_phi_object":
            del template_payload['customAttributes'][index]
            continue
        else:
            index += 1
    update_template_response = update_template(admin_auth_token, template_id, template_payload)
    assert update_template_response.status_code == 200

    # and check
    get_template_response = get_template(admin_auth_token, template_id)
    assert get_template_response.status_code == 200, f"{get_template_response.text}"

    # teardown
    single_self_signup_patient_teardown(admin_auth_token, patient1_id, registration_code1_id, device1_id)


if __name__ == "__main__":
    main()
