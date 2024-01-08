import os
from API_drivers import (login_with_with_credentials, get_entities)


def get_all_entity_types():
    auth_token = login_with_with_credentials(os.getenv('USERNAME'), os.getenv('PASSWORD'))

    get_entities_response = get_entities(auth_token)
    assert get_entities_response.status_code == 200
    data = get_entities_response.json()['data']
    for item in data:
        print(item['name'])



if __name__ == "__main__":
    get_all_entity_types()
