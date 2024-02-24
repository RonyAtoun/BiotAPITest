import uuid
from API_drivers import (
    login_with_credentials,
    create_registration_code, delete_registration_code,
    identified_self_signup_with_registration_code,
    get_patient, delete_patient,
    create_device, delete_device,
    create_generic_entity_template, create_device_template, create_patient_template, create_alert_template,
    create_usage_session_template, get_template,
    update_patient_template)


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
        assert create_registration_code_response.status_code == 201
        registration_code.append(create_registration_code_response.json()['_code'])
        registration_code_id.append(create_registration_code_response.json()['_id'])
        # device_template_name = 'DeviceType1'
        device_id.append(f'test_{uuid.uuid4().hex}'[0:16])
        create_device_response = create_device(admin_auth_token, device_template_name, device_id[n],
                                               registration_code_id[n], organization_id)
        assert create_device_response.status_code == 201
        self_signup_response = identified_self_signup_with_registration_code(admin_auth_token, test_name, email[n],
                                                                             registration_code[n], organization_id)
        assert self_signup_response.status_code == 201
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
        assert delete_patient_response.status_code == 204
        delete_device_response = delete_device(admin_auth_token, device_id[n])
        assert delete_device_response.status_code == 204
        delete_registration_response = delete_registration_code(admin_auth_token, registration_code_id[n])
        assert delete_registration_response.status_code == 204


def create_single_patient_self_signup(admin_auth_token, organization_id, device_template_name):
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    template_name = "RegistrationCode"
    create_registration_code_response = create_registration_code(admin_auth_token, template_name,
                                                                 str(uuid.uuid4()), organization_id)
    assert create_registration_code_response.status_code == 201
    registration_code = create_registration_code_response.json()['_code']
    registration_code_id = create_registration_code_response.json()['_id']
    device_id = f'test_{uuid.uuid4().hex}'[0:16]
    create_device_response = create_device(admin_auth_token, device_template_name, device_id,
                                           registration_code_id, organization_id)
    assert create_device_response.status_code == 201
    self_signup_response = identified_self_signup_with_registration_code(admin_auth_token, test_name, email,
                                                                         registration_code, organization_id)
    assert self_signup_response.status_code == 201
    patient_id = self_signup_response.json()['patient']['_id']

    # login
    patient_auth_token = login_with_credentials(email, "Q2207819w@")
    return patient_auth_token, patient_id, registration_code_id, device_id


def single_self_signup_patient_teardown(admin_auth_token, patient_id, registration_code_id, device_id):
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204
    delete_device_response = delete_device(admin_auth_token, device_id)
    assert delete_device_response.status_code == 204
    delete_registration_response = delete_registration_code(admin_auth_token, registration_code_id)
    assert delete_registration_response.status_code == 204


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
    elif entity_type == "patient":
        create_template_response = create_patient_template(auth_token, test_display_name, test_name, organization_id,
                                                           entity_type)
    elif entity_type == "patient-alert" or entity_type == "device-alert":
        create_template_response = create_alert_template(auth_token, test_display_name, test_name,
                                                         test_referenced_attrib_name,
                                                         test_reference_attrib_display_name, organization_id,
                                                         entity_type, parent_template_id)
    else:
        create_template_response = None

    assert create_template_response.status_code == 201
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
    assert get_patient_response.status_code == 200
    patient_payload = get_patient_response.json()
    template_id = get_patient_response.json()['_template']['id']
    get_template_response = get_template(auth_token, template_id)
    assert get_template_response.status_code == 200
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
    assert update_template_response.status_code == 200

    return template_id, patient_payload
