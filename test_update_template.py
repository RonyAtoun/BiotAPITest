from API_drivers import *
from api_test_helpers import *


def main():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    patient1_auth_token, patient1_id, registration_code1_id, device1_id = create_single_patient_self_signup(
        admin_auth_token, "00000000-0000-0000-0000-000000000000", 'DeviceType1')

    get_patient_response = get_patient(admin_auth_token, patient1_id)
    assert get_patient_response.status_code == 200, f"{get_patient_response.text}"

    template_id = get_patient_response.json()['_template']['id']
    get_template_response = get_template(admin_auth_token, template_id)
    assert get_template_response.status_code == 200, f"{get_template_response.text}"
    template_payload = map_template(get_template_response.json())
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


if __name__ == "__main__":
    main()
