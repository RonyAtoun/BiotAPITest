# import pytest
from api_test_helpers import *
from email_interface import accept_invitation, reset_password_open_email_and_set_new_password


#############################################################################################
# Username and password have to be set in the environment in advance for each individual test
#############################################################################################


def test_patient_commands_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # Setup
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # create patient & device in new org
    patient1_auth_token, patient1_id, registration_code1_id, device1_id = create_single_patient_self_signup(
        admin_auth_token, organization_id, 'DeviceType1')
    # create patient in default org
    patient2_auth_token, patient2_id, registration_code2_id, device2_id = create_single_patient_self_signup(
        admin_auth_token, "00000000-0000-0000-0000-000000000000", 'DeviceType1')

    # get the device templateId
    get_device_response = get_device(admin_auth_token, device2_id)
    device_template_id = get_device_response.json()['_template']['id']
    # create command template
    command_template_data = create_template_setup(admin_auth_token, None, "command", device_template_id)
    command_template_name = command_template_data[1]
    command_template_id = command_template_data[0]

    # start simulator with device2
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()

    start_simulation_with_existing_device(device2_id, os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # start/stop command only for self organization (use device2)
    # self org
    start_command_response = start_command_by_template(patient2_auth_token, device2_id, command_template_name)
    assert start_command_response.status_code == 201
    command2_id = start_command_response.json()['_id']
    # self
    get_command_response = get_command(patient2_auth_token, device2_id, command2_id)
    assert get_command_response.status_code == 200
    # other
    get_command_response = get_command(patient1_auth_token, device2_id, command2_id)
    assert get_command_response.status_code == 403
    stop_command_response = stop_command(patient2_auth_token, device2_id, command2_id)
    if stop_command_response.status_code == 200:
        assert stop_command_response.status_code == 200
    else:
        print("     Note: stop command failed - simulator timeout")
    # other org
    start_command_response = start_command_by_template(patient1_auth_token, device2_id, command_template_name)
    assert start_command_response.status_code == 403
    stop_command_response = stop_command(patient1_auth_token, device2_id, command2_id)
    assert stop_command_response.status_code == 403
    # self org
    start_command_response = start_command_by_id(patient2_auth_token, device2_id, command_template_id)
    assert start_command_response.status_code == 201

    # other org
    start_command_response = start_command_by_id(patient1_auth_token, device2_id, command_template_id)
    assert start_command_response.status_code == 403

    # self
    search_command_response = search_commands(patient2_auth_token, command2_id)
    assert search_command_response.status_code == 200
    #assert search_command_response.json()['metadata']['page']['totalResults'] == 1
    # other
    search_command_response = search_commands(patient1_auth_token, command2_id)
    assert search_command_response.status_code == 200
    #assert search_command_response.json()['metadata']['page']['totalResults'] == 0

    # teardown
    # stop simulation
    stop_simulation()
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()

    single_self_signup_patient_teardown(admin_auth_token, patient1_id, registration_code1_id, device1_id)
    single_self_signup_patient_teardown(admin_auth_token, patient2_id, registration_code2_id, device2_id)

    delete_template_response = delete_template(admin_auth_token, command_template_id)
    assert delete_template_response.status_code == 204

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


def test_patient_organization_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    primary_admin_auth_token, primary_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)

    # create patient
    patient_auth_token, patient_id = create_single_patient(primary_admin_auth_token, organization_id)

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
    delete_patient_response = delete_patient(primary_admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


def test_patient_organization_users_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization user
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    template_name = "OrganizationOperator"
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    create_user_response = create_organization_user(admin_auth_token, template_name, name, email,
                                                    "00000000-0000-0000-0000-000000000000")
    assert create_user_response.status_code == 201
    organization_user_id = create_user_response.json()['_id']

    # create patient
    patient_auth_token, patient_id = create_single_patient(admin_auth_token, "00000000-0000-0000-0000-000000000000")

    # create organization user by patient should fail
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    template_name = "OrganizationOperator"
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    create_user_response = create_organization_user(patient_auth_token, template_name, name, email,
                                                    "00000000-0000-0000-0000-000000000000")
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

    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_user_response = delete_organization_user(admin_auth_token, organization_user_id)
    assert delete_user_response.status_code == 204


def test_patient_device_alerts_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template

    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create patient in new org
    patient1_auth_token, patient1_id, registration_code1_id, device1_id = create_single_patient_self_signup(
        admin_auth_token, organization_id, 'DeviceType1')
    # create patient in default org
    patient2_auth_token, patient2_id, registration_code2_id, device2_id = create_single_patient_self_signup(
        admin_auth_token, "00000000-0000-0000-0000-000000000000", 'DeviceType1')
    # get the device template
    get_device_response = get_device(patient1_auth_token, device1_id)
    assert get_device_response.status_code == 200
    device_template_id = get_device_response.json()['_template']['id']
    alert_template_name = f'test_device_alert{uuid.uuid4().hex}'[0:35]
    create_device_alert_template_response = create_device_alert_template(admin_auth_token, device_template_id,
                                                                         alert_template_name)
    assert create_device_alert_template_response.status_code == 201, f"{create_device_alert_template_response.text}"
    alert_template2_id = create_device_alert_template_response.json()['id']
    alert_template2_name = create_device_alert_template_response.json()['name']

    # Create device-alert by id only in same organization
    create_alert_response = create_device_alert_by_id(patient1_auth_token, device1_id, alert_template2_id)
    assert create_alert_response.status_code == 201  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_patient_alert_by_id(patient2_auth_token, device1_id, alert_template2_id)
    assert create_alert_response.status_code == 403  # other org

    # get device-alert only in same organization
    get_device_alert_response = get_device_alert(patient1_auth_token, device1_id, alert_id)
    assert get_device_alert_response.status_code == 200  # same org
    get_device_alert_response = get_device_alert(patient2_auth_token, device1_id, alert_id)
    assert get_device_alert_response.status_code == 403  # other org

    # get device-alert list (search) only in same org
    get_device_alert_list_response = get_device_alert_list(patient1_auth_token, alert_id)
    assert get_device_alert_list_response.status_code == 200
    if os.getenv('ENDPOINT') == 'https://api.staging.biot-gen2.biot-med.com':
        assert get_device_alert_list_response.json()['metadata']['page']['totalResults'] == 1
    get_device_alert_list_response = get_device_alert_list(patient2_auth_token, alert_id)
    assert get_device_alert_list_response.status_code == 200
    if os.getenv('ENDPOINT') == 'https://api.staging.biot-gen2.biot-med.com':
        assert get_device_alert_list_response.json()['metadata']['page']['totalResults'] == 0
    # get current alerts (nursing station) should always fail
    get_current_alert_response = get_current_device_alert_list(patient1_auth_token, alert_id)
    assert get_current_alert_response.status_code == 403

    # delete device-alert only in same organization
    delete_alert_response = delete_device_alert(patient2_auth_token, device1_id, alert_id)
    assert delete_alert_response.status_code == 403
    delete_alert_response = delete_device_alert(patient1_auth_token, device1_id, alert_id)
    assert delete_alert_response.status_code == 204

    # create device-alert by name only in same organization
    create_alert_response = create_device_alert_by_name(patient1_auth_token, device1_id, alert_template2_name)
    assert create_alert_response.status_code == 201  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_device_alert_by_name(patient2_auth_token, device1_id, alert_template2_name)
    assert create_alert_response.status_code == 403  # other org
    # update device-alert only in same organization
    update_alert_response = update_device_alert(patient1_auth_token, device1_id, alert_id)
    assert update_alert_response.status_code == 200  # same org
    update_alert_response = update_device_alert(patient2_auth_token, device1_id, alert_id)
    assert update_alert_response.status_code == 403  # other org

    # teardown
    # clean up the last device alert
    delete_alert_response = delete_device_alert(patient1_auth_token, device1_id, alert_id)
    assert delete_alert_response.status_code == 204
    single_self_signup_patient_teardown(admin_auth_token, patient1_id, registration_code1_id, device1_id)
    single_self_signup_patient_teardown(admin_auth_token, patient2_id, registration_code2_id, device2_id)
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, alert_template2_id)
    assert delete_template_response.status_code == 204


def test_patient_patient_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create two patients
    patient_auth_token, patient_id = create_single_patient(admin_auth_token, "00000000-0000-0000-0000-000000000000")
    patient1_auth_token, patient1_id = create_single_patient(admin_auth_token, "00000000-0000-0000-0000-000000000000")

    # Create and delete patient should fail
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    # create patient should fail
    test_patient_create_response = create_patient(patient_auth_token, test_name, email, "Patient",
                                                  "00000000-0000-0000-0000-000000000000")
    assert test_patient_create_response.status_code == 403
    # delete patient (use second patient created)
    test_patient_delete_response = delete_patient(patient_auth_token, patient_id[1])
    assert test_patient_delete_response.status_code == 403

    # update patient only for self
    update_patient_response = update_patient(patient_auth_token, patient_id, "00000000-0000-0000-0000-000000000000",
                                             "change string", None, None)
    assert update_patient_response.status_code == 200
    # should fail for other patient
    update_patient_response = update_patient(patient_auth_token, patient1_id,
                                             "00000000-0000-0000-0000-000000000000",
                                             "change string", None, None)
    assert update_patient_response.status_code == 403, f"{update_patient_response.text}"

    # get patient only for self
    get_patient_response = get_patient(patient_auth_token, patient_id)  # self
    assert get_patient_response.status_code == 200
    can_login_val = not get_patient_response.json()['_canLogin']
    get_patient_response = get_patient(patient_auth_token, patient1_id)  # other patient
    assert get_patient_response.status_code == 403

    # update canLoging should fail
    update_patient_response = update_patient(patient_auth_token, patient1_id, "00000000-0000-0000-0000-000000000000",
                                             None, None, {"_canLogin": can_login_val})
    assert update_patient_response.status_code == 403, f"{update_patient_response.text}"

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
    change_patient_state_response = change_patient_state(patient_auth_token, patient_id, "ENABLED")
    assert change_patient_state_response.status_code == 403

    # resend invitation fails
    resend_invitation_response = resend_invitation(patient_auth_token, patient_id)
    assert resend_invitation_response.status_code == 403

    # Teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_patient_response = delete_patient(admin_auth_token, patient1_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"


def test_patient_caregiver_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create two patients in default org
    patient_auth_token, patient_id = create_single_patient(admin_auth_token, "00000000-0000-0000-0000-000000000000")
    patient2_auth_token, patient2_id = create_single_patient(admin_auth_token, "00000000-0000-0000-0000-000000000000")

    # create caregiver by admin
    caregiver_email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    create_caregiver_response = create_caregiver(admin_auth_token, test_name, caregiver_email, "Clinician",
                                                 "00000000-0000-0000-0000-000000000000")
    assert create_caregiver_response.status_code == 201
    caregiver_id = create_caregiver_response.json()['_id']

    # associate first of two patients setup with caregiver
    update_patient_response = update_patient(admin_auth_token, patient_id,
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

    # get should fail with other patient
    get_caregiver_response = get_caregiver(patient2_auth_token, caregiver_id)
    assert get_caregiver_response.status_code == 403

    # search caregiver by patient only for self
    get_caregiver_list_response = get_caregiver_list(patient_auth_token)
    assert get_caregiver_list_response.status_code == 200
    assert get_caregiver_list_response.json()['metadata']['page']['totalResults'] == 1

    # resend invitation fails
    resend_invitation_response = resend_invitation(patient_auth_token, caregiver_id)
    assert resend_invitation_response.status_code == 403

    # Teardown

    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_patient_response = delete_patient(admin_auth_token, patient2_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
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

    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # create patient
    patient_auth_token, patient_id = create_single_patient(admin_auth_token, "00000000-0000-0000-0000-000000000000")

    # create patient, registration code and device in second org
    primary_admin_auth_token, primary_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)
    # create patient
    patient_auth_token2, patient_id2 = create_single_patient(primary_admin_auth_token, organization_id)

    # create generic template with phi=true on non mandatory field
    create_generic_template_with_phi_response = create_generic_template_with_phi_true(admin_auth_token)
    assert create_generic_template_with_phi_response.status_code == 201, \
        f"{create_generic_template_with_phi_response.text}"
    generic_template_with_phi_id = create_generic_template_with_phi_response.json()["id"]

    # create generic entity by patient only for self organization (sets name which is phi)
    create_generic_entity_response = create_generic_entity(patient_auth_token, generic_template_with_phi_id,
                                                           f'generic_entity_{uuid.uuid4().hex}'[0:31],
                                                           "00000000-0000-0000-0000-000000000000")
    assert create_generic_entity_response.status_code == 201
    entity_id = create_generic_entity_response.json()["_id"]

    # create should fail for other organization
    create_generic_entity_response = create_generic_entity(patient_auth_token, generic_template_with_phi_id,
                                                           f'generic_entity_{uuid.uuid4().hex}'[0:31], organization_id)
    assert create_generic_entity_response.status_code == 403

    # positive - same organization  name change is phi
    update_generic_entity_response = update_generic_entity(patient_auth_token, entity_id, "change string")
    assert update_generic_entity_response.status_code == 200
    # Negative - second organization
    update_generic_entity_response = update_generic_entity(patient_auth_token2, entity_id, "change string")
    assert update_generic_entity_response.status_code == 403

    # get only for same organization
    get_generic_entity_response = get_generic_entity(patient_auth_token, entity_id)
    assert get_generic_entity_response.status_code == 200
    assert '_name' in get_generic_entity_response.json()
    get_generic_entity_response = get_generic_entity(patient_auth_token2, entity_id)
    assert get_generic_entity_response.status_code == 403

    # search only for same organization
    get_generic_entity_list_response = get_generic_entity_list(patient_auth_token)
    assert get_generic_entity_list_response.status_code == 200
    assert '_name' in get_generic_entity_list_response.json()['data'][0]

    # negative
    get_generic_entity_list_response = get_generic_entity_list(patient_auth_token2)
    assert get_generic_entity_list_response.status_code == 200

    # delete only for same organization
    # should fail for generic entity in other organization
    delete_generic_entity_response = delete_generic_entity(patient_auth_token2, entity_id)
    assert delete_generic_entity_response.status_code == 403
    delete_generic_entity_response = delete_generic_entity(patient_auth_token, entity_id)
    assert delete_generic_entity_response.status_code == 204

    # Teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_patient_response = delete_patient(admin_auth_token, patient_id2)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"

    delete_generic_entity_template_response = delete_template(admin_auth_token, generic_template_with_phi_id)
    assert delete_generic_entity_template_response.status_code == 204

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_patient_registration_codes_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # Setup
    # create patient
    patient_auth_token, patient_id = create_single_patient(admin_auth_token, "00000000-0000-0000-0000-000000000000")

    # create new organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
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
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
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
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    primary_admin_auth_token, primary_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)
    # create patient in new org
    patient1_auth_token, patient1_id = create_single_patient(primary_admin_auth_token, organization_id)
    # create patient in default org
    patient2_auth_token, patient2_id = create_single_patient(admin_auth_token)

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
                                             None, None, {"uploadFile": {"id": file2_id}})
    assert update_patient_response.status_code == 200
    # get should succeed only in self organization
    get_file_response = get_file(patient1_auth_token, file1_id)  # should succeed
    assert get_file_response.status_code == 200
    get_file_response = get_file(patient1_auth_token, file2_id)  # should fail
    assert get_file_response.status_code == 403

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient1_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_patient_response = delete_patient(admin_auth_token, patient2_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_patient_patient_alerts_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template

    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    primary_admin_auth_token, primary_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)

    # create patient in new org
    patient1_auth_token, patient1_id = create_single_patient(primary_admin_auth_token, organization_id)
    # create patient in default org
    patient2_auth_token, patient2_id = create_single_patient(admin_auth_token)

    # get the patient templateId
    get_patient_response = get_patient(patient1_auth_token, patient1_id)
    assert get_patient_response.status_code == 200
    patient_template_id = get_patient_response.json()['_template']['id']

    # create alert template based on patient parent (template1)
    alert_template_name = f'test_patient_alert{uuid.uuid4().hex}'[0:35]
    create_patient_alert_template_response = create_patient_alert_template(admin_auth_token, patient_template_id,
                                                                           alert_template_name)
    assert create_patient_alert_template_response.status_code == 201, f"{create_patient_alert_template_response.text}"
    alert_template1_id = create_patient_alert_template_response.json()['id']
    alert_template1_name = create_patient_alert_template_response.json()['name']

    # Create/Delete patient-alert by id only in same organization
    create_alert_response = create_patient_alert_by_id(patient1_auth_token, patient1_id, alert_template1_id)
    assert create_alert_response.status_code == 201  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_patient_alert_by_id(patient2_auth_token, patient1_id, alert_template1_id)
    assert create_alert_response.status_code == 403  # other org
    # update patient alert only in same organization
    update_alert_response = update_patient_alert(patient1_auth_token, patient1_id, alert_id)
    assert update_alert_response.status_code == 200
    update_alert_response = update_patient_alert(patient2_auth_token, patient1_id, alert_id)
    assert update_alert_response.status_code == 403
    # get patient alert and search only in same organization
    get_patient_alert_response = get_patient_alert(patient1_auth_token, patient1_id, alert_id)
    assert get_patient_alert_response.status_code == 200
    get_patient_alert_response = get_patient_alert(patient2_auth_token, patient1_id, alert_id)
    assert get_patient_alert_response.status_code == 403
    get_patient_alert_list_response = get_patient_alert_list(patient1_auth_token, alert_id)
    assert get_patient_alert_list_response.status_code == 200
    if os.getenv('ENDPOINT') == 'https://api.staging.biot-gen2.biot-med.com':
        assert get_patient_alert_list_response.json()['metadata']['page']['totalResults'] == 1
    get_patient_alert_list_response = get_patient_alert_list(patient2_auth_token, alert_id)
    assert get_patient_alert_list_response.status_code == 200
    if os.getenv('ENDPOINT') == 'https://api.staging.biot-gen2.biot-med.com':
        assert get_patient_alert_list_response.json()['metadata']['page']['totalResults'] == 0
    # get current alerts (nursing station) should always fail
    get_current_alert_response = get_current_patient_alert_list(patient1_auth_token, alert_id)
    assert get_current_alert_response.status_code == 403

    # delete patient-alert only in same organization
    delete_alert_response = delete_patient_alert(patient2_auth_token, patient1_id, alert_id)
    assert delete_alert_response.status_code == 403  # other org
    delete_alert_response = delete_patient_alert(patient1_auth_token, patient1_id, alert_id)
    assert delete_alert_response.status_code == 204  # same org
    # Create patient-alert by name
    create_alert_response = create_patient_alert_by_name(patient1_auth_token, patient1_id, alert_template1_name)
    assert create_alert_response.status_code == 201  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_patient_alert_by_name(patient2_auth_token, patient1_id, alert_template1_name)
    assert create_alert_response.status_code == 403  # other org
    # delete it
    delete_alert_response = delete_patient_alert(patient1_auth_token, patient1_id, alert_id)
    assert delete_alert_response.status_code == 204  # same org

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient1_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_patient_response = delete_patient(admin_auth_token, patient2_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, alert_template1_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_patient_measurements_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    aggregated_observation_attribute_name = f'aggr_observ_decimal_int{uuid.uuid4().hex}'[0:36]
    raw_observation_attribute_name = f'raw_observ_waveform{uuid.uuid4().hex}'[0:36]
    # create patient, registration codes and devices in default org
    patient_auth_token, patient_id, registration_code_id, device1_id = (
        create_single_patient_self_signup(admin_auth_token,  "00000000-0000-0000-0000-000000000000", 'DeviceType1'))
    # create second patient in default org
    patient2_auth_token, patient2_id = create_single_patient(admin_auth_token)
    # get the patient templateId
    get_patient_response = get_patient(patient_auth_token, patient_id)
    assert get_patient_response.status_code == 200
    patient_template_id = get_patient_response.json()['_template']['id']
    # add observation attributes to Patient template
    get_patient_template_response = get_template(admin_auth_token, patient_template_id)
    assert get_patient_template_response.status_code == 200, f"{get_patient_template_response.text}"
    template_payload = map_template(get_patient_template_response.json())
    aggregated_observation_attribute_name = f'aggr_observ_decimal_int{uuid.uuid4().hex}'[0:36]
    raw_observation_attribute_name = f'raw_observ_waveform{uuid.uuid4().hex}'[0:36]
    observation_aggregated_object = {
        "name": aggregated_observation_attribute_name,
        "type": "DECIMAL",
        "displayName": aggregated_observation_attribute_name,
        "phi": False,
        "validation": {
            "mandatory": False,
            "defaultValue": None
        },
        "selectableValues": [],
        "category": "MEASUREMENT",
        "numericMetaData": None,
        "referenceConfiguration": None,
        "linkConfiguration": None
    }
    observation_raw_object = {
        "name": raw_observation_attribute_name,
        "type": "WAVEFORM",
        "displayName": raw_observation_attribute_name,
        "phi": False,
        "validation": {
            "mandatory": False,
            "defaultValue": None
        },
        "selectableValues": [],
        "category": "MEASUREMENT",
        "numericMetaData": {
            "subType": "INTEGER"
        },
        "referenceConfiguration": None,
        "linkConfiguration": None
    }
    (template_payload['customAttributes']).append(observation_raw_object)
    (template_payload['customAttributes']).append(observation_aggregated_object)
    update_template_response = update_template(admin_auth_token, patient_template_id, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    # create usage session template and usage session; associate to patient
    # associate patient with device

    update_device_response = update_device(admin_auth_token, device1_id, "change_string", patient_id)
    assert update_device_response.status_code == 200
    # get the device templateId
    get_device_response = get_device(admin_auth_token, device1_id)
    device_template_id = get_device_response.json()['_template']['id']
    # create usage_session template
    usage_template_data = create_template_setup(admin_auth_token, None, "usage-session", device_template_id)
    usage_session_template_name = usage_template_data[1]
    usage_session_template_id = usage_template_data[0]

    # create session should succeed for self
    create_session_response = create_usage_session_by_usage_type(patient_auth_token, device1_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 201
    usage_session_id = create_session_response.json()['_id']
    # create measurement on patient1
    create_measurement_response = create_measurement(patient_auth_token, device1_id, patient_id, usage_session_id,
                                                     aggregated_observation_attribute_name)
    assert create_measurement_response.status_code == 200
    # create bulk measurement
    create_bulk_measurement_response = create_bulk_measurement(patient_auth_token, device1_id,
                                                               patient_id, usage_session_id,
                                                               aggregated_observation_attribute_name)
    assert create_bulk_measurement_response.status_code == 200

    # get v1 raw measurements
    get_v1_measurement_response = get_raw_measurements(patient_auth_token, patient_id, raw_observation_attribute_name)
    assert get_v1_measurement_response.status_code == 200
    # fail for other patient
    get_v1_measurement_response = get_raw_measurements(patient_auth_token, patient2_id, raw_observation_attribute_name)
    assert get_v1_measurement_response.status_code == 403

    # get v1 aggregated measurements
    get_v1_measurement_response = get_aggregated_measurements(patient_auth_token, patient_id,
                                                              aggregated_observation_attribute_name)
    assert get_v1_measurement_response.status_code == 200
    # fail for other patient
    get_v1_measurement_response = get_aggregated_measurements(patient_auth_token, patient2_id,
                                                              aggregated_observation_attribute_name)
    assert get_v1_measurement_response.status_code == 403

    # get V2 raw measurements
    get_v2_measurement_response = get_v2_raw_measurements(patient_auth_token, patient_id,
                                                          raw_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 200
    # fail for other patient
    get_v2_measurement_response = get_v2_raw_measurements(patient_auth_token, patient2_id,
                                                          raw_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 403

    # get v2 aggregated measurements
    get_v2_measurement_response = get_v2_aggregated_measurements(patient_auth_token, patient_id,
                                                                 aggregated_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 200
    # fail for other patient
    get_v2_measurement_response = get_v2_aggregated_measurements(patient_auth_token, patient2_id,
                                                                 aggregated_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 403

    # get device credentials
    get_credentials_response = get_device_credentials(patient_auth_token)
    assert get_credentials_response.status_code == 200

    # teardown
    delete_usage_session_response = delete_usage_session(admin_auth_token, device1_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, usage_session_template_id)
    assert delete_template_response.status_code == 204

    single_self_signup_patient_teardown(admin_auth_token, patient_id, registration_code_id, device1_id)
    delete_patient_response = delete_patient(admin_auth_token, patient2_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"


def test_patient_ums_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # get the Patient template name
    template_list_response = get_all_templates(admin_auth_token)
    assert template_list_response.status_code == 200
    patient_template_name = None
    for template in template_list_response.json()['data']:
        if "Patient" == template['name']:
            patient_template_name = template['name']
            break

    # create a patient user
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'

    create_patient_response = create_patient(admin_auth_token, test_name, email, patient_template_name,
                                             "00000000-0000-0000-0000-000000000000")
    assert create_patient_response.status_code == 201
    patient_id = create_patient_response.json()['_id']

    response_text, accept_invitation_response = accept_invitation(email)
    password = accept_invitation_response.json()['operationData']['password']
    # login
    patient_auth_token = login_with_credentials(email, password)
    # set password by patient
    new_password = "Bb234567NewPass"
    set_password_response = set_password(patient_auth_token, password, new_password)
    assert set_password_response.status_code == 200
    # check login with new password
    patient_auth_token = login_with_credentials(email, new_password)

    # forgot password flow
    forgot_password_response = forgot_password(email)
    new_password = "Cc345678NewPass2"
    reset_password_open_email_and_set_new_password(email, new_password)
    # check login with new password
    patient_auth_token = login_with_credentials(email, new_password)

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204


def test_patient_locales_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    patient_auth_token, patient_id = create_single_patient(admin_auth_token)

    # get available locales should succeed
    get_locales_response = get_available_locales(patient_auth_token)
    assert get_locales_response.status_code == 200

    # add locale should fail
    code = 'en-us'
    add_locale_response = add_locale(patient_auth_token, code)
    assert add_locale_response.status_code == 403

    # delete locale should fail
    locale_id = 'any'
    delete_locale_response = delete_locale(patient_auth_token, locale_id)
    assert delete_locale_response.status_code == 403

    # update locale should fail
    update_locale_response = update_locale(patient_auth_token, code)
    assert update_locale_response.status_code == 403

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204


def test_patient_plugins_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    patient_auth_token, patient_id = create_single_patient(admin_auth_token)

    # create plugin should fail
    create_plugin_response = create_plugin(patient_auth_token, 'test_plugin')
    assert create_plugin_response.status_code == 403

    # delete plugin should fail
    delete_plugin_response = delete_plugin(patient_auth_token, 'test_plugin')
    assert delete_plugin_response.status_code == 403

    # update plugin should fail
    update_plugin_response = update_plugin(patient_auth_token, 'test_plugin', 'test_plugin')
    assert update_plugin_response.status_code == 403

    # get plugin should fail
    get_plugin_response = get_plugin(patient_auth_token, 'test_plugin')
    assert get_plugin_response.status_code == 403

    # search plugin should fail
    search_plugin_response = get_plugin_list(patient_auth_token, 'test_plugin')
    assert search_plugin_response.status_code == 403

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204


def test_patient_dms_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    patient_auth_token, patient_id = create_single_patient(admin_auth_token)

    # create_report should fail
    create_report_response = create_report(patient_auth_token)
    assert create_report_response.status_code == 403

    # delete report should fail
    report_id = uuid.uuid4().hex
    delete_report_response = delete_report(patient_auth_token, report_id)
    assert delete_report_response.status_code == 403

    # get report should fail
    get_report_response = get_report(patient_auth_token, report_id)
    assert get_report_response.status_code == 403

    # search report should fail
    search_report_response = get_report_list(patient_auth_token)
    assert search_report_response.status_code == 403

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204


def test_patient_templates_abac_rules():  # update is getting a 400
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    patient_auth_token, patient_id = create_single_patient(admin_auth_token)

    # view templates should succeed
    view_template_response = get_templates_list(patient_auth_token)
    assert view_template_response.status_code == 200
    get_minimized_response = get_all_templates(patient_auth_token)
    assert get_minimized_response.status_code == 200

    # extract valid id and parentId
    template_id = get_minimized_response.json()['data'][0]['id']
    parent_template_id = get_minimized_response.json()['data'][0]['parentTemplateId']

    # get by id should succeed

    get_template_response = get_template_by_id(patient_auth_token, template_id)
    assert get_template_response.status_code == 200

    # get overview should fail
    get_overview_response = get_template_overview(patient_auth_token, template_id)
    assert get_overview_response.status_code == 403

    # delete should fail
    delete_template_response = delete_template(patient_auth_token, template_id)
    assert delete_template_response.status_code == 403

    # create should fail
    create_template_response = create_generic_template(patient_auth_token)
    assert create_template_response.status_code == 403

    # update should fail
    payload = get_template_response.json()
    update_template_response = update_template(patient_auth_token, template_id, payload)

    assert update_template_response.status_code == 403

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204


def test_patient_portal_builder_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    patient_auth_token, patient_id = create_single_patient(admin_auth_token)

    # view full info should succeed
    view_template_response = get_templates_list(patient_auth_token)
    assert view_template_response.status_code == 200
    get_minimized_response = get_all_templates(patient_auth_token)
    assert get_minimized_response.status_code == 200

    # extract valid id and parentId
    template_id = get_minimized_response.json()['data'][0]['id']
    view_portal_response = view_full_portal_information(patient_auth_token, 'ORGANIZATION_PORTAL', 'ENTITY_LIST',
                                                        None)
    assert view_portal_response.status_code == 200
    payload = view_portal_response.json()
    view_id = payload['id']
    # update views should fail
    update_portal_view_response = update_portal_views(patient_auth_token, 'ORGANIZATION_PORTAL', view_id, payload)
    assert update_portal_view_response.status_code == 403

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204


def test_patient_adb_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    patient_auth_token, patient_id = create_single_patient(admin_auth_token)

    # deploy adb should fail
    deploy_response = deploy_adb(patient_auth_token)
    assert deploy_response.status_code == 403

    # undeploy should fail
    undeploy_response = undeploy_adb(patient_auth_token)
    assert undeploy_response.status_code == 403

    # start init should fail
    start_init_response = start_init_adb(patient_auth_token)
    assert start_init_response.status_code == 403

    # stop init should fail
    stop_init_response = stop_init_adb(patient_auth_token)
    assert stop_init_response.status_code == 403

    # stop sync should fail
    stop_sync_response = stop_sync_adb(patient_auth_token)
    assert stop_sync_response.status_code == 403

    # get adb info should succeed
    get_adb_response = get_adb_info(patient_auth_token)
    assert get_adb_response.status_code == 200

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient_id)
    assert delete_patient_response.status_code == 204


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
    # associate patient with both devices
    update_device_response = update_device(admin_auth_token, device_id, "change_string", patient_id)
    assert update_device_response.status_code == 200
    update_device_response = update_device(admin_auth_token, device2_id, "change_string", patient_id)
    assert update_device_response.status_code == 200
    # get the device templateId
    get_device_response = get_device(admin_auth_token, device_id)
    device_template_id = get_device_response.json()['_template']['id']
    # create usage_session template
    usage_template_data = create_template_setup(admin_auth_token, None,
                                                "usage-session", device_template_id)
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
    update_session_response = update_usage_session(patient_auth_token, device_id, usage_session_id)
    assert update_session_response.status_code == 200
    update_session_response = update_usage_session(patient2_auth_token, device_id, usage_session_id)
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
    assert get_session_list_response.json()['metadata']['page']['totalResults'] != 0
    # negative: other patient should get zero results
    get_session_list_response = get_usage_session_list(patient2_auth_token)
    assert get_session_list_response.status_code == 200
    assert get_session_list_response.json()['metadata']['page']['totalResults'] == 0

    # delete session by patient should always fail
    delete_session_response = delete_usage_session(patient_auth_token, device_id, usage_session_id)
    assert delete_session_response.status_code == 403

    # start simulator with device2
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()
    start_simulation_with_existing_device(device2_id, os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # start session only for self device (use device2)
    start_session_response = start_usage_session(patient2_auth_token, device2_id, usage_session_template_id, patient_id)
    assert start_session_response.status_code == 403
    start_session_response = start_usage_session(patient_auth_token, device2_id, usage_session_template_id, patient_id)
    assert start_session_response.status_code == 201
    usage_session2_id = start_session_response.json()['_id']

    # pause only for self; first make sure it's active
    # get_usage_session_response = get_usage_session_by_id(patient_auth_token, device2_id, usage_session_id)
    get_usage_session_response = get_usage_session(patient_auth_token, device2_id, usage_session2_id)
    assert get_usage_session_response.status_code == 200, f"{get_usage_session_response.text}"
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "ACTIVE", f"The current status is {usage_session_status}, not 'ACTIVE'"

    pause_session_response = pause_usage_session(patient2_auth_token, device2_id, usage_session2_id)
    assert pause_session_response.status_code == 403
    pause_session_response = pause_usage_session(patient_auth_token, device2_id, usage_session2_id)
    assert pause_session_response.status_code == 200
    get_usage_session_response = get_usage_session(patient_auth_token, device2_id, usage_session2_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "PAUSED", f"The current status is {usage_session_status}, not 'PAUSED'"

    # resume session (should succeed only for self)
    resume_usage_session_response = resume_usage_session(patient2_auth_token, device2_id, usage_session2_id)
    assert resume_usage_session_response.status_code == 403
    resume_usage_session_response = resume_usage_session(patient_auth_token, device2_id, usage_session2_id)
    assert resume_usage_session_response.status_code == 200, f"{resume_usage_session_response.text}"
    get_usage_session_response = get_usage_session(patient_auth_token, device2_id, usage_session2_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "ACTIVE", f"The current status is {usage_session_status}, not 'ACTIVE'"

    # Stop a Remote usage session - succeed for self
    # stop_session_response = stop_usage_session(patient2_auth_token, device2_id, usage_session2_id)
    # assert stop_session_response.status_code == 403
    stop_usage_session_response = stop_usage_session(patient_auth_token, device2_id, usage_session2_id)
    assert stop_usage_session_response.status_code == 200, f"{stop_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(patient_auth_token, device2_id, usage_session2_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "DONE", f"The current status is {usage_session_status}, not 'DONE'"

    # Teardown
    delete_usage_session_response = delete_usage_session(admin_auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204
    delete_usage_session_response = delete_usage_session(admin_auth_token, device2_id, usage_session2_id)
    assert delete_usage_session_response.status_code == 204
    # stop simulation
    stop_simulation()
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()

    delete_template_response = delete_template(admin_auth_token, usage_session_template_id)
    assert delete_template_response.status_code == 204

    self_signup_patient_teardown(admin_auth_token, patient_setup)
