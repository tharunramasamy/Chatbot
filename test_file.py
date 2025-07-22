import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Constants from .env
client_id = os.getenv("ZOHO_CLIENT_ID")
client_secret = os.getenv("ZOHO_CLIENT_SECRET")
refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
access_token = os.getenv("ZOHO_ACCESS_TOKEN")
BASE_URL = "https://www.zohoapis.com/crm/v2"

# Zoho domain based on region
AUTH_URL = "https://accounts.zoho.com/oauth/v2/token"

# Step 1: Get Access Token
def get_access_token():
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }
    response = requests.post(AUTH_URL, params=params)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception("Failed to get access token", response.text)

# Step 2: Fetch Deals and Save to File
def get_deals(access_token, output_file="zoho_deals.txt"):
    crm_url = f"https://www.zohoapis.com/crm/v2/Deals"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    response = requests.get(crm_url, headers=headers)

    if response.status_code == 200:
        deals = response.json().get("data", [])
        with open(output_file, "w", encoding="utf-8") as f:
            for deal in deals:
                f.write("-" * 60 + "\n")
                for key, value in deal.items():
                    f.write(f"{key}: {value}\n")
        print(f"Deals written to '{output_file}'")
    else:
        raise Exception("Failed to fetch deals", response.text)

# Main flow
if __name__ == "__main__":
    token = get_access_token()
    get_deals(token)
