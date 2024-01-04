import os

import pytest
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, parse_qs, urlparse

MAX_RETRIES = 3

slack_token = os.getenv('SLACK')
channel_id = "C04M7N12T7G"
url = f"https://slack.com/api/conversations.history"


@pytest.fixture()
def get_user_token_and_id():
    user_email = "reginay+1228@biotmail.com"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json"
    }
    params = {
        "channel": channel_id
    }
    for attempt in range(MAX_RETRIES):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])[0:5]
            for message in messages:
                user_email_in_letter = (((message.get("files")[0])["to"])[0])["address"]
                if user_email_in_letter == user_email:
                    html_content = (message.get("files")[0])["preview"]
                    soup = BeautifulSoup(html_content, 'html.parser')
                    href = soup.a['href']
                    decoded_url = unquote(href)
                    parsed_url = urlparse(decoded_url)
                    query_params = parse_qs(parsed_url.query)
                    token = query_params.get('token', [''])[0]
                    entity_id = query_params.get('entityId', [''])[0]
                    print(f"This is token {token} for entity id {entity_id}")
                    return token, entity_id, user_email
        else:
            print(f"Error: {response.status_code}, {response.text}")
    else:
        print("Number of attempts to retrieve email has been used. No email found.")


def test_accept_invitation(get_user_token_and_id):
    token, entity_id, user_email = get_user_token_and_id
    signup_url = f"https://api.qa.biot-gen2.biot-med.com/organization/v1/tokens/{token}?entityId={entity_id}" \
                 f"&operation=accept-invitation"
    headers = {'Content-Type': 'application/json'}
    payload = f"{{\"operationData\":{{\"password\":\"Aa123456\",\"username\":\"{user_email}\"}}}}"
    response = requests.request("POST", signup_url, headers=headers, data=payload)
    assert response.status_code == 200, f"Error: {response.status_code}, {response.text}"
    print(response.text)
