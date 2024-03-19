import uuid
from API_drivers import *
from email_interface import accept_invitation


def self_signup_patient_setup(admin_auth_token, organization_id, device_template_name):
    # create two patients, registration codes and devices
    patient_id = []
    email = []
    device_id = []
    registration_code = []
    registration_code_id = []
    for n in range(2):
        test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                     "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
        email.append(f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com')
        template_name = "RegistrationCode"
        create_registration_code_response = create_registration_code(admin_auth_token, template_name,
                                                                     str(uuid.uuid4()), organization_id)
        assert create_registration_code_response.status_code == 201, f"{create_registration_code_response.text}"
        registration_code.append(create_registration_code_response.json()['_code'])
        registration_code_id.append(create_registration_code_response.json()['_id'])
        # device_template_name = 'DeviceType1'
        device_id.append(f'test_{uuid.uuid4().hex}'[0:16])
        create_device_response = create_device(admin_auth_token, device_template_name, device_id[n],
                                               registration_code_id[n], organization_id)
        assert create_device_response.status_code == 201, f"{create_device_response.text}"
        self_signup_response = identified_self_signup_with_registration_code(admin_auth_token, test_name, email[n],
                                                                             registration_code[n], organization_id)
        assert self_signup_response.status_code == 201, f"{self_signup_response.text}"
        patient_id.append(self_signup_response.json()['patient']['_id'])

    # login with one of the two patients
    patient_auth_token = login_with_credentials(email[0], "Q2207819w@")
    return {
        'patient_id': patient_id,
        'email': email,
        'device_id': device_id,
        'registration_code': registration_code,
        'registration_code_id': registration_code_id,
        'patient_auth_token': patient_auth_token
    }


def self_signup_patient_teardown(admin_auth_token, patient_setup):
    patient_id = patient_setup['patient_id']
    device_id = patient_setup['device_id']
    registration_code_id = patient_setup['registration_code_id']
    # Teardown
    for n in range(2):
        delete_patient_response = delete_patient(admin_auth_token, patient_id[n])
        assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
        delete_device_response = delete_device(admin_auth_token, device_id[n])
        assert delete_device_response.status_code == 204, f"{delete_device_response.text}"
        delete_registration_response = delete_registration_code(admin_auth_token, registration_code_id[n])
        assert delete_registration_response.status_code == 204, f"{delete_registration_response.text}"


def create_single_patient_self_signup(admin_auth_token, organization_id, device_template_name):
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    template_name = "RegistrationCode"
    create_registration_code_response = create_registration_code(admin_auth_token, template_name,
                                                                 str(uuid.uuid4()), organization_id)
    assert create_registration_code_response.status_code == 201, f"{create_registration_code_response.text}"
    registration_code = create_registration_code_response.json()['_code']
    registration_code_id = create_registration_code_response.json()['_id']
    device_id = f'test_{uuid.uuid4().hex}'[0:16]
    create_device_response = create_device(admin_auth_token, device_template_name, device_id,
                                           registration_code_id, organization_id)
    assert create_device_response.status_code == 201, f"{create_device_response.text}"
    self_signup_response = identified_self_signup_with_registration_code(admin_auth_token, test_name, email,
                                                                         registration_code, organization_id)
    assert self_signup_response.status_code == 201, f"{self_signup_response.text}"
    patient_id = self_signup_response.json()['patient']['_id']

    # login
    patient_auth_token = login_with_credentials(email, "Q2207819w@")
    return patient_auth_token, patient_id, registration_code_id, device_id


def single_self_signup_patient_teardown(admin_auth_token, patient_id, registration_code_id, device_id):
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_device_response = delete_device(admin_auth_token, device_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"
    delete_registration_response = delete_registration_code(admin_auth_token, registration_code_id)
    assert delete_registration_response.status_code == 204, f"{delete_registration_response.text}"


def create_template_setup(auth_token, organization_id, entity_type, parent_template_id):
    test_display_name = f'test_templ_{uuid.uuid4().hex}'[0:35]
    test_name = f'rony_test_{uuid.uuid4().hex}'[0:35]
    test_referenced_attrib_name = f'my built in attribute_{uuid.uuid4().hex}'[0:35]
    test_reference_attrib_display_name = test_referenced_attrib_name
    if entity_type == "generic-entity":
        create_template_response = create_generic_entity_template(auth_token, test_display_name, test_name,
                                                                  test_referenced_attrib_name,
                                                                  test_reference_attrib_display_name, organization_id)
    elif entity_type == "device":
        create_template_response = create_device_template(auth_token, test_display_name, test_name,
                                                          test_referenced_attrib_name,
                                                          test_reference_attrib_display_name, organization_id,
                                                          entity_type, None)
    elif entity_type == "usage-session":
        create_template_response = create_usage_session_template(auth_token, test_display_name, test_name,
                                                                 test_referenced_attrib_name,
                                                                 test_reference_attrib_display_name, organization_id,
                                                                 entity_type, parent_template_id)
    elif entity_type == "command":
        create_template_response = create_command_template(auth_token, test_display_name, test_name,
                                                           test_referenced_attrib_name,
                                                           test_reference_attrib_display_name, organization_id,
                                                           entity_type, parent_template_id)

    elif entity_type == "patient-alert" or entity_type == "device-alert":
        create_template_response = create_alert_template(auth_token, test_display_name, test_name,
                                                         test_referenced_attrib_name,
                                                         test_reference_attrib_display_name, organization_id,
                                                         entity_type, parent_template_id)
    else:
        create_template_response = None

    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    return (create_template_response.json()['id'], create_template_response.json()['name'],
            create_template_response.json()['displayName'])


def update_patient_template_with_file_entity(auth_token, patient_id, file_name):
    append_data = {
        "name": file_name,
        "type": "FILE",
        "displayName": file_name,
        "phi": False,
        "validation": {
            "mandatory": False,
            "max": 20971520,
            "defaultValue": None
        },
        "selectableValues": [],
        "category": "REGULAR",
        "numericMetaData": None,
        "referenceConfiguration": None,
        "linkConfiguration": None
    }
    get_patient_response = get_patient(auth_token, patient_id)
    assert get_patient_response.status_code == 200, f"{get_patient_response.text}"
    patient_payload = get_patient_response.json()
    template_id = get_patient_response.json()['_template']['id']
    get_template_response = get_template(auth_token, template_id)
    assert get_template_response.status_code == 200, f"{get_template_response.text}"
    # add the file element
    template_attributes = get_template_response.json()['templateAttributes']
    template_attributes[0]['organizationSelectionConfiguration'] = {
        "selected": [],
        "all": True
    }
    del template_attributes[0]['organizationSelection']
    del template_attributes[0]['name']
    del template_attributes[0]['basePath']
    del template_attributes[0]['validation']
    del template_attributes[0]['category']
    del template_attributes[0]['selectableValues']
    del template_attributes[0]['numericMetaData']
    del template_attributes[0]['typeEnum']

    payload = {
        "displayName": get_template_response.json()['displayName'],
        "name": get_template_response.json()['name'],
        "description": get_template_response.json()['description'],
        "ownerOrganizationId": get_template_response.json()['ownerOrganizationId'],
        "forceUpdate": True,
        "customAttributes": get_template_response.json()['customAttributes'],
        "builtInAttributes": [],  # get_template_response.json()['builtInAttributes'],
        "templateAttributes": [],  # template_attributes,
    }
    # payload['customAttributes'].append(append_data)

    update_template_response = update_patient_template(auth_token, template_id, payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    return template_id, patient_payload


def create_single_patient(auth_token):
    # create a patient
    # get the Patient template name
    template_list_response = get_all_templates(auth_token)
    assert template_list_response.status_code == 200, f"{template_list_response.text}"
    patient_template_name = None
    for template in template_list_response.json()['data']:
        if "Patient" == template['name']:
            patient_template_name = template['name']
            break

    # create a patient user
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'

    create_patient_response = create_patient(auth_token, test_name, email, patient_template_name,
                                             "00000000-0000-0000-0000-000000000000")
    assert create_patient_response.status_code == 201, f"{create_patient_response.text}"
    patient_id = create_patient_response.json()['_id']

    response_text, accept_invitation_response = accept_invitation(email)
    password = accept_invitation_response.json()['operationData']['password']
    # login
    patient_auth_token = login_with_credentials(email, password)
    return patient_auth_token, patient_id


def check_simulator_status():
    simulation_status_response = get_simulation_status()
    while 'code' not in simulation_status_response.json():
        simulation_status_response = get_simulation_status()
    return simulation_status_response.json()["code"]
