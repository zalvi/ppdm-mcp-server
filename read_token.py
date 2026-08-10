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


def get_backup_jobs_summary(host,username, password):
    token = read_token(host, username, password)
    jobs_list = jobs(host, token)
    jobs_ok = []
    jobs_failed = []
    jobs_unknown = []
    for job in jobs_list:
        if job["result"]["status"] == "OK":
            jobs_ok.append(job)
        elif job["result"]["status"] == "FAILED":
            jobs_failed.append(job)
        else:
            jobs_unknown.append(job)
    return {
            "total_jobs": len(jobs_list),
            "jobs_ok": len(jobs_ok),
            "jobs_failed": len(jobs_failed),
            "jobs_unknown": len(jobs_unknown)   
        }

if __name__ == "__main__":
    result = get_backup_jobs_summary("localhost:5000", "admin", "test")
    print(json.dumps(result))
