import uuid
import os
from helpers import (login_with_with_credentials, create_registration_code, delete_registration_code, create_device,
                     identified_self_signup_with_registration_code, anonymous_self_signup_with_registration_code,
                     delete_patient, get_device, delete_device, create_organization, delete_organization,
                     update_organization, get_organization, get_organization_list)

user_name = os.getenv('USERNAME')  # Has to be set in the environment in advance
pass_word = os.getenv('PASSWORD')
admin_auth_token = login_with_with_credentials(user_name, pass_word)


def test_patient_organization_abac_rules():
    # create organization
    template_id = "2aaa71cf-8a10-4253-9576-6fd160a85b2d"
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # create patient, registration and device
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    template_name = "RegistrationCode"
    create_registration_code_response = create_registration_code(admin_auth_token, template_name, str(uuid.uuid4()))
    assert create_registration_code_response.status_code == 201
    registration_code = create_registration_code_response.json()['_code']
    registration_code_id = create_registration_code_response.json()['_id']
    device_template_name = 'DeviceType1'
    device_id = f'test_{uuid.uuid4().hex}'[0:16]
    create_device_response_code = create_device(admin_auth_token, device_template_name, device_id, registration_code_id)
    assert create_device_response_code.status_code == 201
    self_signup_response_code = identified_self_signup_with_registration_code(admin_auth_token, test_name, email,
                                                                              registration_code, organization_id)
    assert self_signup_response_code.status_code == 201
    patient_id = self_signup_response_code.json()['patient']['_id']
    patient_auth_token = login_with_with_credentials(email, "Ab12z456")

    # create, update and delete organization must fail
    create_organization_response = create_organization(patient_auth_token, template_id)
    assert create_organization_response.status_code == 403
    delete_organization_response = delete_organization(patient_auth_token, organization_id)
    assert delete_organization_response.status_code == 403
    update_organization_response = update_organization(patient_auth_token, organization_id, "changed test text")
    assert update_organization_response.status_code == 403

    # Get organization by list or by id -- only for own organization
    get_organization_response = get_organization(patient_auth_token, organization_id)
    # positive (own organization)
    assert get_organization_response.status_code == 200
    # negative
    get_organization_response = get_organization(patient_auth_token, "00000000-0000-0000-0000-000000000000")
    assert get_organization_response.status_code == 403
    # positive (own organization)
    get_organization_list_response = get_organization_list(patient_auth_token, organization_id)
    assert get_organization_list_response.status_code == 200
    # negative
    get_organization_list_response = get_organization_list(patient_auth_token, "00000000-0000-0000-0000-000000000000")
    #assert get_organization_list_response.status_code == 403

    # Teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204
    delete_device_response_code = delete_device(admin_auth_token, device_id)
    assert delete_device_response_code.status_code == 204
    delete_registration_response = delete_registration_code(admin_auth_token, registration_code_id)
    assert delete_registration_response.status_code == 204
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


def test_patient_patient_abac_rules():
    # create two patients, registration codes and devices
    patient_id = []
    email = []
    device_id = []
    registration_code = []
    registration_code_id = []
    for n in range(2):
        test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                     "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
        tmp = (f'integ_test_{uuid.uuid4().hex}'[0:16])
        email.append(tmp + '_@biotmail.com')
        template_name = "RegistrationCode"
        create_registration_code_response = create_registration_code(admin_auth_token, template_name, str(uuid.uuid4()))
        assert create_registration_code_response.status_code == 201
        registration_code.append(create_registration_code_response.json()['_code'])
        registration_code_id.append(create_registration_code_response.json()['_id'])
        device_template_name = 'DeviceType1'
        device_id.append(f'test_{uuid.uuid4().hex}'[0:16])
        create_device_response_code = create_device(admin_auth_token, device_template_name, device_id[n],
                                                    registration_code_id[n])
        assert create_device_response_code.status_code == 201
        self_signup_response_code = identified_self_signup_with_registration_code(admin_auth_token, test_name, email[n],
                                                    registration_code[n], "00000000-0000-0000-0000-000000000000")
        assert self_signup_response_code.status_code == 201
        patient_id.append(self_signup_response_code.json()['patient']['_id'])

    # login with one of the two patients
    patient_auth_token = login_with_with_credentials(email[0], "Ab12z456")
    # Create and delete patient should fail

    # Teardown
    for n in range(2):
        delete_patient_response = delete_patient(admin_auth_token, patient_id[n])
        assert delete_patient_response.status_code == 204
        delete_device_response_code = delete_device(admin_auth_token, device_id[n])
        assert delete_device_response_code.status_code == 204
        delete_registration_response = delete_registration_code(admin_auth_token, registration_code_id[n])
        assert delete_registration_response.status_code == 204
