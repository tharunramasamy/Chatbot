import streamlit as st
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from zoho_utils import get_deals, get_leads, get_tasks
from pitch_memory import chat_with_ai
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the .env file
load_dotenv()

# Page Configuration and Styling
st.set_page_config(
    page_title="Opti.AI - Intelligent Sales Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add CSS styling
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 10px;
    color: white;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.metric-card h2 {
    margin: 10px 0 0 0;
    font-size: 2em;
    font-weight: bold;
}

.user-message {
    background-color: #e3f2fd;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
    border-left: 4px solid #2196f3;
}

.bot-message {
    background-color: #f3e5f5;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
    border-left: 4px solid #9c27b0;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    padding-left: 20px;
    padding-right: 20px;
}
</style>
""", unsafe_allow_html=True)

USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "Admin"},
    "Manoj R": {"password": "manoj123", "role": "owner", "name": "Manoj R"},
}

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "authenticated": False,
        "user": None,
        "chat_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_logout():
    """Display logout button in sidebar"""
    with st.sidebar:
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.chat_history = []
            st.rerun()

def show_login():
    """Display login form"""
    st.markdown("# OptiSale AI - Intelligent Sales Assistant")
    st.markdown("### Please login to continue")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                st.markdown("#### Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login", use_container_width=True):
                    if username in USERS and USERS[username]["password"] == password:
                        st.session_state.authenticated = True
                        st.session_state.user = USERS[username]
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

def main_interface():
    """Main application interface"""
    # Sidebar
    st.sidebar.title("Opti.ai")
    st.sidebar.markdown("Welcome to your AI-powered sales assistant!")
    st.sidebar.markdown(f" User: {st.session_state.user['name']}")
    
    if st.sidebar.button(" New Chat", key="new_chat"):
        st.session_state.chat_history = []
        st.rerun()

    show_logout()

    # Main content with tabs
    tab2, tab1 = st.tabs([" AI Chat", " Dashboard"])

    # Dashboard Tab
    with tab1:
        st.markdown("# Sales Dashboard")
        
        # Metrics row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.spinner("Loading deals..."):
                deals = get_deals() or {}
                if isinstance(deals, dict) and "Error" not in deals:
                    total_deals = sum(len(v) for v in deals.values()) if deals else 0
                else:
                    total_deals = 0
                st.markdown(f'<div class="metric-card">Total Deals<br><h2>{total_deals}</h2></div>', unsafe_allow_html=True)
        
        with col2:
            with st.spinner("Loading leads..."):
                leads = get_leads() or []
                if isinstance(leads, list) and leads and "Error" not in str(leads[0]):
                    lead_count = len(leads)
                else:
                    lead_count = 0
                st.markdown(f'<div class="metric-card">Active Leads<br><h2>{lead_count}</h2></div>', unsafe_allow_html=True)
        
        with col3:
            with st.spinner("Loading tasks..."):
                tasks = get_tasks() or []
                if isinstance(tasks, list) and tasks and "Error" not in str(tasks[0]):
                    task_count = len(tasks)
                else:
                    task_count = 0
                st.markdown(f'<div class="metric-card">Pending Tasks<br><h2>{task_count}</h2></div>', unsafe_allow_html=True)

        # Data sections
        st.markdown("---")
        
        # Deals section
        with st.expander("Recent Deals", expanded=True):
            if isinstance(deals, dict) and deals and "Error" not in deals:
                for owner, owner_deals in deals.items():
                    if owner_deals:  # Only show if there are deals
                        st.subheader(f" Owner: {owner}")
                        df = pd.DataFrame(owner_deals)
                        st.dataframe(df, use_container_width=True)
            else:
                st.warning("No deals data available or error fetching data")
        
        # Leads section
        with st.expander(" Recent Leads"):
            if isinstance(leads, list) and leads and "Error" not in str(leads[0]):
                df = pd.DataFrame(leads)
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No leads data available or error fetching data")

        # Tasks section
        with st.expander("Your Tasks"):
            if isinstance(tasks, list) and tasks and "Error" not in str(tasks[0]):
                df = pd.DataFrame(tasks)
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No tasks data available or error fetching data")

    # AI Chat Tab
    with tab2:
        st.markdown("Opti.ai ")
        st.markdown("Ask me about your sales data, deals, leads, or get AI-powered insights!")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.get('chat_history', []):
                role_class = "user-message" if msg["role"] == "user" else "bot-message"
                st.markdown(f'<div class="{role_class}">{msg["content"]}</div>', unsafe_allow_html=True)

        # Chat input
        query = st.chat_input("Ask me about sales, deals, leads, or your CRM data...")
        
        if query:
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": query})
            
            with st.spinner(" Analyzing your question..."):
                try:
                    # Check if it's a CRM-specific query
                    if any(keyword in query.lower() for keyword in ["deal", "lead", "task", "contact", "crm", "sales"]):
                        response = process_crm_query(query)
                    else:
                        response = chat_with_ai(query)
                    
                    # Add AI response to history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Error processing query: {str(e)}")
                    error_msg = f"I apologize, but I encountered an error processing your request: {str(e)}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                    st.rerun()

def process_crm_query(query):
    """Process CRM-specific queries and return formatted response"""
    query_lower = query.lower()
    
    try:
        # Determine what data to fetch based on query
        if "deal" in query_lower:
            data = get_deals()
            data_type = "deals"
        elif "lead" in query_lower:
            data = get_leads()
            data_type = "leads"
        elif "task" in query_lower:
            data = get_tasks()
            data_type = "tasks"
        else:
            # For general CRM queries, provide overview
            deals = get_deals()
            leads = get_leads()
            tasks = get_tasks()
            return generate_crm_overview(deals, leads, tasks, query)
        
        if data:
            return format_crm_response(data, data_type, query)
        else:
            return f"No {data_type} found in your CRM."
            
    except Exception as e:
        logger.error(f"Error processing CRM query: {str(e)}")
        return f"I encountered an error accessing your CRM data: {str(e)}"

def format_crm_response(data, data_type, original_query):
    """Format CRM data response with AI analysis"""
    try:
        # Check for errors in data
        if isinstance(data, dict) and "Error" in data:
            return f"Error fetching {data_type}: {data['Error']}"
        
        if not data:
            return f"No {data_type} found in your CRM."
        
        # Generate summary based on data type
        if data_type == "deals":
            if isinstance(data, dict):
                total_deals = sum(len(v) for v in data.values())
                summary = f"**Found {total_deals} deals across {len(data)} owners**\n\n"
                
                # Add recent deals
                recent_deals = []
                for owner, owner_deals in data.items():
                    for deal in owner_deals[:2]:  # Get first 2 deals per owner
                        recent_deals.append(f"• **{deal['Deal Name']}** (Owner: {owner}, Stage: {deal['Stage']}, Amount: ${deal['Amount'] or 'N/A'})")
                
                if recent_deals:
                    summary += "**Recent Deals:**\n" + "\n".join(recent_deals[:5])
                    
                # Add AI analysis
                ai_context = f"Based on the CRM deals data, provide insights for this query: {original_query}"
                ai_response = chat_with_ai(ai_context)
                summary += f"\n\n **AI Analysis:**\n{ai_response}"
                
                return summary
                
        elif data_type == "leads":
            if isinstance(data, list):
                summary = f" **Found {len(data)} leads**\n\n"
                
                # Add recent leads
                recent_leads = []
                for lead in data[:5]:
                    recent_leads.append(f"• **{lead['Lead Name']}** (Company: {lead['Company'] or 'N/A'}, Owner: {lead['Lead Owner'] or 'N/A'})")
                
                if recent_leads:
                    summary += "**Recent Leads:**\n" + "\n".join(recent_leads)
                
                # Add AI analysis
                ai_context = f"Based on the CRM leads data, provide insights for this query: {original_query}"
                ai_response = chat_with_ai(ai_context)
                summary += f"\n\n **AI Analysis:**\n{ai_response}"
                
                return summary
                
        elif data_type == "tasks":
            if isinstance(data, list):
                summary = f" **Found {len(data)} tasks**\n\n"
                
                # Add recent tasks
                recent_tasks = []
                for task in data[:5]:
                    recent_tasks.append(f"• **{task['Subject']}** (Status: {task['Status']}, Due: {task['Due Date'] or 'N/A'})")
                
                if recent_tasks:
                    summary += "**Recent Tasks:**\n" + "\n".join(recent_tasks)
                
                # Add AI analysis
                ai_context = f"Based on the CRM tasks data, provide insights for this query: {original_query}"
                ai_response = chat_with_ai(ai_context)
                summary += f"\n\n **AI Analysis:**\n{ai_response}"
                
                return summary
        
        return f"Found {data_type} data, but couldn't format it properly."
        
    except Exception as e:
        logger.error(f"Error formatting CRM response: {str(e)}")
        return f"I found your {data_type} data but encountered an error formatting the response: {str(e)}"

def generate_crm_overview(deals, leads, tasks, query):
    """Generate a comprehensive CRM overview"""
    try:
        overview = " **CRM Overview:**\n\n"
        
        # Deals summary
        if deals and isinstance(deals, dict) and "Error" not in deals:
            total_deals = sum(len(v) for v in deals.values())
            overview += f" **Deals:** {total_deals} total deals\n"
        else:
            overview += " **Deals:** No deals data available\n"
        
        # Leads summary
        if leads and isinstance(leads, list) and "Error" not in str(leads[0]):
            overview += f" **Leads:** {len(leads)} active leads\n"
        else:
            overview += " **Leads:** No leads data available\n"
        
        # Tasks summary
        if tasks and isinstance(tasks, list) and "Error" not in str(tasks[0]):
            overview += f" **Tasks:** {len(tasks)} pending tasks\n"
        else:
            overview += " **Tasks:** No tasks data available\n"
        
        # Add AI analysis
        ai_context = f"Based on this CRM overview, provide insights for: {query}"
        ai_response = chat_with_ai(ai_context)
        overview += f"\n **AI Insights:**\n{ai_response}"
        
        return overview
        
    except Exception as e:
        logger.error(f"Error generating CRM overview: {str(e)}")
        return f"I encountered an error generating your CRM overview: {str(e)}"

if __name__ == "__main__":
    init_session_state()
    
    if st.session_state.authenticated:
        main_interface()
    else:
        show_login()