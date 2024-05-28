from api_test_helpers import *
from email_interface import accept_invitation, reset_password_open_email_and_set_new_password
from dotenv import load_dotenv

load_dotenv()


#############################################################################################
# Username and password have to be set in the environment in advance for each individual test
#############################################################################################

# @pytest.mark.skip
def test_org_user_commands_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # Setup
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200, f"{get_self_org_response.text}"
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # create a device in default org
    create_device_response = create_device_without_registration_code(admin_auth_token, 'DeviceType1',
                                                                     "00000000-0000-0000-0000-000000000000")
    assert create_device_response.status_code == 201, f"{create_device_response.text}"
    device_default_id = create_device_response.json()['_id']
    device_template_id = create_device_response.json()['_template']['id']

    # create command template

    command_template_name = f'command_{uuid.uuid4().hex}'[0:16]
    command_template_response = create_command_template_with_support_stop_true(admin_auth_token, command_template_name,
                                                                               device_template_id)
    assert command_template_response.status_code == 201, f"{command_template_response.text}"
    command_template_id = command_template_response.json()['id']

    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin in mew and default organizations
    org_user_new_auth_token, org_user_new_id, password = create_single_org_user(admin_auth_token,
                                                                                org_user_template_name,
                                                                                organization_id)
    org_user_default_auth_token, org_user_default_id, password = create_single_org_user(admin_auth_token,
                                                                                        org_user_template_name,
                                                                                        "00000000-0000-0000-0000-000000000000")
    # start simulator with device
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()
    start_simulation_with_existing_device(device_default_id, os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # start/stop command only for self organization
    # self org
    start_command_response = start_command_by_template(org_user_default_auth_token, device_default_id,
                                                       command_template_name)
    assert start_command_response.status_code == 201, f"{start_command_response.text}"
    command2_id = start_command_response.json()['_id']
    # self
    get_command_response = get_command(org_user_default_auth_token, device_default_id, command2_id)
    assert get_command_response.status_code == 200, f"{get_command_response.text}"
    # other
    get_command_response = get_command(org_user_new_auth_token, device_default_id, command2_id)
    assert get_command_response.status_code == 403, f"{get_command_response.text}"
    stop_command_response = stop_command(org_user_default_auth_token, device_default_id, command2_id)
    assert stop_command_response.status_code == 200, f"{stop_command_response.text}"
    # other org
    start_command_response = start_command_by_template(org_user_new_auth_token, device_default_id,
                                                       command_template_name)
    assert start_command_response.status_code == 403, f"{start_command_response.text}"
    stop_command_response = stop_command(org_user_new_auth_token, device_default_id, command2_id)
    assert stop_command_response.status_code == 403, f"{stop_command_response.text}"
    # self org start by id
    start_command_response = start_command_by_id(org_user_default_auth_token, device_default_id, command_template_id)
    assert start_command_response.status_code == 201, f"{start_command_response.text}"

    # other org
    start_command_response = start_command_by_id(org_user_new_auth_token, device_default_id, command_template_id)
    assert start_command_response.status_code == 403, f"{start_command_response.text}"

    # self
    search_command_response = search_commands(org_user_default_auth_token, command2_id)
    assert search_command_response.status_code == 200, f"{search_command_response.text}"
    assert search_command_response.json()['metadata']['page']['totalResults'] == 1, \
        f"totalResult={search_command_response.json()['metadata']['page']['totalResults']}"
    # other
    search_command_response = search_commands(org_user_new_auth_token, command2_id)
    assert search_command_response.status_code == 200, f"{search_command_response.text}"
    assert search_command_response.json()['metadata']['page']['totalResults'] == 0, \
        f"totalResults={search_command_response.json()['metadata']['page']['totalResults']}"

    # teardown
    # stop simulation
    stop_simulation()
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_default_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_new_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_device_response = delete_device(admin_auth_token, device_default_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"

    delete_template_response = delete_template(admin_auth_token, command_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"


# @pytest.mark.skip
def test_org_user_organization_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization, get org_admin and login with admin
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200, f"{get_self_org_response.text}"
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        organization_id)

    # create, update  and delete organization must fail
    create_organization_response = create_organization(org_user_auth_token, template_id)
    assert create_organization_response.status_code == 403, f"{create_organization_response.text}"
    delete_organization_response = delete_organization(org_user_auth_token, organization_id)
    assert delete_organization_response.status_code == 403, f"{delete_organization_response.text}"
    update_organization_response = update_organization(org_user_auth_token, organization_id, "changed test text")
    assert update_organization_response.status_code == 403, f"{update_organization_response.text}"

    # Get organization by list or by id -- only for own organization
    get_organization_response = get_organization(org_user_auth_token, organization_id)
    # positive (own organization)
    assert get_organization_response.status_code == 200, f"{get_organization_response.text}"
    # negative
    get_organization_response = get_organization(org_user_auth_token, "00000000-0000-0000-0000-000000000000")
    assert get_organization_response.status_code == 403, f"{get_organization_response.text}"
    # positive (own organization should return one result)
    get_organization_list_response = get_organization_list(org_user_auth_token)
    assert get_organization_list_response.status_code == 200, f"{get_organization_list_response.text}"
    assert get_organization_list_response.json()['metadata']['page']['totalResults'] == 1
    # negative (system admin should get all defined organizations)
    get_organization_list_response = get_organization_list(admin_auth_token)
    assert get_organization_list_response.status_code == 200, f"{get_organization_list_response.text}"
    assert get_organization_list_response.json()['metadata']['page']['totalResults'] > 1, \
        f"Total Results={get_organization_list_response.json()['metadata']['page']['totalResults']}"

    # Teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"


# @pytest.mark.skip
def test_org_user_org_users_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # get the org admin credentials
    org_admin_auth_token, org_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)
    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        organization_id)

    # Create org_user should only succeed  in same organization
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    # create org_user should fail in other org
    test_org_user_create_response = create_organization_user(org_user_auth_token, org_user_template_name, test_name,
                                                             email, "00000000-0000-0000-0000-000000000000")
    assert test_org_user_create_response.status_code == 403
    # create org_user should succeed in same org
    new_org_org_user_auth_toke, new_org_user_id, new_org_user_password = create_single_org_user(org_user_auth_token,
                                                                          org_user_template_name, organization_id)

    # first create an org_user by admin in default org
    default_org_user_auth_token, default_org_user_id, new_org_user_password = create_single_org_user(admin_auth_token,
                                                        org_user_template_name, "00000000-0000-0000-0000-000000000000")

    # update org_user only for own org
    update_org_user_response = update_organization_user(org_user_auth_token, new_org_user_id, organization_id,
                                                         "change string")
    assert update_org_user_response.status_code == 200
    # should fail for org_user in other org
    update_org_user_response = update_organization_user(org_user_auth_token, default_org_user_id,
                                                 "00000000-0000-0000-0000-000000000000", "change string")

    assert update_org_user_response.status_code == 403

    # enable/disable only in same organization
    change_org_user_state_response = change_organization_user_state(org_user_auth_token, default_org_user_id, "ENABLED")
    assert change_org_user_state_response.status_code == 403
    change_org_user_state_response = change_organization_user_state(org_user_auth_token, new_org_user_id, "ENABLED")
    assert change_org_user_state_response.status_code == 200

    # resend invitation only for admins and only in same org
    # create another org_user without accepting invitation
    test_name2 = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                  "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email2 = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_org_user_create_response = create_organization_user(admin_auth_token, org_user_template_name, test_name2,
                                                             email2, organization_id)

    assert test_org_user_create_response.status_code == 201
    new_org_user2_id = test_org_user_create_response.json()['_id']
    resend_invitation_response = resend_invitation(org_user_auth_token, new_org_user2_id)
    assert resend_invitation_response.status_code == 403
    resend_invitation_response = resend_invitation(org_admin_auth_token, new_org_user2_id)
    assert resend_invitation_response.status_code == 200

    # get org_user only in same organization
    get_org_user_response = get_organization_user(org_user_auth_token, new_org_user_id)  # same org
    assert get_org_user_response.status_code == 200
    get_org_user_response = get_organization_user(org_user_auth_token, default_org_user_id)  # other org patient
    assert get_org_user_response.status_code == 403

    # search org_user only in same organization

    get_org_user_list_response = get_organization_user_list(org_user_auth_token)
    assert get_org_user_list_response.status_code == 200
    assert get_org_user_list_response.json()['metadata']['page']['totalResults'] == 4, f"{get_org_user_list_response.text}"

    # delete org_user only in same organization
    test_org_user_delete_response = delete_organization_user(org_user_auth_token, default_org_user_id)
    assert test_org_user_delete_response.status_code == 403
    test_org_user_delete_response = delete_organization_user(org_user_auth_token, new_org_user_id)
    assert test_org_user_delete_response.status_code == 204

    # Teardown

    delete_org_user_response = delete_organization_user(admin_auth_token, default_org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_org_user_response = delete_organization_user(admin_auth_token, new_org_user2_id)
    assert delete_org_user_response.status_code == 204
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204
    delete_org_response = delete_organization(admin_auth_token, organization_id)
    assert delete_org_response.status_code == 204


# @pytest.mark.skip
def test_org_user_patient_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # get the org admin credentials
    org_admin_auth_token, org_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)
    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        organization_id)

    # Create patient should only succeed  in same organization
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    # create patient should fail in other org
    test_patient_create_response = create_patient(org_user_auth_token, test_name, email, "Patient",
                                                  "00000000-0000-0000-0000-000000000000")
    assert test_patient_create_response.status_code == 403
    # create patient should succeed in same org
    new_org_patient_auth_toke, new_org_patient_id = create_single_patient(org_user_auth_token, organization_id)

    # first create a patient by admin in default org
    default_org_patient_auth_token, default_org_patient_id = create_single_patient(admin_auth_token)

    # update patient only for own org
    update_patient_response = update_patient(org_user_auth_token, new_org_patient_id, organization_id,
                                             "change string", None, None)
    assert update_patient_response.status_code == 200
    # should fail for patient in other org
    update_patient_response = update_patient(org_user_auth_token, default_org_patient_id,
                                             "00000000-0000-0000-0000-000000000000", "change string", None, None)

    assert update_patient_response.status_code == 403

    # enable/disable only in same organization
    change_patient_state_response = change_patient_state(org_user_auth_token, default_org_patient_id, "ENABLED")
    assert change_patient_state_response.status_code == 403
    change_patient_state_response = change_patient_state(org_user_auth_token, new_org_patient_id, "ENABLED")
    assert change_patient_state_response.status_code == 200

    # resend invitation only for admins and only in same org
    # create another patient without accepting invitation
    test_name2 = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                  "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email2 = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_patient_create_response = create_patient(org_user_auth_token, test_name2, email2, "Patient", organization_id)
    assert test_patient_create_response.status_code == 201
    new_org_patient2_id = test_patient_create_response.json()['_id']
    resend_invitation_response = resend_invitation(org_user_auth_token, new_org_patient2_id)
    assert resend_invitation_response.status_code == 403
    resend_invitation_response = resend_invitation(org_admin_auth_token, new_org_patient2_id)
    assert resend_invitation_response.status_code == 200

    # get patient only in same organization
    get_patient_response = get_patient(org_user_auth_token, new_org_patient_id)  # same org
    assert get_patient_response.status_code == 200
    can_login_val = not get_patient_response.json()['_canLogin']
    get_patient_response = get_patient(org_user_auth_token, default_org_patient_id)  # other org patient
    assert get_patient_response.status_code == 403

    # update canLoging should only by admins and only in same organization
    update_patient_response = update_patient(org_user_auth_token, new_org_patient_id, organization_id,
                                             None, None, {"_canLogin": can_login_val})
    assert update_patient_response.status_code == 403, f"{update_patient_response.text}"

    update_patient_response = update_patient(org_admin_auth_token, new_org_patient_id, organization_id,
                                             None, None, {"_canLogin": can_login_val})
    assert update_patient_response.status_code == 200, f"{update_patient_response.text}"

    update_patient_response = update_patient(org_admin_auth_token, default_org_patient_id,
                                             "00000000-0000-0000-0000-000000000000", None, None,
                                             {"_canLogin": can_login_val})
    assert update_patient_response.status_code == 403, f"{update_patient_response.text}"

    # search patient only in same organization

    get_patient_list_response = get_patient_list(org_user_auth_token)
    assert get_patient_list_response.status_code == 200
    assert get_patient_list_response.json()['metadata']['page']['totalResults'] == 2

    # delete patient only in same organization
    test_patient_delete_response = delete_patient(org_user_auth_token, default_org_patient_id)
    assert test_patient_delete_response.status_code == 403
    test_patient_delete_response = delete_patient(org_user_auth_token, new_org_patient_id)
    assert test_patient_delete_response.status_code == 204

    # Teardown

    delete_patient_response = delete_patient(admin_auth_token, default_org_patient_id)
    assert delete_patient_response.status_code == 204
    delete_patient_response = delete_patient(admin_auth_token, new_org_patient2_id)
    assert delete_patient_response.status_code == 204
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204
    delete_org_response = delete_organization(admin_auth_token, organization_id)
    assert delete_org_response.status_code == 204


# @pytest.mark.skip
def test_org_user_device_alerts_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200, f"{get_self_org_response.text}"
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template

    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # create patient + device in new org
    patient1_auth_token, patient1_id, registration_code1_id, device1_id = create_single_patient_self_signup(
        admin_auth_token, organization_id, 'DeviceType1')
    # create patient + device in default org
    # create patient in new org
    patient2_auth_token, patient2_id, registration_code2_id, device2_id = create_single_patient_self_signup(
        admin_auth_token, "00000000-0000-0000-0000-000000000000", 'DeviceType1')
    # get the device template
    get_device_response = get_device(patient1_auth_token, device1_id)
    assert get_device_response.status_code == 200, f"{get_device_response.text}"
    device_template_id = get_device_response.json()['_template']['id']

    alert_template_name = f'test_device_alert{uuid.uuid4().hex}'[0:35]
    create_device_alert_template_response = create_device_alert_template(admin_auth_token, device_template_id,
                                                                         alert_template_name)
    assert create_device_alert_template_response.status_code == 201, f"{create_device_alert_template_response.text}"
    alert_template2_id = create_device_alert_template_response.json()['id']
    alert_template2_name = create_device_alert_template_response.json()['name']

    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin in mew and default organizations
    org_user_new_auth_token, org_user_new_id, password = create_single_org_user(admin_auth_token,
                                                                                org_user_template_name,
                                                                                organization_id)
    org_user_default_auth_token, org_user_default_id, password = create_single_org_user(admin_auth_token,
                                                                                        org_user_template_name,
                                                                                 "00000000-0000-0000-0000-000000000000")

    # Create device-alert by id only in same organization
    create_alert_response = create_device_alert_by_id(org_user_new_auth_token, device1_id, alert_template2_id)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_device_alert_by_id(org_user_new_auth_token, device2_id, alert_template2_id)
    assert create_alert_response.status_code == 403, f"{create_alert_response.text}"  # other org
    # create a device in default org for next test
    create_alert_response = create_device_alert_by_id(org_user_default_auth_token, device2_id, alert_template2_id)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # other org
    alert2_id = create_alert_response.json()['_id']

    # get device-alert only in same organization
    get_device_alert_response = get_device_alert(org_user_new_auth_token, device1_id, alert_id)
    assert get_device_alert_response.status_code == 200, f"{get_device_alert_response.text}"  # same org
    get_device_alert_response = get_device_alert(org_user_new_auth_token, device2_id, alert2_id)
    assert get_device_alert_response.status_code == 403, f"{get_device_alert_response.text}"  # other org

    # get device-alert list (search) only in same org
    get_device_alert_list_response = get_device_alert_list(org_user_new_auth_token, alert_id)
    assert get_device_alert_list_response.status_code == 200, f"{get_device_alert_list_response.text}"
    get_device_alert_list_response = get_device_alert_list(org_user_default_auth_token, alert_id)
    assert get_device_alert_list_response.status_code == 200, f"{get_device_alert_list_response.text}"
    # get current alerts (nursing station)
    get_current_alert_response = get_current_device_alert_list(org_user_new_auth_token, alert_id)
    assert get_current_alert_response.status_code == 200, f"{get_current_alert_response.text}"
    get_current_alert_response = get_current_device_alert_list(org_user_default_auth_token, alert_id)
    assert get_current_alert_response.status_code == 200, f"{get_current_alert_response.text}"

    # update device-alert only in same organization
    update_alert_response = update_device_alert(org_user_new_auth_token, device1_id, alert_id)
    assert update_alert_response.status_code == 200, f"{update_alert_response.text}"  # same org
    update_alert_response = update_device_alert(org_user_new_auth_token, device2_id, alert2_id)
    assert update_alert_response.status_code == 403, f"{update_alert_response.text}"  # other org

    # delete device-alert is blocked by template for org user admin
    # get the org admin credentials
    org_admin_auth_token, org_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)
    delete_alert_response = delete_device_alert(org_admin_auth_token, device1_id, alert_id)
    assert delete_alert_response.status_code == 403, f"{delete_alert_response.text}"
    delete_alert_response = delete_device_alert(org_user_new_auth_token, device1_id, alert_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"
    delete_alert_response = delete_device_alert(org_user_default_auth_token, device2_id, alert2_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"

    # create device-alert by name only in same organization
    create_alert_response = create_device_alert_by_name(org_user_new_auth_token, device1_id, alert_template2_name)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # same org
    alert3_id = create_alert_response.json()['_id']
    create_alert_response = create_device_alert_by_name(org_user_new_auth_token, device2_id, alert_template2_name)
    assert create_alert_response.status_code == 403, f"{create_alert_response.text}"  # other org

    # teardown
    # clean up the last device alert
    delete_alert_response = delete_device_alert(patient1_auth_token, device1_id, alert3_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"

    # delete patients, devices and reg codes
    single_self_signup_patient_teardown(admin_auth_token, patient1_id, registration_code1_id, device1_id)
    single_self_signup_patient_teardown(admin_auth_token, patient2_id, registration_code2_id, device2_id)

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_default_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_new_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"
    delete_template_response = delete_template(admin_auth_token, alert_template2_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"


# @pytest.mark.skip
def test_org_user_caregiver_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # get the org admin credentials
    org_admin_auth_token, org_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)
    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        organization_id)
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    # Create caregiver should only succeed  in same organization
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    # create caregiver should fail in other org
    test_caregiver_create_response = create_caregiver(org_user_auth_token, test_name, email, caregiver_template_name,
                                                      "00000000-0000-0000-0000-000000000000")
    assert test_caregiver_create_response.status_code == 403
    # create caregiver should succeed in same org
    new_org_caregiver_auth_toke, new_org_caregiver_id = create_single_caregiver(org_user_auth_token,
                                                                                caregiver_template_name,
                                                                                organization_id)

    # first create a caregiver by admin in default org
    default_org_caregiver_auth_token, default_org_caregiver_id = create_single_caregiver(admin_auth_token,
                                                                                         caregiver_template_name,
                                                                                         "00000000-0000-0000-0000-000000000000")

    # update caregiver only for own org
    update_caregiver_response = update_caregiver(org_user_auth_token, new_org_caregiver_id, organization_id,
                                                 "change string")
    assert update_caregiver_response.status_code == 200
    # should fail for caregiver in other org
    update_caregiver_response = update_caregiver(org_user_auth_token, default_org_caregiver_id,
                                                 "00000000-0000-0000-0000-000000000000", "change string")

    assert update_caregiver_response.status_code == 403

    # enable/disable only in same organization
    change_caregiver_state_response = change_caregiver_state(org_user_auth_token, default_org_caregiver_id, "ENABLED")
    assert change_caregiver_state_response.status_code == 403
    change_caregiver_state_response = change_caregiver_state(org_user_auth_token, new_org_caregiver_id, "ENABLED")
    assert change_caregiver_state_response.status_code == 200

    # resend invitation only for admins and only in same org
    # create another caregiver without accepting invitation
    test_name2 = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                  "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email2 = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_caregiver_create_response = create_caregiver(org_user_auth_token, test_name2, email2, caregiver_template_name,
                                                      organization_id)
    assert test_caregiver_create_response.status_code == 201
    new_org_caregiver2_id = test_caregiver_create_response.json()['_id']
    resend_invitation_response = resend_invitation(org_user_auth_token, new_org_caregiver2_id)
    assert resend_invitation_response.status_code == 403
    resend_invitation_response = resend_invitation(org_admin_auth_token, new_org_caregiver2_id)
    assert resend_invitation_response.status_code == 200

    # get caregiver only in same organization
    get_caregiver_response = get_caregiver(org_user_auth_token, new_org_caregiver_id)  # same org
    assert get_caregiver_response.status_code == 200
    get_caregiver_response = get_caregiver(org_user_auth_token, default_org_caregiver_id)  # other org patient
    assert get_caregiver_response.status_code == 403

    # search caregiver only in same organization

    get_caregiver_list_response = get_caregiver_list(org_user_auth_token)
    assert get_caregiver_list_response.status_code == 200
    assert get_caregiver_list_response.json()['metadata']['page']['totalResults'] == 2

    # delete caregiver only in same organization
    test_caregiver_delete_response = delete_caregiver(org_user_auth_token, default_org_caregiver_id)
    assert test_caregiver_delete_response.status_code == 403
    test_caregiver_delete_response = delete_caregiver(org_user_auth_token, new_org_caregiver_id)
    assert test_caregiver_delete_response.status_code == 204

    # Teardown

    delete_caregiver_response = delete_caregiver(admin_auth_token, default_org_caregiver_id)
    assert delete_caregiver_response.status_code == 204
    delete_caregiver_response = delete_caregiver(admin_auth_token, new_org_caregiver2_id)
    assert delete_caregiver_response.status_code == 204
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204
    delete_org_response = delete_organization(admin_auth_token, organization_id)
    assert delete_org_response.status_code == 204


# @pytest.mark.skip
def test_org_user_devices_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        organization_id)
    # create a device by admin in new org
    device_template_id, device_template_name, device_template_display_name = (
        create_template_setup(admin_auth_token, organization_id, "device", None))
    create_device_response = create_device_without_registration_code(admin_auth_token, device_template_name,
                                                                     organization_id)
    assert create_device_response.status_code == 201
    device_new_id = create_device_response.json()['_id']
    # create device by admin in default org
    create_device_response = create_device_without_registration_code(admin_auth_token, "DeviceType1",
                                                                     "00000000-0000-0000-0000-000000000000")
    assert create_device_response.status_code == 201
    device_default_id = create_device_response.json()['_id']

    # create device by org_user fails
    create_device_response = create_device_without_registration_code(org_user_auth_token, device_template_name,
                                                                     organization_id)
    assert create_device_response.status_code == 403

    # update device by org_user only in same org
    update_device_response = update_device(org_user_auth_token, device_new_id, "change_string", None)
    assert update_device_response.status_code == 200
    update_device_response = update_device(org_user_auth_token, device_default_id, "change_string", None)
    assert update_device_response.status_code == 403

    # delete device by org_user fails
    delete_device_response = delete_device(org_user_auth_token, device_new_id)
    assert delete_device_response.status_code == 403

    # get device succeeds for only in same organization
    get_device_response = get_device(org_user_auth_token, device_new_id)
    assert get_device_response.status_code == 200
    get_device_response = get_device(org_user_auth_token, device_default_id)
    assert get_device_response.status_code == 403

    # search device by org_user only in same org
    # Positive - for self
    get_device_list_response = get_device_list(org_user_auth_token)
    assert get_device_list_response.status_code == 200
    assert get_device_list_response.json()['metadata']['page']['totalResults'] == 1

    # Teardown
    delete_device_response = delete_device(admin_auth_token, device_new_id)
    assert delete_device_response.status_code == 204
    delete_device_response = delete_device(admin_auth_token, device_default_id)
    assert delete_device_response.status_code == 204
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, device_template_id)
    assert delete_template_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204
    delete_org_response = delete_organization(admin_auth_token, organization_id)
    assert delete_org_response.status_code == 204


# @pytest.mark.skip
def test_org_user_generic_entity_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        organization_id)

    # create generic entity template in both organizations
    generic_entity_template_id = create_template_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                                       "generic-entity", None)[0]
    generic_entity_template_id2 = create_template_setup(admin_auth_token, organization_id,
                                                        "generic-entity", None)[0]
    # NOTE: function returns tuple. First element is id

    # create generic entity by org_user only for self organization
    create_generic_entity_response = create_generic_entity(org_user_auth_token, generic_entity_template_id,
                                                           f'generic_entity_{uuid.uuid4().hex}'[0:31],
                                                           "00000000-0000-0000-0000-000000000000")
    assert create_generic_entity_response.status_code == 403

    create_generic_entity_response = create_generic_entity(org_user_auth_token, generic_entity_template_id2,
                                                           f'generic_entity_{uuid.uuid4().hex}'[0:31], organization_id)
    assert create_generic_entity_response.status_code == 201
    entity_id = create_generic_entity_response.json()["_id"]

    # update generic entity by org_user only for self organization
    # create second generic entity by admin on default organization
    create_generic_entity_response2 = create_generic_entity(admin_auth_token, generic_entity_template_id,
                                                            f'generic_entity_{uuid.uuid4().hex}'[0:31],
                                                            "00000000-0000-0000-0000-000000000000")
    assert create_generic_entity_response2.status_code == 201

    entity2_id = create_generic_entity_response2.json()["_id"]

    # positive - same organization
    update_generic_entity_response = update_generic_entity(org_user_auth_token, entity_id, "change string")
    assert update_generic_entity_response.status_code == 200
    # Negative - second organization
    update_generic_entity_response = update_generic_entity(org_user_auth_token, entity2_id, "change string")
    assert update_generic_entity_response.status_code == 403

    # get only for same organization
    get_generic_entity_response = get_generic_entity(org_user_auth_token, entity_id)
    assert get_generic_entity_response.status_code == 200
    get_generic_entity_response = get_generic_entity(org_user_auth_token, entity2_id)
    assert get_generic_entity_response.status_code == 403

    # search only for same organization
    get_generic_entity_list_response = get_generic_entity_list(org_user_auth_token)
    assert get_generic_entity_list_response.status_code == 200

    assert get_generic_entity_list_response.json()['metadata']['page']['totalResults'] == 1

    # delete only for same organization
    delete_generic_entity_response = delete_generic_entity(org_user_auth_token, entity_id)
    assert delete_generic_entity_response.status_code == 204
    # should fail for generic entity in other organization
    delete_generic_entity_response = delete_generic_entity(org_user_auth_token, entity2_id)
    assert delete_generic_entity_response.status_code == 403

    # Teardown
    # delete second generic entity created
    delete_generic_entity_response = delete_generic_entity(admin_auth_token, entity2_id)
    assert delete_generic_entity_response.status_code == 204
    # delete org_user
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"
    # delete generic entity templates
    delete_generic_entity_template_response = delete_template(admin_auth_token, generic_entity_template_id)
    assert delete_generic_entity_template_response.status_code == 204
    delete_generic_entity_template_response = delete_template(admin_auth_token, generic_entity_template_id2)
    assert delete_generic_entity_template_response.status_code == 204
    # delete org_user template
    delete_generic_entity_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_generic_entity_template_response.status_code == 204
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_org_user_registration_codes_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # Setup
    # first create new organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        organization_id)

    # create registration code by org_user in new organization should succeed
    registration_code1 = str(uuid.uuid4())
    create_registration_code1_response = create_registration_code(org_user_auth_token, "RegistrationCode",
                                                                  registration_code1, organization_id)
    assert create_registration_code1_response.status_code == 201
    registration_code1_id = create_registration_code1_response.json()['_id']

    # create registration code by org_user of different organization should fail
    registration_code2 = str(uuid.uuid4())
    create_registration_code2_response = create_registration_code(org_user_auth_token, "RegistrationCode",
                                                                  registration_code2,
                                                                  "00000000-0000-0000-0000-000000000000")
    assert create_registration_code2_response.status_code == 403

    # create a registration code by admin in default organization for negative update tests
    create_registration_code2_response = create_registration_code(admin_auth_token, "RegistrationCode",
                                                                  registration_code2,
                                                                  "00000000-0000-0000-0000-000000000000")
    assert create_registration_code2_response.status_code == 201
    registration_code2_id = create_registration_code2_response.json()['_id']

    # update registration code should succeed in same organization (code1 - using same code)
    update_registration_code_response = update_registration_code(org_user_auth_token, registration_code1_id,
                                                                 str(uuid.uuid4()))
    assert update_registration_code_response.status_code == 200

    # update registration code (code2) by or_user of default organization should fail
    update_registration_code_response = update_registration_code(org_user_auth_token, registration_code2_id,
                                                                 str(uuid.uuid4()))
    assert update_registration_code_response.status_code == 403

    # get in same org should succeed
    get_registration_code_response = get_registration_code(org_user_auth_token, registration_code1_id)
    assert get_registration_code_response.status_code == 200

    # get in different org should fail
    get_registration_code_response = get_registration_code(org_user_auth_token, registration_code2_id)
    assert get_registration_code_response.status_code == 403

    # search in same org should succeed
    get_registration_code_list_response = get_registration_code_list(org_user_auth_token)
    assert get_registration_code_list_response.status_code == 200
    assert get_registration_code_list_response.json()['metadata']['page']['totalResults'] == 1

    # delete in same org should succeed
    delete_registration_response = delete_registration_code(org_user_auth_token, registration_code1_id)
    assert delete_registration_response.status_code == 204

    # delete in different org should fail
    delete_registration_response = delete_registration_code(org_user_auth_token, registration_code2_id)
    assert delete_registration_response.status_code == 403

    # Teardown
    # delete org_user
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"
    # delete org_user template
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204
    # delete registration code of second organization
    delete_registration_response = delete_registration_code(admin_auth_token, registration_code2_id)
    assert delete_registration_response.status_code == 204
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_org_user_files_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # add file attribute to Patient template
    patient_template_id = "a38f32d7-de6c-4252-9061-9bcdc253f6c9"
    get_patient_template_response = get_template(admin_auth_token, patient_template_id)
    assert get_patient_template_response.status_code == 200, f"{get_patient_template_response.text}"
    template_payload = map_template(get_patient_template_response.json())
    file_attribute_name = f'file_attr_integ_test{uuid.uuid4().hex}'[0:36]
    file_attribute = {
        "name": file_attribute_name,
        "type": "FILE",
        "displayName": "file_attr_integ_test",
        "phi": False,
        "validation": {
            "mandatory": False,
            "max": 3221225472
        },
        "selectableValues": [],
        "category": "REGULAR"
    }
    (template_payload['customAttributes']).append(file_attribute)
    update_template_response = update_template(admin_auth_token, patient_template_id, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    primary_admin_auth_token, primary_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)
    # create patient in new org
    patient1_auth_token, patient1_id = create_single_patient(primary_admin_auth_token, organization_id)
    # create patient in default org
    patient2_auth_token, patient2_id = create_single_patient(admin_auth_token)

    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        organization_id)


    # create files in new organization and default
    name = f'test_file{uuid.uuid4().hex}'[0:16]
    mime_type = 'text/plain'
    data = open('./upload-file.txt', 'rb').read()
    create_file_response = create_file(org_user_auth_token, name, mime_type)
    assert create_file_response.status_code == 200
    file1_id = create_file_response.json()['id']
    signed_url = create_file_response.json()['signedUrl']
    upload_response = requests.put(signed_url, data=data, headers={'Content-Type': 'text/plain'})
    assert upload_response.status_code == 200
    create_file2_response = create_file(admin_auth_token, name, mime_type)
    assert create_file2_response.status_code == 200
    file2_id = create_file2_response.json()['id']
    signed_url2 = create_file2_response.json()['signedUrl']
    upload_response = requests.put(signed_url2, data=data, headers={'Content-Type': 'text/plain'})
    assert upload_response.status_code == 200, f"{upload_response.text}"
    # associate files to patients
    update_patient_response = update_patient(admin_auth_token, patient1_id, organization_id, None, None,
                                             {file_attribute_name: {"id": file1_id}})
    assert update_patient_response.status_code == 200, f"{update_patient_response.text}"
    update_patient_response = update_patient(admin_auth_token, patient2_id, "00000000-0000-0000-0000-000000000000",
                                             None, None,
                                             {file_attribute_name: {"id": file2_id}})
    assert update_patient_response.status_code == 200

    # get should succeed only in self organization
    get_file_response = get_file(org_user_auth_token, file1_id)  # should succeed
    assert get_file_response.status_code == 200
    get_file_response = get_file(org_user_auth_token, file2_id)  # should fail
    assert get_file_response.status_code == 403

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient1_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_patient_response = delete_patient(admin_auth_token, patient2_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204

    # revert changes in Patient Template
    get_template_response = get_template(admin_auth_token, patient_template_id)
    template_payload = map_template(get_template_response.json())
    index = 0
    for element in template_payload['customAttributes']:
        if element['name'] == file_attribute_name:
            del template_payload['customAttributes'][index]
            continue
        else:
            index += 1
    update_template_response = update_template(admin_auth_token, patient_template_id, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"


# @pytest.mark.skip
def test_org_user_patient_alerts_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200, f"{get_self_org_response.text}"
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template

    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']
    primary_admin_auth_token, primary_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)

    # create patients in new org and default
    patient1_auth_token, patient1_id = create_single_patient(primary_admin_auth_token, organization_id)
    get_patient_response = get_patient(patient1_auth_token, patient1_id)
    assert get_patient_response.status_code == 200, f"{get_patient_response.text}"
    patient_template_id = get_patient_response.json()['_template']['id']
    patient2_auth_token, patient2_id = create_single_patient(admin_auth_token,
                                                             "00000000-0000-0000-0000-000000000000")

    # create alert template based on patient parent (template1)
    alert_template_name = f'test_patient_alert{uuid.uuid4().hex}'[0:35]
    create_patient_alert_template_response = create_patient_alert_template(admin_auth_token, patient_template_id,
                                                                           alert_template_name)
    assert create_patient_alert_template_response.status_code == 201, f"{create_patient_alert_template_response.text}"
    alert_template1_id = create_patient_alert_template_response.json()['id']
    alert_template1_name = create_patient_alert_template_response.json()['name']

    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin in mew and default organizations
    org_user_new_auth_token, org_user_new_id, password = create_single_org_user(admin_auth_token,
                                                                                org_user_template_name,
                                                                                organization_id)
    org_user_default_auth_token, org_user_default_id, password = create_single_org_user(admin_auth_token,
                                                        org_user_template_name,  "00000000-0000-0000-0000-000000000000")

    # Create/Delete patient-alert by id only in same organization
    create_alert_response = create_patient_alert_by_id(org_user_new_auth_token, patient1_id, alert_template1_id)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_patient_alert_by_id(org_user_new_auth_token, patient2_id, alert_template1_id)
    assert create_alert_response.status_code == 403, f"{create_alert_response.text}"  # other org
    # create an alert in default org for next test
    create_alert_response = create_patient_alert_by_id(org_user_default_auth_token, patient2_id, alert_template1_id)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # other org
    alert2_id = create_alert_response.json()['_id']

    # update patient alert only in same organization
    update_alert_response = update_patient_alert(org_user_new_auth_token, patient1_id, alert_id)
    assert update_alert_response.status_code == 200, f"{update_alert_response.text}"
    update_alert_response = update_patient_alert(org_user_new_auth_token, patient2_id, alert2_id)
    assert update_alert_response.status_code == 403, f"{update_alert_response.text}"

    # get patient alert and search only in same organization
    get_patient_alert_response = get_patient_alert(org_user_new_auth_token, patient1_id, alert_id)
    assert get_patient_alert_response.status_code == 200, f"{get_patient_alert_response.text}"
    get_patient_alert_response = get_patient_alert(org_user_new_auth_token, patient2_id, alert2_id)
    assert get_patient_alert_response.status_code == 403, f"{get_patient_alert_response.text}"

    get_patient_alert_list_response = get_patient_alert_list(org_user_new_auth_token, alert_id)
    assert get_patient_alert_list_response.status_code == 200, f"{get_patient_alert_list_response.text}"
    assert get_patient_alert_list_response.json()['metadata']['page']['totalResults'] == 1, \
        f"{get_patient_alert_list_response.json()['metadata']['page']['totalResults']}"
    get_patient_alert_list_response = get_patient_alert_list(org_user_new_auth_token, alert2_id)
    assert get_patient_alert_list_response.status_code == 200, f"{get_patient_alert_list_response.text}"
    assert get_patient_alert_list_response.json()['metadata']['page']['totalResults'] == 0, \
        f"{get_patient_alert_list_response.json()['metadata']['page']['totalResults']}"

    # get current alerts (nursing station) only in same org
    get_current_alert_response = get_current_patient_alert_list(org_user_new_auth_token, alert_id)
    assert get_current_alert_response.status_code == 200, f"{get_current_alert_response.text}"
    # assert get_current_alert_response.json()['metadata']['page']['totalResults'] == 1, \
    #    f"{get_current_alert_response.json()['metadata']['page']['totalResults']}"
    get_current_alert_response = get_current_patient_alert_list(org_user_new_auth_token, alert2_id)
    assert get_current_alert_response.status_code == 200, f"{get_current_alert_response.text}"
    # assert get_current_alert_response.json()['metadata']['page']['totalResults'] == 0  getting 1

    # delete patient-alert only in same organization
    delete_alert_response = delete_device_alert(primary_admin_auth_token, patient1_id, alert_id)
    assert delete_alert_response.status_code == 403, f"{delete_alert_response.text}"
    delete_alert_response = delete_patient_alert(org_user_new_auth_token, patient1_id, alert_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"  # other org
    delete_alert_response = delete_patient_alert(org_user_default_auth_token, patient2_id, alert2_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"  # same org

    # Create patient-alert by name
    create_alert_response = create_patient_alert_by_name(org_user_new_auth_token, patient1_id, alert_template1_name)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_patient_alert_by_name(org_user_new_auth_token, patient2_id,
                                                         alert_template1_name)
    assert create_alert_response.status_code == 403, f"{create_alert_response.text}"  # other org
    # delete it
    delete_alert_response = delete_patient_alert(org_user_new_auth_token, patient1_id, alert_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"  # same org

    # teardown
    delete_patient_response = delete_patient(admin_auth_token, patient1_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_patient_response = delete_patient(admin_auth_token, patient2_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_default_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_new_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"
    delete_template_response = delete_template(admin_auth_token, alert_template1_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response}"


# @pytest.mark.skip
def test_org_user_measurements_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    aggregated_observation_attribute_name = f'aggr_observ_decimal_int{uuid.uuid4().hex}'[0:36]
    raw_observation_attribute_name = f'raw_observ_waveform{uuid.uuid4().hex}'[0:36]
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200, f"{get_self_org_response.text}"
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']
    # create single patient, registration code and device in default org
    patient_auth_token, patient_id, registration_code_id, device_id = (
        create_single_patient_self_signup(admin_auth_token,
                                          "00000000-0000-0000-0000-000000000000", 'DeviceType1'))

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

    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin in mew and default organizations
    org_user_new_auth_token, org_user_new_id, password = create_single_org_user(admin_auth_token,
                                                                                org_user_template_name,
                                                                                organization_id)
    org_user_default_auth_token, org_user_default_id, password = create_single_org_user(admin_auth_token,
                                                                                        org_user_template_name,
                                                                                        "00000000-0000-0000-0000-000000000000")
    # create usage session template and usage session; associate to patient
    # get the device templateId
    get_device_response = get_device(admin_auth_token, device_id)
    device_template_id = get_device_response.json()['_template']['id']

    # create usage_session template
    usage_template_data = create_template_setup(admin_auth_token, None, "usage-session", device_template_id)
    usage_session_template_name = usage_template_data[1]
    usage_session_template_id = usage_template_data[0]

    # create session by caregiver should succeed for same org
    create_session_response = create_usage_session_by_usage_type(org_user_default_auth_token, device_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 201, f"{create_session_response.text}"
    usage_session_id = create_session_response.json()['_id']
    # create measurement on patient1
    create_measurement_response = create_measurement(org_user_default_auth_token, device_id, patient_id,
                                                     usage_session_id, aggregated_observation_attribute_name)
    assert create_measurement_response.status_code == 200, f"{create_measurement_response.text}"
    # create bulk measurement
    create_bulk_measurement_response = create_bulk_measurement(org_user_default_auth_token, device_id,
                                                               patient_id, usage_session_id,
                                                               aggregated_observation_attribute_name)
    assert create_bulk_measurement_response.status_code == 200, f"{create_bulk_measurement_response.text}"

    # get v1 raw measurements should succeed for same org caregiver
    get_v1_measurement_response = get_raw_measurements(org_user_default_auth_token, patient_id,
                                                       raw_observation_attribute_name)
    assert get_v1_measurement_response.status_code == 200, f"{get_v1_measurement_response.text}"
    # fail for other org caregiver
    get_v1_measurement_response = get_raw_measurements(org_user_new_auth_token, patient_id,
                                                       raw_observation_attribute_name)
    assert get_v1_measurement_response.status_code == 403, f"{get_v1_measurement_response.text}"

    # get v1 aggregated measurements should succeed for same org caregiver
    get_v1_measurement_response = get_aggregated_measurements(org_user_default_auth_token, patient_id,
                                                              aggregated_observation_attribute_name)
    assert get_v1_measurement_response.status_code == 200, f"{get_v1_measurement_response.text}"
    # fail for other org caregiver
    get_v1_measurement_response = get_aggregated_measurements(org_user_new_auth_token, patient_id,
                                                              aggregated_observation_attribute_name)
    assert get_v1_measurement_response.status_code == 403, f"{get_v1_measurement_response.text}"

    # get V2 raw measurements should succeed for same org caregiver
    get_v2_measurement_response = get_v2_raw_measurements(org_user_default_auth_token, patient_id,
                                                          raw_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 200, f"{get_v2_measurement_response.text}"
    # fail for other org caregiver
    get_v2_measurement_response = get_v2_raw_measurements(org_user_new_auth_token, patient_id,
                                                          raw_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 403, f"{get_v2_measurement_response.text}"

    # get v2 aggregated measurements should succeed for same org caregiver
    get_v2_measurement_response = get_v2_aggregated_measurements(org_user_default_auth_token, patient_id,
                                                                 aggregated_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 200, f"{get_v2_measurement_response.text}"
    # fail for other org caregiver
    get_v2_measurement_response = get_v2_aggregated_measurements(org_user_new_auth_token, patient_id,
                                                                 aggregated_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 403, f"{get_v2_measurement_response.text}"

    # get device credentials should always succeed (try with caregiver from new org)
    get_credentials_response = get_device_credentials(org_user_new_auth_token)
    assert get_credentials_response.status_code == 200, f"{get_credentials_response.text}"

    # teardown
    delete_usage_session_response = delete_usage_session(admin_auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, usage_session_template_id)
    assert delete_template_response.status_code == 204

    single_self_signup_patient_teardown(admin_auth_token, patient_id, registration_code_id, device_id)

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_default_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_new_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"


# @pytest.mark.skip
def test_org_user_ums_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create org_user by admin in default organization
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin (also tests login)
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        "00000000-0000-0000-0000-000000000000")
    org_user_email = get_self_user_email(org_user_auth_token)

    # set password by org_user
    new_password = "Bb234567NewPass"
    set_password_response = set_password(org_user_auth_token, password, new_password)
    assert set_password_response.status_code == 200
    # check login with new password
    caregiver_auth_token = login_with_credentials(org_user_email, new_password)

    # forgot password flow
    forgot_password_response = forgot_password(org_user_email)
    new_password = "Cc345678NewPass2"
    reset_password_open_email_and_set_new_password(org_user_email, new_password)
    # check login with new password
    caregiver_auth_token = login_with_credentials(org_user_email, new_password)

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_org_user_locales_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create org_user by admin in default organization
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin (also tests login)
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        "00000000-0000-0000-0000-000000000000")

    # get available locales should succeed
    get_locales_response = get_available_locales(org_user_auth_token)
    assert get_locales_response.status_code == 200

    # add locale should fail
    code = 'en-us'
    add_locale_response = add_locale(org_user_auth_token, code)
    assert add_locale_response.status_code == 403

    # delete locale should fail
    locale_id = 'any'
    delete_locale_response = delete_locale(org_user_auth_token, locale_id)
    assert delete_locale_response.status_code == 403

    # update locale should fail
    update_locale_response = update_locale(org_user_auth_token, code)
    assert update_locale_response.status_code == 403

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_org_user_plugins_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create org_user by admin in default organization
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin (also tests login)
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        "00000000-0000-0000-0000-000000000000")

    # create plugin should fail
    create_plugin_response = create_plugin(org_user_auth_token, 'test_plugin')
    assert create_plugin_response.status_code == 403

    # delete plugin should fail
    delete_plugin_response = delete_plugin(org_user_auth_token, 'test_plugin')
    assert delete_plugin_response.status_code == 403

    # update plugin should fail
    update_plugin_response = update_plugin(org_user_auth_token, 'test_plugin', 'test_plugin')
    assert update_plugin_response.status_code == 403

    # get plugin should fail
    get_plugin_response = get_plugin(org_user_auth_token, 'test_plugin')
    assert get_plugin_response.status_code == 403

    # search plugin should fail
    search_plugin_response = get_plugin_list(org_user_auth_token, 'test_plugin')
    assert search_plugin_response.status_code == 403

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_org_user_dms_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create org_user by admin in default organization
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create 2 org_users by admin
    org_user1_auth_token, org_user1_id, password1 = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                           "00000000-0000-0000-0000-000000000000")
    org_user2_auth_token, org_user2_id, password2 = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                           "00000000-0000-0000-0000-000000000000")

    # create_report should succeed
    create_report_response = create_report(org_user1_auth_token)
    assert create_report_response.status_code == 201, f"{create_report_response.text}"
    report_id = create_report_response.json()['id']

    # get report should succeed for self
    get_report_response = get_report(org_user1_auth_token, report_id)
    assert get_report_response.status_code == 200, f"{get_report_response.text}"
    get_report_response = get_report(org_user2_auth_token, report_id)
    assert get_report_response.status_code == 403, f"{get_report_response.text}"

    # search report should succeed
    search_report_response = get_report_list(org_user1_auth_token)
    assert search_report_response.status_code == 200, f"{search_report_response.text}"

    # delete report should succeed
    delete_report_response = delete_report(org_user1_auth_token, report_id)
    assert delete_report_response.status_code == 204, f"{delete_report_response.text}"

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user1_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user2_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"
    delete_caregiver_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_caregiver_template_response.status_code == 204, f"{delete_caregiver_template_response.text}"


# @pytest.mark.skip
def test_org_user_templates_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        "00000000-0000-0000-0000-000000000000")

    # view templates should succeed
    view_template_response = get_templates_list(org_user_auth_token)
    assert view_template_response.status_code == 200
    get_minimized_response = get_all_templates(org_user_auth_token)
    assert get_minimized_response.status_code == 200

    # extract valid id and parentId
    template_id = get_minimized_response.json()['data'][0]['id']
    parent_template_id = get_minimized_response.json()['data'][0]['parentTemplateId']

    # get by id should succeed

    get_template_response = get_template_by_id(org_user_auth_token, template_id)
    assert get_template_response.status_code == 200

    # get overview should fail
    get_overview_response = get_template_overview(org_user_auth_token, template_id)
    assert get_overview_response.status_code == 403

    # delete should fail
    delete_template_response = delete_template(org_user_auth_token, template_id)
    assert delete_template_response.status_code == 403

    # create should fail
    create_template_response = create_generic_template(org_user_auth_token)
    assert create_template_response.status_code == 403

    # update should fail
    payload = get_template_response.json()
    update_template_response = update_template(org_user_auth_token, template_id, payload)

    assert update_template_response.status_code == 403

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_org_user_portal_builder_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        "00000000-0000-0000-0000-000000000000")

    # view full info should succeed
    view_template_response = get_templates_list(org_user_auth_token)
    assert view_template_response.status_code == 200
    get_minimized_response = get_all_templates(org_user_auth_token)
    assert get_minimized_response.status_code == 200

    # extract valid id and parentId
    template_id = get_minimized_response.json()['data'][0]['id']
    view_portal_response = view_full_portal_information(org_user_auth_token, 'ORGANIZATION_PORTAL', 'ENTITY_LIST',
                                                        None)
    assert view_portal_response.status_code == 200
    payload = view_portal_response.json()
    view_id = payload['id']
    # update views should fail
    update_portal_view_response = update_portal_views(org_user_auth_token, 'ORGANIZATION_PORTAL', view_id, payload)
    assert update_portal_view_response.status_code == 403

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_org_user_adb_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin
    org_user_auth_token, org_user_id, password = create_single_org_user(admin_auth_token, org_user_template_name,
                                                                        "00000000-0000-0000-0000-000000000000")

    # deploy adb should fail
    deploy_response = deploy_adb(org_user_auth_token)
    assert deploy_response.status_code == 403

    # undeploy should fail
    undeploy_response = undeploy_adb(org_user_auth_token)
    assert undeploy_response.status_code == 403

    # start init should fail
    start_init_response = start_init_adb(org_user_auth_token)
    assert start_init_response.status_code == 403

    # stop init should fail
    stop_init_response = stop_init_adb(org_user_auth_token)
    assert stop_init_response.status_code == 403

    # stop sync should fail
    stop_sync_response = stop_sync_adb(org_user_auth_token)
    assert stop_sync_response.status_code == 403

    # get adb info should succeed
    get_adb_response = get_adb_info(org_user_auth_token)
    assert get_adb_response.status_code == 200

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_org_user_usage_session_abac_rules():  # IP
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200, f"{get_self_org_response.text}"
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']
    # create single patient, registration code and device in default org
    patient_auth_token, patient_id, registration_code_id, device_id = (
        create_single_patient_self_signup(admin_auth_token,
                                          "00000000-0000-0000-0000-000000000000", 'DeviceType1'))
    # create a second device in default org
    create_device_response = create_device_without_registration_code(admin_auth_token, 'DeviceType1',
                                                                     "00000000-0000-0000-0000-000000000000")
    assert create_device_response.status_code == 201, f"{create_device_response.text}"
    device2_id = create_device_response.json()['_id']
    # associate patient with 2nd device
    # update_device_response = update_device(admin_auth_token, device2_id, "change_string", patient_id)
    # assert update_device_response.status_code == 200, f"{update_device_response.text}"

    # create organization user
    create_template_response = create_org_user_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']
    # create org_user by admin in mew and default organizations
    org_user_new_auth_token, org_user_new_id, password = create_single_org_user(admin_auth_token,
                                                                                org_user_template_name,
                                                                                organization_id)
    org_user_default_auth_token, org_user_default_id, password = create_single_org_user(admin_auth_token,
                                                    org_user_template_name, "00000000-0000-0000-0000-000000000000")

    # get the device templateId
    get_device_response = get_device(admin_auth_token, device_id)
    device_template_id = get_device_response.json()['_template']['id']
    # create usage_session template
    usage_template_data = create_template_setup(admin_auth_token, None,
                                                "usage-session", device_template_id)
    usage_session_template_name = usage_template_data[1]
    usage_session_template_id = usage_template_data[0]

    # create session should succeed for caregiver in same org
    create_session_response = create_usage_session_by_usage_type(org_user_default_auth_token, device_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 201, f"{create_session_response.text}"
    usage_session_id = create_session_response.json()['_id']
    # create session should fail for caregiver in other org
    create_session_response = create_usage_session_by_usage_type(org_user_new_auth_token, device_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 403, f"{create_session_response.text}"

    # update session should succeed for caregiver in same org and fail for caregiver in other org
    update_session_response = update_usage_session(org_user_default_auth_token, device_id, usage_session_id)
    assert update_session_response.status_code == 200, f"{update_session_response.text}"
    update_session_response = update_usage_session(org_user_new_auth_token, device_id, usage_session_id)
    assert update_session_response.status_code == 403, f"{update_session_response.text}"

    # get session should succeed only for same org
    get_session_response = get_usage_session(org_user_default_auth_token, device_id, usage_session_id)
    assert get_session_response.status_code == 200, f"{get_session_response.text}"
    get_session_response = get_usage_session(org_user_new_auth_token, device_id, usage_session_id)
    assert get_session_response.status_code == 403, f"{get_session_response.text}"

    # search usage session by caregiver only in same org
    # Positive - for same
    get_session_list_response = get_usage_session_list(org_user_default_auth_token)
    assert get_session_list_response.status_code == 200, f"{get_session_list_response.text}"
    assert get_session_list_response.json()['metadata']['page']['totalResults'] != 0, \
        f"{get_session_list_response.json()['metadata']['page']['totalResults']}"
    # negative: other caregiver should get zero results
    get_session_list_response = get_usage_session_list(org_user_new_auth_token)
    assert get_session_list_response.status_code == 200, f"{get_session_list_response.text}"
    assert get_session_list_response.json()['metadata']['page']['totalResults'] == 0, \
        f"{get_session_list_response.json()['metadata']['page']['totalResults']}"

    # delete session by caregiver should succeed for same org and fail for other org
    delete_session_response = delete_usage_session(org_user_new_auth_token, device_id, usage_session_id)
    assert delete_session_response.status_code == 403, f"{delete_session_response.text}"
    delete_session_response = delete_usage_session(org_user_default_auth_token, device_id, usage_session_id)
    assert delete_session_response.status_code == 204, f"{delete_session_response.text}"

    # patient_template_id = get_patient(admin_auth_token, patient_id).json()['_template']['id']
    # patient_template = get_template_by_id(admin_auth_token, patient_template_id)

    # start simulator with device2
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()
    assert sim_status == "NO_RUNNING_SIMULATION", "Simulator failed to start"
    start_simulation_with_existing_device(device2_id, os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # start session only in same organization
    start_session_response = start_usage_session(org_user_new_auth_token, device2_id, usage_session_template_id,
                                                 patient_id)
    assert start_session_response.status_code == 403, f"{start_session_response.text}"
    start_session_response = start_usage_session(org_user_default_auth_token, device2_id, usage_session_template_id,
                                                 patient_id)
    assert start_session_response.status_code == 201, f"{start_session_response.text}"
    usage_session2_id = start_session_response.json()['_id']

    # pause only for same organization; first make sure it's active

    get_usage_session_response = get_usage_session(org_user_default_auth_token, device2_id, usage_session2_id)
    assert get_usage_session_response.status_code == 200, f"{get_usage_session_response.text}"
    while get_usage_session_response.json()["_state"] != 'ACTIVE':
        get_usage_session_response = get_usage_session(org_user_default_auth_token, device2_id, usage_session2_id)
        if get_usage_session_response.json()["_state"] == 'DONE':  # restart simulation
            break
        assert get_usage_session_response.status_code == 200, f"{get_usage_session_response.text}"

    assert get_usage_session_response.json()["_state"] == "ACTIVE", \
        f"The current status is {get_usage_session_response.json()['_state']}, not 'ACTIVE', simulator timeout"

    pause_session_response = pause_usage_session(org_user_new_auth_token, device2_id, usage_session2_id)
    assert pause_session_response.status_code == 403, f"{pause_session_response.text}"
    pause_session_response = pause_usage_session(org_user_default_auth_token, device2_id, usage_session2_id)
    assert pause_session_response.status_code == 200, f"{pause_session_response.text}"
    get_usage_session_response = get_usage_session(org_user_default_auth_token, device2_id, usage_session2_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "PAUSED", f"The current status is {usage_session_status}, not 'PAUSED'"

    # resume session (should succeed only for self)
    resume_usage_session_response = resume_usage_session(org_user_new_auth_token, device2_id, usage_session2_id)
    assert resume_usage_session_response.status_code == 403
    resume_usage_session_response = resume_usage_session(org_user_default_auth_token, device2_id, usage_session2_id)
    assert resume_usage_session_response.status_code == 200, f"{resume_usage_session_response.text}"
    get_usage_session_response = get_usage_session(org_user_default_auth_token, device2_id, usage_session2_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "ACTIVE", f"The current status is {usage_session_status}, not 'ACTIVE'"

    # Stop a Remote usage session - succeed for own organization
    stop_usage_session_response = stop_usage_session(org_user_default_auth_token, device2_id, usage_session2_id)
    assert stop_usage_session_response.status_code == 200, f"{stop_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(org_user_default_auth_token, device2_id, usage_session2_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "DONE", f"The current status is {usage_session_status}, not 'DONE'"

    # Teardown
    # stop simulation
    stop_simulation()
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()

    delete_session_response = delete_usage_session(admin_auth_token, device2_id, usage_session2_id)
    assert delete_session_response.status_code == 204, f"{delete_session_response.text}"

    delete_template_response = delete_template(admin_auth_token, usage_session_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    single_self_signup_patient_teardown(admin_auth_token, patient_id, registration_code_id, device_id)

    delete_device_response = delete_device(admin_auth_token, device2_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_default_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_org_user_response = delete_organization_user(admin_auth_token, org_user_new_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"

    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"
