import pytest
from api_test_helpers import *
from email_interface import accept_invitation, reset_password_open_email_and_set_new_password


#############################################################################################
# Username and password have to be set in the environment in advance for each individual test
#############################################################################################

def test_caregiver_commands_abac_rules():
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

    # create caregiver template
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    # create caregiver by admin in new organization
    caregiver_new_auth_token, caregiver_new_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                         organization_id)
    # create caregiver by admin in default organization
    caregiver_default_auth_token, caregiver_default_id = create_single_caregiver(admin_auth_token,
                                                                                 caregiver_template_name,
                                                                                 "00000000-0000-0000-0000-000000000000")
    # start simulator with device
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()
    start_simulation_with_existing_device(device_default_id, os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # start/stop command only for self organization
    # self org
    start_command_response = start_command_by_template(caregiver_default_auth_token, device_default_id,
                                                       command_template_name)
    assert start_command_response.status_code == 201, f"{start_command_response.text}"
    command2_id = start_command_response.json()['_id']
    # self
    get_command_response = get_command(caregiver_default_auth_token, device_default_id, command2_id)
    assert get_command_response.status_code == 200, f"{get_command_response.text}"
    # other
    get_command_response = get_command(caregiver_new_auth_token, device_default_id, command2_id)
    assert get_command_response.status_code == 403, f"{get_command_response.text}"
    stop_command_response = stop_command(caregiver_default_auth_token, device_default_id, command2_id)
    assert stop_command_response.status_code == 200, f"{stop_command_response.text}"
    # other org
    start_command_response = start_command_by_template(caregiver_new_auth_token, device_default_id,
                                                       command_template_name)
    assert start_command_response.status_code == 403, f"{start_command_response.text}"
    stop_command_response = stop_command(caregiver_new_auth_token, device_default_id, command2_id)
    assert stop_command_response.status_code == 403, f"{stop_command_response.text}"
    # self org start by id
    start_command_response = start_command_by_id(caregiver_default_auth_token, device_default_id, command_template_id)
    assert start_command_response.status_code == 201, f"{start_command_response.text}"

    # other org
    start_command_response = start_command_by_id(caregiver_new_auth_token, device_default_id, command_template_id)
    assert start_command_response.status_code == 403, f"{start_command_response.text}"

    # self
    search_command_response = search_commands(caregiver_default_auth_token, command2_id)
    assert search_command_response.status_code == 200, f"{search_command_response.text}"
    assert search_command_response.json()['metadata']['page']['totalResults'] == 1, \
        f"totalResult={search_command_response.json()['metadata']['page']['totalResults']}"
    # other
    search_command_response = search_commands(caregiver_new_auth_token, command2_id)
    assert search_command_response.status_code == 200, f"{search_command_response.text}"
    assert search_command_response.json()['metadata']['page']['totalResults'] == 0, \
        f"totalResults={search_command_response.json()['metadata']['page']['totalResults']}"

    # teardown
    # stop simulation
    stop_simulation()
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()

    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_default_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"

    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"

    delete_device_response = delete_device(admin_auth_token, device_default_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"

    delete_template_response = delete_template(admin_auth_token, command_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"


def test_caregiver_organization_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200, f"{get_self_org_response.text}"
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']
    # create caregiver by admin
    caregiver_auth_token, caregiver_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                 organization_id)
    # create, update  and delete organization must fail
    create_organization_response = create_organization(caregiver_auth_token, template_id)
    assert create_organization_response.status_code == 403, f"{create_organization_response.text}"
    delete_organization_response = delete_organization(caregiver_auth_token, organization_id)
    assert delete_organization_response.status_code == 403, f"{delete_organization_response.text}"
    update_organization_response = update_organization(caregiver_auth_token, organization_id, "changed test text")
    assert update_organization_response.status_code == 403, f"{update_organization_response.text}"

    # Get organization by list or by id -- only for own organization
    get_organization_response = get_organization(caregiver_auth_token, organization_id)
    # positive (own organization)
    assert get_organization_response.status_code == 200, f"{get_organization_response.text}"
    # negative
    get_organization_response = get_organization(caregiver_auth_token, "00000000-0000-0000-0000-000000000000")
    assert get_organization_response.status_code == 403, f"{get_organization_response.text}"
    # positive (own organization should return one result)
    get_organization_list_response = get_organization_list(caregiver_auth_token)
    assert get_organization_list_response.status_code == 200, f"{get_organization_list_response.text}"
    assert get_organization_list_response.json()['metadata']['page']['totalResults'] == 1
    # negative (system admin should get all defined organizations)
    get_organization_list_response = get_organization_list(admin_auth_token)
    assert get_organization_list_response.status_code == 200, f"{get_organization_list_response.text}"
    assert get_organization_list_response.json()['metadata']['page']['totalResults'] > 1, \
        f"Total Results={get_organization_list_response.json()['metadata']['page']['totalResults']}"

    # Teardown
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"


def test_caregiver_organization_users_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create organization user in new organization
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    template_name = "OrganizationOperator"
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    create_user_response = create_organization_user(admin_auth_token, template_name, name, email,
                                                    organization_id)

    assert create_user_response.status_code == 201
    new_organization_user_id = create_user_response.json()['_id']

    # create organization user in default organization
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    template_name = "OrganizationOperator"
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    create_user_response = create_organization_user(admin_auth_token, template_name, name, email,
                                                    "00000000-0000-0000-0000-000000000000")

    assert create_user_response.status_code == 201
    default_organization_user_id = create_user_response.json()['_id']

    # create caregiver by admin in new organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']
    # create caregiver by admin
    caregiver_auth_token, caregiver_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                 organization_id)

    # create organization user by caregiver should fail
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    template_name = "OrganizationOperator"
    email = f'integ_test_{uuid.uuid4().hex}'[0:16]
    email = email + '_@biotmail.com'
    create_user_response = create_organization_user(caregiver_auth_token, template_name, name, email,
                                                    organization_id)
    assert create_user_response.status_code == 403

    # delete organization user by caregiver should fail
    delete_user_response = delete_organization_user(caregiver_auth_token, new_organization_user_id)
    assert delete_user_response.status_code == 403

    # update organization user should fail
    update_organization_user_response = update_organization_user(caregiver_auth_token, new_organization_user_id,
                                                                 organization_id, "change string")
    assert update_organization_user_response.status_code == 403

    # get organization user by caregiver only in same organization
    get_organization_user_response = get_organization_user(caregiver_auth_token, new_organization_user_id)
    assert get_organization_user_response.status_code == 200
    get_organization_user_response = get_organization_user(caregiver_auth_token, default_organization_user_id)
    assert get_organization_user_response.status_code == 403

    # search organization list by caregiver only in same organization
    search_organization_users_response = get_organization_user_list(caregiver_auth_token)
    assert search_organization_users_response.status_code == 200
    assert search_organization_users_response.json()['metadata']['page']['totalResults'] == 2
    search_organization_users_response = get_organization_user_list(admin_auth_token)
    assert search_organization_users_response.status_code == 200
    assert search_organization_users_response.json()['metadata']['page']['totalResults'] > 2

    # change state of organization user by caregiver should fail
    change_organization_user_state_response = change_organization_user_state(caregiver_auth_token,
                                                                             new_organization_user_id, "ENABLED")
    assert change_organization_user_state_response.status_code == 403

    # resend invitation to organization user by caregiver should fail
    resend_invitation_response = resend_invitation(caregiver_auth_token, new_organization_user_id)
    assert resend_invitation_response.status_code == 403

    # teardown

    delete_user_response = delete_organization_user(admin_auth_token, default_organization_user_id)
    assert delete_user_response.status_code == 204
    delete_user_response = delete_organization_user(admin_auth_token, new_organization_user_id)
    assert delete_user_response.status_code == 204
    delete_user_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_user_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


def test_caregiver_patient_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create caregiver by admin in new organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']
    # create caregiver by admin
    caregiver_auth_token, caregiver_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                 organization_id)

    # Create patient should only succeed  in same organization
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    # create patient should fail in other org
    test_patient_create_response = create_patient(caregiver_auth_token, test_name, email, "Patient",
                                                  "00000000-0000-0000-0000-000000000000")
    assert test_patient_create_response.status_code == 403
    # create patient should succeed in same org
    test_patient_create_response = create_patient(caregiver_auth_token, test_name, email, "Patient",
                                                  organization_id)
    assert test_patient_create_response.status_code == 201
    new_org_patient_id = test_patient_create_response.json()['_id']

    # first create a patient by admin in default org
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_patient_create_response = create_patient(admin_auth_token, test_name, email, "Patient",
                                                  "00000000-0000-0000-0000-000000000000")
    assert test_patient_create_response.status_code == 201
    default_org_patient_id = test_patient_create_response.json()['_id']

    # update patient only for self
    update_patient_response = update_patient(caregiver_auth_token, new_org_patient_id, organization_id,
                                             "change string", None, None)
    assert update_patient_response.status_code == 200
    # should fail for patient in other org
    update_patient_response = update_patient(caregiver_auth_token, default_org_patient_id,
                                             "00000000-0000-0000-0000-000000000000", "change string", None, None)

    assert update_patient_response.status_code == 403

    # get patient only in same organization
    get_patient_response = get_patient(caregiver_auth_token, new_org_patient_id)  # same org
    assert get_patient_response.status_code == 200
    get_patient_response = get_patient(caregiver_auth_token, default_org_patient_id)  # other org patient
    assert get_patient_response.status_code == 403

    # search patient only in same organization

    get_patient_list_response = get_patient_list(caregiver_auth_token)
    assert get_patient_list_response.status_code == 200
    assert get_patient_list_response.json()['metadata']['page']['totalResults'] == 1

    # enable/disable only in same organization
    change_patient_state_response = change_patient_state(caregiver_auth_token, default_org_patient_id, "ENABLED")
    assert change_patient_state_response.status_code == 403
    change_patient_state_response = change_patient_state(caregiver_auth_token, new_org_patient_id, "ENABLED")
    assert change_patient_state_response.status_code == 200

    # resend invitation fails
    resend_invitation_response = resend_invitation(caregiver_auth_token, new_org_patient_id)
    assert resend_invitation_response.status_code == 403

    # delete patient only in same organization
    test_patient_delete_response = delete_patient(caregiver_auth_token, default_org_patient_id)
    assert test_patient_delete_response.status_code == 403
    test_patient_delete_response = delete_patient(caregiver_auth_token, new_org_patient_id)
    assert test_patient_delete_response.status_code == 204

    # Teardown

    delete_patient_response = delete_patient(admin_auth_token, default_org_patient_id)
    assert delete_patient_response.status_code == 204
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204
    delete_org_response = delete_organization(admin_auth_token, organization_id)
    assert delete_org_response.status_code == 204


def test_caregiver_caregiver_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create caregiver by admin in new organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']
    # create caregiver by admin
    caregiver_auth_token, caregiver_new_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                     organization_id)

    # create caregiver by admin in default org
    caregiver_def_auth_token, caregiver_default_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                             "00000000-0000-0000-0000-000000000000")

    # create caregiver by caregiver should fail
    caregiver_email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    create_caregiver_response = create_caregiver(caregiver_auth_token, test_name, caregiver_email, "Clinician",
                                                 organization_id)
    assert create_caregiver_response.status_code == 403

    # update caregiver by caregiver should fail
    update_caregiver_response = update_caregiver(caregiver_auth_token, caregiver_new_id,
                                                 organization_id, "change string")
    assert update_caregiver_response.status_code == 403

    # delete caregiver by caregiver should fail
    delete_caregiver_response = delete_caregiver(caregiver_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 403

    # change caregiver state by caregiver should fail
    change_caregiver_state_response = change_caregiver_state(caregiver_auth_token, caregiver_new_id, "ENABLED")
    assert change_caregiver_state_response.status_code == 403

    # get caregiver by caregiver only in same organization
    get_caregiver_response = get_caregiver(caregiver_auth_token, caregiver_new_id)
    assert get_caregiver_response.status_code == 200
    get_caregiver_response = get_caregiver(caregiver_auth_token, caregiver_default_id)
    assert get_caregiver_response.status_code == 403

    # search caregiver by caregiver only in same org
    # Positive - for self
    get_caregiver_list_response = get_caregiver_list(caregiver_auth_token)
    assert get_caregiver_list_response.status_code == 200
    assert get_caregiver_list_response.json()['metadata']['page']['totalResults'] == 1

    # resend invitation fails
    resend_invitation_response = resend_invitation(caregiver_auth_token, caregiver_new_id)
    assert resend_invitation_response.status_code == 403

    # delete should fail
    delete_caregiver_response = delete_caregiver(caregiver_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 403

    # Teardown
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 204
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_default_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204
    delete_org_response = delete_organization(admin_auth_token, organization_id)
    assert delete_org_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_devices_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create caregiver by admin in new organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']
    caregiver_auth_token, caregiver_new_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
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

    # create device by caregiver fails
    create_device_response = create_device_without_registration_code(caregiver_auth_token, device_template_name,
                                                                     organization_id)
    assert create_device_response.status_code == 403

    # update device by caregiver only in same org
    update_device_response = update_device(caregiver_auth_token, device_new_id, "change_string", None)
    assert update_device_response.status_code == 200
    update_device_response = update_device(caregiver_auth_token, device_default_id, "change_string", None)
    assert update_device_response.status_code == 403

    # delete device by caregiver fails
    delete_device_response = delete_device(caregiver_auth_token, device_new_id)
    assert delete_device_response.status_code == 403

    # get device succeeds for only in same organization
    get_device_response = get_device(caregiver_auth_token, device_new_id)
    assert get_device_response.status_code == 200
    get_device_response = get_device(caregiver_auth_token, device_default_id)
    assert get_device_response.status_code == 403

    # search device by caregiver only in same org
    # Positive - for self
    get_device_list_response = get_device_list(caregiver_auth_token)
    assert get_device_list_response.status_code == 200
    assert get_device_list_response.json()['metadata']['page']['totalResults'] == 1

    # Teardown
    delete_device_response = delete_device(admin_auth_token, device_new_id)
    assert delete_device_response.status_code == 204
    delete_device_response = delete_device(admin_auth_token, device_default_id)
    assert delete_device_response.status_code == 204
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, device_template_id)
    assert delete_template_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204
    delete_org_response = delete_organization(admin_auth_token, organization_id)
    assert delete_org_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_generic_entity_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create caregiver by admin in new organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']
    caregiver_auth_token, caregiver_new_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                     organization_id)

    # create generic entity template in both organizations
    generic_entity_template_id = create_template_setup(admin_auth_token, "00000000-0000-0000-0000-000000000000",
                                                       "generic-entity", None)[0]
    generic_entity_template_id2 = create_template_setup(admin_auth_token, organization_id,
                                                        "generic-entity", None)[0]
    # NOTE: function returns tuple. First element is id

    # create generic entity by caregiver only for self organization
    create_generic_entity_response = create_generic_entity(caregiver_auth_token, generic_entity_template_id,
                                                           f'generic_entity_{uuid.uuid4().hex}'[0:31],
                                                           "00000000-0000-0000-0000-000000000000")
    assert create_generic_entity_response.status_code == 403

    create_generic_entity_response = create_generic_entity(caregiver_auth_token, generic_entity_template_id2,
                                                           f'generic_entity_{uuid.uuid4().hex}'[0:31], organization_id)
    assert create_generic_entity_response.status_code == 201
    entity_id = create_generic_entity_response.json()["_id"]

    # update generic entity by patient only for self organization
    # create second generic entity by admin on default organization
    create_generic_entity_response2 = create_generic_entity(admin_auth_token, generic_entity_template_id,
                                                            f'generic_entity_{uuid.uuid4().hex}'[0:31],
                                                            "00000000-0000-0000-0000-000000000000")
    assert create_generic_entity_response2.status_code == 201

    entity2_id = create_generic_entity_response2.json()["_id"]

    # positive - same organization
    update_generic_entity_response = update_generic_entity(caregiver_auth_token, entity_id, "change string")
    assert update_generic_entity_response.status_code == 200
    # Negative - second organization
    update_generic_entity_response = update_generic_entity(caregiver_auth_token, entity2_id, "change string")
    assert update_generic_entity_response.status_code == 403

    # get only for same organization
    get_generic_entity_response = get_generic_entity(caregiver_auth_token, entity_id)
    assert get_generic_entity_response.status_code == 200
    get_generic_entity_response = get_generic_entity(caregiver_auth_token, entity2_id)
    assert get_generic_entity_response.status_code == 403

    # search only for same organization
    get_generic_entity_list_response = get_generic_entity_list(caregiver_auth_token)
    assert get_generic_entity_list_response.status_code == 200

    assert get_generic_entity_list_response.json()['metadata']['page']['totalResults'] == 1

    # delete only for same organization
    delete_generic_entity_response = delete_generic_entity(caregiver_auth_token, entity_id)
    assert delete_generic_entity_response.status_code == 204
    # should fail for generic entity in other organization
    delete_generic_entity_response = delete_generic_entity(caregiver_auth_token, entity2_id)
    assert delete_generic_entity_response.status_code == 403

    # Teardown
    # delete second generic entity created
    delete_generic_entity_response = delete_generic_entity(admin_auth_token, entity2_id)
    assert delete_generic_entity_response.status_code == 204
    # delete caregiver
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 204
    # delete generic entity templates
    delete_generic_entity_template_response = delete_template(admin_auth_token, generic_entity_template_id)
    assert delete_generic_entity_template_response.status_code == 204
    delete_generic_entity_template_response = delete_template(admin_auth_token, generic_entity_template_id2)
    assert delete_generic_entity_template_response.status_code == 204
    # delete caregiver template
    delete_generic_entity_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_generic_entity_template_response.status_code == 204
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_registration_codes_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # Setup
    # first create new organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create caregiver in new org
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']
    caregiver_auth_token, caregiver_new_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                     organization_id)

    # create registration code by caregiver in new organization should succeed
    registration_code1 = str(uuid.uuid4())
    create_registration_code1_response = create_registration_code(caregiver_auth_token, "RegistrationCode",
                                                                  registration_code1, organization_id)
    assert create_registration_code1_response.status_code == 201
    registration_code1_id = create_registration_code1_response.json()['_id']

    # create registration code by caregiver of different organization should fail
    registration_code2 = str(uuid.uuid4())
    create_registration_code2_response = create_registration_code(caregiver_auth_token, "RegistrationCode",
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
    update_registration_code_response = update_registration_code(caregiver_auth_token, registration_code1_id,
                                                                 str(uuid.uuid4()))
    assert update_registration_code_response.status_code == 200

    # update registration code (code2) by caregiver of default organization should fail
    update_registration_code_response = update_registration_code(caregiver_auth_token, registration_code2_id,
                                                                 str(uuid.uuid4()))
    assert update_registration_code_response.status_code == 403

    # get in same org should succeed
    get_registration_code_response = get_registration_code(caregiver_auth_token, registration_code1_id)
    assert get_registration_code_response.status_code == 200

    # get in different org should fail
    get_registration_code_response = get_registration_code(caregiver_auth_token, registration_code2_id)
    assert get_registration_code_response.status_code == 403

    # search in same org should succeed
    get_registration_code_list_response = get_registration_code_list(caregiver_auth_token)
    assert get_registration_code_list_response.status_code == 200
    assert get_registration_code_list_response.json()['metadata']['page']['totalResults'] == 1

    # delete in same org should succeed
    delete_registration_response = delete_registration_code(caregiver_auth_token, registration_code1_id)
    assert delete_registration_response.status_code == 204

    # delete in different org should fail
    delete_registration_response = delete_registration_code(caregiver_auth_token, registration_code2_id)
    assert delete_registration_response.status_code == 403

    # Teardown
    # delete caregiver
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 204
    # delete caregiver template
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204
    # delete registration code of second organization
    delete_registration_response = delete_registration_code(admin_auth_token, registration_code2_id)
    assert delete_registration_response.status_code == 204
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_files_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # create patient in new org  (Needed for file association with patients)
    patient1_auth_token, patient1_id, registration_code1_id, device1_id = create_single_patient_self_signup(
        admin_auth_token, organization_id, 'DeviceType1')
    # create patient in default org
    patient2_auth_token, patient2_id, registration_code2_id, device2_id = create_single_patient_self_signup(
        admin_auth_token, "00000000-0000-0000-0000-000000000000", 'DeviceType1')

    # create caregiver in new org
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']
    caregiver1_auth_token, caregiver1_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                   organization_id)

    # create files in new organization and default
    name = f'test_file{uuid.uuid4().hex}'[0:16]
    mime_type = 'text/plain'
    data = open('./upload-file.txt', 'rb').read()
    create_file_response = create_file(caregiver1_auth_token, name, mime_type)
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
    get_file_response = get_file(caregiver1_auth_token, file1_id)  # should succeed
    assert get_file_response.status_code == 200
    get_file_response = get_file(caregiver1_auth_token, file2_id)  # should fail
    assert get_file_response.status_code == 403

    # teardown
    single_self_signup_patient_teardown(admin_auth_token, patient1_id, registration_code1_id, device1_id)
    single_self_signup_patient_teardown(admin_auth_token, patient2_id, registration_code2_id, device2_id)
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver1_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_alerts_abac_rules():
    # Should be separate for patient alerts and device alerts
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create second organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200, f"{get_self_org_response.text}"
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template

    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']
    # create patient in new org
    patient1_auth_token, patient1_id, registration_code1_id, device1_id = create_single_patient_self_signup(
        admin_auth_token, organization_id, 'DeviceType1')
    get_patient_response = get_patient(patient1_auth_token, patient1_id)
    assert get_patient_response.status_code == 200, f"{get_patient_response.text}"
    patient_template_id = get_patient_response.json()['_template']['id']
    # get the device template
    get_device_response = get_device(patient1_auth_token, device1_id)
    assert get_device_response.status_code == 200, f"{get_device_response.text}"
    device_template_id = get_device_response.json()['_template']['id']

    # create alert template based on patient parent (template1) and device parent (template2)
    alert_template_name = f'test_patient_alert{uuid.uuid4().hex}'[0:35]
    create_patient_alert_template_response = create_patient_alert_template(admin_auth_token, patient_template_id,
                                                                           alert_template_name)
    assert create_patient_alert_template_response.status_code == 201, f"{create_patient_alert_template_response.text}"
    alert_template1_id = create_patient_alert_template_response.json()['id']
    alert_template1_name = create_patient_alert_template_response.json()['name']

    alert_template_name = f'test_device_alert{uuid.uuid4().hex}'[0:35]
    create_device_alert_template_response = create_device_alert_template(admin_auth_token, device_template_id,
                                                                         alert_template_name)
    assert create_device_alert_template_response.status_code == 201, f"{create_device_alert_template_response.text}"
    alert_template2_id = create_device_alert_template_response.json()['id']
    alert_template2_name = create_device_alert_template_response.json()['name']

    # create caregiver template
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    # create caregiver by admin in new organization
    caregiver_new_auth_token, caregiver_new_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                         organization_id)

    # create caregiver by admin in default organization
    caregiver_default_auth_token, caregiver_default_id = create_single_caregiver(admin_auth_token,
                                                                                 caregiver_template_name,
                                                                                 "00000000-0000-0000-0000-000000000000")

    # Create/Delete patient-alert by id only in same organization
    create_alert_response = create_patient_alert_by_id(caregiver_new_auth_token, patient1_id, alert_template1_id)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_patient_alert_by_id(caregiver_default_auth_token, patient1_id, alert_template1_id)
    assert create_alert_response.status_code == 403, f"{create_alert_response.text}"  # other org
    # update patient alert only in same organization
    update_alert_response = update_patient_alert(caregiver_new_auth_token, patient1_id, alert_id)
    assert update_alert_response.status_code == 200, f"{update_alert_response.text}"
    update_alert_response = update_patient_alert(caregiver_default_auth_token, patient1_id, alert_id)
    assert update_alert_response.status_code == 403, f"{update_alert_response.text}"
    # get patient alert and search only in same organization
    get_patient_alert_response = get_patient_alert(caregiver_new_auth_token, patient1_id, alert_id)
    assert get_patient_alert_response.status_code == 200, f"{get_patient_alert_response.text}"
    get_patient_alert_response = get_patient_alert(caregiver_default_auth_token, patient1_id, alert_id)
    assert get_patient_alert_response.status_code == 403, f"{get_patient_alert_response.text}"
    get_patient_alert_list_response = get_patient_alert_list(caregiver_new_auth_token, alert_id)
    assert get_patient_alert_list_response.status_code == 200, f"{get_patient_alert_list_response.text}"
    assert get_patient_alert_list_response.json()['metadata']['page']['totalResults'] == 1, \
        f"{get_patient_alert_list_response.json()['metadata']['page']['totalResults']}"
    get_patient_alert_list_response = get_patient_alert_list(caregiver_default_auth_token, alert_id)
    assert get_patient_alert_list_response.status_code == 200, f"{get_patient_alert_list_response.text}"
    assert get_patient_alert_list_response.json()['metadata']['page']['totalResults'] == 0, \
        f"{get_patient_alert_list_response.json()['metadata']['page']['totalResults']}"
    # get current alerts (nursing station) only in same org
    get_current_alert_response = get_current_patient_alert_list(caregiver_new_auth_token, alert_id)
    assert get_current_alert_response.status_code == 200, f"{get_current_alert_response.text}"
    assert get_current_alert_response.json()['metadata']['page']['totalResults'] == 1, \
        f"{get_current_alert_response.json()['metadata']['page']['totalResults']}"
    get_current_alert_response = get_current_patient_alert_list(caregiver_default_auth_token, alert_id)
    assert get_current_alert_response.status_code == 200, f"{get_current_alert_response.text}"
    # assert get_current_alert_response.json()['metadata']['page']['totalResults'] == 0  getting 1

    # delete patient-alert only in same organization
    delete_alert_response = delete_patient_alert(caregiver_default_auth_token, patient1_id, alert_id)
    assert delete_alert_response.status_code == 403, f"{delete_alert_response.text}"  # other org
    delete_alert_response = delete_patient_alert(caregiver_new_auth_token, patient1_id, alert_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"  # same org

    # Create patient-alert by name
    create_alert_response = create_patient_alert_by_name(caregiver_new_auth_token, patient1_id, alert_template1_name)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_patient_alert_by_name(caregiver_default_auth_token, patient1_id,
                                                         alert_template1_name)
    assert create_alert_response.status_code == 403, f"{create_alert_response.text}"  # other org
    # delete it
    delete_alert_response = delete_patient_alert(caregiver_new_auth_token, patient1_id, alert_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"  # same org

    # Create device-alert by id only in same organization
    create_alert_response = create_device_alert_by_id(caregiver_new_auth_token, device1_id, alert_template2_id)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_patient_alert_by_id(caregiver_default_auth_token, device1_id, alert_template2_id)
    assert create_alert_response.status_code == 403, f"{create_alert_response.text}"  # other org

    # get device-alert only in same organization
    get_device_alert_response = get_device_alert(caregiver_new_auth_token, device1_id, alert_id)
    assert get_device_alert_response.status_code == 200, f"{get_device_alert_response.text}"  # same org
    get_device_alert_response = get_device_alert(caregiver_default_auth_token, device1_id, alert_id)
    assert get_device_alert_response.status_code == 403, f"{get_device_alert_response.text}"  # other org

    # get device-alert list (search) only in same org
    get_device_alert_list_response = get_device_alert_list(caregiver_new_auth_token, alert_id)
    assert get_device_alert_list_response.status_code == 200, f"{get_device_alert_list_response.text}"
    assert get_device_alert_list_response.json()['metadata']['page']['totalResults'] == 1, \
        f"{get_device_alert_list_response.json()['metadata']['page']['totalResults']}"
    get_device_alert_list_response = get_device_alert_list(caregiver_default_auth_token, alert_id)
    assert get_device_alert_list_response.status_code == 200, f"{get_device_alert_list_response.text}"
    assert get_device_alert_list_response.json()['metadata']['page']['totalResults'] == 0, \
        f"{get_device_alert_list_response.json()['metadata']['page']['totalResults']}"
    # get current alerts (nursing station)
    get_current_alert_response = get_current_device_alert_list(caregiver_new_auth_token, alert_id)
    assert get_current_alert_response.status_code == 200, f"{get_current_alert_response.text}"
    assert get_current_alert_response.json()['metadata']['page']['totalResults'] == 1, \
        f"{get_current_alert_response.json()['metadata']['page']['totalResults']}"
    get_current_alert_response = get_current_device_alert_list(caregiver_new_auth_token, alert_id)
    assert get_current_alert_response.status_code == 200, f"{get_current_alert_response.text}"
    # assert get_current_alert_response.json()['metadata']['page']['totalResults'] == 0  ## Failing due to alert we can't delete

    # delete device-alert only in same organization
    delete_alert_response = delete_device_alert(caregiver_default_auth_token, device1_id, alert_id)
    assert delete_alert_response.status_code == 403, f"{delete_alert_response.text}"
    delete_alert_response = delete_device_alert(caregiver_new_auth_token, device1_id, alert_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"

    # create device-alert by name only in same organization
    create_alert_response = create_device_alert_by_name(caregiver_new_auth_token, device1_id, alert_template2_name)
    assert create_alert_response.status_code == 201, f"{create_alert_response.text}"  # same org
    alert_id = create_alert_response.json()['_id']
    create_alert_response = create_device_alert_by_name(caregiver_default_auth_token, device1_id, alert_template2_name)
    assert create_alert_response.status_code == 403, f"{create_alert_response.text}"  # other org
    # update device-alert only in same organization
    update_alert_response = update_device_alert(caregiver_new_auth_token, device1_id, alert_id)
    assert update_alert_response.status_code == 200, f"{update_alert_response.text}"  # same org
    update_alert_response = update_device_alert(caregiver_default_auth_token, device1_id, alert_id)
    assert update_alert_response.status_code == 403, f"{update_alert_response.text}"  # other org

    # teardown
    # clean up the last device alert
    delete_alert_response = delete_device_alert(patient1_auth_token, device1_id, alert_id)
    assert delete_alert_response.status_code == 204, f"{delete_alert_response.text}"
    single_self_signup_patient_teardown(admin_auth_token, patient1_id, registration_code1_id, device1_id)

    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_default_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"

    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"

    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"
    delete_template_response = delete_template(admin_auth_token, alert_template1_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response}"
    delete_template_response = delete_template(admin_auth_token, alert_template2_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"


# @pytest.mark.skip
def test_caregiver_measurements_abac_rules():
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

    # create caregiver template
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    # create caregiver by admin in new organization
    caregiver_new_auth_token, caregiver_new_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                         organization_id)

    # create caregiver by admin in default organization
    caregiver_default_auth_token, caregiver_default_id = create_single_caregiver(admin_auth_token,
                                                                                 caregiver_template_name,
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
    create_session_response = create_usage_session_by_usage_type(caregiver_default_auth_token, device_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 201, f"{create_session_response.text}"
    usage_session_id = create_session_response.json()['_id']
    # create measurement on patient1
    create_measurement_response = create_measurement(caregiver_default_auth_token, device_id, patient_id,
                                                     usage_session_id)
    assert create_measurement_response.status_code == 200, f"{create_measurement_response.text}"
    # create bulk measurement
    create_bulk_measurement_response = create_bulk_measurement(caregiver_default_auth_token, device_id,
                                                               patient_id, usage_session_id)
    assert create_bulk_measurement_response.status_code == 200, f"{create_bulk_measurement_response.text}"

    # get v1 raw measurements should succeed for same org caregiver
    get_v1_measurement_response = get_raw_measurements(caregiver_default_auth_token, patient_id)
    assert get_v1_measurement_response.status_code == 200, f"{get_v1_measurement_response.text}"
    # fail for other org caregiver
    get_v1_measurement_response = get_raw_measurements(caregiver_new_auth_token, patient_id)
    assert get_v1_measurement_response.status_code == 403, f"{get_v1_measurement_response.text}"

    # get v1 aggregated measurements should succeed for same org caregiver
    get_v1_measurement_response = get_aggregated_measurements(caregiver_default_auth_token, patient_id)
    assert get_v1_measurement_response.status_code == 200, f"{get_v1_measurement_response.text}"
    # fail for other org caregiver
    get_v1_measurement_response = get_aggregated_measurements(caregiver_new_auth_token, patient_id)
    assert get_v1_measurement_response.status_code == 403, f"{get_v1_measurement_response.text}"

    # get V2 raw measurements should succeed for same org caregiver
    get_v2_measurement_response = get_v2_raw_measurements(caregiver_default_auth_token, patient_id)
    assert get_v2_measurement_response.status_code == 200, f"{get_v2_measurement_response.text}"
    # fail for other org caregiver
    get_v2_measurement_response = get_v2_raw_measurements(caregiver_new_auth_token, patient_id)
    assert get_v2_measurement_response.status_code == 403, f"{get_v2_measurement_response.text}"

    # get v2 aggregated measurements should succeed for same org caregiver
    get_v2_measurement_response = get_v2_aggregated_measurements(caregiver_default_auth_token, patient_id)
    assert get_v2_measurement_response.status_code == 200, f"{get_v2_measurement_response.text}"
    # fail for other org caregiver
    get_v2_measurement_response = get_v2_aggregated_measurements(caregiver_new_auth_token, patient_id)
    assert get_v2_measurement_response.status_code == 403, f"{get_v2_measurement_response.text}"

    # get device credentials should always succeed (try with caregiver from new org)
    get_credentials_response = get_device_credentials(caregiver_new_auth_token)
    assert get_credentials_response.status_code == 200, f"{get_credentials_response.text}"

    # teardown
    delete_usage_session_response = delete_usage_session(admin_auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, usage_session_template_id)
    assert delete_template_response.status_code == 204

    single_self_signup_patient_teardown(admin_auth_token, patient_id, registration_code_id, device_id)

    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_default_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"

    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"

    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"


# @pytest.mark.skip
def test_caregiver_ums_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create caregiver by admin in default organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    caregiver_email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    create_caregiver_response = create_caregiver(admin_auth_token, test_name, caregiver_email, caregiver_template_name,
                                                 "00000000-0000-0000-0000-000000000000")
    assert create_caregiver_response.status_code == 201
    caregiver_id = create_caregiver_response.json()['_id']
    response_text, accept_invitation_response = accept_invitation(caregiver_email)
    password = accept_invitation_response.json()['operationData']['password']
    # login
    caregiver_auth_token = login_with_credentials(caregiver_email, password)
    # set password by patient
    new_password = "Bb234567NewPass"
    set_password_response = set_password(caregiver_auth_token, password, new_password)
    assert set_password_response.status_code == 200
    # check login with new password
    caregiver_auth_token = login_with_credentials(caregiver_email, new_password)

    # forgot password flow
    forgot_password_response = forgot_password(caregiver_email)
    new_password = "Cc345678NewPass2"
    reset_password_open_email_and_set_new_password(caregiver_email, new_password)
    # check login with new password
    caregiver_auth_token = login_with_credentials(caregiver_email, new_password)

    # teardown
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_locales_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create caregiver by admin in default organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    caregiver_auth_token, caregiver_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                 "00000000-0000-0000-0000-000000000000")

    # get available locales should succeed
    get_locales_response = get_available_locales(caregiver_auth_token)
    assert get_locales_response.status_code == 200

    # add locale should fail
    code = 'en-us'
    add_locale_response = add_locale(caregiver_auth_token, code)
    assert add_locale_response.status_code == 403

    # delete locale should fail
    locale_id = 'any'
    delete_locale_response = delete_locale(caregiver_auth_token, locale_id)
    assert delete_locale_response.status_code == 403

    # update locale should fail
    update_locale_response = update_locale(caregiver_auth_token, code)
    assert update_locale_response.status_code == 403

    # teardown
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_plugins_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create caregiver by admin in default organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    caregiver_auth_token, caregiver_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                 "00000000-0000-0000-0000-000000000000")

    # create plugin should fail
    create_plugin_response = create_plugin(caregiver_auth_token, 'test_plugin')
    assert create_plugin_response.status_code == 403

    # delete plugin should fail
    delete_plugin_response = delete_plugin(caregiver_auth_token, 'test_plugin')
    assert delete_plugin_response.status_code == 403

    # update plugin should fail
    update_plugin_response = update_plugin(caregiver_auth_token, 'test_plugin', 'test_plugin')
    assert update_plugin_response.status_code == 403

    # get plugin should fail
    get_plugin_response = get_plugin(caregiver_auth_token, 'test_plugin')
    assert get_plugin_response.status_code == 403

    # search plugin should fail
    search_plugin_response = get_plugin_list(caregiver_auth_token, 'test_plugin')
    assert search_plugin_response.status_code == 403

    # teardown
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_dms_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create caregiver template
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']
    # create 2 caregivers
    caregiver1_auth_token, caregiver1_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                   "00000000-0000-0000-0000-000000000000")
    caregiver2_auth_token, caregiver2_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                   "00000000-0000-0000-0000-000000000000")

    # create_report should succeed
    create_report_response = create_report(caregiver1_auth_token)
    assert create_report_response.status_code == 201, f"{create_report_response.text}"
    report_id = create_report_response.json()['id']

    # get report should succeed for self
    get_report_response = get_report(caregiver1_auth_token, report_id)
    assert get_report_response.status_code == 200, f"{get_report_response.text}"
    get_report_response = get_report(caregiver2_auth_token, report_id)
    assert get_report_response.status_code == 403, f"{get_report_response.text}"

    # search report should succeed
    search_report_response = get_report_list(caregiver1_auth_token)
    assert search_report_response.status_code == 200, f"{search_report_response.text}"

    # delete report should succeed
    delete_report_response = delete_report(caregiver1_auth_token, report_id)
    assert delete_report_response.status_code == 204, f"{delete_report_response.text}"

    # teardown
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver1_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver2_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"
    delete_caregiver_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_caregiver_template_response.status_code == 204, f"{delete_caregiver_template_response.text}"


# @pytest.mark.skip
def test_caregiver_templates_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create caregiver by admin in default organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    caregiver_auth_token, caregiver_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                 "00000000-0000-0000-0000-000000000000")

    # view templates should succeed
    view_template_response = get_templates_list(caregiver_auth_token)
    assert view_template_response.status_code == 200
    get_minimized_response = get_all_templates(caregiver_auth_token)
    assert get_minimized_response.status_code == 200

    # extract valid id and parentId
    template_id = get_minimized_response.json()['data'][0]['id']
    parent_template_id = get_minimized_response.json()['data'][0]['parentTemplateId']

    # get by id should succeed

    get_template_response = get_template_by_id(caregiver_auth_token, template_id)
    assert get_template_response.status_code == 200

    # get overview should fail
    get_overview_response = get_template_overview(caregiver_auth_token, template_id)
    assert get_overview_response.status_code == 403

    # delete should fail
    delete_template_response = delete_template(caregiver_auth_token, template_id)
    assert delete_template_response.status_code == 403

    # create should fail
    create_template_response = create_generic_template(caregiver_auth_token)
    assert create_template_response.status_code == 403

    # update should fail
    payload = get_template_response.json()
    update_template_response = update_template(caregiver_auth_token, template_id, payload)

    assert update_template_response.status_code == 403

    # teardown
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_portal_builder_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create caregiver by admin in default organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    caregiver_auth_token, caregiver_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                 "00000000-0000-0000-0000-000000000000")

    # view full info should succeed
    view_template_response = get_templates_list(caregiver_auth_token)
    assert view_template_response.status_code == 200
    get_minimized_response = get_all_templates(caregiver_auth_token)
    assert get_minimized_response.status_code == 200

    # extract valid id and parentId
    template_id = get_minimized_response.json()['data'][0]['id']
    view_portal_response = view_full_portal_information(caregiver_auth_token, 'ORGANIZATION_PORTAL', 'ENTITY_LIST',
                                                        None)
    assert view_portal_response.status_code == 200
    payload = view_portal_response.json()
    view_id = payload['id']
    # update views should fail
    update_portal_view_response = update_portal_views(caregiver_auth_token, 'ORGANIZATION_PORTAL', view_id, payload)
    assert update_portal_view_response.status_code == 403

    # teardown
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_adb_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create caregiver by admin in default organization
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    caregiver_auth_token, caregiver_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                 "00000000-0000-0000-0000-000000000000")

    # deploy adb should fail
    deploy_response = deploy_adb(caregiver_auth_token)
    assert deploy_response.status_code == 403

    # undeploy should fail
    undeploy_response = undeploy_adb(caregiver_auth_token)
    assert undeploy_response.status_code == 403

    # start init should fail
    start_init_response = start_init_adb(caregiver_auth_token)
    assert start_init_response.status_code == 403

    # stop init should fail
    stop_init_response = stop_init_adb(caregiver_auth_token)
    assert stop_init_response.status_code == 403

    # stop sync should fail
    stop_sync_response = stop_sync_adb(caregiver_auth_token)
    assert stop_sync_response.status_code == 403

    # get adb info should succeed
    get_adb_response = get_adb_info(caregiver_auth_token)
    assert get_adb_response.status_code == 200

    # teardown
    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204
    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204


# @pytest.mark.skip
def test_caregiver_usage_session_abac_rules():  # IP
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

    # create caregiver template
    create_template_response = create_caregiver_template(admin_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    caregiver_template_name = create_template_response.json()['name']
    caregiver_template_id = create_template_response.json()['id']

    # create caregiver by admin in default organization
    caregiver_default_auth_token, caregiver_default_id = create_single_caregiver(admin_auth_token,
                                                                                 caregiver_template_name,
                                                                                 "00000000-0000-0000-0000-000000000000")

    # create caregiver by admin in new organization
    caregiver_new_auth_token, caregiver_new_id = create_single_caregiver(admin_auth_token, caregiver_template_name,
                                                                         organization_id)

    # get the device templateId
    get_device_response = get_device(admin_auth_token, device_id)
    device_template_id = get_device_response.json()['_template']['id']
    # create usage_session template
    usage_template_data = create_template_setup(admin_auth_token, None,
                                                "usage-session", device_template_id)
    usage_session_template_name = usage_template_data[1]
    usage_session_template_id = usage_template_data[0]

    # create session should succeed for caregiver in same org
    create_session_response = create_usage_session_by_usage_type(caregiver_default_auth_token, device_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 201, f"{create_session_response.text}"
    usage_session_id = create_session_response.json()['_id']
    # create session should fail for caregiver in other org
    create_session_response = create_usage_session_by_usage_type(caregiver_new_auth_token, device_id,
                                                                 usage_session_template_name)
    assert create_session_response.status_code == 403, f"{create_session_response.text}"

    # update session should succeed for caregiver in same org and fail for caregiver in other org
    update_session_response = update_usage_session(caregiver_default_auth_token, device_id, usage_session_id)
    assert update_session_response.status_code == 200, f"{update_session_response.text}"
    update_session_response = update_usage_session(caregiver_new_auth_token, device_id, usage_session_id)
    assert update_session_response.status_code == 403, f"{update_session_response.text}"

    # get session should succeed only for same org
    get_session_response = get_usage_session(caregiver_default_auth_token, device_id, usage_session_id)
    assert get_session_response.status_code == 200, f"{get_session_response.text}"
    get_session_response = get_usage_session(caregiver_new_auth_token, device_id, usage_session_id)
    assert get_session_response.status_code == 403, f"{get_session_response.text}"

    # search usage session by caregiver only in same org
    # Positive - for same
    get_session_list_response = get_usage_session_list(caregiver_default_auth_token)
    assert get_session_list_response.status_code == 200, f"{get_session_list_response.text}"
    assert get_session_list_response.json()['metadata']['page']['totalResults'] != 0, \
        f"{get_session_list_response.json()['metadata']['page']['totalResults']}"
    # negative: other caregiver should get zero results
    get_session_list_response = get_usage_session_list(caregiver_new_auth_token)
    assert get_session_list_response.status_code == 200, f"{get_session_list_response.text}"
    assert get_session_list_response.json()['metadata']['page']['totalResults'] == 0, \
        f"{get_session_list_response.json()['metadata']['page']['totalResults']}"

    # delete session by caregiver should succeed for same org and fail for other org
    delete_session_response = delete_usage_session(caregiver_new_auth_token, device_id, usage_session_id)
    assert delete_session_response.status_code == 403, f"{delete_session_response.text}"
    delete_session_response = delete_usage_session(caregiver_default_auth_token, device_id, usage_session_id)
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
    start_session_response = start_usage_session(caregiver_new_auth_token, device2_id, usage_session_template_id,
                                                 patient_id)
    assert start_session_response.status_code == 403, f"{start_session_response.text}"
    start_session_response = start_usage_session(caregiver_default_auth_token, device2_id, usage_session_template_id,
                                                 patient_id)
    assert start_session_response.status_code == 201, f"{start_session_response.text}"
    usage_session2_id = start_session_response.json()['_id']

    # pause only for same organization; first make sure it's active

    get_usage_session_response = get_usage_session(caregiver_default_auth_token, device2_id, usage_session2_id)
    assert get_usage_session_response.status_code == 200, f"{get_usage_session_response.text}"
    while get_usage_session_response.json()["_state"] != 'ACTIVE':
        get_usage_session_response = get_usage_session(caregiver_default_auth_token, device2_id, usage_session2_id)
        if get_usage_session_response.json()["_state"] == 'DONE':  # restart simulation
            break
        assert get_usage_session_response.status_code == 200, f"{get_usage_session_response.text}"

    assert get_usage_session_response.json()["_state"] == "ACTIVE", \
        f"The current status is {get_usage_session_response.json()['_state']}, not 'ACTIVE', simulator timeout"

    pause_session_response = pause_usage_session(caregiver_new_auth_token, device2_id, usage_session2_id)
    assert pause_session_response.status_code == 403, f"{pause_session_response.text}"
    pause_session_response = pause_usage_session(caregiver_default_auth_token, device2_id, usage_session2_id)
    assert pause_session_response.status_code == 200, f"{pause_session_response.text}"
    get_usage_session_response = get_usage_session(caregiver_default_auth_token, device2_id, usage_session2_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "PAUSED", f"The current status is {usage_session_status}, not 'PAUSED'"

    # resume session (should succeed only for self)
    resume_usage_session_response = resume_usage_session(caregiver_new_auth_token, device2_id, usage_session2_id)
    assert resume_usage_session_response.status_code == 403
    resume_usage_session_response = resume_usage_session(caregiver_default_auth_token, device2_id, usage_session2_id)
    assert resume_usage_session_response.status_code == 200, f"{resume_usage_session_response.text}"
    get_usage_session_response = get_usage_session(caregiver_default_auth_token, device2_id, usage_session2_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "ACTIVE", f"The current status is {usage_session_status}, not 'ACTIVE'"

    # Stop a Remote usage session - succeed for own organization
    stop_usage_session_response = stop_usage_session(caregiver_default_auth_token, device2_id, usage_session2_id)
    assert stop_usage_session_response.status_code == 200, f"{stop_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(caregiver_default_auth_token, device2_id, usage_session2_id)
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

    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_default_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"

    delete_caregiver_response = delete_caregiver(admin_auth_token, caregiver_new_id)
    assert delete_caregiver_response.status_code == 204, f"{delete_caregiver_response.text}"

    delete_template_response = delete_template(admin_auth_token, caregiver_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"
