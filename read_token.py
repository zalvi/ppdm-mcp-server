import requests
import json
import os
import logging

logging.basicConfig(level=logging.INFO)

def read_token(host,username, password):
    url = f"http://{host}/api/v2/login"
    payload = json.dumps({
        "username": username,
        "password": password
    })
    headers = {
        'Content-Type': 'application/json'  
    }
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
      return response.json().get("access_token")
    elif response.status_code == 401:
        logging.error("Unauthorized: Check your username and password.")
        raise PermissionError(f"Unauthorized access: {response.status_code} {response.text}")
    else:
        logging.error(f"Failed to read token: {response.status_code} - {response.text}")
        raise Exception(f"Failed to read token: {response.status_code} {response.text}")


def jobs(host,token):
    url = f"http://{host}/api/v2/activities"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    if token is None:
        logging.error("Token is None. Cannot fetch jobs.")
        raise ValueError("Token is None. Cannot fetch jobs.")
    else:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["content"]
        elif response.status_code == 401:
            logging.error("Unauthorized: Check your token.")
            raise PermissionError(f"Unauthorized access: {response.status_code} {response.text}")
        else:
            logging.error(f"Failed to fetch jobs: {response.status_code} - {response.text}")
            raise Exception(f"Failed to fetch jobs: {response.status_code} {response.text}")
        
if __name__ == "__main__":
    token = read_token("localhost:5000", "admin", "test")
    jobs_list = jobs("localhost:5000", token)
    print(f"Got {len(jobs_list)} jobs.")
    print(jobs_list[0])  # Print the first job for verification