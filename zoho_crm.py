import requests
import os
import logging
from dotenv import load_dotenv
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
client_id = os.getenv("ZOHO_CLIENT_ID")
client_secret = os.getenv("ZOHO_CLIENT_SECRET")
refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
access_token = os.getenv("ZOHO_ACCESS_TOKEN")
BASE_URL = "https://www.zohoapis.com/crm/v2"

def validate_config():
    missing = []
    for k,v in {"ZOHO_CLIENT_ID":client_id,"ZOHO_CLIENT_SECRET":client_secret,"ZOHO_REFRESH_TOKEN":refresh_token}.items():
        if not v: missing.append(k)
    if missing:
        logger.error(f"Missing Zoho configuration: {', '.join(missing)}")
        return False
    return True

def refresh_access_token():
    global access_token
    if not validate_config():
        return False
    try:
        url = "https://accounts.zoho.com/oauth/v2/token"
        params = {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token"
        }
        response = requests.post(url, params=params, timeout=30)
        logger.info(f"Token refresh response status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                os.environ["ZOHO_ACCESS_TOKEN"] = access_token
                logger.info("Access token refreshed successfully")
                return True
            logger.error("No access token in response")
            return False
        logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during token refresh: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        return False

def get_headers():
    global access_token
    if not access_token:
        logger.info("No access token, attempting to refresh")
        if not refresh_access_token():
            return None
    return {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

def make_api_request(url, max_retries=2):
    for attempt in range(max_retries + 1):
        headers = get_headers()
        if not headers:
            return {"Error": "Unable to get valid headers for API request"}
        try:
            logger.info(f"Making API request to: {url} (attempt {attempt + 1})")
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401 and attempt < max_retries:
                logger.warning("Received 401, refreshing token and retrying")
                if refresh_access_token(): continue
                return {"Error": "Unable to refresh access token"}
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"Error": error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during API request: {e}"
            logger.error(error_msg)
            if attempt == max_retries: return {"Error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during API request: {e}"
            logger.error(error_msg)
            return {"Error": error_msg}
    return {"Error": "Max retries exceeded"}

def _extract_name(field_data):
    if isinstance(field_data, dict): return field_data.get("name", "Unknown")
    if isinstance(field_data, str): return field_data
    return None

def _extract_tags(record):
    # Check for several possible fields ("Tag", "Tags", etc.)
    for field in ["Tag", "Tags"]:
        tags = record.get(field)
        if isinstance(tags, list):
            return [t.get("name", str(t)) for t in tags]
        elif isinstance(tags, str):
            return [tags]
    return []

def fetch_all_records(module, per_page=200):
    all_records_dict = {}  # Use dict for deduplication
    page = 1
    while True:
        url = f"{BASE_URL}/{module}?per_page={per_page}&page={page}"
        res = make_api_request(url)
        if "Error" in res:
            logger.error(f"Error fetching {module}: {res['Error']}")
            break
        data = res.get("data", [])
        for record in data:
            rid = record.get("id")
            if rid: all_records_dict[rid] = record  # deduplicate by Zoho's unique id
        more = res.get("info", {}).get("more_records", False)
        if not more: break
        page += 1
    return list(all_records_dict.values())

def get_deals():
    deals = fetch_all_records("Deals")
    filtered_deals = defaultdict(list)
    for deal in deals:
        deal_data = {
            "Deal ID": deal.get("id"),
            "Deal Name": deal.get("Deal_Name", "Unnamed Deal"),
            "Account Name": _extract_name(deal.get("Account_Name")),
            "Deal Owner": _extract_name(deal.get("Owner")),
            "Stage": deal.get("Stage", "Unknown"),
            "Amount": deal.get("Amount"),
            "Closing Date": deal.get("Closing_Date"),
            "Service Line": deal.get("Service_Line"),
            "Accelerators/Personalized Service": deal.get("Accelerators_or_Personalized_Service"),
            "Tags": _extract_tags(deal),
            "Created Time": deal.get("Created_Time"),
            "Modified Time": deal.get("Modified_Time")
        }
        owner = deal_data["Deal Owner"] or "Unknown Owner"
        filtered_deals[owner].append(deal_data)
    logger.info(f"Successfully processed {sum(len(v) for v in filtered_deals.values())} deals")
    return dict(filtered_deals)

def get_leads():
    leads = fetch_all_records("Leads")
    filtered_leads = defaultdict(list)
    for lead in leads:
        lead_data = {
            "Lead ID": lead.get("id"),
            "Lead Name": lead.get("Full_Name", "Unnamed Lead"),
            "Company": lead.get("Company", "No Company"),
            "Lead Owner": _extract_name(lead.get("Owner")),
            "Email": lead.get("Email", "No Email"),
            "Phone": lead.get("Phone", "No Phone"),
            "Lead Status": lead.get("Lead_Status", "Unknown"),
            "Lead Source": lead.get("Lead_Source", "Unknown"),
            "Tags": _extract_tags(lead),
            "Created Time": lead.get("Created_Time"),
            "Modified Time": lead.get("Modified_Time")
        }
        owner = lead_data["Lead Owner"] or "Unknown Owner"
        filtered_leads[owner].append(lead_data)
    logger.info(f"Successfully processed {sum(len(v) for v in filtered_leads.values())} leads")
    return dict(filtered_leads)

def get_tasks():
    tasks = fetch_all_records("Tasks")
    filtered_tasks = defaultdict(list)
    for task in tasks:
        task_data = {
            "Task ID": task.get("id"),
            "Task Subject": task.get("Subject", "Unnamed Task"),
            "Task Owner": _extract_name(task.get("Owner")),
            "Status": task.get("Status", "Not Started"),
            "Priority": task.get("Priority", "Normal"),
            "Due Date": task.get("Due_Date"),
            "Related To": _extract_name(task.get("What_Id")),
            "Start Date": task.get("Start_Date"),
            "Description": task.get("Description", "No Description"),
            "Created Time": task.get("Created_Time"),
            "Modified Time": task.get("Modified_Time")
        }
        owner = task_data["Task Owner"] or "Unknown Owner"
        filtered_tasks[owner].append(task_data)
    logger.info(f"Successfully processed {sum(len(v) for v in filtered_tasks.values())} tasks")
    return dict(filtered_tasks)

def get_notes():
    notes = fetch_all_records("Notes")
    filtered_notes = defaultdict(list)
    for note in notes:
        note_data = {
            "Note ID": note.get("id"),
            "Note Title": note.get("Note_Title", "Untitled Note"),
            "Note Content": note.get("Note_Content", "No Content"),
            "Note Owner": _extract_name(note.get("Owner")),
            "Created By": _extract_name(note.get("Created_By")),
            "Modified By": _extract_name(note.get("Modified_By")),
            "Parent Module": note.get("Parent_Id", {}).get("module", "Unknown"),
            "Parent Record": _extract_name(note.get("Parent_Id")),
            "Created Time": note.get("Created_Time"),
            "Modified Time": note.get("Modified_Time")
        }
        owner = note_data["Note Owner"] or "Unknown Owner"
        filtered_notes[owner].append(note_data)
    logger.info(f"Successfully processed {sum(len(v) for v in filtered_notes.values())} notes")
    return dict(filtered_notes)

def filter_data_by_owner(data, owner_name):
    if owner_name == "All" or not owner_name:
        return data
    if isinstance(data, dict):
        return data.get(owner_name, [])
    return []

def get_crm_summary(owner_name="All"):
    leads_data = get_leads()
    deals_data = get_deals()
    tasks_data = get_tasks()
    notes_data = get_notes()
    # Flatten or filter
    if owner_name != "All":
        leads = filter_data_by_owner(leads_data, owner_name)
        deals = filter_data_by_owner(deals_data, owner_name)
        tasks = filter_data_by_owner(tasks_data, owner_name)
        notes = filter_data_by_owner(notes_data, owner_name)
    else:
        leads, deals, tasks, notes = [], [], [], []
        for owner_leads in leads_data.values():
            if isinstance(owner_leads, list): leads.extend(owner_leads)
        for owner_deals in deals_data.values():
            if isinstance(owner_deals, list): deals.extend(owner_deals)
        for owner_tasks in tasks_data.values():
            if isinstance(owner_tasks, list): tasks.extend(owner_tasks)
        for owner_notes in notes_data.values():
            if isinstance(owner_notes, list): notes.extend(owner_notes)
    closed_deal_stages = {"closed won", "closedwon", "closed_won"}
    closed_deals = [deal for deal in deals if deal.get('Stage', '').replace(" ", "").lower() in closed_deal_stages]
    total_deal_value = sum(deal.get('Amount', 0) for deal in deals if deal.get('Amount'))
    closed_deal_value = sum(deal.get('Amount', 0) for deal in closed_deals if deal.get('Amount'))
    return {
        "leads": leads,
        "deals": deals,
        "tasks": tasks,
        "notes": notes,
        "summary": {
            "total_leads": len(leads),
            "total_deals": len(deals),
            "total_tasks": len(tasks),
            "total_notes": len(notes),
            "total_deal_value": total_deal_value,
            "closed_deals": len(closed_deals),
            "closed_deal_value": closed_deal_value
        }
    }

def test_connection():
    if not validate_config():
        return False, "Configuration missing"
    url = f"{BASE_URL}/Leads?per_page=1"
    response_data = make_api_request(url)
    if "Error" in response_data:
        return False, f"API connection failed: {response_data['Error']}"
    return True, "API connection successful"

def get_deals_by_stage(stage=None):
    deals = get_deals()
    if "Error" in deals:
        return deals
    if not stage:
        return deals
    filtered_deals = defaultdict(list)
    for owner, owner_deals in deals.items():
        for deal in owner_deals:
            if deal.get("Stage", "").lower() == stage.lower():
                filtered_deals[owner].append(deal)
    return dict(filtered_deals)

def get_tasks_by_status(status=None):
    tasks = get_tasks()
    if "Error" in tasks:
        return tasks
    if not status:
        return tasks
    filtered_tasks = defaultdict(list)
    for owner, owner_tasks in tasks.items():
        for task in owner_tasks:
            if task.get("Status", "").lower() == status.lower():
                filtered_tasks[owner].append(task)
    return dict(filtered_tasks)

def get_leads_by_status(status=None):
    leads = get_leads()
    if "Error" in leads:
        return leads
    if not status:
        return leads
    filtered_leads = defaultdict(list)
    for owner, owner_leads in leads.items():
        for lead in owner_leads:
            if lead.get("Lead Status", "").lower() == status.lower():
                filtered_leads[owner].append(lead)
    return dict(filtered_leads)