from test_constants import *
from email_interface import *
from API_drivers import *


def test_manu_admin_organisation_abac_rules():
    # TEST - Create Organization
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    create_organization_response = create_organization(auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # TEST - Update the Created Organisation
    change_string = f'Updated Org Name + {uuid.uuid4().hex}'[0:32]
    update_organization_response = update_organization(auth_token, organization_id, change_string)
    assert update_organization_response.status_code == 200, f"Status code {update_organization_response.status_code} " \
                                                            f"{update_organization_response.text}"

    # TEST - Get Created Organisation by id
    get_organisation_response = get_organization(auth_token, organization_id)
    assert get_organisation_response.status_code == 200, f"Status code {get_organisation_response.status_code} " \
                                                         f"{get_organisation_response.text}"

    # TEST - Search all Organisations
    search_organisations_response = get_organization_list(auth_token)
    assert search_organisations_response.status_code == 200, f"Status code " \
                                                             f"{search_organisations_response.status_code} " \
                                                             f"{search_organisations_response.text}"

    # TEST - Delete the Created Organisation
    delete_organisation_response = delete_organization(auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"Status code {delete_organisation_response.status_code} " \
                                                            f"{delete_organisation_response.text}"
    # TEST - Delete the Default Organisation - must be forbidden
    delete_default_organisation_response = delete_organization(auth_token, DEFAULT_ORGANISATION_ID)
    assert delete_default_organisation_response.status_code == 403, f"Status code " \
                                                                    f"{delete_organisation_response.status_code} " \
                                                                    f"{delete_organisation_response.text}"


def test_manu_admin_patient_abac_rules():
    # TEST - Create Patient in Custom Organisation - must be forbidden
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    create_organization_response = create_organization(auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:351],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}
    email = f'integ_test_{uuid.uuid4().hex}'[0:16] + '@biotmail.com'
    create_patient_custom_response = create_patient(auth_token, name, email, PATIENT_TEMPLATE_NAME, organization_id)
    assert create_patient_custom_response.status_code == 403, f"Status code " \
                                                              f"{create_patient_custom_response.status_code} " \
                                                              f"{create_patient_custom_response.text}"

    # accept invitation as an Admin of a Custom Organisation
    get_organisation_response = get_organization(auth_token, organization_id)
    primary_admin_id = get_organisation_response.json()["_primaryAdministrator"]["id"]
    get_organisation_user_response = get_organization_user(auth_token, primary_admin_id)
    primary_admin_email = get_organisation_user_response.json()["_email"]
    accept_invitation(primary_admin_email)
    auth_token = login_with_credentials(primary_admin_email, "Aa123456strong!@")
    get_self_user_email_response = get_self_user_email(auth_token)
    assert get_self_user_email_response == primary_admin_email, \
        f"Actual email '{get_self_user_email_response}' does not match the expected"
    email = f'integ_test_phi{uuid.uuid4().hex}'[0:16] + '@biotmail.com'

    # create a Patient with phi attribute in Custom Organisation
    create_patient_custom_response = create_patient_with_phi(auth_token, name, email, PATIENT_TEMPLATE_NAME,
                                                             organization_id)  # create patient with phi attributes
    phi_attribute = "phitruelabel"
    assert create_patient_custom_response.status_code == 201, f"Status code " \
                                                              f"{create_patient_custom_response.status_code}" \
                                                              f" {create_patient_custom_response.text}"
    patient_id = create_patient_custom_response.json()["_id"]
    get_patient_by_id_response = get_patient(auth_token, patient_id)
    phi_attribute_value = get_patient_by_id_response.json()["phitruelabel"]
    assert phi_attribute_value in get_patient_by_id_response.text, \
        f"'{phi_attribute_value}' should be present in the response"
    assert phi_attribute_value == "testphi", f"phi attribute is '{phi_attribute_value}' instead of expected"

    # TEST - Edit Patient in Custom Organisation - must be allowed
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    get_self_user_email_response = get_self_user_email(auth_token)
    assert get_self_user_email_response == os.getenv('MANU_ADMIN_LOGIN'), \
        f"Actual email '{get_self_user_email_response}' does not match the expected"
    change_string = "Updated description"
    update_patient_response = update_patient_without_caregiver(auth_token, patient_id, organization_id, change_string)
    updated_description = update_patient_response.json()["_description"]
    assert update_patient_response.status_code == 200, f"Status code {update_patient_response.status_code} " \
                                                       f"{update_patient_response.text}"
    assert updated_description == change_string, f"'{updated_description}' doesn't match the expected value " \
                                                 f"{change_string}"

    # TEST - Get Patient by ID in Custom Organisation and Verify that phi attribute is not seen for manu admin
    get_patient_by_id_response = get_patient(auth_token, patient_id)
    assert get_patient_by_id_response.status_code == 200, f"Status code {get_patient_by_id_response.status_code} " \
                                                          f"{get_patient_by_id_response.text}"
    assert patient_id == get_patient_by_id_response.json()["_id"], f"{patient_id} doesn't match the expected"
    patient = json.loads(get_patient_by_id_response.text)
    for key, value in patient.items():
        assert phi_attribute not in key, f"PHI=true attribute {phi_attribute} is present in response"

    # TEST - Disable a Patient in Custom Organisation
    disable_patient_response = change_patient_state(auth_token, patient_id, state='DISABLED')
    assert disable_patient_response.status_code == 200, f"Status code {disable_patient_response.status_code} " \
                                                        f"{disable_patient_response.text}"
    assert disable_patient_response.json()["_enabled"] == "DISABLED", f"Patient's state is " \
                                                                      f"{disable_patient_response.json()['_enabled']}" \
                                                                      f" instead of ""DISABLED"

    # TEST - Disable a Patient in Custom Organisation
    enable_patient_response = change_patient_state(auth_token, patient_id, state='ENABLED')
    assert enable_patient_response.status_code == 200, f"Status code {enable_patient_response.status_code} " \
                                                       f"{enable_patient_response.text}"
    assert enable_patient_response.json()["_enabled"] == "ENABLED", f"Patient's state is " \
                                                                    f"{disable_patient_response.json()['_enabled']}" \
                                                                    f" instead of ""ENABLED"

    # TEST - Resend Invitation to a Patient in Custom Organisation
    resend_invitation_response = resend_invitation(auth_token, patient_id)
    assert resend_invitation_response.status_code == 200, f"Status code {resend_invitation_response.status_code}" \
                                                          f" {resend_invitation_response.text}"
    assert resend_invitation_response.json()["userId"] == patient_id

    # TEST - Search Patients
    get_patients_response = get_patient_list(auth_token)
    assert get_patients_response.status_code == 200, f"Status code {get_patients_response.status_code} " \
                                                     f"{get_patient_by_id_response.text}"
    patients_data = json.loads(get_patients_response.text)
    all_patients = patients_data["data"]
    for patient in all_patients:
        for key, value in patient.items():
            assert phi_attribute not in key, f"PHI=true attribute {phi_attribute} is present in response"

    # TEST - Delete Patient in Custom Organisation
    delete_patient_response = delete_patient(auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"Status code {delete_patient_response.status_code} " \
                                                       f"{delete_patient_response.text}"

    # TEST - Delete Custom Organisation
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    get_self_user_email_response = get_self_user_email(auth_token)
    assert get_self_user_email_response == os.getenv('MANU_ADMIN_LOGIN'), \
        f"Actual email '{get_self_user_email_response}' does not match the expected"
    delete_organisation_response = delete_organization(auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"Status code {delete_organisation_response.status_code}" \
                                                            f"{delete_organisation_response.text}"

    # TEST - Create Patient in Default Organisation - without phi attributes
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    get_self_user_email_response = get_self_user_email(auth_token)
    assert get_self_user_email_response == os.getenv('MANU_ADMIN_LOGIN'), \
        f"Actual email '{get_self_user_email_response}' does not match the expected"
    organization_id = DEFAULT_ORGANISATION_ID
    email = f'integ_test_no_phi{uuid.uuid4().hex}'[0:16] + '@biotmail.com'
    create_patient_default_response = create_patient(auth_token, name, email, "Patient", organization_id)
    assert create_patient_default_response.status_code == 201, f"Status code " \
                                                               f"{create_patient_default_response.status_code}" \
                                                               f" {create_patient_default_response.text}"
    patient_id = create_patient_default_response.json()["_id"]

    # TEST - Create Patient in Default Organisation - with phi attributes - must be forbidden
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    get_self_user_email_response = get_self_user_email(auth_token)
    assert get_self_user_email_response == os.getenv('MANU_ADMIN_LOGIN'), \
        f"Actual email '{get_self_user_email_response}' does not match the expected"
    organization_id = DEFAULT_ORGANISATION_ID
    email = f'integ_test_patient_phi{uuid.uuid4().hex}'[0:16] + '@biotmail.com'
    create_patient_with_phi_default_response = create_patient_with_phi(auth_token, name, email, PATIENT_TEMPLATE_NAME,
                                                                       organization_id)
    assert create_patient_with_phi_default_response.status_code == 403, \
        f"{create_patient_with_phi_default_response.text}"

    # TEST - Get Patient by ID in Default Organisation - without phi attributes
    get_patient_by_id_response = get_patient(auth_token, patient_id)
    assert get_patient_by_id_response.status_code == 200, f"Status code {get_patient_by_id_response.status_code}" \
                                                          f"{get_patient_by_id_response.text}"
    assert patient_id == get_patient_by_id_response.json()["_id"]

    # TEST - Search Patients in Custom organisation
    get_patients_response = get_patient_list(auth_token)
    assert get_patients_response.status_code == 200, f"Status code {get_patients_response.status_code}" \
                                                     f"{get_patients_response.text}"

    # TEST - Delete Patient in Default Organisation
    delete_patient_response = delete_patient(auth_token, patient_id)
    assert delete_patient_response.status_code == 204, f"Status code {delete_patient_response.status_code}" \
                                                       f"{delete_patient_response.text}"


def test_manu_admin_caregiver_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # create a Custom Organisation
    create_organization_response = create_organization(auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}

    # create Caregiver Template
    create_caregiver_template_response = create_caregiver_template(auth_token)
    template_name = create_caregiver_template_response.json()["name"]
    template_id = create_caregiver_template_response.json()["id"]
    email = f'Caregiver_Templ_{uuid.uuid4().hex}'[0:35] + '@biotmail.com'

    # TEST - Create Caregiver in Custom Organisation
    create_caregiver_response = create_caregiver(auth_token, name, email, template_name, organization_id)
    assert create_caregiver_response.status_code == 201, f"Status code {create_organization_response.status_code}" \
                                                         f" {create_organization_response.text}"
    caregiver_id = create_caregiver_response.json()["_id"]

    # TEST - Update Caregiver in Custom Organisation
    change_string = "updated caregiver test"
    update_caregiver_response = update_caregiver(auth_token, caregiver_id, organization_id, change_string)
    assert update_caregiver_response.status_code == 200, f"Status code {update_caregiver_response.status_code}" \
                                                         f" {update_caregiver_response.text}"
    assert update_caregiver_response.json()["_description"] == change_string, \
        f'{update_caregiver_response.json()["_description"]} doesn\'t match the {change_string}'

    # TEST - Caregiver in Custom Organisation by ID
    get_caregiver_by_id_response = get_caregiver(auth_token, caregiver_id)
    assert get_caregiver_by_id_response.status_code == 200
    assert get_caregiver_by_id_response.json()["_id"] == caregiver_id

    # TEST - Disable a Caregiver in Custom Organisation
    disable_caregiver_response = change_caregiver_state(auth_token, caregiver_id, state='DISABLED')
    assert disable_caregiver_response.status_code == 200, f"Status code {disable_caregiver_response.status_code} " \
                                                          f"{disable_caregiver_response.text}"
    assert disable_caregiver_response.json()["_enabled"] == "DISABLED", f"Caregiver's state is " \
                                                                        f"{disable_caregiver_response.json()['_enabled']}" \
                                                                        f"instead of ""DISABLED"

    # TEST - Disable a Caregiver in Custom Organisation
    enable_caregiver_response = change_caregiver_state(auth_token, caregiver_id, state='ENABLED')
    assert enable_caregiver_response.status_code == 200, f"Status code {enable_caregiver_response.status_code} " \
                                                         f"{enable_caregiver_response.text}"
    assert enable_caregiver_response.json()["_enabled"] == "ENABLED", f"Caregiver's state is " \
                                                                      f"{enable_caregiver_response.json()['_enabled']}" \
                                                                      f" instead of ""ENABLED"

    # TEST - Resend Invitation to a Caregiver in Custom Organisation
    resend_invitation_response = resend_invitation(auth_token, caregiver_id)
    assert resend_invitation_response.status_code == 200, f"Status code {resend_invitation_response.status_code}" \
                                                          f" {resend_invitation_response.text}"
    assert resend_invitation_response.json()["userId"] == caregiver_id

    # TEST - Search Caregivers
    get_caregivers_response = get_caregiver_list(auth_token)
    assert get_caregivers_response.status_code == 200

    # TEST - Delete Caregiver fin Custom Organisation
    delete_caregiver_response = delete_caregiver(auth_token, caregiver_id)
    assert delete_caregiver_response.status_code == 204
    get_caregiver_by_id_response = get_caregiver(auth_token, caregiver_id)
    assert get_caregiver_by_id_response.status_code == 404
    assert get_caregiver_by_id_response.json()["code"] == "USER_NOT_FOUND"

    # delete Organisation
    delete_organisation_response = delete_organization(auth_token, organization_id)
    assert delete_organisation_response.status_code == 204

    # delete Caregiver template
    delete_caregiver_template_response = delete_template(auth_token, template_id)
    assert delete_caregiver_template_response.status_code == 204


def test_manu_admin_org_user_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # create a Custom Organisation
    create_organization_response = create_organization(auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()["_id"]
    name = {"firstName": f'first_name_test_{uuid.uuid4().hex}'[0:35],
            "lastName": f'last_name_test_{uuid.uuid4().hex}'[0:35]}

    # create Org-n User Template
    create_org_user_template_response = create_org_user_template(auth_token)
    template_name = create_org_user_template_response.json()["name"]
    template_id = create_org_user_template_response.json()["id"]
    email = f'Org_User_Template_{uuid.uuid4().hex}'[0:32] + '@biotmail.com'

    # TEST - Create Org-n User in Custom Organisation
    create_org_user_response = create_organization_user(auth_token, template_name, name, email, organization_id)
    org_user_id = create_org_user_response.json()["_id"]
    assert create_org_user_response.status_code == 201, f"Status code {create_org_user_response.status_code}" \
                                                        f" {create_org_user_response.text}"

    # TEST - Update Org-n User in Custom Organisation
    change_string = "updated org user test"
    update_org_user_response = update_organization_user(auth_token, org_user_id, organization_id, change_string)
    assert update_org_user_response.status_code == 200, f"Status code {update_org_user_response.status_code}" \
                                                        f" {update_org_user_response.text}"
    assert update_org_user_response.json()["_description"] == change_string, \
        f'{update_org_user_response.json()["_description"]} doesn\'t match the {change_string}'

    # TEST - Get Org-n User in Custom Organisation by ID
    get_org_user_by_id_response = get_organization_user(auth_token, org_user_id)
    assert get_org_user_by_id_response.status_code == 200
    assert get_org_user_by_id_response.json()["_id"] == org_user_id

    # TEST - Disable an Org-n User in Custom Organisation
    disable_org_user_response = change_organization_user_state(auth_token, org_user_id, state='DISABLED')
    assert disable_org_user_response.status_code == 200, f"Status code {disable_org_user_response.status_code} " \
                                                         f"{disable_org_user_response.text}"
    assert disable_org_user_response.json()["_enabled"] == "DISABLED", f"Caregiver's state is " \
                                                                       f"{disable_org_user_response.json()['_enabled']}" \
                                                                       f" instead of ""DISABLED"

    # TEST - Disable an Org-n User in Custom Organisation
    enable_org_user_response = change_organization_user_state(auth_token, org_user_id, state='ENABLED')
    assert enable_org_user_response.status_code == 200, f"Status code {enable_org_user_response.status_code} " \
                                                        f"{enable_org_user_response.text}"
    assert enable_org_user_response.json()["_enabled"] == "ENABLED", f"Caregiver's state is " \
                                                                     f"{enable_org_user_response.json()['_enabled']}" \
                                                                     f" instead of ""ENABLED"

    # TEST - Resend Invitation to an Org-n User in Custom Organisation
    resend_invitation_response = resend_invitation(auth_token, org_user_id)
    assert resend_invitation_response.status_code == 200, f"Status code {resend_invitation_response.status_code}" \
                                                          f" {resend_invitation_response.text}"
    assert resend_invitation_response.json()["userId"] == org_user_id

    # TEST - Search Org-n Users
    get_org_users_response = get_organization_user_list(auth_token)
    assert get_org_users_response.status_code == 200

    # TEST - Delete Org-n User in Custom Organisation
    delete_org_user_response = delete_organization_user(auth_token, org_user_id)
    assert delete_org_user_response.status_code == 204
    get_org_user_by_id_response = get_organization_user(auth_token, org_user_id)
    assert get_org_user_by_id_response.status_code == 404
    assert get_org_user_by_id_response.json()["code"] == "USER_NOT_FOUND"

    # delete Organisation
    delete_organisation_response = delete_organization(auth_token, organization_id)
    assert delete_organisation_response.status_code == 204

    # delete Org-n User template
    delete_caregiver_template_response = delete_template(auth_token, template_id)
    assert delete_caregiver_template_response.status_code == 204


def test_manu_admin_device_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # create a Device Template
    device_template_response = create_device_template_with_session(auth_token)
    assert device_template_response.status_code == 201, f"{device_template_response.text}"
    template_name = device_template_response.json()["name"]
    template_id = device_template_response.json()["id"]

    # create a Custom Organisation
    create_organization_response = create_organization(auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # TEST - Create Device in a Custom Org-n
    create_device_response = create_device_without_registration_code(auth_token, template_name, organization_id)
    device_id = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # TEST - Update Device
    update_device_response, updated_string = update_device_without_patient(auth_token, device_id)
    assert update_device_response.status_code == 200, f"{update_device_response.text}"

    # TEST - Get Device by ID
    get_device_by_id_response = get_device(auth_token, device_id)
    assert get_device_by_id_response.status_code == 200
    device_description_updated = update_device_response.json()["_description"]
    assert device_description_updated == updated_string, f"{device_description_updated} is not equal to " \
                                                         f"{updated_string}"

    # TEST - Search Devices
    search_devices_response = get_device_list(auth_token)
    assert search_devices_response.status_code == 200, f"{search_devices_response.text}"

    # TEST - Delete Device
    delete_device_response = delete_device(auth_token, device_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"

    # delete Organisation
    delete_organisation_response = delete_organization(auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"{delete_organisation_response.text}"

    # delete Device template
    delete_device_template_response = delete_template(auth_token, template_id)
    assert delete_device_template_response.status_code == 204, f"{delete_device_template_response.text}"


def test_manu_admin_usage_session_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # create a Device Template
    device_template_response = create_device_template_with_session(auth_token)
    assert device_template_response.status_code == 201, f"{device_template_response.text}"
    template_name = device_template_response.json()["name"]
    device_template_id = device_template_response.json()["id"]

    # get usage session template
    usage_session_templates_response = get_template_by_parent_id(auth_token, parent_template_id=device_template_id)
    assert usage_session_templates_response.status_code == 200, f"{usage_session_templates_response.text}"
    usage_sessions_templates = json.loads(usage_session_templates_response.text)
    usage_session_data = usage_sessions_templates["data"]
    usage_session_template_id = None
    for usage_template in usage_session_data:
        usage_session_template_id = usage_template["id"]

    # create a Custom Organisation
    create_organization_response = create_organization(auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # accept invitation as an admin of custom Org-n
    get_organisation_response = get_organization(auth_token, organization_id)
    primary_admin_id = get_organisation_response.json()["_primaryAdministrator"]["id"]
    get_organisation_user_response = get_organization_user(auth_token, primary_admin_id)
    primary_admin_email = get_organisation_user_response.json()["_email"]
    accept_invitation(primary_admin_email)
    auth_token = login_with_credentials(primary_admin_email, "Aa123456strong!@")
    get_self_user_email_response = get_self_user_email(auth_token)
    assert get_self_user_email_response == primary_admin_email, \
        f"Actual email '{get_self_user_email_response}' does not match the expected"

    # create Device in a Custom Org-n
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    create_device_response = create_device_without_registration_code(auth_token, template_name, organization_id)
    device_id = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # create Patient in custom Org-n
    auth_token = login_with_credentials(primary_admin_email, "Aa123456strong!@")
    patient_email = f'patient_usage{uuid.uuid4().hex}'[0:32] + '@biotmail.com'
    name = {"firstName": f'Patient',
            "lastName": f'Usage'}
    create_patient_default_response = create_patient(auth_token, name, patient_email, PATIENT_TEMPLATE_NAME,
                                                     organization_id)
    assert create_patient_default_response.status_code == 201, f"{create_patient_default_response.text}"
    patient_id = create_patient_default_response.json()["_id"]

    # accept invitation as a Patient of custom Org-n
    accept_invitation(patient_email)
    auth_token = login_with_credentials(patient_email, "Aa123456strong!@")
    get_self_user_email_response = get_self_user_email(auth_token)
    assert get_self_user_email_response == patient_email, \
        f"Actual email '{get_self_user_email_response}' does not match the expected"

    # assign device to a Patient
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    update_device_response = update_device_with_new_patient(auth_token, device_id, patient_id)
    assert update_device_response.status_code == 200, f"{update_device_response.text}"

    # Start a session with device in simulator
    start_simulation_with_existing_device(device_id, os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # TEST - Start a Remote Usage session and Get a Remote Usage session by ID
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    start_usage_session_response = start_usage_session_without_name(auth_token, device_id, usage_session_template_id,
                                                                    patient_id)
    assert start_usage_session_response.status_code == 201, f"{start_usage_session_response.text}"
    usage_session_id = start_usage_session_response.json()["_id"]
    get_usage_session_response = get_usage_session_by_id(auth_token, device_id, usage_session_id)
    assert get_usage_session_response.status_code == 200, f"{get_usage_session_response.text}"
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "ACTIVE", f"The current status is {usage_session_status}, not 'ACTIVE'"

    # TEST - Pause a Remote usage session
    pause_usage_session_response = pause_usage_session(auth_token, device_id, usage_session_id)
    assert pause_usage_session_response.status_code == 200, f"{pause_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(auth_token, device_id, usage_session_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "PAUSED", f"The current status is {usage_session_status}, not 'PAUSED'"

    # TEST - Resume a Remote usage session
    resume_usage_session_response = resume_usage_session(auth_token, device_id, usage_session_id)
    assert resume_usage_session_response.status_code == 200, f"{resume_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(auth_token, device_id, usage_session_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "ACTIVE", f"The current status is {usage_session_status}, not 'ACTIVE'"

    # TEST - Stop a Remote usage session
    stop_usage_session_response = stop_usage_session(auth_token, device_id, usage_session_id)
    assert stop_usage_session_response.status_code == 200, f"{stop_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(auth_token, device_id, usage_session_id)
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "DONE", f"The current status is {usage_session_status}, not 'DONE'"

    # TEST - Delete a Remote Usage session
    delete_usage_session_response = delete_usage_session(auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204, f"{delete_usage_session_response.text}"

    # stop simulation
    stop_simulation()
    simulation_status_response = get_simulation_status()
    simulation_status = simulation_status_response.json()["code"]
    assert simulation_status == "NO_RUNNING_SIMULATION"

    # TEST - Create an External Usage session
    create_usage_session_response = create_usage_session_without_name(auth_token, device_id, patient_id,
                                                                      usage_session_template_id)
    assert create_usage_session_response.status_code == 201, f"{create_usage_session_response.text}"
    usage_session_id = create_usage_session_response.json()["_id"]

    # TEST - Edit an External Usage session and Get an External Usage session by ID
    update_external_usage_session_response = update_usage_session(auth_token, device_id, usage_session_id)
    assert update_external_usage_session_response.status_code == 200, f"{update_external_usage_session_response.text}"
    get_usage_session_response = get_usage_session_by_id(auth_token, device_id, usage_session_id)
    assert get_usage_session_response.status_code == 200, f"{get_usage_session_response.text}"
    usage_session_status = get_usage_session_response.json()["_state"]
    assert usage_session_status == "PAUSING", f"The current status is {usage_session_status}, not 'PAUSING'"

    # TEST - Delete an External Usage session
    delete_usage_session_response = delete_usage_session(auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204, f"{delete_usage_session_response.text}"

    # as a Patient of custom organisation create usage External session with PHI=true attribute
    auth_token = login_with_credentials(patient_email, "Aa123456strong!@")
    create_usage_with_phi_response = create_usage_session_with_name(auth_token, device_id, patient_id,
                                                                    usage_session_template_id)
    assert create_usage_with_phi_response.status_code == 201, f"{create_usage_with_phi_response.text}"
    usage_session_id = create_usage_with_phi_response.json()["_id"]
    get_usage_session_response = get_usage_session_by_id(auth_token, device_id, usage_session_id)
    phi_attribute = get_usage_session_response.json()["_name"]
    usage_session = json.loads(get_usage_session_response.text)
    i = 0
    for key, value in usage_session.items():
        if value is not None and isinstance(value, str):
            if phi_attribute in value:
                i += 1
    assert i == 2, "PHI attribute is not visible for Patient"

    # TEST - Verify that phi=true attribute is not seen by Manu Admin
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    get_usage_session_response = get_usage_session_by_id(auth_token, device_id, usage_session_id)
    usage_session = json.loads(get_usage_session_response.text)
    i = 0
    for key, value in usage_session.items():
        if value is not None and isinstance(value, str):
            if phi_attribute in value:
                i += 1
    assert i == 0, "PHI attribute is visible for Manu Admin"

    # TEST - Search Usage sessions
    search_usage_sessions_response = get_usage_session_list(auth_token)
    assert search_usage_sessions_response.status_code == 200, f"{search_usage_sessions_response.text}"

    # TEST - Search Current Open Usage sessions
    search_current_usage_sessions_response = get_current_usage_sessions(auth_token)
    assert search_current_usage_sessions_response.status_code == 200, f"{search_current_usage_sessions_response.text}"

    # Delete an External Usage session
    delete_usage_session_response = delete_usage_session(auth_token, device_id, usage_session_id)
    assert delete_usage_session_response.status_code == 204, f"{delete_usage_session_response.text}"

    # Delete Device
    delete_device_response = delete_device(auth_token, device_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"

    # Delete Organisation
    delete_organisation_response = delete_organization(auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"{delete_organisation_response.text}"

    # Delete Device template
    delete_device_template_response = delete_template(auth_token, device_template_id)
    assert delete_device_template_response.status_code == 204, f"{delete_device_template_response.text}"


def test_manu_admin_generic_entity_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # create generic template without phi=true
    create_generic_template_no_phi_response = create_generic_template(auth_token)
    assert create_generic_template_no_phi_response.status_code == 201, f"{create_generic_template_no_phi_response.text}"
    generic_template_no_phi_id = create_generic_template_no_phi_response.json()["id"]

    # create generic template with phi=true
    create_generic_template_with_phi_response = create_generic_template_with_phi_true(auth_token)
    assert create_generic_template_with_phi_response.status_code == 201, \
        f"{create_generic_template_with_phi_response.text}"
    generic_template_with_phi_id = create_generic_template_with_phi_response.json()["id"]

    # TEST - Create Generic Entity without phi=true
    generic_name_no_phi = f"Generic_Entity_No_PHI{uuid.uuid4().hex}"[0:32]
    create_generic_entity_response = create_generic_entity(auth_token, generic_template_no_phi_id, generic_name_no_phi,
                                                           DEFAULT_ORGANISATION_ID)
    assert create_generic_entity_response.status_code == 201, f"{create_generic_template_no_phi_response.text}"
    generic_entity_id = create_generic_entity_response.json()["_id"]

    # TEST - Update Generic Entity
    update_generic_entity_response = update_generic_entity(auth_token, generic_entity_id, "generic_name_updated")
    assert update_generic_entity_response.status_code == 200, f"{update_generic_entity_response.text}"
    assert update_generic_entity_response.json()["_name"] == "generic_name_updated"

    # TEST - Get Generic Entity by ID
    get_generic_entity_response = get_generic_entity(auth_token, generic_entity_id)
    assert get_generic_entity_response.status_code == 200, f"{get_generic_entity_response.text}"

    # TEST - Search Generic Entities
    search_generic_entities_list_response = get_generic_entity_list(auth_token)
    assert search_generic_entities_list_response.status_code == 200, f"{search_generic_entities_list_response.text}"

    # TEST - Delete Generic Entity
    delete_generic_entity_response = delete_generic_entity(auth_token, generic_entity_id)
    assert delete_generic_entity_response.status_code == 204, f"{delete_generic_entity_response.text}"

    # TEST - Create Generic Entity with phi=true - access denied
    generic_name_phi = f"Generic_Entity_PHI{uuid.uuid4().hex}"[0:32]
    create_generic_entity_response = create_generic_entity(auth_token, generic_template_with_phi_id, generic_name_phi,
                                                           DEFAULT_ORGANISATION_ID)
    assert create_generic_entity_response.status_code == 403, f"{create_generic_template_no_phi_response.text}"

    # TEST - Delete Generic Entity template
    delete_generic_template_no_phi_response = delete_template(auth_token, generic_template_no_phi_id)
    assert delete_generic_template_no_phi_response.status_code == 204, f"{delete_generic_template_no_phi_response.text}"
    delete_generic_template_with_phi = delete_template(auth_token, generic_template_with_phi_id)
    assert delete_generic_template_with_phi.status_code == 204, f"{delete_generic_template_with_phi.text}"


def test_manu_admin_registration_code_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # create Registration Code template
    create_registration_code_template_response = create_registration_code_template(auth_token)
    assert create_registration_code_template_response.status_code == 201, \
        f"{create_registration_code_template_response.text}"
    registration_code_template_id = create_registration_code_template_response.json()["id"]
    registration_code_template_name = create_registration_code_template_response.json()["name"]

    # TEST - Create Registration Code
    registration_code = f"RC_{uuid.uuid4().hex}"[0:32]
    create_registration_code_response = create_registration_code(auth_token, registration_code_template_name,
                                                                 registration_code, DEFAULT_ORGANISATION_ID)
    assert create_registration_code_response.status_code == 201, f"{create_registration_code_response.text}"
    registration_code_id = create_registration_code_response.json()["_id"]

    # TEST - Update Registration Code
    changed_code = f"RC_updated_{uuid.uuid4().hex}"[0:32]
    update_registration_code_response = update_registration_code(auth_token, registration_code_id, changed_code)
    assert update_registration_code_response.status_code == 200, f"{update_registration_code_response.text}"
    assert update_registration_code_response.json()["_code"] == changed_code

    # TEST - Delete Registration Code
    delete_registration_code_response = delete_registration_code(auth_token, registration_code_id)
    assert delete_registration_code_response.status_code == 204, f"{delete_registration_code_response.text}"

    # delete Registration Code Template
    delete_registration_code_response = delete_template(auth_token, registration_code_template_id)
    assert delete_registration_code_response.status_code == 204, f"{delete_registration_code_response.text}"


def test_manu_admin_command_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # create device template
    device_template_response = create_device_template_with_session(auth_token)
    assert device_template_response.status_code == 201, f"{device_template_response.text}"
    template_name = device_template_response.json()["name"]
    device_template_id = device_template_response.json()["id"]

    # create command template
    command_template_name = f'cmd_support_stop_{uuid.uuid4().hex}'[0:32]
    create_command_template_response = create_command_template_with_support_stop_true(auth_token, command_template_name,                                                                                 device_template_id)
    assert create_command_template_response.status_code == 201, f"{create_command_template_response.text}"
    command_template_id = create_command_template_response.json()['id']

    # create device in Default Org-n
    create_device_response = create_device_without_registration_code(auth_token, template_name, DEFAULT_ORGANISATION_ID)
    device_id = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # start simulation
    start_simulation_with_existing_device(device_id, os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # TEST - Start Command in Default Org-n
    start_command_response = start_command_by_id(auth_token, device_id, command_template_id)
    assert start_command_response.status_code == 201, f"{start_command_response.text}"
    command_id = start_command_response.json()['_id']
    get_command_response = get_command(auth_token, device_id, command_id)
    command_state = get_command_response.json()['_state']
    assert command_state == "IN_PROGRESS"

    # TEST - Stop Command in Default Org-n
    stop_command_response = stop_command(auth_token, device_id, command_id)
    assert stop_command_response.status_code == 200, f"{start_command_response.text}"
    get_command_response = get_command(auth_token, device_id, command_id)
    command_state = get_command_response.json()['_state']
    assert command_state == "ABORTED"

    # TEST - Start another Command in Default Org-n and wait till it's Completed
    start_command_response = start_command_by_id(auth_token, device_id, command_template_id)
    assert start_command_response.status_code == 201, f"{start_command_response.text}"
    command2_id = start_command_response.json()['_id']
    get_command_response = get_command(auth_token, device_id, command2_id)
    command2_state = get_command_response.json()['_state']
    assert command2_state == "IN_PROGRESS"
    time.sleep(10)
    get_command_response = get_command(auth_token, device_id, command2_id)
    command2_state = get_command_response.json()['_state']
    assert command2_state == "COMPLETED"

    # stop simulation
    stop_simulation()
    simulation_status_response = get_simulation_status()
    simulation_status = simulation_status_response.json()["code"]
    assert simulation_status == "NO_RUNNING_SIMULATION"

    # Delete Device
    delete_device_response = delete_device(auth_token, device_id)
    assert delete_device_response.status_code == 204, f"{delete_device_response.text}"

    # Delete Device template
    delete_device_template_response = delete_template(auth_token, device_template_id)
    assert delete_device_template_response.status_code == 204, f"{delete_device_template_response.text}"


def test_manu_admin_device_alerts_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # Create Device template
    device_template_response = create_device_template_with_session(auth_token)
    assert device_template_response.status_code == 201, f"{device_template_response.text}"
    device_template_name = device_template_response.json()["name"]
    device_template_id = device_template_response.json()["id"]

    # Create Device Alert template
    name = f'alert_templ{uuid.uuid4().hex}'[0:32]
    create_device_alert_template_response = create_device_alert_template(auth_token, device_template_id, name)
    assert create_device_alert_template_response.status_code == 201, f'{create_device_alert_template_response.text}'
    device_alert_template_id = create_device_alert_template_response.json()["id"]

    # Create a Custom Organisation
    create_organization_response = create_organization(auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # Create Device in Custom organisation
    create_device_response = create_device_without_registration_code(auth_token, device_template_name, organization_id)
    device_id = create_device_response.json()["_id"]
    assert create_device_response.status_code == 201, f"{create_device_response.text}"

    # TEST - Create Device Alert by ID in Custom organisation
    create_device_alert_response = create_device_alert_by_id(auth_token, device_id, device_alert_template_id)
    assert create_device_alert_response.status_code == 201, f'{create_device_alert_response.text}'
    device_alert_id = create_device_alert_response.json()["_id"]

    # TEST - Update Device Alert created by ID in Custom organisation
    update_device_alert_response = update_device_alert(auth_token, device_id, device_alert_id)
    assert update_device_alert_response.status_code == 200, f'{update_device_alert_response.text}'

    # TEST - Get By ID Device Alert created by ID in Custom organisation
    get_device_alert_by_id_response = get_device_alert(auth_token, device_id, device_alert_id)
    assert get_device_alert_by_id_response.status_code == 200, f'{get_device_alert_by_id_response.text}'

    # TEST - Search Device Alerts
    search_device_alerts_response = get_device_alert_list(auth_token, device_alert_id)
    assert search_device_alerts_response.status_code == 200, f'{search_device_alerts_response.text}'

    # TEST - Get current Alerts
    get_current_alerts_response = get_current_device_alert_list(auth_token, organization_id)
    assert get_current_alerts_response.status_code == 200, f"{get_current_alerts_response.text}"

    # TEST - Delete Alert created by ID in Custom organisation
    delete_device_alert_response = delete_device_alert(auth_token, device_id, device_alert_id)
    assert delete_device_alert_response.status_code == 204, f"{delete_device_alert_response.text}"

    # Delete Device
    delete_device_response = delete_device(auth_token, device_id)
    assert delete_device_response.status_code == 204, f"{delete_device_alert_response.text}"

    # Delete Organisation
    delete_organisation_response = delete_organization(auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"{delete_organisation_response.text}"

    # Delete Device template
    delete_device_template_response = delete_template(auth_token, device_template_id)
    assert delete_device_template_response.status_code == 204, f"{delete_device_template_response.text}"


def test_manu_admin_patient_alert_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # create a Custom Organisation
    create_organization_response = create_organization(auth_token, ORGANISATION_TEMPLATE_ID)
    assert create_organization_response.status_code == 201, f"Status code {create_organization_response.status_code} " \
                                                            f"{create_organization_response.text}"
    organization_id = create_organization_response.json()['_id']

    # accept invitation as an admin of custom Org-n
    get_organisation_response = get_organization(auth_token, organization_id)
    primary_admin_id = get_organisation_response.json()["_primaryAdministrator"]["id"]
    get_organisation_user_response = get_organization_user(auth_token, primary_admin_id)
    primary_admin_email = get_organisation_user_response.json()["_email"]
    accept_invitation(primary_admin_email)
    auth_token = login_with_credentials(primary_admin_email, "Aa123456strong!@")
    get_self_user_email_response = get_self_user_email(auth_token)
    assert get_self_user_email_response == primary_admin_email, \
        f"Actual email '{get_self_user_email_response}' does not match the expected"

    # create Patient in custom Org-n
    auth_token = login_with_credentials(primary_admin_email, "Aa123456strong!@")
    patient_email = f'patient_alert{uuid.uuid4().hex}'[0:32] + '@biotmail.com'
    name = {"firstName": f'Patient',
            "lastName": f'Usage'}
    create_patient_default_response = create_patient(auth_token, name, patient_email, PATIENT_TEMPLATE_NAME,
                                                     organization_id)
    assert create_patient_default_response.status_code == 201, f"{create_patient_default_response.text}"
    patient_id = create_patient_default_response.json()["_id"]

    # create a Patient Alert Template
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))
    name = f'alert_templ{uuid.uuid4().hex}'[0:32]
    create_patient_alert_template_response = create_patient_alert_template(auth_token, PATIENT_TEMPLATE_ID, name)
    assert create_patient_alert_template_response.status_code == 201, f'{create_patient_alert_template_response.text}'
    patient_alert_template_name = create_patient_alert_template_response.json()["name"]
    patient_alert_template_id = create_patient_alert_template_response.json()["id"]

    # TEST - Create Patient Alert by Name in Custom Organisation
    create_patient_alert_response = create_patient_alert_by_name(auth_token, patient_id, patient_alert_template_name)
    assert create_patient_alert_response.status_code == 201, f'{create_patient_alert_response.text}'
    patient_alert_id = create_patient_alert_response.json()["_id"]

    # TEST - Update Patient Alert created by Name in Custom Organisation
    update_patient_alert_response = update_patient_alert(auth_token, patient_id, patient_alert_id)
    assert update_patient_alert_response.status_code == 200, f'{update_patient_alert_response.text}'

    # TEST - Get By ID Patient Alert created by ID in Custom organisation
    get_patient_alert_by_id_response = get_patient_alert(auth_token, patient_id, patient_alert_id)
    assert get_patient_alert_by_id_response.status_code == 200, f'{get_patient_alert_by_id_response.text}'

    # TEST - Search Patient Alerts
    search_patient_alerts_response = get_patient_alert_list(auth_token, organization_id)
    assert search_patient_alerts_response.status_code == 200, f'{search_patient_alerts_response.text}'

    # TEST - Get current Alerts
    get_current_alerts_response = get_current_patient_alert_list(auth_token, organization_id)
    assert get_current_alerts_response.status_code == 200, f"{get_current_alerts_response.text}"

    # TEST - Delete Patient Alert created by Name in Custom organisation
    delete_patient_alert_response = delete_patient_alert(auth_token, patient_id, patient_alert_id)
    assert delete_patient_alert_response.status_code == 204, f"{delete_patient_alert_response.text}"

    # delete Organisation
    delete_organisation_response = delete_organization(auth_token, organization_id)
    assert delete_organisation_response.status_code == 204, f"{delete_organisation_response.text}"

    # delete Patient Alert template
    delete_patient_alert_template_response = delete_template(auth_token, patient_alert_template_id)
    assert delete_patient_alert_template_response.status_code == 204, f"{ delete_patient_alert_template_response.text}"


def test_manu_admin_locales_abac_rules():
    auth_token = login_with_credentials(os.getenv('MANU_ADMIN_LOGIN'), os.getenv('MANU_ADMIN_PASSWORD'))

    # TEST - Get available Locales
    get_locales_response = get_available_locales(auth_token)
    assert get_locales_response.status_code == 200, f'{get_locales_response.text}'
    available_locales = get_locales_response.json()['availableLocales']
    codes = [locale['code'] for locale in available_locales]
    locale_to_update = None
    for code in codes:
        if code != "en-us":
            locale_to_update = code
            break

    # TEST - Delete Locale
    delete_locale_response = delete_locale(auth_token, locale_to_update)
    assert delete_locale_response.status_code == 200, f"{delete_locale_response.text}"
    get_locales_response = get_available_locales(auth_token)
    available_locales = get_locales_response.json()['availableLocales']
    codes = [locale['code'] for locale in available_locales]
    for code in codes:
        if locale_to_update == code:
            raise ValueError(f"The code {locale_to_update} is present though is supposed to be deleted.")

    # TEST - Add Locale
    add_locale_response = add_locale(auth_token, locale_to_update)
    assert add_locale_response.status_code == 200, f"{add_locale_response.text}"
    get_locales_response = get_available_locales(auth_token)
    available_locales = get_locales_response.json()['availableLocales']
    codes = [locale['code'] for locale in available_locales]
    i = 0
    for code in codes:
        if locale_to_update == code:
            i = i + 1
    assert i == 1, f"The code {locale_to_update} is absent though is supposed to be added."

    # TEST - Update default Locale to es-es and back to en-us
    update_default_locale_response = update_locale(auth_token, locale_to_update)
    assert update_default_locale_response.status_code == 200, f"{update_default_locale_response.text}"
    get_locales_response = get_available_locales(auth_token)
    default_locale = get_locales_response.json()['defaultLocaleCode']
    assert default_locale == locale_to_update
    update_default_locale_response = update_locale(auth_token, 'en-us')
    assert update_default_locale_response.status_code == 200, f"{update_default_locale_response.text}"
    get_locales_response = get_available_locales(auth_token)
    default_locale = get_locales_response.json()['defaultLocaleCode']
    assert default_locale == 'en-us'
