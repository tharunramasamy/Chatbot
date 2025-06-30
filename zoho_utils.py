import requests
import os
import logging
from dotenv import load_dotenv
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Zoho API configuration
client_id = os.getenv("ZOHO_CLIENT_ID")
client_secret = os.getenv("ZOHO_CLIENT_SECRET")
refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
access_token = os.getenv("ZOHO_ACCESS_TOKEN")

BASE_URL = "https://www.zohoapis.com/crm/v2"

def validate_config():
    """Validate that all required Zoho configuration is present"""
    missing = []
    if not client_id:
        missing.append("ZOHO_CLIENT_ID")
    if not client_secret:
        missing.append("ZOHO_CLIENT_SECRET")
    if not refresh_token:
        missing.append("ZOHO_REFRESH_TOKEN")
    
    if missing:
        logger.error(f"Missing Zoho configuration: {', '.join(missing)}")
        return False
    return True

def refresh_access_token():
    """Refresh the Zoho API access token using the refresh token"""
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
            else:
                logger.error("No access token in response")
                return False
        else:
            logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during token refresh: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        return False

def get_headers():
    """Get the headers required for API requests"""
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
    """Make an API request with automatic token refresh on 401"""
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
                if refresh_access_token():
                    continue
                else:
                    return {"Error": "Unable to refresh access token"}
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"Error": error_msg}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during API request: {e}"
            logger.error(error_msg)
            if attempt == max_retries:
                return {"Error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during API request: {e}"
            logger.error(error_msg)
            return {"Error": error_msg}
    
    return {"Error": "Max retries exceeded"}

def _extract_name(field_data):
    """Improved helper function to extract name from Zoho field data"""
    if isinstance(field_data, dict):
        return field_data.get("name", field_data.get("full_name", "Unknown"))
    elif isinstance(field_data, str):
        return field_data
    elif field_data is None:
        return "Unassigned"
    else:
        return str(field_data)

def filter_data_by_owner(data, owner_filter=None):
    """Filter data by specific owner(s)"""
    if not data or "Error" in str(data) or not owner_filter:
        return data
    
    if isinstance(owner_filter, str):
        owner_filter = [owner_filter]
    
    filtered_data = {}
    for owner, records in data.items():
        if owner in owner_filter:
            filtered_data[owner] = records
    
    return filtered_data

def get_deals(owner_filter=None):
    """Fetch deals data from Zoho CRM with optional owner filtering"""
    try:
        url = f"{BASE_URL}/Deals"
        response_data = make_api_request(url)
        
        if "Error" in response_data:
            logger.error(f"Error fetching deals: {response_data['Error']}")
            return {"Error": [response_data["Error"]]}
        
        deals = response_data.get("data", [])
        if not deals:
            logger.info("No deals found")
            return {"No Deals": []}
        
        filtered_deals = defaultdict(list)
        
        for deal in deals:
            try:
                deal_id = deal.get("id")
                notes = "No notes available"
                
                # Extract deal data with improved owner handling
                deal_data = {
                    "Deal ID": deal_id,
                    "Deal Name": deal.get("Deal_Name", "Unnamed Deal"),
                    "Account Name": _extract_name(deal.get("Account_Name")),
                    "Deal Owner": _extract_name(deal.get("Owner")),
                    "Stage": deal.get("Stage", "Unknown"),
                    "Amount": deal.get("Amount", 0),
                    "Closing Date": deal.get("Closing_Date", "Not Set"),
                    "Service Line": deal.get("Service_Line", "Not Specified"),
                    "Accelerators/Personalized Service": deal.get("Accelerators_or_Personalized_Service", "None"),
                    "Tags": deal.get("Tags", []),
                    "Notes": notes
                }
                
                owner = deal_data["Deal Owner"] or "Unassigned"
                
                # Apply owner filter if specified
                if not owner_filter or owner in owner_filter:
                    filtered_deals[owner].append(deal_data)
                    
            except Exception as e:
                logger.error(f"Error processing deal {deal.get('id', 'unknown')}: {e}")
                continue
        
        result = dict(filtered_deals)
        logger.info(f"Successfully processed {sum(len(v) for v in result.values())} deals")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in get_deals: {e}")
        return {"Error": [f"Unexpected error: {str(e)}"]}

def get_leads(owner_filter=None):
    """Fetch leads data from Zoho CRM with optional owner filtering"""
    try:
        url = f"{BASE_URL}/Leads"
        response_data = make_api_request(url)
        
        if "Error" in response_data:
            logger.error(f"Error fetching leads: {response_data['Error']}")
            return {"Error": [response_data["Error"]]}
        
        leads = response_data.get("data", [])
        if not leads:
            logger.info("No leads found")
            return {"No Leads": []}
        
        filtered_leads = defaultdict(list)
        
        for lead in leads:
            try:
                lead_id = lead.get("id")
                
                # Improved lead data extraction with better owner handling
                lead_data = {
                    "Lead ID": lead_id,
                    "Lead Name": lead.get("Full_Name", lead.get("Last_Name", "Unnamed Lead")),
                    "First Name": lead.get("First_Name", ""),
                    "Last Name": lead.get("Last_Name", ""),
                    "Company": lead.get("Company", "No Company"),
                    "Lead Owner": _extract_name(lead.get("Owner")),
                    "Email": lead.get("Email", "No Email"),
                    "Phone": lead.get("Phone", "No Phone"),
                    "Mobile": lead.get("Mobile", "No Mobile"),
                    "Lead Status": lead.get("Lead_Status", "Unknown"),
                    "Lead Source": lead.get("Lead_Source", "Unknown"),
                    "Industry": lead.get("Industry", "Not Specified"),
                    "Tags": lead.get("Tags", []),
                    "Created Time": lead.get("Created_Time", "Unknown"),
                    "Modified Time": lead.get("Modified_Time", "Unknown")
                }
                
                # Ensure proper owner classification
                owner = lead_data["Lead Owner"]
                if not owner or owner.strip() == "":
                    owner = "Unassigned"
                
                # Apply owner filter if specified
                if not owner_filter or owner in owner_filter:
                    filtered_leads[owner].append(lead_data)
                    
            except Exception as e:
                logger.error(f"Error processing lead {lead.get('id', 'unknown')}: {e}")
                continue
        
        result = dict(filtered_leads)
        logger.info(f"Successfully processed {sum(len(v) for v in result.values())} leads across {len(result)} owners")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in get_leads: {e}")
        return {"Error": [f"Unexpected error: {str(e)}"]}

def get_tasks(owner_filter=None):
    """Fetch tasks data from Zoho CRM with optional owner filtering"""
    try:
        url = f"{BASE_URL}/Tasks"
        response_data = make_api_request(url)
        
        if "Error" in response_data:
            logger.error(f"Error fetching tasks: {response_data['Error']}")
            return {"Error": [response_data["Error"]]}
        
        tasks = response_data.get("data", [])
        if not tasks:
            logger.info("No tasks found")
            return {"No Tasks": []}
        
        filtered_tasks = defaultdict(list)
        
        for task in tasks:
            try:
                task_id = task.get("id")
                
                # Improved task data extraction
                task_data = {
                    "Task ID": task_id,
                    "Task Subject": task.get("Subject", "Unnamed Task"),
                    "Task Owner": _extract_name(task.get("Owner")),
                    "Status": task.get("Status", "Not Started"),
                    "Priority": task.get("Priority", "Normal"),
                    "Due Date": task.get("Due_Date", "Not Set"),
                    "Start Date": task.get("Start_Date", "Not Set"),
                    "Related To": _extract_name(task.get("What_Id")),
                    "Description": task.get("Description", "No Description"),
                    "Created Time": task.get("Created_Time", "Unknown"),
                    "Modified Time": task.get("Modified_Time", "Unknown")
                }
                
                # Ensure proper owner classification
                owner = task_data["Task Owner"]
                if not owner or owner.strip() == "":
                    owner = "Unassigned"
                
                # Apply owner filter if specified
                if not owner_filter or owner in owner_filter:
                    filtered_tasks[owner].append(task_data)
                    
            except Exception as e:
                logger.error(f"Error processing task {task.get('id', 'unknown')}: {e}")
                continue
        
        result = dict(filtered_tasks)
        logger.info(f"Successfully processed {sum(len(v) for v in result.values())} tasks across {len(result)} owners")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in get_tasks: {e}")
        return {"Error": [f"Unexpected error: {str(e)}"]}

def get_deals_by_stage(stage=None, owner_filter=None):
    """Get deals filtered by stage and optionally by owner"""
    try:
        deals = get_deals(owner_filter)
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
        
    except Exception as e:
        logger.error(f"Error filtering deals by stage: {e}")
        return {"Error": [str(e)]}

def get_summary_stats(owner_filter=None):
    """Get summary statistics for dashboard with optional owner filtering"""
    try:
        deals = get_deals(owner_filter)
        leads = get_leads(owner_filter)
        tasks = get_tasks(owner_filter)
        
        stats = {
            "total_deals": 0,
            "total_leads": 0,
            "total_tasks": 0,
            "deals_by_owner": {},
            "leads_by_owner": {},
            "tasks_by_owner": {}
        }
        
        # Calculate deals stats
        if isinstance(deals, dict) and "Error" not in deals:
            stats["total_deals"] = sum(len(v) for v in deals.values())
            stats["deals_by_owner"] = {k: len(v) for k, v in deals.items()}
        
        # Calculate leads stats
        if isinstance(leads, dict) and "Error" not in leads:
            stats["total_leads"] = sum(len(v) for v in leads.values())
            stats["leads_by_owner"] = {k: len(v) for k, v in leads.items()}
        
        # Calculate tasks stats
        if isinstance(tasks, dict) and "Error" not in tasks:
            stats["total_tasks"] = sum(len(v) for v in tasks.values())
            stats["tasks_by_owner"] = {k: len(v) for k, v in tasks.items()}
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting summary stats: {e}")
        return {"Error": str(e)}

def get_data_for_owner(owner_name):
    """Get all data (deals, leads, tasks) for a specific owner"""
    try:
        owner_filter = [owner_name] if owner_name != "All" else None
        
        deals = get_deals(owner_filter)
        leads = get_leads(owner_filter)
        tasks = get_tasks(owner_filter)
        
        return {
            "deals": deals,
            "leads": leads,
            "tasks": tasks
        }
        
    except Exception as e:
        logger.error(f"Error getting data for owner {owner_name}: {e}")
        return {"Error": str(e)}

def get_all_owners():
    """Get list of all owners across deals, leads, and tasks"""
    try:
        all_owners = set()
        
        # Get owners from deals
        deals = get_deals()
        if isinstance(deals, dict) and "Error" not in deals:
            all_owners.update(deals.keys())
        
        # Get owners from leads
        leads = get_leads()
        if isinstance(leads, dict) and "Error" not in leads:
            all_owners.update(leads.keys())
        
        # Get owners from tasks
        tasks = get_tasks()
        if isinstance(tasks, dict) and "Error" not in tasks:
            all_owners.update(tasks.keys())
        
        # Remove generic entries
        all_owners.discard("No Deals")
        all_owners.discard("No Leads")
        all_owners.discard("No Tasks")
        all_owners.discard("Error")
        
        return sorted(list(all_owners))
        
    except Exception as e:
        logger.error(f"Error getting all owners: {e}")
        return []