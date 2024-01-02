import uuid
import os
from helpers import (login_with_with_credentials, create_organization_template, delete_template, create_generic_entity,
                     delete_generic_entity)

user_name = os.getenv('USERNAME')  # Has to be set in the environment in advance
pass_word = os.getenv('PASSWORD')
auth_token = login_with_with_credentials(user_name, pass_word)


def test_create_template():
    test_display_name = f'test_templ_{uuid.uuid4().hex}'[0:35]
    test_name = f'rony_test_{uuid.uuid4().hex}'[0:35]
    test_referenced_attrib_name = f'my built in attribute_{uuid.uuid4().hex}'[0:35]
    test_reference_attrib_display_name = test_referenced_attrib_name
    create_template_response = create_organization_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                                               test_reference_attrib_display_name, "00000000-0000-0000-0000-000000000000")
    if "TEMPLATE_DUPLICATE_NAME" in str(
            create_template_response.content):  # delete previously created template with same name
        tmp = str(create_template_response.content)
        template_id = tmp.split('[')[2].split(']')[0]
        delete_template_response = delete_template(auth_token, template_id)
        assert delete_template_response.status_code == 204
        create_template_response = create_organization_template(auth_token, test_display_name, test_name,
                                                   test_referenced_attrib_name,
                                                   test_reference_attrib_display_name, "00000000-0000-0000-0000-000000000000")

    assert create_template_response.status_code == 201
    data = create_template_response.json()
    assert data["name"] == test_name
    template_id = data["id"]
    delete_template_response = delete_template(auth_token, template_id)
    assert delete_template_response.status_code == 204


def test_create_generic_entity():  # redo create_template to make this test independent
    test_display_name = f'test_templ_{uuid.uuid4().hex}'[0:35]
    test_name = f'rony_test_{uuid.uuid4().hex}'[0:31]
    test_referenced_attrib_name = f'my built in attribute_{uuid.uuid4().hex}'[0:35]
    test_reference_attrib_display_name = test_referenced_attrib_name
    create_template_response = create_organization_template(auth_token, test_display_name, test_name, test_referenced_attrib_name,
                                               test_reference_attrib_display_name, "00000000-0000-0000-0000-000000000000")
    if "TEMPLATE_DUPLICATE_NAME" in str(
            create_template_response.content):  # delete previously created template with same name
        tmp = str(create_template_response.content)
        template_id = tmp.split('[')[2].split(']')[0]
        delete_template_response = delete_template(auth_token, template_id)
        assert delete_template_response.status_code == 204
        create_template_response = create_organization_template(auth_token, test_display_name, test_name,
                                                   test_referenced_attrib_name,
                                                   test_reference_attrib_display_name, "00000000-0000-0000-0000-000000000000")

    assert create_template_response.status_code == 201
    data = create_template_response.json()
    assert data["name"] == test_name
    template_id = data["id"]
    create_generic_entity_response = create_generic_entity(auth_token, template_id, test_name,
                                                           "00000000-0000-0000-0000-000000000000")
    assert create_generic_entity_response.status_code == 201
    assert create_generic_entity_response.json()["_name"] == test_name
    # teardown
    entity_id = create_generic_entity_response.json()["_id"]
    delete_generic_entity_response = delete_generic_entity(auth_token, entity_id)
    assert delete_generic_entity_response.status_code == 204
    delete_template_response = delete_template(auth_token, template_id)
    assert delete_template_response.status_code == 204

