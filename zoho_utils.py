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

def get_deals():
    """Fetch deals data from Zoho CRM and return it in a structured format"""
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
                # Skip fetching notes for the deal
                notes = "No notes available"  # Simply add a placeholder message
                
                # Extract deal data
                deal_data = {
                    "Deal ID": deal_id,
                    "Deal Name": deal.get("Deal_Name", "Unnamed Deal"),
                    "Account Name": _extract_name(deal.get("Account_Name")),
                    "Deal Owner": _extract_name(deal.get("Owner")),
                    "Stage": deal.get("Stage", "Unknown"),
                    "Amount": deal.get("Amount"),
                    "Closing Date": deal.get("Closing_Date"),
                    "Service Line": deal.get("Service_Line"),
                    "Accelerators/Personalized Service": deal.get("Accelerators_or_Personalized_Service"),
                    "Tags": deal.get("Tags"),
                    "Notes": notes  # Use the placeholder instead of fetching notes
                }
                
                owner = deal_data["Deal Owner"] or "Unknown Owner"
                filtered_deals[owner].append(deal_data)
                
            except Exception as e:
                logger.error(f"Error processing deal {deal.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully processed {sum(len(v) for v in filtered_deals.values())} deals")
        return dict(filtered_deals)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_deals: {e}")
        return {"Error": [f"Unexpected error: {str(e)}"]}

def _extract_name(field_data):
    """Helper function to extract name from Zoho field data"""
    if isinstance(field_data, dict):
        return field_data.get("name", "Unknown")
    elif isinstance(field_data, str):
        return field_data
    else:
        return None

# Additional utility functions
def get_deals_by_stage(stage=None):
    """Get deals filtered by stage"""
    try:
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
        
    except Exception as e:
        logger.error(f"Error filtering deals by stage: {e}")
        return {"Error": [str(e)]}

def get_leads():
    """Fetch leads data from Zoho CRM and return it in a structured format"""
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
                
                # Extract lead data
                lead_data = {
                    "Lead ID": lead_id,
                    "Lead Name": lead.get("Full_Name", "Unnamed Lead"),
                    "Company": lead.get("Company", "No Company"),
                    "Lead Owner": _extract_name(lead.get("Owner")),
                    "Email": lead.get("Email", "No Email"),
                    "Phone": lead.get("Phone", "No Phone"),
                    "Lead Status": lead.get("Lead_Status", "Unknown"),
                    "Tags": lead.get("Tags", []),
                }
                
                owner = lead_data["Lead Owner"] or "Unknown Owner"
                filtered_leads[owner].append(lead_data)
                
            except Exception as e:
                logger.error(f"Error processing lead {lead.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully processed {sum(len(v) for v in filtered_leads.values())} leads")
        return dict(filtered_leads)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_leads: {e}")
        return {"Error": [f"Unexpected error: {str(e)}"]}


def get_tasks():
    """Fetch tasks data from Zoho CRM and return it in a structured format"""
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
                
                # Extract task data
                task_data = {
                    "Task ID": task_id,
                    "Task Subject": task.get("Subject", "Unnamed Task"),
                    "Task Owner": _extract_name(task.get("Owner")),
                    "Status": task.get("Status", "Not Started"),
                    "Priority": task.get("Priority", "Normal"),
                    "Due Date": task.get("Due_Date"),
                    "Related To": _extract_name(task.get("What_Id")),
                    "Start Date": task.get("Start_Date"),
                }
                
                owner = task_data["Task Owner"] or "Unknown Owner"
                filtered_tasks[owner].append(task_data)
                
            except Exception as e:
                logger.error(f"Error processing task {task.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully processed {sum(len(v) for v in filtered_tasks.values())} tasks")
        return dict(filtered_tasks)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_tasks: {e}")
        return {"Error": [f"Unexpected error: {str(e)}"]}

