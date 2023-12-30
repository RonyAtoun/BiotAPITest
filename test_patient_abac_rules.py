import uuid
import os

from helpers import (login_with_with_credentials, create_registration_code, delete_registration_code, create_device,
                     identified_self_signup_with_registration_code, delete_patient, get_device, delete_device,
                     create_organization, delete_organization, create_organization_user, delete_organization_user,
                     update_organization_user, change_organization_user_state, get_organization_user, get_organization_user_list,
                     update_organization, get_organization, get_organization_list, create_patient, update_patient,
                     get_patient, get_patient_list, change_patient_state, create_caregiver, update_caregiver,
                     delete_caregiver, change_caregiver_state, get_caregiver, get_caregiver_list, resend_invitation)


#############################################################################################
# Username and password have to be set in the environment in advance for each individual test
#############################################################################################


def test_patient_organization_abac_rules():
    admin_auth_token = login_with_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    template_id = "2aaa71cf-8a10-4253-9576-6fd160a85b2d"
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # create patient, registration and device
    patient_setup = self_signup_patient_setup(admin_auth_token, organization_id)
    patient_auth_token = patient_setup['patient_auth_token']

    # create, update  and delete organization must fail
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
    # positive (own organization should return one result)
    get_organization_list_response = get_organization_list(patient_auth_token)
    assert get_organization_list_response.status_code == 200
    assert get_organization_list_response.json()['metadata']['page']['totalResults'] == 1
    # negative (system admin should get all defined organizations)
    get_organization_list_response = get_organization_list(admin_auth_token)
    assert get_organization_list_response.status_code == 200
    assert get_organization_list_response.json()['metadata']['page']['totalResults'] > 1

    # Teardown
    self_signup_patient_teardown(admin_auth_token, patient_setup)
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


def test_patient_organization_users_abac_rules():
    admin_auth_token = login_with_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization user
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    template_name = "OrganizationOperator"
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    employee_id = f'test_{uuid.uuid4().hex}'[0:35]
    create_user_response = create_organization_user(admin_auth_token, template_name, name, email, employee_id)
    assert create_user_response.status_code == 201
    organization_user_id = create_user_response.json()['_id']

    # create patient, registration and device
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000")
    patient_auth_token = patient_setup['patient_auth_token']

    # create organization user by patient should fail
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    template_name = "OrganizationOperator"
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    employee_id = f'test_{uuid.uuid4().hex}'[0:35]
    create_user_response = create_organization_user(patient_auth_token, template_name, name, email, employee_id)
    assert create_user_response.status_code == 403

    # delete organization user by patient should fail
    delete_user_response = delete_organization_user(patient_auth_token, organization_user_id)
    assert delete_user_response.status_code == 403

    # update organization user should fail
    update_organization_user_response = update_organization_user(patient_auth_token, organization_user_id,
                                             "00000000-0000-0000-0000-000000000000", "change string")
    assert update_organization_user_response.status_code == 403

    # get organization user by patient should fail
    get_organization_user_response = get_organization_user(patient_auth_token, organization_user_id)
    assert get_organization_user_response.status_code == 403

    # search organization list by patient should fail
    search_organization_users_response = get_organization_user_list(patient_auth_token)
    assert search_organization_users_response.status_code == 403

    # change state of organization user by patient should fail
    change_organization_user_state_response = change_organization_user_state(patient_auth_token, patient_auth_token,
                                                                             "ENABLED")
    assert change_organization_user_state_response.status_code == 403

    # resend invitation to organization user by patient should fail
    resend_invitation_response = resend_invitation(patient_auth_token, organization_user_id)
    assert resend_invitation_response.status_code == 403

    # teardown
    self_signup_patient_teardown(admin_auth_token, patient_setup)
    delete_user_response = delete_organization_user(admin_auth_token, organization_user_id)
    assert delete_user_response.status_code == 204


def test_patient_patient_abac_rules():
    admin_auth_token = login_with_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create two patients, registration codes and devices
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000")
    patient_id = patient_setup['patient_id']
    patient_auth_token = patient_setup['patient_auth_token']

    # Create and delete patient should fail
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    # create patient
    test_patient_create_response = create_patient(patient_auth_token, test_name, email, "Patient",
                                                  "00000000-0000-0000-0000-000000000000")
    assert test_patient_create_response.status_code == 403
    # delete patient (use second patient created)
    test_patient_delete_response = delete_patient(patient_auth_token, patient_id[1])
    assert test_patient_delete_response.status_code == 403

    # update patient only for self
    update_patient_response = update_patient(patient_auth_token, patient_id[0], "00000000-0000-0000-0000-000000000000",
                                             "change string", None)
    assert update_patient_response.status_code == 200
    # should fail for other patient
    update_patient_response = update_patient(patient_auth_token, patient_id[1],
                                             "00000000-0000-0000-0000-000000000000",
                                             "change string", None)
    assert update_patient_response.status_code == 403

    # get patient only for self
    get_patient_response = get_patient(patient_auth_token, patient_id[0])  # self
    assert get_patient_response.status_code == 200
    get_patient_response = get_patient(patient_auth_token, patient_id[1])  # other patient
    assert get_patient_response.status_code == 403

    # search patient only for self
    # Positive - for self
    get_patient_list_response = get_patient_list(patient_auth_token)
    assert get_patient_list_response.status_code == 200
    assert get_patient_list_response.json()['metadata']['page']['totalResults'] == 1
    # negative (system admin should get all defined patients)
    get_patient_list_response = get_patient_list(admin_auth_token)
    assert get_patient_list_response.status_code == 200
    assert get_patient_list_response.json()['metadata']['page']['totalResults'] > 1

    # enable/disable should fail
    change_patient_state_response = change_patient_state(patient_auth_token, patient_id[0], "ENABLED")
    assert change_patient_state_response.status_code == 403

    # resend invitation fails
    resend_invitation_response = resend_invitation(patient_auth_token, patient_id[0])
    assert resend_invitation_response.status_code == 403

    # Teardown
    self_signup_patient_teardown(admin_auth_token, patient_setup)


def test_patient_caregiver_abac_rules():
    admin_auth_token = login_with_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create two patients, registration codes and devices
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000")
    patient_id = patient_setup['patient_id']
    patient_auth_token = patient_setup['patient_auth_token']  # logged in with first of two emails created
    patient_email = patient_setup['email']

    # create caregiver by admin
    caregiver_email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    create_caregiver_response = create_caregiver(admin_auth_token, test_name, caregiver_email, "Clinician",
                                                 "00000000-0000-0000-0000-000000000000")
    assert create_caregiver_response.status_code == 201
    caregiver_id = create_caregiver_response.json()['_id']

    # associate first of two patients setup with caregiver
    update_patient_response = update_patient(admin_auth_token, patient_id[0],
                                             "00000000-0000-0000-0000-000000000000", "change string",
                                             caregiver_id)
    assert update_patient_response.status_code == 200

    # create caregiver by patient should fail
    caregiver_email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    create_caregiver_response = create_caregiver(patient_auth_token, test_name, caregiver_email, "Clinician",
                                                 "00000000-0000-0000-0000-000000000000")
    assert create_caregiver_response.status_code == 403

    # update caregiver by patient should fail
    update_caregiver_response = update_caregiver(patient_auth_token, caregiver_id,
                                                 "00000000-0000-0000-0000-000000000000", "change string")
    assert update_caregiver_response.status_code == 403

    # delete caregiver by patient should fail
    delete_caregiver_response = delete_caregiver(patient_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 403

    # change caregiver state by patient should fail
    change_caregiver_state_response = change_caregiver_state(patient_auth_token, caregiver_id, "ENABLED")
    assert change_caregiver_state_response.status_code == 403

    # get caregiver by patient only for self
    get_caregiver_response = get_caregiver(patient_auth_token, caregiver_id)
    assert get_caregiver_response.status_code == 200
    # login with the second patient who is not associated with caregiver
    patient2_auth_token = login_with_with_credentials(patient_email[1], "Ab12z456")
    # get should now fail
    get_caregiver_response = get_caregiver(patient2_auth_token, caregiver_id)
    assert get_caregiver_response.status_code == 403

    # search caregiver by patient only for self
    # Positive - for self
    get_caregiver_list_response = get_caregiver_list(patient_auth_token)
    assert get_caregiver_list_response.status_code == 200
    assert get_caregiver_list_response.json()['metadata']['page']['totalResults'] == 1
    # negative (system admin should get all defined patients)
    get_caregiver_list_response = get_caregiver_list(admin_auth_token)
    assert get_caregiver_list_response.status_code == 200
    assert get_caregiver_list_response.json()['metadata']['page']['totalResults'] > 1

    # resend invitation fails
    resend_invitation_response = resend_invitation(patient_auth_token, caregiver_id)
    assert resend_invitation_response.status_code == 403

    # Teardown
    self_signup_patient_teardown(admin_auth_token, patient_setup)
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204


def self_signup_patient_setup(admin_auth_token, organization_id):
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
        create_registration_code_response = create_registration_code(admin_auth_token, template_name, str(uuid.uuid4()))
        assert create_registration_code_response.status_code == 201
        registration_code.append(create_registration_code_response.json()['_code'])
        registration_code_id.append(create_registration_code_response.json()['_id'])
        device_template_name = 'DeviceType1'
        device_id.append(f'test_{uuid.uuid4().hex}'[0:16])
        create_device_response = create_device(admin_auth_token, device_template_name, device_id[n],
                                               registration_code_id[n])
        assert create_device_response.status_code == 201
        self_signup_response = identified_self_signup_with_registration_code(admin_auth_token, test_name, email[n],
                                                                             registration_code[n], organization_id)
        assert self_signup_response.status_code == 201
        patient_id.append(self_signup_response.json()['patient']['_id'])

    # login with one of the two patients
    patient_auth_token = login_with_with_credentials(email[0], "Ab12z456")
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
