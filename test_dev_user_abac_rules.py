import pytest
import time
from api_test_helpers import *
from email_interface import reset_password_open_email_and_set_new_password
from dotenv import load_dotenv
from test_constants import *

load_dotenv()


#############################################################################################
# Username and password have to be set in the environment in advance for each individual test
#############################################################################################

# @pytest.mark.skip
def test_dev_user_commands_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # create device template
    device_template_response = create_device_template_with_session(dev_user_auth_token)[0]
    assert device_template_response.status_code == 201, f"{device_template_response.text}"
    template_name = device_template_response.json()["name"]
    device_template_id = device_template_response.json()["id"]

    # create command template #1
    command_template_name = f'test_cmd_sprt_stop1_{uuid.uuid4().hex}'[0:32]
    create_command_template_response = create_command_template_with_support_stop_true(dev_user_auth_token,
                                                                                      command_template_name,
                                                                                      device_template_id)
    assert create_command_template_response.status_code == 201, f"{create_command_template_response.text}"
    command_template_id = create_command_template_response.json()['id']

    # create command template #2
    command_template2_name = f'test_cmd_sprt_stop2_{uuid.uuid4().hex}'[0:32]
    create_command_template2_response = create_command_template_with_support_stop_true(dev_user_auth_token,
                                                                                       command_template2_name,
                                                                                       device_template_id)
    assert create_command_template2_response.status_code == 201, f"{create_command_template2_response.text}"
    command_template2_id = create_command_template_response.json()['id']

    # create device in Default Org-n
    create_device_response = create_device_without_registration_code(dev_user_auth_token, template_name,
                                                                     DEFAULT_ORGANISATION_ID)
    device_id = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # start simulator with device
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()
    start_simulation_with_existing_device(device_id, os.getenv('USERNAME'), os.getenv('PASSWORD'))

    # TEST - Start Command in Default Org-n
    start_command_response = start_command_by_id(dev_user_auth_token, device_id, command_template_id)
    assert start_command_response.status_code == 201, f"{start_command_response.text}"
    command_id = start_command_response.json()['_id']
    get_command_response = get_command(dev_user_auth_token, device_id, command_id)
    command_state = get_command_response.json()['_state']
    while command_state != "IN_PROGRESS":
        get_command_response = get_command(dev_user_auth_token, device_id, command_id)
        command_state = get_command_response.json()['_state']
        if command_state in ["TIMEOUT", "FAILED"]:
            break
    assert command_state == 'IN_PROGRESS', f'Command state is "{command_state}"'

    # TEST - Stop Command in Default Org-n
    stop_command_response = stop_command(dev_user_auth_token, device_id, command_id)
    assert stop_command_response.status_code == 200, f"{start_command_response.text}"
    get_command_response = get_command(dev_user_auth_token, device_id, command_id)
    command_state = get_command_response.json()['_state']
    while command_state not in ["ABORTED", "STOPPING"]:
        get_command_response = get_command(dev_user_auth_token, device_id, command_id)
        command_state = get_command_response.json()['_state']
        if command_state in ["TIMEOUT", "FAILED"]:
            break
    assert command_state == 'ABORTED' or command_state == 'STOPPING', f'Command state is "{command_state}"'

    # TEST - Start another Command in Default Org-n and wait till it's Completed
    start_command2_response = start_command_by_id(dev_user_auth_token, device_id, command_template2_id)
    assert start_command2_response.status_code == 201, f"{start_command2_response.text}"
    command2_id = start_command2_response.json()['_id']
    get_command2_response = get_command(dev_user_auth_token, device_id, command2_id)
    command2_state = get_command2_response.json()['_state']
    while command2_state != "COMPLETED":
        get_command2_response = get_command(dev_user_auth_token, device_id, command2_id)
        command2_state = get_command2_response.json()['_state']
        if command2_state in ["TIMEOUT", "FAILED"]:
            break
    assert command2_state == 'COMPLETED', f'Command state is "{command2_state}"'

    # stop simulation
    stop_simulation()
    simulation_status_response = get_simulation_status()
    simulation_status = simulation_status_response.json()["code"]
    assert simulation_status == "NO_RUNNING_SIMULATION"

    # Delete Device
    delete_device_response = delete_device(dev_user_auth_token, device_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"
    # Delete command templates
    delete_template_response = delete_template(dev_user_auth_token, command_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"
    delete_template_response = delete_template(dev_user_auth_token, command_template2_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"
    # Delete Device template
    delete_device_template_response = delete_template(dev_user_auth_token, device_template_id)
    assert delete_device_template_response.status_code == 204, f"{delete_device_template_response.text}"

    #   assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # Delete dev user
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"


# @pytest.mark.skip
def test_dev_user_organization_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization, get org_admin and login with admin
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200, f"{get_self_org_response.text}"
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # create, update  and delete organization succeeds
    create_organization_response = create_organization(dev_user_auth_token, template_id)
    assert create_organization_response.status_code == 201, f"{create_organization_response.text}"
    new_org_id = create_organization_response.json()['_id']

    update_organization_response = update_organization(dev_user_auth_token, new_org_id, "changed test text")
    assert update_organization_response.status_code == 200, f"{update_organization_response.text}"

    delete_organization_response = delete_organization(dev_user_auth_token, new_org_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"

    # Get organization by list or by id -- should succeed
    get_organization_response = get_organization(dev_user_auth_token, organization_id)
    assert get_organization_response.status_code == 200, f"{get_organization_response.text}"

    # positive (own organization should return one result)
    get_organization_list_response = get_organization_list(dev_user_auth_token)
    assert get_organization_list_response.status_code == 200, f"{get_organization_list_response.text}"
    assert get_organization_list_response.json()['metadata']['page']['totalResults'] > 1

    # Teardown

    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"


# @pytest.mark.skip
def test_dev_user_org_users_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # create organization user by dev user should succeed
    create_template_response = create_org_user_template(dev_user_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    org_user_template_name = create_template_response.json()['name']
    org_user_template_id = create_template_response.json()['id']

    # Create org_user should always succeed
    # create org_user in default org
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_org_user_create_response = create_organization_user(dev_user_auth_token, org_user_template_name, test_name,
                                                             email, DEFAULT_ORGANISATION_ID)
    assert test_org_user_create_response.status_code == 201, f"{test_org_user_create_response.text}"
    default_org_user_id = test_org_user_create_response.json()['_id']
    # create org_user in new org
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_org_user_create_response = create_organization_user(dev_user_auth_token, org_user_template_name, test_name,
                                                             email, organization_id)
    assert test_org_user_create_response.status_code == 201, f"{test_org_user_create_response.text}"
    new_org_user_id = test_org_user_create_response.json()['_id']

    # update org_user should always succeed
    update_org_user_response = update_organization_user(dev_user_auth_token, new_org_user_id, organization_id,
                                                        "change string")
    assert update_org_user_response.status_code == 200, f"{update_org_user_response.text}"

    update_org_user_response = update_organization_user(dev_user_auth_token, default_org_user_id,
                                                        DEFAULT_ORGANISATION_ID, "change string")

    assert update_org_user_response.status_code == 200, f"{update_org_user_response.text}"

    # enable/disable should succeed
    change_org_user_state_response = change_organization_user_state(dev_user_auth_token, default_org_user_id, "ENABLED")
    assert change_org_user_state_response.status_code == 200, f"{change_org_user_state_response.text}"
    change_org_user_state_response = change_organization_user_state(dev_user_auth_token, new_org_user_id, "ENABLED")
    assert change_org_user_state_response.status_code == 200, f"{change_org_user_state_response.text}"

    # resend invitation should always succeed
    resend_invitation_response = resend_invitation(dev_user_auth_token, default_org_user_id)
    assert resend_invitation_response.status_code == 200, f"{resend_invitation_response.text}"
    resend_invitation_response = resend_invitation(dev_user_auth_token, new_org_user_id)
    assert resend_invitation_response.status_code == 200, f"{resend_invitation_response.text}"

    # get org_user should always succeed
    get_org_user_response = get_organization_user(dev_user_auth_token, new_org_user_id)
    assert get_org_user_response.status_code == 200, f"{get_org_user_response.text}"
    get_org_user_response = get_organization_user(dev_user_auth_token, default_org_user_id)
    assert get_org_user_response.status_code == 200, f"{get_org_user_response.text}"

    # search org_user should always succeed

    get_org_user_list_response = get_organization_user_list(dev_user_auth_token)
    assert get_org_user_list_response.status_code == 200

    # delete org_user should always succeed
    test_org_user_delete_response = delete_organization_user(dev_user_auth_token, default_org_user_id)
    assert test_org_user_delete_response.status_code == 204, f"{test_org_user_delete_response.text}"
    test_org_user_delete_response = delete_organization_user(dev_user_auth_token, new_org_user_id)
    assert test_org_user_delete_response.status_code == 204, f"{test_org_user_delete_response.text}"

    # Teardown

    delete_template_response = delete_template(admin_auth_token, org_user_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"
    delete_dev_user_response = delete_organization_user(dev_user_auth_token, dev_user_id)
    assert delete_dev_user_response.status_code == 204, f"{delete_dev_user_response.text}"
    delete_org_response = delete_organization(admin_auth_token, organization_id)
    assert delete_org_response.status_code == 204, f"{delete_org_response.text}"


# @pytest.mark.skip
def test_dev_user_patient_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # Create patient should always succeed
    # create patient in default org
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_patient_create_response = create_patient(dev_user_auth_token, test_name, email, "Patient",
                                                  DEFAULT_ORGANISATION_ID)
    assert test_patient_create_response.status_code == 201, f"{test_patient_create_response.text}"
    default_patient_id = test_patient_create_response.json()['_id']
    # create patient in new org
    test_name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
                 "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '_@biotmail.com'
    test_patient_create_response = create_patient(dev_user_auth_token, test_name, email, "Patient",
                                                  organization_id)
    assert test_patient_create_response.status_code == 201, f"{test_patient_create_response.text}"
    new_patient_id = test_patient_create_response.json()['_id']

    # update patient should always succeed

    update_patient_response = update_patient(dev_user_auth_token, new_patient_id, organization_id,
                                             "change string", None, None)
    assert update_patient_response.status_code == 200, f"{update_patient_response.text}"

    update_patient_response = update_patient(dev_user_auth_token, default_patient_id, DEFAULT_ORGANISATION_ID,
                                             "change string", None, None)
    assert update_patient_response.status_code == 200, f"{update_patient_response.text}"

    # enable/disable should succeed
    change_patient_state_response = change_patient_state(dev_user_auth_token, default_patient_id, "ENABLED")
    assert change_patient_state_response.status_code == 200, f"{change_patient_state_response.text}"
    change_patient_state_response = change_patient_state(dev_user_auth_token, new_patient_id, "ENABLED")
    assert change_patient_state_response.status_code == 200, f"{change_patient_state_response.text}"

    # resend invitation should always succeed

    resend_invitation_response = resend_invitation(dev_user_auth_token, new_patient_id)
    assert resend_invitation_response.status_code == 200, f"{resend_invitation_response.text}"
    resend_invitation_response = resend_invitation(dev_user_auth_token, default_patient_id)
    assert resend_invitation_response.status_code == 200, f"{resend_invitation_response.text}"

    # get patient always succeeds
    get_patient_response = get_patient(dev_user_auth_token, new_patient_id)  # same org
    assert get_patient_response.status_code == 200, f"{get_patient_response.text}"
    can_login_val = not get_patient_response.json()['_canLogin']
    get_patient_response = get_patient(dev_user_auth_token, default_patient_id)  # other org patient
    assert get_patient_response.status_code == 200, f"{get_patient_response.text}"

    # update canLoging should always succeed
    update_patient_response = update_patient(dev_user_auth_token, new_patient_id, organization_id,
                                             None, None, {"_canLogin": can_login_val})
    assert update_patient_response.status_code == 200, f"{update_patient_response.text}"

    update_patient_response = update_patient(dev_user_auth_token, default_patient_id,
                                             DEFAULT_ORGANISATION_ID, None, None,
                                             {"_canLogin": can_login_val})
    assert update_patient_response.status_code == 200, f"{update_patient_response.text}"

    # search patient always

    get_patient_list_response = get_patient_list(dev_user_auth_token)
    assert get_patient_list_response.status_code == 200

    # delete patient always succeeds
    test_patient_delete_response = delete_patient(dev_user_auth_token, default_patient_id)
    assert test_patient_delete_response.status_code == 204, f"{test_patient_delete_response.text}"
    test_patient_delete_response = delete_patient(dev_user_auth_token, new_patient_id)
    assert test_patient_delete_response.status_code == 204, f"{test_patient_delete_response.text}"

    # ########################################### phi test start ###########################################

    get_patient_template_response = get_template(admin_auth_token, PATIENT_TEMPLATE_ID)
    assert get_patient_template_response.status_code == 200, f"{get_patient_template_response.text}"
    template_payload = map_template(get_patient_template_response.json())

    # add phi attribute to Patient template
    phi_name = f'test_phi_object_patient{uuid.uuid4().hex}'[0:36]
    phi_object = {
        "name": phi_name,
        "id": str(uuid.uuid4()),
        "basePath": None,
        "displayName": "test phi object patient",
        "phi": True,
        "type": "LABEL",
        "validation": {
            "mandatory": False,
            "min": None,
            "max": None,
            "regex": None
        },
        "numericMetaData": None,
        "referenceConfiguration": None
    }
    (template_payload['customAttributes']).append(phi_object)
    update_template_response = update_template(admin_auth_token, PATIENT_TEMPLATE_ID, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    # create a Patient with phi attribute in Custom Organisation as Admin of custom Org-n
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '@biotmail.com'
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    create_patient_custom_response = create_patient_with_phi(dev_user_auth_token, name, email, PATIENT_TEMPLATE_NAME,
                                                             organization_id,
                                                             phi_name)  # create patient with phi attributes
    phi_attribute_key = phi_name
    assert create_patient_custom_response.status_code == 201, f"Status code " \
                                                              f"{create_patient_custom_response.status_code}" \
                                                              f" {create_patient_custom_response.text}"
    phi_patient_id = create_patient_custom_response.json()["_id"]
    get_patient_by_id_response = get_patient(dev_user_auth_token, phi_patient_id)
    phi_attribute_value = get_patient_by_id_response.json()[phi_name]
    assert phi_attribute_value in get_patient_by_id_response.text, \
        f"'{phi_attribute_value}' should be present in the response"
    assert phi_attribute_value == "testphi", f"phi attribute is '{phi_attribute_value}' instead of expected"

    # revert changes in Patient Template
    get_template_response = get_template(dev_user_auth_token, PATIENT_TEMPLATE_ID)
    template_payload = map_template(get_template_response.json())
    index = 0
    for element in template_payload['customAttributes']:
        if element['name'] == phi_name:
            del template_payload['customAttributes'][index]
            continue
        else:
            index += 1
    update_template_response = update_template(dev_user_auth_token, PATIENT_TEMPLATE_ID, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    # ########################################### phi test end ###########################################

    # Teardown

    delete_patient_response = delete_patient(admin_auth_token, phi_patient_id)
    assert delete_patient_response.status_code == 204
    delete_dev_user_response = delete_organization_user(dev_user_auth_token, dev_user_id)
    assert delete_dev_user_response.status_code == 204, f"{delete_dev_user_response.text}"
    delete_org_response = delete_organization(admin_auth_token, organization_id)
    assert delete_org_response.status_code == 204


# @pytest.mark.skip
def test_dev_user_device_alerts_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # Create Device template
    device_template_response = create_device_template_with_session(dev_user_auth_token)[0]
    assert device_template_response.status_code == 201, f"{device_template_response.text}"
    device_template_name = device_template_response.json()["name"]
    device_template_id = device_template_response.json()["id"]

    # Create Device Alert template
    name = f'test_alert_templ{uuid.uuid4().hex}'[0:32]
    create_device_alert_template_response = create_device_alert_template(dev_user_auth_token, device_template_id, name)
    assert create_device_alert_template_response.status_code == 201, f'{create_device_alert_template_response.text}'
    device_alert_template_id = create_device_alert_template_response.json()["id"]

    # Create a Custom Organisation
    create_organization_response = create_organization(dev_user_auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # create a Caregiver in Custom Organisation
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    caregiver_email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '@biotmail.com'
    create_caregiver_custom_response = create_caregiver(dev_user_auth_token, name, caregiver_email, "Clinician",
                                                        organization_id)
    assert create_caregiver_custom_response.status_code == 201, f"Status code " \
                                                                f"{create_caregiver_custom_response.status_code}" \
                                                                f" {create_caregiver_custom_response.text}"
    accept_invitation(caregiver_email)

    # Create Device in Custom organisation
    # auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    create_device_response = create_device_without_registration_code(dev_user_auth_token, device_template_name,
                                                                     organization_id)
    device_id = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # TEST - Create Device Alert by ID in Custom organisation
    create_device_alert_response = create_device_alert_by_id(dev_user_auth_token, device_id, device_alert_template_id)
    assert create_device_alert_response.status_code == 201, f'{create_device_alert_response.text}'
    device_alert_id = create_device_alert_response.json()["_id"]

    # TEST - Update Device Alert created by ID in Custom organisation
    update_device_alert_response = update_device_alert(dev_user_auth_token, device_id, device_alert_id)
    assert update_device_alert_response.status_code == 200, f'{update_device_alert_response.text}'

    # TEST - Get By ID Device Alert created by ID in Custom organisation
    get_device_alert_by_id_response = get_device_alert(dev_user_auth_token, device_id, device_alert_id)
    assert get_device_alert_by_id_response.status_code == 200, f'{get_device_alert_by_id_response.text}'

    # TEST - Search Device Alerts
    search_device_alerts_response = get_device_alert_list(dev_user_auth_token, device_alert_id)
    assert search_device_alerts_response.status_code == 200, f'{search_device_alerts_response.text}'

    # TEST - Get current Alerts
    get_current_alerts_response = get_current_device_alert_list(dev_user_auth_token, organization_id)
    assert get_current_alerts_response.status_code == 200, f"{get_current_alerts_response.text}"

    # TEST - Delete Alert created by ID in Custom organisation
    delete_device_alert_response = delete_device_alert(dev_user_auth_token, device_id, device_alert_id)
    assert delete_device_alert_response.status_code == 204, f"{delete_device_alert_response.text}"

    # Delete Device
    delete_device_response = delete_device(dev_user_auth_token, device_id)
    assert delete_device_response.status_code == 204, f"{delete_device_alert_response.text}"

    # Delete Organisation
    delete_organisation_response = delete_organization(dev_user_auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"{delete_organisation_response.text}"

    # Delete Device template
    delete_device_template_response = delete_template(dev_user_auth_token, device_template_id)
    assert delete_device_template_response.status_code == 204, f"{delete_device_template_response.text}"
    # delete dev user
    delete_dev_user_response = delete_organization_user(dev_user_auth_token, dev_user_id)
    assert delete_dev_user_response.status_code == 204, f"{delete_dev_user_response.text}"


# @pytest.mark.skip
def test_dev_user_caregiver_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # create a Custom Organisation
    create_organization_response = create_organization(dev_user_auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}

    # create Caregiver Template
    create_caregiver_template_response = create_caregiver_template(dev_user_auth_token)
    assert create_caregiver_template_response.status_code == 201, f"{create_caregiver_template_response.text}"
    template_name = create_caregiver_template_response.json()["name"]
    template_id = create_caregiver_template_response.json()["id"]
    email = f'Test_caregiver_{uuid.uuid4().hex}'[0:35] + '@biotmail.com'

    # TEST - Create Caregiver in Custom Organisation
    create_caregiver_response = create_caregiver(dev_user_auth_token, name, email, template_name, organization_id)
    assert create_caregiver_response.status_code == 201, f"Status code {create_organization_response.status_code}" \
                                                         f" {create_organization_response.text}"
    caregiver_id = create_caregiver_response.json()["_id"]

    # TEST - Update Caregiver in Custom Organisation
    change_string = "updated caregiver test"
    update_caregiver_response = update_caregiver(dev_user_auth_token, caregiver_id, organization_id, change_string)
    assert update_caregiver_response.status_code == 200, f"Status code {update_caregiver_response.status_code}" \
                                                         f" {update_caregiver_response.text}"
    assert update_caregiver_response.json()["_description"] == change_string, \
        f'{update_caregiver_response.json()["_description"]} doesn\'t match the {change_string}'

    # TEST - Caregiver in Custom Organisation by ID
    get_caregiver_by_id_response = get_caregiver(dev_user_auth_token, caregiver_id)
    assert get_caregiver_by_id_response.status_code == 200
    assert get_caregiver_by_id_response.json()["_id"] == caregiver_id

    # TEST - Disable a Caregiver in Custom Organisation
    disable_caregiver_response = change_caregiver_state(dev_user_auth_token, caregiver_id, state='DISABLED')
    assert disable_caregiver_response.status_code == 200, f"Status code {disable_caregiver_response.status_code} " \
                                                          f"{disable_caregiver_response.text}"
    assert disable_caregiver_response.json()["_enabled"] == "DISABLED", f"Caregiver's state is " \
                                                                        f"{disable_caregiver_response.json()['_enabled']}" \
                                                                        f"instead of ""DISABLED"

    # TEST - Disable a Caregiver in Custom Organisation
    enable_caregiver_response = change_caregiver_state(dev_user_auth_token, caregiver_id, state='ENABLED')
    assert enable_caregiver_response.status_code == 200, f"Status code {enable_caregiver_response.status_code} " \
                                                         f"{enable_caregiver_response.text}"
    assert enable_caregiver_response.json()["_enabled"] == "ENABLED", f"Caregiver's state is " \
                                                                      f"{enable_caregiver_response.json()['_enabled']}" \
                                                                      f" instead of ""ENABLED"

    # TEST - Resend Invitation to a Caregiver in Custom Organisation
    resend_invitation_response = resend_invitation(dev_user_auth_token, caregiver_id)
    assert resend_invitation_response.status_code == 200, f"Status code {resend_invitation_response.status_code}" \
                                                          f" {resend_invitation_response.text}"
    assert resend_invitation_response.json()["userId"] == caregiver_id

    # TEST - Search Caregivers
    get_caregivers_response = get_caregiver_list(dev_user_auth_token)
    assert get_caregivers_response.status_code == 200

    # TEST - Delete Caregiver in Custom Organisation
    delete_caregiver_response = delete_caregiver(dev_user_auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204
    get_caregiver_by_id_response = get_caregiver(dev_user_auth_token, caregiver_id)
    assert get_caregiver_by_id_response.status_code == 404
    assert get_caregiver_by_id_response.json()["code"] == "USER_NOT_FOUND"

    # delete Organisation
    delete_organisation_response = delete_organization(dev_user_auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"{delete_organisation_response.text}"

    # delete Caregiver template
    delete_caregiver_template_response = delete_template(dev_user_auth_token, template_id)
    assert delete_caregiver_template_response.status_code == 204, f"{delete_caregiver_template_response.text}"
    delete_dev_user_response = delete_organization_user(dev_user_auth_token, dev_user_id)
    assert delete_dev_user_response.status_code == 204, f"{delete_dev_user_response.text}"


# @pytest.mark.skip
def test_dev_user_devices_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)
    # create a Device Template
    device_template_response = create_device_template_with_session(dev_user_auth_token)[0]
    assert device_template_response.status_code == 201, f"{device_template_response.text}"
    template_name = device_template_response.json()["name"]
    template_id = device_template_response.json()["id"]

    # create a Custom Organisation
    create_organization_response = create_organization(dev_user_auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # TEST - Create Device in a Custom Org-n
    create_device_response = create_device_without_registration_code(dev_user_auth_token, template_name,
                                                                     organization_id)
    device_id = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # TEST - Update Device
    update_device_response, updated_string = update_device_without_patient(dev_user_auth_token, device_id)
    assert update_device_response.status_code == 200, f"{update_device_response.text}"

    # TEST - Get Device by ID
    get_device_by_id_response = get_device(dev_user_auth_token, device_id)
    assert get_device_by_id_response.status_code == 200
    device_description_updated = update_device_response.json()["_description"]
    assert device_description_updated == updated_string, f"{device_description_updated} is not equal to " \
                                                         f"{updated_string}"

    # TEST - Search Devices
    search_devices_response = get_device_list(dev_user_auth_token)
    assert search_devices_response.status_code == 200, f"{search_devices_response.text}"

    # TEST - Delete Device
    delete_device_response = delete_device(dev_user_auth_token, device_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"

    # delete Organisation
    delete_organisation_response = delete_organization(dev_user_auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"{delete_organisation_response.text}"

    # delete Device template
    delete_device_template_response = delete_template(dev_user_auth_token, template_id)
    assert delete_device_template_response.status_code == 204, f"{delete_device_template_response.text}"
    delete_dev_user_response = delete_organization_user(dev_user_auth_token, dev_user_id)
    assert delete_dev_user_response.status_code == 204, f"{delete_dev_user_response.text}"


# @pytest.mark.skip
def test_dev_user_generic_entity_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # create generic template without phi=true
    create_generic_template_no_phi_response = create_generic_template(dev_user_auth_token)
    assert create_generic_template_no_phi_response.status_code == 201, f"{create_generic_template_no_phi_response.text}"
    generic_template_no_phi_id = create_generic_template_no_phi_response.json()["id"]

    # create generic template with phi=true
    create_generic_template_with_phi_response = create_generic_template_with_phi_true(dev_user_auth_token)
    assert create_generic_template_with_phi_response.status_code == 201, \
        f"{create_generic_template_with_phi_response.text}"
    generic_template_with_phi_id = create_generic_template_with_phi_response.json()["id"]

    # TEST - Create Generic Entity without phi=true
    generic_name_no_phi = f"Generic_Entity_No_PHI{uuid.uuid4().hex}"[0:32]
    create_generic_entity_response = create_generic_entity(dev_user_auth_token, generic_template_no_phi_id,
                                                           generic_name_no_phi,
                                                           DEFAULT_ORGANISATION_ID)
    assert create_generic_entity_response.status_code == 201, f"{create_generic_entity_response.text}"
    generic_entity_id = create_generic_entity_response.json()["_id"]

    # TEST - Update Generic Entity
    update_generic_entity_response = update_generic_entity(dev_user_auth_token, generic_entity_id,
                                                           "generic_name_updated")
    assert update_generic_entity_response.status_code == 200, f"{update_generic_entity_response.text}"
    assert update_generic_entity_response.json()["_name"] == "generic_name_updated"

    # TEST - Get Generic Entity by ID
    get_generic_entity_response = get_generic_entity(dev_user_auth_token, generic_entity_id)
    assert get_generic_entity_response.status_code == 200, f"{get_generic_entity_response.text}"

    # TEST - Search Generic Entities
    search_generic_entities_list_response = get_generic_entity_list(dev_user_auth_token)
    assert search_generic_entities_list_response.status_code == 200, f"{search_generic_entities_list_response.text}"

    # TEST - Delete Generic Entity
    delete_generic_entity_response = delete_generic_entity(dev_user_auth_token, generic_entity_id)
    assert delete_generic_entity_response.status_code == 204, f"{delete_generic_entity_response.text}"

    # TEST - Create Generic Entity with phi=true - success
    generic_name_phi = f"Generic_Entity_PHI{uuid.uuid4().hex}"[0:32]
    create_generic_entity_response = create_generic_entity(dev_user_auth_token, generic_template_with_phi_id,
                                                           generic_name_phi,
                                                           DEFAULT_ORGANISATION_ID)
    assert create_generic_entity_response.status_code == 201, f"{create_generic_entity_response.text}"
    # and Delete it
    generic_entity_with_phi_id = create_generic_entity_response.json()["_id"]

    delete_generic_entity_response = delete_generic_entity(dev_user_auth_token, generic_entity_with_phi_id)
    assert delete_generic_entity_response.status_code == 204, f"{delete_generic_entity_response.text}"

    # TEST - Delete Generic Entity template
    delete_generic_template_no_phi_response = delete_template(dev_user_auth_token, generic_template_no_phi_id)
    assert delete_generic_template_no_phi_response.status_code == 204, f"{delete_generic_template_no_phi_response.text}"
    delete_generic_template_with_phi = delete_template(dev_user_auth_token, generic_template_with_phi_id)
    assert delete_generic_template_with_phi.status_code == 204, f"{delete_generic_template_with_phi.text}"

    delete_dev_user_response = delete_organization_user(dev_user_auth_token, dev_user_id)
    assert delete_dev_user_response.status_code == 204, f"{delete_dev_user_response.text}"


# @pytest.mark.skip
def test_dev_user_registration_codes_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # Setup
    # first create new organization
    get_self_org_response = get_self_organization(admin_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(admin_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)
    # create registration code by org_user in new organization should succeed
    registration_code1 = str(uuid.uuid4())
    create_registration_code1_response = create_registration_code(dev_user_auth_token, "RegistrationCode",
                                                                  registration_code1, organization_id)
    assert create_registration_code1_response.status_code == 201
    registration_code1_id = create_registration_code1_response.json()['_id']

    # create registration code by dev_user should succeed always
    registration_code2 = str(uuid.uuid4())
    create_registration_code2_response = create_registration_code(dev_user_auth_token, "RegistrationCode",
                                                                  registration_code2,
                                                                  DEFAULT_ORGANISATION_ID)
    assert create_registration_code2_response.status_code == 201

    registration_code2_id = create_registration_code2_response.json()['_id']

    # update registration code should succeed in both orgs
    update_registration_code_response = update_registration_code(dev_user_auth_token, registration_code1_id,
                                                                 str(uuid.uuid4()))
    assert update_registration_code_response.status_code == 200

    # update registration code (code2)
    update_registration_code_response = update_registration_code(dev_user_auth_token, registration_code2_id,
                                                                 str(uuid.uuid4()))
    assert update_registration_code_response.status_code == 200

    # get  should always succeed
    get_registration_code_response = get_registration_code(dev_user_auth_token, registration_code1_id)
    assert get_registration_code_response.status_code == 200

    # get in different org should fail
    get_registration_code_response = get_registration_code(dev_user_auth_token, registration_code2_id)
    assert get_registration_code_response.status_code == 200

    # search in same should succeed
    get_registration_code_list_response = get_registration_code_list(dev_user_auth_token)
    assert get_registration_code_list_response.status_code == 200
    assert get_registration_code_list_response.json()['metadata']['page']['totalResults'] >= 1

    # delete in same org should succeed
    delete_registration_response = delete_registration_code(dev_user_auth_token, registration_code1_id)
    assert delete_registration_response.status_code == 204

    # delete in different org should succeed
    delete_registration_response = delete_registration_code(dev_user_auth_token, registration_code2_id)
    assert delete_registration_response.status_code == 204

    # Teardown
    # delete org_user
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"
    # delete second organization
    delete_organization_response = delete_organization(admin_auth_token, organization_id)
    assert delete_organization_response.status_code == 204


# @pytest.mark.skip
def test_dev_user_files_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)
    # create second organization
    get_self_org_response = get_self_organization(dev_user_auth_token)
    assert get_self_org_response.status_code == 200
    template_id = get_self_org_response.json()['_ownerOrganization']['templateId']  # default org template
    create_organization_response = create_organization(dev_user_auth_token, template_id)
    assert create_organization_response.status_code == 201
    organization_id = create_organization_response.json()['_id']

    # add file attribute to Patient template
    patient_template_id = "a38f32d7-de6c-4252-9061-9bcdc253f6c9"
    get_patient_template_response = get_template(dev_user_auth_token, patient_template_id)
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
    update_template_response = update_template(dev_user_auth_token, patient_template_id, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    # primary_admin_auth_token, primary_admin_id = get_manu_admin_credentials(admin_auth_token, organization_id)
    # create patient in new org
    patient1_auth_token, patient1_id = create_single_patient(dev_user_auth_token, organization_id)
    # create patient in default org
    patient2_auth_token, patient2_id = create_single_patient(dev_user_auth_token)

    # create files in new organization and default
    name = f'test_file{uuid.uuid4().hex}'[0:16]
    mime_type = 'text/plain'
    data = open('./upload-file.txt', 'rb').read()
    create_file_response = create_file(dev_user_auth_token, name, mime_type)
    assert create_file_response.status_code == 200
    file1_id = create_file_response.json()['id']
    signed_url = create_file_response.json()['signedUrl']
    upload_response = requests.put(signed_url, data=data, headers={'Content-Type': 'text/plain'})
    assert upload_response.status_code == 200
    create_file2_response = create_file(dev_user_auth_token, name, mime_type)
    assert create_file2_response.status_code == 200
    file2_id = create_file2_response.json()['id']
    signed_url2 = create_file2_response.json()['signedUrl']
    upload_response = requests.put(signed_url2, data=data, headers={'Content-Type': 'text/plain'})
    assert upload_response.status_code == 200, f"{upload_response.text}"
    # associate files to patients
    update_patient_response = update_patient(dev_user_auth_token, patient1_id, organization_id, None, None,
                                             {file_attribute_name: {"id": file1_id}})
    assert update_patient_response.status_code == 200, f"{update_patient_response.text}"
    update_patient_response = update_patient(dev_user_auth_token, patient2_id, DEFAULT_ORGANISATION_ID,
                                             None, None,
                                             {file_attribute_name: {"id": file2_id}})
    assert update_patient_response.status_code == 200

    # get should succeed only in both organizations
    get_file_response = get_file(dev_user_auth_token, file1_id)  # should succeed
    assert get_file_response.status_code == 200
    get_file_response = get_file(dev_user_auth_token, file2_id)  # should fail
    assert get_file_response.status_code == 200

    # teardown
    delete_patient_response = delete_patient(dev_user_auth_token, patient1_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_patient_response = delete_patient(dev_user_auth_token, patient2_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"
    delete_org_user_response = delete_organization_user(dev_user_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204
    # delete second organization
    delete_organization_response = delete_organization(dev_user_auth_token, organization_id)
    assert delete_organization_response.status_code == 204

    # revert changes in Patient Template
    get_template_response = get_template(dev_user_auth_token, patient_template_id)
    template_payload = map_template(get_template_response.json())
    index = 0
    for element in template_payload['customAttributes']:
        if element['name'] == file_attribute_name:
            del template_payload['customAttributes'][index]
            continue
        else:
            index += 1
    update_template_response = update_template(dev_user_auth_token, patient_template_id, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"
    # delete org_user
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"


# @pytest.mark.skip
def test_dev_user_patient_alerts_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)
    # create a Custom Organisation
    create_organization_response = create_organization(dev_user_auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # create Patient in custom Org-n
    patient_email = f'test_patient_alert{uuid.uuid4().hex}'[0:32] + '@biotmail.com'
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    create_patient_default_response = create_patient(dev_user_auth_token, name, patient_email, PATIENT_TEMPLATE_NAME,
                                                     organization_id)
    assert create_patient_default_response.status_code == 201, f"{create_patient_default_response.text}"
    patient_id = create_patient_default_response.json()["_id"]
    accept_invitation(patient_email)

    # create a Patient Alert Template
    name = f'test_alert_templ{uuid.uuid4().hex}'[0:32]
    create_patient_alert_template_response = create_patient_alert_template(dev_user_auth_token, PATIENT_TEMPLATE_ID,
                                                                           name)
    assert create_patient_alert_template_response.status_code == 201, f'{create_patient_alert_template_response.text}'
    patient_alert_template_name = create_patient_alert_template_response.json()["name"]
    patient_alert_template_id = create_patient_alert_template_response.json()["id"]

    # TEST - Create Patient Alert by Name in Custom Organisation
    create_patient_alert_response = create_patient_alert_by_name(dev_user_auth_token, patient_id,
                                                                 patient_alert_template_name)
    assert create_patient_alert_response.status_code == 201, f'{create_patient_alert_response.text}'
    patient_alert_id = create_patient_alert_response.json()["_id"]

    # TEST - Update Patient Alert created by Name in Custom Organisation
    update_patient_alert_response = update_patient_alert(dev_user_auth_token, patient_id, patient_alert_id)
    assert update_patient_alert_response.status_code == 200, f'{update_patient_alert_response.text}'

    # TEST - Get By ID Patient Alert created by ID in Custom organisation
    get_patient_alert_by_id_response = get_patient_alert(dev_user_auth_token, patient_id, patient_alert_id)
    assert get_patient_alert_by_id_response.status_code == 200, f'{get_patient_alert_by_id_response.text}'

    # TEST - Search Patient Alerts
    search_patient_alerts_response = get_patient_alert_list(dev_user_auth_token, organization_id)
    assert search_patient_alerts_response.status_code == 200, f'{search_patient_alerts_response.text}'

    # TEST - Get current Alerts
    get_current_alerts_response = get_current_patient_alert_list(dev_user_auth_token, organization_id)
    assert get_current_alerts_response.status_code == 200, f"{get_current_alerts_response.text}"

    # TEST - Delete Patient Alert
    delete_patient_alert_response = delete_patient_alert(dev_user_auth_token, patient_id, patient_alert_id)
    assert delete_patient_alert_response.status_code == 204, f"{delete_patient_alert_response.text}"

    # TEST - Delete Patient
    delete_patient_response = delete_patient(dev_user_auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"{delete_patient_response.text}"

    # delete Organisation
    delete_organisation_response = delete_organization(dev_user_auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"{delete_organisation_response.text}"

    # delete Patient Alert template
    delete_patient_alert_template_response = delete_template(dev_user_auth_token, patient_alert_template_id)
    assert delete_patient_alert_template_response.status_code == 204, f"{delete_patient_alert_template_response.text}"
    # delete org_user
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"


# @pytest.mark.skip
def test_dev_user_measurements_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)
    # create Custom organization
    create_organization_response = create_organization(dev_user_auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # accept invitation as an Admin of a Custom Organisation
    #   get_organisation_response = get_organization(auth_token, organization_id)
    #   primary_admin_id = get_organisation_response.json()["_primaryAdministrator"]["id"]
    #   get_organisation_user_response = get_organization_user(auth_token, primary_admin_id)
    #   primary_admin_email = get_organisation_user_response.json()["_email"]
    #   accept_invitation(primary_admin_email)
    #   auth_token = login_with_credentials(primary_admin_email, "Aa123456strong!@")
    #   get_self_user_email_response = get_self_user_email(auth_token)
    #   assert get_self_user_email_response == primary_admin_email, \
    #       f"Actual email '{get_self_user_email_response}' does not match the expected"

    # Create Patient in Custom Organisation
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:351],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '@biotmail.com'
    create_patient_custom_response = create_patient(dev_user_auth_token, name, email, PATIENT_TEMPLATE_NAME,
                                                    organization_id)
    assert create_patient_custom_response.status_code == 201, f"Status code " \
                                                              f"{create_patient_custom_response.status_code} " \
                                                              f"{create_patient_custom_response.text}"
    patient_id_custom = create_patient_custom_response.json()["_id"]

    # Create Patient in Default Organisation as manu admin
    # auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:351],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '@biotmail.com'
    create_patient_default_response = create_patient(dev_user_auth_token, name, email, PATIENT_TEMPLATE_NAME,
                                                     DEFAULT_ORGANISATION_ID)
    assert create_patient_custom_response.status_code == 201, f"Status code " \
                                                              f"{create_patient_custom_response.status_code} " \
                                                              f"{create_patient_custom_response.text}"
    patient_id_default = create_patient_default_response.json()["_id"]

    # add observation attributes to Patient template
    get_patient_template_response = get_template(dev_user_auth_token, PATIENT_TEMPLATE_ID)
    assert get_patient_template_response.status_code == 200, f"{get_patient_template_response.text}"
    template_payload = map_template(get_patient_template_response.json())
    aggregated_observation_attribute_name = f'test_integ_dec_int{uuid.uuid4().hex}'[0:36]
    raw_observation_attribute_name = f'test_integ_waveform{uuid.uuid4().hex}'[0:36]
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
    update_template_response = update_template(dev_user_auth_token, PATIENT_TEMPLATE_ID, template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    # create a Device Template
    device_template_response, usage_session_template_response = create_device_template_with_session(dev_user_auth_token)
    assert device_template_response.status_code == 201, f"{device_template_response.text}"
    template_name = device_template_response.json()["name"]
    device_template_id = device_template_response.json()["id"]
    usage_session_template_id = usage_session_template_response.json()["id"]

    # Create Device in a Default Org-n
    create_device_response = create_device_without_registration_code(dev_user_auth_token, template_name,
                                                                     DEFAULT_ORGANISATION_ID)
    device_id_default = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # Create Device in a Custom Org-n
    create_device_response = create_device_without_registration_code(dev_user_auth_token, template_name,
                                                                     organization_id)
    device_id_custom = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # create session for Default Org-n
    create_session_response = create_usage_session_without_name(dev_user_auth_token, device_id_default,
                                                                patient_id_default,
                                                                usage_session_template_id)
    assert create_session_response.status_code == 201, f"{create_session_response.text}"
    usage_session_default_id = create_session_response.json()['_id']

    # create session for Custom Org-n
    create_session_response = create_usage_session_without_name(dev_user_auth_token, device_id_custom,
                                                                patient_id_custom,
                                                                usage_session_template_id)
    assert create_session_response.status_code == 201, f"{create_session_response.text}"
    usage_session_custom_id = create_session_response.json()['_id']

    # create measurement on Patient from Default org-n
    create_measurement_response = create_measurement(dev_user_auth_token, device_id_default, patient_id_default,
                                                     usage_session_default_id, aggregated_observation_attribute_name)
    assert create_measurement_response.status_code == 200, f"{create_measurement_response.text}"

    # create measurement on Patient from Default org-n
    create_measurement_response = create_measurement(dev_user_auth_token, device_id_custom, patient_id_custom,
                                                     usage_session_custom_id, aggregated_observation_attribute_name)
    assert create_measurement_response.status_code == 200, f"{create_measurement_response.text}"

    # create bulk measurement in Default Org-n
    create_bulk_measurement_response = create_bulk_measurement(dev_user_auth_token, device_id_default,
                                                               patient_id_default, usage_session_default_id,
                                                               aggregated_observation_attribute_name)
    assert create_bulk_measurement_response.status_code == 200, f"{create_bulk_measurement_response.text}"

    # create bulk measurement in Custom Org-n
    create_bulk_measurement_response = create_bulk_measurement(dev_user_auth_token, device_id_custom,
                                                               patient_id_custom, usage_session_custom_id,
                                                               aggregated_observation_attribute_name)
    assert create_bulk_measurement_response.status_code == 200, f"{create_bulk_measurement_response.text}"

    # TEST - get v1 raw measurements from Patient in Default Org-n
    get_v1_raw_measurement_response = get_raw_measurements(dev_user_auth_token, patient_id_default,
                                                           raw_observation_attribute_name)
    assert get_v1_raw_measurement_response.status_code == 200, f"{get_v1_raw_measurement_response.text}"
    # TEST - get v1 raw measurements from Patient in Custom Org-n
    get_v1_raw_measurement_response = get_raw_measurements(dev_user_auth_token, patient_id_custom,
                                                           raw_observation_attribute_name)
    assert get_v1_raw_measurement_response.status_code == 200, f"{get_v1_raw_measurement_response.text}"

    # TEST - get v1 aggregated measurements from Patient in Default Org-n
    get_v1_aggr_measurement_response = get_aggregated_measurements(dev_user_auth_token, patient_id_default,
                                                                   aggregated_observation_attribute_name)
    assert get_v1_aggr_measurement_response.status_code == 200, f"{get_v1_aggr_measurement_response.text}"

    # TEST - get v1 aggregated measurements from Patient in Custom Org-n
    get_v1_aggr_measurement_response = get_aggregated_measurements(dev_user_auth_token, patient_id_custom,
                                                                   aggregated_observation_attribute_name)
    assert get_v1_aggr_measurement_response.status_code == 200, f"{get_v1_aggr_measurement_response.text}"

    # TEST - get V2 raw measurements from Patient in Default Org-n
    get_v2_raw_measurement_response = get_v2_raw_measurements(dev_user_auth_token, patient_id_default,
                                                              raw_observation_attribute_name)
    assert get_v2_raw_measurement_response.status_code == 200, f"{get_v2_raw_measurement_response.text}"
    # TEST - get V2 raw measurements from Patient in Custom Org-n
    get_v2_raw_measurement_response = get_v2_raw_measurements(dev_user_auth_token, patient_id_custom,
                                                              raw_observation_attribute_name)
    assert get_v2_raw_measurement_response.status_code == 200, f"{get_v2_raw_measurement_response.text}"

    # TEST - get v2 aggregated measurements from Patient in Default Org-n
    get_v2_measurement_response = get_v2_aggregated_measurements(dev_user_auth_token, patient_id_default,
                                                                 aggregated_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 200, f"{get_v2_measurement_response.text}"
    # TEST - get v2 aggregated measurements from Patient in Custom Org-n
    get_v2_measurement_response = get_v2_aggregated_measurements(dev_user_auth_token, patient_id_custom,
                                                                 aggregated_observation_attribute_name)
    assert get_v2_measurement_response.status_code == 200, f"{get_v2_measurement_response.text}"

    # TEST - get device credentials should always succeed (try with caregiver from new org)
    get_credentials_response = get_device_credentials(dev_user_auth_token)
    assert get_credentials_response.status_code == 200, f"{get_credentials_response.text}"

    # teardown
    delete_usage_session_response = delete_usage_session(dev_user_auth_token, device_id_default,
                                                         usage_session_default_id)
    assert delete_usage_session_response.status_code == 204, f"{delete_usage_session_response.text}"
    delete_usage_session_response = delete_usage_session(dev_user_auth_token, device_id_custom, usage_session_custom_id)
    assert delete_usage_session_response.status_code == 204, f"{delete_usage_session_response.text}"
    delete_template_response = delete_template(dev_user_auth_token, usage_session_template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"

    # delete devices
    delete_device_response = delete_device(dev_user_auth_token, device_id_custom)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"
    delete_device_response = delete_device(dev_user_auth_token, device_id_default)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"

    # delete second organization
    delete_organization_response = delete_organization(dev_user_auth_token, organization_id)
    assert delete_organization_response.status_code == 204, f"{delete_organization_response.text}"

    # delete device template
    delete_device_template_response = delete_template(dev_user_auth_token, device_template_id)
    assert delete_device_template_response.status_code == 204, f"{delete_device_template_response.text}"

    # revert changes in Patient Template
    # delete raw attribute from Patient Template
    get_template_response = get_template(dev_user_auth_token, PATIENT_TEMPLATE_ID)
    template_payload = map_template(get_template_response.json())
    index = 0
    for element in template_payload['customAttributes']:
        if element['name'] == raw_observation_attribute_name:
            del template_payload['customAttributes'][index]
        else:
            index += 1
    update_template_response = update_patient_template_force_true(dev_user_auth_token, PATIENT_TEMPLATE_ID,
                                                                  template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    # delete aggregated attribute from Patient Template
    get_template_response = get_template(dev_user_auth_token, PATIENT_TEMPLATE_ID)
    template_payload = map_template(get_template_response.json())
    index = 0
    for element in template_payload['customAttributes']:
        if element['name'] == aggregated_observation_attribute_name:
            del template_payload['customAttributes'][index]
        else:
            index += 1
    update_template_response = update_patient_template_force_true(dev_user_auth_token, PATIENT_TEMPLATE_ID,
                                                                  template_payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    # delete org_user
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204, f"{delete_org_user_response.text}"


# @pytest.mark.skip
def test_dev_user_ums_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)
    dev_user_email = get_self_user_email(dev_user_auth_token)

    # set password by org_user
    new_password = "Bb234567NewPass"
    set_password_response = set_password(dev_user_auth_token, password, new_password)
    assert set_password_response.status_code == 200
    # check login with new password
    caregiver_auth_token = login_with_credentials(dev_user_email, new_password)

    # forgot password flow
    forgot_password_response = forgot_password(dev_user_email)
    new_password = "Cc345678NewPass2"
    reset_password_open_email_and_set_new_password(dev_user_email, new_password)
    # check login with new password
    caregiver_auth_token = login_with_credentials(dev_user_email, new_password)

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204


# @pytest.mark.skip
def test_dev_user_locales_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # get available locales should succeed
    get_locales_response = get_available_locales(dev_user_auth_token)
    assert get_locales_response.status_code == 200

    # get first non default in list
    default_code = get_locales_response.json()['defaultLocaleCode']
    system_code = get_locales_response.json()['systemLocaleCode']
    code = None
    for codes in get_locales_response.json()['availableLocales']:
        if codes['code'] != default_code and codes['code'] != system_code:
            code = codes['code']

    # code = get_locales_response.json()['availableLocales'][1]['code']
    # delete locale should succeed
    if code is not None:
        delete_locale_response = delete_locale(dev_user_auth_token, code)
        assert delete_locale_response.status_code == 200

    # add locale should succeed
    if code is not None:
        add_locale_response = add_locale(dev_user_auth_token, code)
        assert add_locale_response.status_code == 200

    # update locale should succeed
    update_locale_response = update_locale(dev_user_auth_token, code)
    assert update_locale_response.status_code == 200

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204


# @pytest.mark.skip
def test_dev_user_plugins_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # TEST - Create Plugin
    plugin_name = f'test_plugin{uuid.uuid4().hex}'[0:16]
    create_plugin_response = create_plugin(dev_user_auth_token, plugin_name)
    assert create_plugin_response.status_code == 201, f"{create_plugin_response.text}"
    plugin_display_name = create_plugin_response.json()["displayName"]
    assert plugin_display_name == plugin_name

    # TEST - Update plugin
    updated_display_name = 'updated_' + plugin_name
    time.sleep(5)
    update_plugin_response = update_plugin(dev_user_auth_token, 'Plugin-' + plugin_name, updated_display_name)
    assert update_plugin_response.status_code == 200, f"{update_plugin_response.text}"
    plugin_display_name = update_plugin_response.json()["displayName"]
    assert plugin_display_name == updated_display_name

    # TEST - Get plugin by name
    get_plugin_response = get_plugin(dev_user_auth_token, 'Plugin-' + plugin_name)
    assert get_plugin_response.status_code == 200, f"{get_plugin_response.text}"

    # TEST - Search plugin
    search_plugin_response = get_plugin_list(dev_user_auth_token, 'Plugin-' + plugin_name)
    assert search_plugin_response.status_code == 200, f"{search_plugin_response.text}"

    # TEST - Delete plugin
    delete_plugin_response = delete_plugin(dev_user_auth_token, 'Plugin-' + plugin_name)
    assert delete_plugin_response.status_code == 204, f"{delete_plugin_response.text}"

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204


# @pytest.mark.skip
def test_dev_user_dms_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)
    # TEST - Create report
    create_report_response = create_report(dev_user_auth_token)
    assert create_report_response.status_code == 201, f"{create_report_response.text}"
    report_id = create_report_response.json()['id']

    # TEST - Get report by id
    get_report_response = get_report(dev_user_auth_token, report_id)
    assert get_report_response.status_code == 200, f"{get_report_response.text}"

    # TEST - Search reports - only self
    search_report_response = get_report_list(dev_user_auth_token)
    assert search_report_response.status_code == 200, f"{search_report_response.text}"
    reports = search_report_response.json()
    initiator_user_ids_in_reports = [report['reportInitiator']['userId'] for report in reports['data']]
    get_self_user_response = get_self_user(dev_user_auth_token)
    self_user_id = get_self_user_response.json()["_id"]
    for user_id in initiator_user_ids_in_reports:
        assert self_user_id == user_id, f"Self user id {self_user_id} is not equal to report initiator {user_id}"

    # TEST - Delete report
    delete_report_response = delete_report(dev_user_auth_token, report_id)
    assert delete_report_response.status_code == 204, f"{delete_report_response.text}"
    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204


# @pytest.mark.skip
def test_dev_user_templates_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # TEST - View templates should succeed
    view_template_response = get_templates_list(dev_user_auth_token)
    assert view_template_response.status_code == 200, f"{view_template_response.text}"
    get_minimized_response = get_all_templates(dev_user_auth_token)
    assert get_minimized_response.status_code == 200, f"{get_minimized_response.text}"

    # TEST - Create Template
    create_template_response = create_generic_template(dev_user_auth_token)
    assert create_template_response.status_code == 201, f"{create_template_response.text}"
    template_id = create_template_response.json()["id"]

    # TEST - Get by id
    get_template_response = get_template_by_id(dev_user_auth_token, template_id)
    assert get_template_response.status_code == 200, f"{get_minimized_response.text}"

    # TEST - Get overview
    get_overview_response = get_template_overview(dev_user_auth_token, template_id)
    assert get_overview_response.status_code == 200, f"{get_overview_response.text}"

    # TEST - Update Template
    payload = get_template_response.json()
    update_template_response = update_template(dev_user_auth_token, template_id, payload)
    assert update_template_response.status_code == 200, f"{update_template_response.text}"

    # TEST - Delete template
    delete_template_response = delete_template(dev_user_auth_token, template_id)
    assert delete_template_response.status_code == 204, f"{delete_template_response.text}"
    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204


# @pytest.mark.skip
def test_dev_user_portal_builder_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)
    # TEST - View full portal information
    view_portal_response = view_full_portal_information(dev_user_auth_token, 'ORGANIZATION_PORTAL', 'ENTITY_LIST',
                                                        None)
    assert view_portal_response.status_code == 200, f"{view_portal_response}"
    payload = view_portal_response.json()
    view_id = payload['id']

    # TEST - Update view
    update_portal_view_response = update_portal_views(dev_user_auth_token, 'ORGANIZATION_PORTAL', view_id, payload)
    assert update_portal_view_response.status_code == 200, f"{update_portal_view_response.text}"
    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204


# @pytest.mark.skip
def test_dev_user_adb_abac_rules():
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)

    # deploy adb should fail
    deploy_response = deploy_adb(dev_user_auth_token)
    assert deploy_response.status_code == 403

    # undeploy should fail
    undeploy_response = undeploy_adb(dev_user_auth_token)
    assert undeploy_response.status_code == 403

    # TEST - Start init
    start_init_response = start_init_adb(dev_user_auth_token)
    assert start_init_response.status_code == 202, f"{start_init_response.text}"
    get_adb_info_response = get_adb_info(dev_user_auth_token)
    adb_state = get_adb_info_response.json()["activationState"]
    #    while adb_state != "ACTIVE_AND_SYNC_OFF":
    #        get_adb_info_response = get_adb_info(admin_auth_token)
    #        adb_state = get_adb_info_response.json()["activationState"]
    #    assert adb_state == "ACTIVE_AND_SYNC_OFF", f"Expected state 'ACTIVE_AND_SYNC_OFF', actual state '{adb_state}'"

    # TEST - Stop init
    #    start_init_response = start_init_adb(dev_user_auth_token)
    #    assert start_init_response.status_code == 202, f"{start_init_response.text}"
    #    get_adb_info_response = get_adb_info(dev_user_auth_token)
    #    adb_state = get_adb_info_response.json()["activationState"]
    #    assert adb_state == "INITIALIZING", f"Expected state 'INITIALIZING', actual state '{adb_state}'"
    stop_init_response = stop_init_adb(dev_user_auth_token)
    assert stop_init_response.status_code == 200, f"{start_init_response.text}"
    #   while adb_state != "INACTIVE":
    #       get_adb_info_response = get_adb_info(dev_user_auth_token)
    #       adb_state = get_adb_info_response.json()["activationState"]
    #   assert adb_state == "INACTIVE", f"Expected state 'INACTIVE', actual state '{adb_state}'"

    # stop sync should succeed
    stop_sync_response = stop_sync_adb(admin_auth_token)
    assert stop_sync_response.status_code == 200

    # get adb info should succeed
    get_adb_response = get_adb_info(dev_user_auth_token)
    assert get_adb_response.status_code == 200

    # teardown
    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204


# @pytest.mark.skip
def test_dev_user_usage_session_abac_rules():  # IP
    admin_auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    # create dev_user by admin
    dev_user_template_name = get_dev_user_template_name(admin_auth_token)
    dev_user_auth_token, dev_user_id, password = create_single_org_user(admin_auth_token, dev_user_template_name,
                                                                        DEFAULT_ORGANISATION_ID)
    # create a Device Template
    device_template_response, usage_session_template_response = create_device_template_with_session(dev_user_auth_token)
    assert device_template_response.status_code == 201, f"{device_template_response.text}"
    template_name = device_template_response.json()["name"]
    device_template_id = device_template_response.json()["id"]
    usage_session_template_id = usage_session_template_response.json()["id"]

    # create a Custom Organisation
    create_organization_response = create_organization(dev_user_auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

#   # accept invitation as an admin of custom Org-n
#   get_organisation_response = get_organization(auth_token, organization_id)
#   primary_admin_id = get_organisation_response.json()["_primaryAdministrator"]["id"]
#   get_organisation_user_response = get_organization_user(auth_token, primary_admin_id)
#   primary_admin_email = get_organisation_user_response.json()["_email"]
#   accept_invitation(primary_admin_email)
#   auth_token = login_with_credentials(primary_admin_email, "Aa123456strong!@")
#   get_self_user_email_response = get_self_user_email(auth_token)
#   assert get_self_user_email_response == primary_admin_email, \
#       f"Actual email '{get_self_user_email_response}' does not match the expected"

    # create Device in a Custom Org-n
    # auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    create_device_response = create_device_without_registration_code(dev_user_auth_token, template_name, organization_id)
    device_id = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # create Patient in custom Org-n
    # auth_token = login_with_credentials(primary_admin_email, "Aa123456strong!@")
    patient_email = f'test_patient_usage{uuid.uuid4().hex}'[0:32] + '@biotmail.com'
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    create_patient_default_response = create_patient(dev_user_auth_token, name, patient_email, PATIENT_TEMPLATE_NAME,
                                                     organization_id)
    assert create_patient_default_response.status_code == 201, f"{create_patient_default_response.text}"
    patient_id = create_patient_default_response.json()["_id"]

    # accept invitation as a Patient of custom Org-n
    accept_invitation(patient_email)
    patient_auth_token = login_with_credentials(patient_email, "Aa123456strong!@")
    get_self_user_email_response = get_self_user_email(patient_auth_token)
    assert get_self_user_email_response == patient_email, \
        f"Actual email '{get_self_user_email_response}' does not match the expected"

    # assign device to a Patient
    # auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    update_device_response = update_device_with_new_patient(dev_user_auth_token, device_id, patient_id)
    assert update_device_response.status_code == 200, f"{update_device_response.text}"

    # start simulator with device
    sim_status = ' '
    while sim_status != "NO_RUNNING_SIMULATION":
        sim_status = check_simulator_status()
    start_simulation_with_existing_device(device_id, os.getenv('USERNAME'), os.getenv('PASSWORD'))
    simulation_status_response = get_simulation_status()
    device_id_in_simulation_status = simulation_status_response.json()['devicesStatus'][0]['deviceStatistics'][
        'deviceId']
    assert device_id_in_simulation_status == device_id, "Simulation is not started with expected device"

    # TEST - Start a Remote Usage session and Get a Remote Usage session by ID
    # auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    start_usage_session_response = start_usage_session_without_name(dev_user_auth_token, device_id, usage_session_template_id,
                                                                    patient_id)
    assert start_usage_session_response.status_code == 201, f"{start_usage_session_response.text}"
    usage_session_id = start_usage_session_response.json()["_id"]
    get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
    assert get_usage_session_response.status_code == 200, f"{get_usage_session_response.text}"
    usage_session_status = get_usage_session_response.json()["_state"]
    while usage_session_status != "ACTIVE":
        get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
        usage_session_status = get_usage_session_response.json()["_state"]
        if usage_session_status == "DONE":
            break
    assert usage_session_status == "ACTIVE", f"The current status is {usage_session_status}, not 'ACTIVE'"

    # TEST - Pause a Remote usage session
    pause_usage_session_response = pause_usage_session(dev_user_auth_token, device_id, usage_session_id)
    assert pause_usage_session_response.status_code == 200, f"{pause_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    while usage_session_status != "PAUSED":
        get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
        usage_session_status = get_usage_session_response.json()["_state"]
        if usage_session_status == "DONE":
            break
    assert usage_session_status == "PAUSED", f"The current status is {usage_session_status}, not 'PAUSED'"

    # TEST - Resume a Remote usage session
    resume_usage_session_response = resume_usage_session(dev_user_auth_token, device_id, usage_session_id)
    assert resume_usage_session_response.status_code == 200, f"{resume_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    while usage_session_status != "ACTIVE":
        get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
        usage_session_status = get_usage_session_response.json()["_state"]
        if usage_session_status == "DONE":
            break
    assert usage_session_status == "ACTIVE", f"The current status is {usage_session_status}, not 'ACTIVE'"

    # TEST - Stop a Remote usage session
    stop_usage_session_response = stop_usage_session(dev_user_auth_token, device_id, usage_session_id)
    assert stop_usage_session_response.status_code == 200, f"{stop_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    usage_session_stop_reason = get_usage_session_response.json()["_summary"]["_stopReasonCode"]
    while usage_session_status != "DONE" and usage_session_stop_reason != "COMPLETION":
        get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
        usage_session_status = get_usage_session_response.json()["_state"]
        usage_session_stop_reason = get_usage_session_response.json()["_summary"]["_stopReasonCode"]
        if usage_session_status == "DONE" and usage_session_stop_reason == "TIMEOUT":
            break
    assert usage_session_stop_reason == "COMPLETION", f"The stop reason is {usage_session_stop_reason}, not 'COMPLETION'"

    # TEST - Delete a Remote Usage session
    delete_usage_session_response = delete_usage_session(dev_user_auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204, f"{delete_usage_session_response.text}"

    # stop simulation
    stop_simulation()
    simulation_status_response = get_simulation_status()
    simulation_status = simulation_status_response.json()["code"]
    assert simulation_status == "NO_RUNNING_SIMULATION"

    # TEST - Create an External Usage session
    create_usage_session_response = create_usage_session_without_name(dev_user_auth_token, device_id, patient_id,
                                                                      usage_session_template_id)
    assert create_usage_session_response.status_code == 201, f"{create_usage_session_response.text}"
    usage_session_id = create_usage_session_response.json()["_id"]

    # TEST - Edit an External Usage session and Get an External Usage session by ID
    update_external_usage_session_response = update_usage_session(dev_user_auth_token, device_id, usage_session_id)
    assert update_external_usage_session_response.status_code == 200, f"{update_external_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
    assert get_usage_session_response.status_code == 200, f"{get_usage_session_response.text}"
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "PAUSING", f"The current status is {usage_session_status}, not 'PAUSING'"

    # TEST - Delete an External Usage session
    delete_usage_session_response = delete_usage_session(dev_user_auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204, f"{delete_usage_session_response.text}"

    # as a Patient of custom organisation create External usage session with PHI=true attribute
    patient_auth_token = login_with_credentials(patient_email, "Aa123456strong!@")
    create_usage_with_phi_response = create_usage_session_with_name(patient_auth_token, device_id, patient_id,
                                                                    usage_session_template_id)
    assert create_usage_with_phi_response.status_code == 201, f"{create_usage_with_phi_response.text}"
    usage_session_id = create_usage_with_phi_response.json()["_id"]
    get_usage_session_response = get_usage_session_by_id(patient_auth_token, device_id, usage_session_id)
    phi_attribute = get_usage_session_response.json()["_name"]
    usage_session = json.loads(get_usage_session_response.text)
    i = 0
    for key, value in usage_session.items():
        if value is not None and isinstance(value, str):
            if phi_attribute in value:
                i += 1
    assert i == 2, "PHI attribute is not visible for Patient"

    # TEST - Verify that phi=true attribute is seen by dev user
    # auth_token = login_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    get_usage_session_response = get_usage_session_by_id(dev_user_auth_token, device_id, usage_session_id)
    usage_session = json.loads(get_usage_session_response.text)
    i = 0
    for key, value in usage_session.items():
        if value is not None and isinstance(value, str):
            if phi_attribute in value:
                i += 1
    assert i == 2, "PHI attribute is not visible for dev user"

    # TEST - Search Usage sessions
    search_usage_sessions_response = get_usage_session_list(dev_user_auth_token)
    assert search_usage_sessions_response.status_code == 200, f"{search_usage_sessions_response.text}"

    # TEST - Search Current Open Usage sessions
    search_current_usage_sessions_response = get_current_usage_sessions(dev_user_auth_token)
    assert search_current_usage_sessions_response.status_code == 200, f"{search_current_usage_sessions_response.text}"

    # teardown
    # Delete an External Usage session
    delete_usage_session_response = delete_usage_session(dev_user_auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204, f"{delete_usage_session_response.text}"

    # Delete Device
    delete_device_response = delete_device(dev_user_auth_token, device_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"

    # Delete Organisation
    delete_organisation_response = delete_organization(dev_user_auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"{delete_organisation_response.text}"

    # Delete Device template
    delete_device_template_response = delete_template(dev_user_auth_token, device_template_id)
    assert delete_device_template_response.status_code == 204, f"{delete_device_template_response.text}"

    delete_org_user_response = delete_organization_user(admin_auth_token, dev_user_id)
    assert delete_org_user_response.status_code == 204
