import pytest
from dotenv import load_dotenv
import requests
import uuid
import os

from API_drivers import (
    login_with_credentials,
    create_registration_code, update_registration_code, delete_registration_code, get_registration_code,
    get_registration_code_list,
    identified_self_signup_with_registration_code,
    create_patient, update_patient, get_patient, get_patient_list, change_patient_state,
    delete_patient,
    create_device, get_device, delete_device, update_device, get_device_list, get_device_credentials,
    create_usage_session_by_usage_type, delete_usage_session, update_usage_session, get_usage_session,
    get_usage_session_list, start_usage_session, stop_usage_session, pause_usage_session, resume_usage_session,
    create_measurement, create_bulk_measurement, get_raw_measurements, get_aggregated_measurements,
    get_v2_aggregated_measurements, get_v2_raw_measurements,
    create_organization_template, create_device_template, create_patient_template, delete_template,
    create_usage_session_template, get_template,
    update_template, update_patient_template,
    create_organization, delete_organization,
    create_organization_user, delete_organization_user, update_organization_user,
    change_organization_user_state, get_organization_user, get_organization_user_list,
    create_generic_entity, delete_generic_entity, update_generic_entity, get_generic_entity,
    get_generic_entity_list,
    update_organization, get_organization, get_organization_list,
    create_caregiver, update_caregiver, delete_caregiver, change_caregiver_state, get_caregiver,
    get_caregiver_list, resend_invitation,
    create_file, get_file)
from api_test_helpers import (
    self_signup_patient_setup, self_signup_patient_teardown, single_self_signup_patient_teardown,
    create_single_patient_self_signup, create_template_setup
)


#############################################################################################
# Username and password have to be set in the environment in advance for each individual test
#############################################################################################

def test_patient_organization_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    template_id = "2aaa71cf-8a10-4253-9576-6fd160a85b2d"  # default organization template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create device template in new organization
    device_template = create_template_setup(admin_auth_token, organization_id, "device", None)
    device_template_name = device_template[1]
    device_template_id = device_template[0]

    # create patient, registration and device
    patient_setup = self_signup_patient_setup(admin_auth_token, organization_id, device_template_name)
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
    delete_template_response = delete_template(admin_auth_token, device_template_id)
    assert delete_template_response.status_code == 204


def test_patient_organization_users_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
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
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                              'DeviceType1')
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
                                                                 "00000000-0000-0000-0000-000000000000",
                                                                 "change string")
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
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create two patients, registration codes and devices
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                              'DeviceType1')
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
                                             "change string", None, None)
    assert update_patient_response.status_code == 200
    # should fail for other patient
    update_patient_response = update_patient(patient_auth_token, patient_id[1],
                                             "00000000-0000-0000-0000-000000000000",
                                             "change string", None, None)
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
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create two patients, registration codes and devices
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                              'DeviceType1')
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
                                             caregiver_id, None)
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
    patient2_auth_token = login_with_credentials(patient_email[1], "Q2207819w@")
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


def test_patient_devices_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create two patients, registration codes and devices
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                              'DeviceType1')
    device_id = patient_setup['device_id']
    registration_code_id = patient_setup['registration_code_id']
    patient_auth_token = patient_setup['patient_auth_token']
    patient_email = patient_setup['email']

    # create device by patient fails
    create_device_response = create_device(patient_auth_token, 'DeviceType1', device_id[0],
                                           registration_code_id[0], "00000000-0000-0000-0000-000000000000")
    assert create_device_response.status_code == 403

    # update device by patient fails
    update_device_response = update_device(patient_auth_token, device_id[0], "change_string", None)
    assert update_device_response.status_code == 403

    # delete device by patient fails
    delete_device_response = delete_device(patient_auth_token, device_id[0])
    assert delete_device_response.status_code == 403

    # get device succeeds for self, fails for other (use patient[0] for self, patient[1] for other
    get_device_response = get_device(patient_auth_token, device_id[0])
    assert get_device_response.status_code == 200
    patient2_auth_token = login_with_credentials(patient_email[1], "Q2207819w@")
    get_device_response = get_device(patient2_auth_token, device_id[0])
    assert get_device_response.status_code == 403

    # search device by patient only for self
    # Positive - for self
    get_device_list_response = get_device_list(patient_auth_token)
    assert get_device_list_response.status_code == 200
    assert get_device_list_response.json()['metadata']['page']['totalResults'] == 1
    # negative (system admin should get all defined patients)
    get_device_list_response = get_device_list(admin_auth_token)
    assert get_device_list_response.status_code == 200
    assert get_device_list_response.json()['metadata']['page']['totalResults'] > 1

    # Teardown
    self_signup_patient_teardown(admin_auth_token, patient_setup)


# @pytest.mark.skip
def test_patient_generic_entity_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create two patients, registration codes and devices (use only one)
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                              'DeviceType1')
    patient_auth_token = patient_setup['patient_auth_token']
    # create organization
    template_id = "2aaa71cf-8a10-4253-9576-6fd160a85b2d"  # default organization template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # create generic entity template in both organizations
    generic_entity_template_id = create_template_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                                       "organization", None)[0]
    generic_entity_template_id2 = create_template_setup(admin_auth_token, organization_id,
                                                        "organization", None)[0]
    # NOTE: function returns tuple. First element is id

    # create generic entity by patient only for self organization
    create_generic_entity_response = create_generic_entity(patient_auth_token, generic_entity_template_id,
                                                           f'generic_entity_{uuid.uuid4().hex}'[0:31],
                                                           "00000000-0000-0000-0000-000000000000")
    assert create_generic_entity_response.status_code == 201
    entity_id = create_generic_entity_response.json()["_id"]

    # create should fail for other organization
    create_generic_entity_response = create_generic_entity(patient_auth_token, generic_entity_template_id,
                                                           f'generic_entity_{uuid.uuid4().hex}'[0:31], organization_id)
    assert create_generic_entity_response.status_code == 403

    # update generic entity by patient only for self organization
    # create second generic entity by admin on second organization
    create_generic_entity_response2 = create_generic_entity(admin_auth_token, generic_entity_template_id2,
                                                            f'generic_entity_{uuid.uuid4().hex}'[0:31], organization_id)
    assert create_generic_entity_response2.status_code == 201

    entity2_id = create_generic_entity_response2.json()["_id"]

    # positive - same organization
    update_generic_entity_response = update_generic_entity(patient_auth_token, entity_id, "change string")
    assert update_generic_entity_response.status_code == 200
    # Negative - second organization
    update_generic_entity_response = update_generic_entity(patient_auth_token, entity2_id, "change string")
    assert update_generic_entity_response.status_code == 403

    # get only for same organization
    get_generic_entity_response = get_generic_entity(patient_auth_token, entity_id)
    assert get_generic_entity_response.status_code == 200
    get_generic_entity_response = get_generic_entity(patient_auth_token, entity2_id)
    assert get_generic_entity_response.status_code == 403  ### getting 200

    # search only for same organization
    get_generic_entity_list_response = get_generic_entity_list(patient_auth_token)
    assert get_generic_entity_list_response.status_code == 200
    assert get_generic_entity_list_response.json()['metadata']['page']['totalResults'] == 1  ### getting all users
    # negative (system admin should get all defined patients)
    get_generic_entity_list_response = get_generic_entity_list(admin_auth_token)
    assert get_generic_entity_list_response.status_code == 200
    assert get_generic_entity_list_response.json()['metadata']['page']['totalResults'] > 1

    # delete only for same organization
    delete_generic_entity_response = delete_generic_entity(patient_auth_token, entity_id)
    assert delete_generic_entity_response.status_code == 204
    # should fail for generic entity in other organization
    delete_generic_entity_response = delete_generic_entity(patient_auth_token, entity2_id)
    assert delete_generic_entity_response.status_code == 403  ### getting 204

    # Teardown
    self_signup_patient_teardown(admin_auth_token, patient_setup)
    # delete second generic entity created
    delete_generic_entity_response = delete_generic_entity(admin_auth_token, entity2_id)
    assert delete_generic_entity_response.status_code == 204
    # delete generic entity templates
    delete_generic_entity_template_response = delete_template(admin_auth_token, generic_entity_template_id)
    assert delete_generic_entity_template_response.status_code == 204
    delete_generic_entity_template_response = delete_template(admin_auth_token, generic_entity_template_id2)
    assert delete_generic_entity_template_response.status_code == 204
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_patient_registration_codes_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # Setup
    # create patients, registration codes and devices in default organization
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                              'DeviceType1')
    patient_auth_token = patient_setup['patient_auth_token']

    # first create new organization
    template_id = "2aaa71cf-8a10-4253-9576-6fd160a85b2d"  # This is the template id of the organization template in the console
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # create registration code by patient in same (default) organization should succeed
    registration_code1 = str(uuid.uuid4())
    create_registration_code1_response = create_registration_code(patient_auth_token, "RegistrationCode",
                                                                  registration_code1,
                                                                  "00000000-0000-0000-0000-000000000000")
    assert create_registration_code1_response.status_code == 201
    registration_code1_id = create_registration_code1_response.json()['_id']

    # create registration code by patient of different organization should fail
    registration_code2 = str(uuid.uuid4())
    create_registration_code2_response = create_registration_code(patient_auth_token, "RegistrationCode",
                                                                  registration_code2, organization_id)
    assert create_registration_code2_response.status_code == 403

    # create a registration code by admin in second organization for negative update tests
    create_registration_code2_response = create_registration_code(admin_auth_token, "RegistrationCode",
                                                                  registration_code2, organization_id)
    assert create_registration_code2_response.status_code == 201
    registration_code2_id = create_registration_code2_response.json()['_id']

    # update registration code should succeed in same organization (code1 - using same code)
    update_registration_code_response = update_registration_code(patient_auth_token, registration_code1_id,
                                                                 str(uuid.uuid4()))
    assert update_registration_code_response.status_code == 200

    # update registration code (code1) by patient of default organization in other organization should fail
    update_registration_code_response = update_registration_code(patient_auth_token, registration_code2_id,
                                                                 str(uuid.uuid4()))
    assert update_registration_code_response.status_code == 403

    # get in same org should succeed
    get_registration_code_response = get_registration_code(patient_auth_token, registration_code1_id)
    assert get_registration_code_response.status_code == 200

    # get in different org should fail
    get_registration_code_response = get_registration_code(patient_auth_token, registration_code2_id)
    assert get_registration_code_response.status_code == 403

    # search in same org should succeed
    get_registration_code_list_response = get_registration_code_list(patient_auth_token)
    assert get_registration_code_list_response.status_code == 200
    # search in second org is not possible as I need an organization without any reg codes and I can't do it with self signup

    # delete in same org should succeed
    delete_registration_response = delete_registration_code(patient_auth_token, registration_code1_id)
    assert delete_registration_response.status_code == 204

    # delete in different org should fail
    delete_registration_response = delete_registration_code(patient_auth_token, registration_code2_id)
    assert delete_registration_response.status_code == 403

    # Teardown
    self_signup_patient_teardown(admin_auth_token, patient_setup)
    # delete registration code of second organization
    delete_registration_response = delete_registration_code(admin_auth_token, registration_code2_id)
    assert delete_registration_response.status_code == 204
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_patient_files_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    template_id = "2aaa71cf-8a10-4253-9576-6fd160a85b2d"  # This is the template id of the organization template in the console
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create patient in new org
    patient1_auth_token, patient1_id, registration_code1_id, device1_id = create_single_patient_self_signup(
        admin_auth_token, organization_id, 'DeviceType1')
    # create patient in default org
    patient2_auth_token, patient2_id, registration_code2_id, device2_id = create_single_patient_self_signup(
        admin_auth_token, "00000000-0000-0000-0000-000000000000", 'DeviceType1')

    # create files in new organization and default , associate the files to patients
    name = f'test_file{uuid.uuid4().hex}'[0:16]
    mime_type = 'text/plain'
    data = open('./upload-file.txt', 'rb').read()
    create_file_response = create_file(patient1_auth_token, name, mime_type)
    assert create_file_response.status_code == 200
    file1_id = create_file_response.json()['id']
    signed_url = create_file_response.json()['signedUrl']
    upload_response = requests.put(signed_url, data=data, headers={'Content-Type': 'text/plain'})
    assert upload_response.status_code == 200
    create_file2_response = create_file(patient2_auth_token, name, mime_type)
    assert create_file2_response.status_code == 200
    file2_id = create_file2_response.json()['id']
    signed_url2 = create_file2_response.json()['signedUrl']
    upload_response = requests.put(signed_url2, data=data, headers={'Content-Type': 'text/plain'})
    assert upload_response.status_code == 200
    # associate files to patients
    update_patient_response = update_patient(admin_auth_token, patient1_id, organization_id, None, None,
                                             {"uploadFile": {"id": file1_id}})
    assert update_patient_response.status_code == 200
    update_patient_response = update_patient(admin_auth_token, patient2_id, "00000000-0000-0000-0000-000000000000",
                                             None, None,
                                             {"uploadFile": {"id": file2_id}})
    assert update_patient_response.status_code == 200
    # get should succeed only in self organization
    get_file_response = get_file(patient1_auth_token, file1_id)  # should succeed
    assert get_file_response.status_code == 200
    get_file_response = get_file(patient1_auth_token, file2_id)  # should fail
    assert get_file_response.status_code == 403

    # teardown
    single_self_signup_patient_teardown(admin_auth_token, patient1_id, registration_code1_id, device1_id)
    single_self_signup_patient_teardown(admin_auth_token, patient2_id, registration_code2_id, device2_id)
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_patient_usage_session_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # Setup
    # create patients, registration codes and devices in default organization
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                              'DeviceType1')
    email = patient_setup['email']
    patient_id = patient_setup['patient_id'][0]
    patient_auth_token = patient_setup['patient_auth_token']
    patient2_auth_token = login_with_credentials(email[1], "Q2207819w@")
    device_id = patient_setup['device_id'][0]
    device2_id = patient_setup['device_id'][1]
    # associate patient with device
    update_device_response = update_device(admin_auth_token, device_id, "change_string", patient_id)
    assert update_device_response.status_code == 200
    # get the device templateId
    get_device_response = get_device(admin_auth_token, device_id)
    device_template_id = get_device_response.json()['_template']['id']
    # create usage_session template
    usage_template_data = create_template_setup(admin_auth_token, None,
                                                "usage_session", device_template_id)
    usage_session_template_name = usage_template_data[1]
    usage_session_template_id = usage_template_data[0]

    # create session should succeed for self
    create_session_response = create_usage_session_by_usage_type(patient_auth_token, device_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 201
    usage_session_id = create_session_response.json()['_id']
    # create session should fail for other user
    create_session_response = create_usage_session_by_usage_type(patient2_auth_token, device_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 403

    # update session should succeed for self and fail for other
    update_session_response = update_usage_session(patient_auth_token, device_id, usage_session_id, "DONE")
    assert update_session_response.status_code == 200
    update_session_response = update_usage_session(patient2_auth_token, device_id, usage_session_id, "DONE")
    assert update_session_response.status_code == 403

    # get session should succeed only for self
    get_session_response = get_usage_session(patient_auth_token, device_id, usage_session_id)
    assert get_session_response.status_code == 200
    get_session_response = get_usage_session(patient2_auth_token, device_id, usage_session_id)
    assert get_session_response.status_code == 403

    # search usage session by patient only for self
    # Positive - for self
    get_session_list_response = get_usage_session_list(patient_auth_token)
    assert get_session_list_response.status_code == 200
    assert get_session_list_response.json()['metadata']['page']['totalResults'] == 1
    # negative: other patient should get zero results
    get_session_list_response = get_usage_session_list(patient2_auth_token)
    assert get_session_list_response.status_code == 200
    assert get_session_list_response.json()['metadata']['page']['totalResults'] == 0

    # delete session by patient should always fail
    delete_session_response = delete_usage_session(patient_auth_token, device_id, usage_session_id)
    assert delete_session_response.status_code == 403

    # start session only for self device (use second device)
    #### Cannot perform these tests since wihout a simulator I can't get the session into active state and update won't work
    #### because the session was initiated by the command API
    #### Same for stop, resume
    # start_session_response = start_usage_session(patient2_auth_token, device2_id, usage_session_template_id, patient_id)
    # assert start_session_response.status_code == 403
    # start_session_response = start_usage_session(patient_auth_token, device_id, usage_session_template_id, patient_id)
    # assert start_session_response.status_code == 201
    # usage_session2_id = start_session_response.json()['_id']

    # pause only for self; first make sure it's active

    # pause_session_response = pause_usage_session(patient2_auth_token, device_id, usage_session2_id)
    # assert pause_session_response.status_code == 403
    # pause_session_response = pause_usage_session(patient_auth_token, device_id, usage_session2_id)
    # assert pause_session_response.status_code == 200

    # Teardown
    # stop_session_response = stop_usage_session(admin_auth_token, device2_id, usage_session2_id)
    # assert stop_session_response.status_code == 200      ###### getting 503
    # stop_usage_session_response = stop_usage_session(patient_auth_token, device_id, usage_session2_id)
    # assert stop_usage_session_response.status_code == 200  ### getting 503
    ##debug
    # stop_usage_session_response = stop_usage_session(admin_auth_token, device_id, usage_session2_id)
    # assert stop_usage_session_response.status_code == 200
    # delete_usage_session_response = delete_usage_session(patient2_auth_token, device_id, usage_session2_id)
    # assert delete_usage_session_response.status_code == 204  ####### getting 403
    delete_usage_session_response = delete_usage_session(admin_auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, usage_session_template_id)
    assert delete_template_response.status_code == 204

    self_signup_patient_teardown(admin_auth_token, patient_setup)


def test_patient_commands_abac_rules():
    # need to figure out how to activate simulator from the tests
    pass


def test_patient_alerts_abac_rules():  ## in progress
    #### Separate for patient alerts and device alerts  ####
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    template_id = "2aaa71cf-8a10-4253-9576-6fd160a85b2d"  # This is the template id of the organization template in the console
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create patient in new org
    patient1_auth_token, patient1_id, registration_code1_id, device1_id = create_single_patient_self_signup(
        admin_auth_token, organization_id, 'DeviceType1')
    # create patient in default org
    patient2_auth_token, patient2_id, registration_code2_id, device2_id = create_single_patient_self_signup(
        admin_auth_token, "00000000-0000-0000-0000-000000000000", 'DeviceType1')

    # create alert template based on patient parent

    # teardown
    single_self_signup_patient_teardown(admin_auth_token, patient1_id, registration_code1_id, device1_id)
    single_self_signup_patient_teardown(admin_auth_token, patient2_id, registration_code2_id, device2_id)
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_patient_measurements_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create two patients, registration codes and devices
    patient_setup = self_signup_patient_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                              'DeviceType1')
    patient_id = patient_setup['patient_id'][0]
    patient_auth_token = patient_setup['patient_auth_token']
    patient2_auth_token = login_with_credentials(patient_setup['email'][1], "Q2207819w@")
    # create usage session template and usage session; associate to patient
    # associate patient with device
    device1_id = patient_setup['device_id'][0]
    device2_id = patient_setup['device_id'][1]
    update_device_response = update_device(admin_auth_token, device1_id, "change_string", patient_id)
    assert update_device_response.status_code == 200
    # get the device templateId
    get_device_response = get_device(admin_auth_token, device1_id)
    device_template_id = get_device_response.json()['_template']['id']
    # create usage_session template
    usage_template_data = create_template_setup(admin_auth_token, None, "usage_session", device_template_id)
    usage_session_template_name = usage_template_data[1]
    usage_session_template_id = usage_template_data[0]

    # create session should succeed for self
    create_session_response = create_usage_session_by_usage_type(patient_auth_token, device1_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 201
    usage_session_id = create_session_response.json()['_id']
    # create measurement on patient1
    create_measurement_response = create_measurement(patient_auth_token, device1_id, patient_id, usage_session_id)
    assert create_measurement_response.status_code == 200
    # create bulk measurement
    create_bulk_measurement_response = create_bulk_measurement(patient_auth_token, device1_id,
                                                               patient_id, usage_session_id)
    assert create_bulk_measurement_response.status_code == 200

    # get v1 raw measurements
    get_v1_measurement_response = get_raw_measurements(patient_auth_token, patient_id)
    assert get_v1_measurement_response.status_code == 200
    # fail for other patient
    get_v1_measurement_response = get_raw_measurements(patient_auth_token, patient_setup['patient_id'][1])
    assert get_v1_measurement_response.status_code == 403

    # get v1 aggregated measurements
    get_v1_measurement_response = get_aggregated_measurements(patient_auth_token, patient_id)
    assert get_v1_measurement_response.status_code == 200
    # fail for other patient
    get_v1_measurement_response = get_aggregated_measurements(patient_auth_token, patient_setup['patient_id'][1])
    assert get_v1_measurement_response.status_code == 403

    # get V2 raw measurements
    get_v2_measurement_response = get_v2_raw_measurements(patient_auth_token, patient_id)
    assert get_v2_measurement_response.status_code == 200
    # fail for other patient
    get_v2_measurement_response = get_v2_raw_measurements(patient_auth_token, patient_setup['patient_id'][1])
    assert get_v2_measurement_response.status_code == 403

    # get v2 aggregated measurements
    get_v2_measurement_response = get_v2_aggregated_measurements(patient_auth_token, patient_id)
    assert get_v2_measurement_response.status_code == 200
    # fail for other patient
    get_v2_measurement_response = get_v2_aggregated_measurements(patient_auth_token, patient_setup['patient_id'][1])
    assert get_v2_measurement_response.status_code == 403

    # get device credentials
    get_credentials_response = get_device_credentials(patient_auth_token)
    assert get_credentials_response.status_code == 200

    # teardown
    delete_usage_session_response = delete_usage_session(admin_auth_token, device1_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, usage_session_template_id)
    assert delete_template_response.status_code == 204

    self_signup_patient_teardown(admin_auth_token, patient_setup)


def test_patient_ums_abac_rules():
    pass
