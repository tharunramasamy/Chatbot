import requests
import os
import json

# Replace with your actual refresh token, client_id, and client_secret
client_id = os.getenv("ZOHO_CLIENT_ID")
client_secret = os.getenv("ZOHO_CLIENT_SECRET")
refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")

# Function to refresh the access token using the refresh token
def refresh_access_token():
    url = 'https://accounts.zoho.com/oauth/v2/token'
    payload = {
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f'Error refreshing access token: {response.status_code} - {response.text}')
        return None

# Function to fetch only note content and creation date, sorted from oldest to newest
def fetch_filtered_notes():
    access_token = refresh_access_token()
    if not access_token:
        print('Failed to get access token')
        return

    headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}
    all_notes = []
    page = 1
    per_page = 200  # Max allowed by Zoho

    while True:
        url = 'https://www.zohoapis.com/crm/v2/Notes'
        params = {
            'fields': 'Note_Content,Created_Time',
            'sort_by': 'Created_Time',
            'sort_order': 'asc',
            'page': page,
            'per_page': per_page
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            notes = data.get('data', [])
            if not notes:
                break
            # Filter only required fields
            filtered_notes = [{
                "content": note.get("Note_Content"),
                "created_date": note.get("Created_Time")
            } for note in notes]
            all_notes.extend(filtered_notes)
            info = data.get('info', {})
            if info.get('more_records'):
                page += 1
            else:
                break
        elif response.status_code == 401:
            print('Access token expired, refreshing...')
            access_token = refresh_access_token()
            if not access_token:
                print('Failed to refresh access token.')
                break
            headers['Authorization'] = f'Zoho-oauthtoken {access_token}'
        else:
            print(f'Error fetching notes: {response.status_code} - {response.text}')
            break

    # Print the filtered notes as JSON
    print(json.dumps(all_notes, indent=2, ensure_ascii=False))

# Call the function
fetch_filtered_notes()
