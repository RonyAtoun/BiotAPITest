import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, parse_qs, urlparse
import time

ENDPOINT = os.getenv('ENDPOINT')
slack_token = os.getenv('SLACK_TOKEN')
MAX_RETRIES = 20


def accept_invitation(user_email):
    channel_id = "C04M7N12T7G"
    url = f"https://slack.com/api/conversations.history"
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
            messages = data.get("messages", [])[0:100]
            for message in messages:
                if "files" in message and isinstance(message["files"], list) and message["files"]:
                    email_topic = message["files"][0].get("title", "")
                else:
                    email_topic = ""
                if email_topic == "Welcome to BioT":
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
                        signup_url = ENDPOINT + f"/organization/v1/tokens/{token}?entityId={entity_id}" \
                                                f"&operation=accept-invitation"
                        headers = {'Content-Type': 'application/json'}
                        payload = f"{{\"operationData\":{{\"password\":\"Aa123456strong!@\",\"username\":\"{user_email}\"}}}}"
                        response = requests.request("POST", signup_url, headers=headers, data=payload)
                        assert response.status_code == 200, f"Error: {response.status_code}, {response.text}"
                        return response.text, response
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")
    else:
        raise Exception(f"Error: Number of {MAX_RETRIES} attempts to retrieve email has been used. No email found.")


def reset_password_open_email_and_set_new_password(user_email, new_password):
    channel_id = "C04M7N12T7G"
    url = f"https://slack.com/api/conversations.history"
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
            messages = data.get("messages", [])[0:100]
            for message in messages:
                if "files" in message and isinstance(message["files"], list) and message["files"]:
                    email_topic = message["files"][0].get("title", "")
                else:
                    email_topic = ""
                if email_topic == "Reset your password":
                    user_email_in_letter = (((message.get("files")[0])["to"])[0])["address"]
                    if user_email_in_letter == user_email and email_topic == "Reset your password":
                        html_content = (message.get("files")[0])["preview"]
                        soup = BeautifulSoup(html_content, 'html.parser')
                        href = soup.a['href']
                        decoded_url = unquote(href)
                        parsed_url = urlparse(decoded_url)
                        query_params = parse_qs(parsed_url.query)
                        token = query_params.get('token', [''])[0]
                        entity_id = query_params.get('entityId', [''])[0]
                        reset_password_url = ENDPOINT + f"/ums/v1/tokens/{token}?entityId={entity_id}&" \
                                                        f"operation=forgotPasswordOperation"
                        headers = {'Content-Type': 'application/json'}
                        payload = f"{{\"operationData\":{{\"password\":\"{new_password}\"}}}}"
                        response = requests.request("POST", reset_password_url, headers=headers, data=payload)
                        assert response.status_code == 200, f"Error: {response.status_code}, {response.text}"
                        return response
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")
    else:
        raise Exception(f"Error: Number of {MAX_RETRIES} attempts to retrieve email has been used. No email found.")
