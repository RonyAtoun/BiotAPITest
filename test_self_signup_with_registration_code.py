import uuid
import os
from helpers import (login_with_with_credentials, create_registration_code, delete_registration_code, create_device,
                     identified_self_signup_with_registration_code, anonymous_self_signup_with_registration_code,
                     delete_patient, get_device, delete_device)


def test_identified_self_signup():
    organization_id = "00000000-0000-0000-0000-000000000000"
    auth_token = login_with_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    template_name = "RegistrationCode"
    create_registration_code_response = create_registration_code(auth_token, template_name, str(uuid.uuid4()), organization_id)
    assert create_registration_code_response.status_code == 201
    registration_code = create_registration_code_response.json()['_code']
    registration_code_id = create_registration_code_response.json()['_id']
    device_template_name = 'DeviceType1'
    device_id = f'test_{uuid.uuid4().hex}'[0:16]
    create_device_response_code = create_device(auth_token, device_template_name, device_id, registration_code_id, organization_id)
    assert create_device_response_code.status_code == 201
    self_signup_response_code = identified_self_signup_with_registration_code(auth_token, test_name, email,
                                                                              registration_code,
                                                                              "00000000-0000-0000-0000-000000000000")
    assert self_signup_response_code.status_code == 201
    patient_id = self_signup_response_code.json()['patient']['_id']
    get_device_response_code = get_device(auth_token, device_id)
    assert get_device_response_code.status_code == 200
    assert get_device_response_code.json()['_patient']['id'] == patient_id
    assert get_device_response_code.json()['_registrationCode']['id'] == registration_code_id

    # Teardown
    delete_patient_response = delete_patient(auth_token, patient_id)
    assert delete_patient_response.status_code == 204
    delete_device_response_code = delete_device(auth_token, device_id)
    assert delete_device_response_code.status_code == 204
    delete_registration_response = delete_registration_code(auth_token, registration_code_id)
    assert delete_registration_response.status_code == 204


def test_anonymous_self_signup():
    organization_id = "00000000-0000-0000-0000-000000000000"
    auth_token = login_with_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    nick_name = f'nickname_test_{uuid.uuid4().hex}'[0:35]
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    template_name = "RegistrationCode"
    create_registration_code_response = create_registration_code(auth_token, template_name, str(uuid.uuid4()), organization_id)
    assert create_registration_code_response.status_code == 201
    registration_code = create_registration_code_response.json()['_code']
    registration_code_id = create_registration_code_response.json()['_id']
    device_template_name = 'DeviceType1'
    device_id = f'test_{uuid.uuid4().hex}'[0:16]
    create_device_response_code = create_device(auth_token, device_template_name, device_id, registration_code_id, organization_id)
    assert create_device_response_code.status_code == 201
    self_signup_response_code = anonymous_self_signup_with_registration_code(auth_token, nick_name, email,
                                                                             registration_code)
    assert self_signup_response_code.status_code == 201
    patient_id = self_signup_response_code.json()['patient']['_id']
    get_device_response_code = get_device(auth_token, device_id)
    assert get_device_response_code.status_code == 200
    assert get_device_response_code.json()['_patient']['id'] == patient_id
    assert get_device_response_code.json()['_registrationCode']['id'] == registration_code_id

    # Teardown
    delete_patient_response = delete_patient(auth_token, patient_id)
    assert delete_patient_response.status_code == 204
    delete_device_response_code = delete_device(auth_token, device_id)
    assert delete_device_response_code.status_code == 204
    delete_registration_response = delete_registration_code(auth_token, registration_code_id)
    assert delete_registration_response.status_code == 204
