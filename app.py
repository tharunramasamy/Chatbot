import streamlit as st
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# Import our custom modules
from google_ai import GoogleAI, get_ai_client, show_ai_status, get_ai_response, get_ai_summary
from zoho_crm import (
    get_deals, get_leads, get_tasks, get_notes, 
    get_crm_summary, test_connection, filter_data_by_owner,
    get_deals_by_stage, get_tasks_by_status, get_leads_by_status
)

# Load environment variables
load_dotenv()

# User credentials dictionary
USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "name": "Admin User",
        "owner_name": "All"
    },
    "RajaMurugavelu": {
        "password": "rajamurugavelu123",
        "role": "owner",
        "name": "Raja Murugavelu",
        "owner_name": "Raja Murugavelu"
    },
    "KumaranV": {
        "password": "kumaranv123",
        "role": "owner",
        "name": "Kumaran V",
        "owner_name": "Kumaran V"
    },
    "SoniyaM": {
        "password": "soniyam123",
        "role": "owner",
        "name": "Soniya M",
        "owner_name": "Soniya M"
    },
    "DineshKumar": {
        "password": "dineshkumar123",
        "role": "owner",
        "name": "Dinesh Kumar",
        "owner_name": "Dinesh Kumar"
    },
    "Presales": {
        "password": "presales123",
        "role": "owner",
        "name": "Presales",
        "owner_name": "Presales"
    },
    "VishnuBhagavath": {
        "password": "vishnubhagavath123",
        "role": "owner",
        "name": "Vishnu Bhagavath",
        "owner_name": "Vishnu Bhagavath"
    },
    "ManojR": {
        "password": "manojr123",
        "role": "owner",
        "name": "Manoj R",
        "owner_name": "Manoj R"
    },
    "PraveenMuthumasaran": {
        "password": "praveenmuthumasaran123",
        "role": "owner",
        "name": "Praveen Muthumasaran",
        "owner_name": "Praveen Muthumasaran"
    },
    "RamKumar": {
        "password": "ramkumar123",
        "role": "owner",
        "name": "Ram Kumar",
        "owner_name": "Ram Kumar"
    },
    "HarishAravindhan": {
        "password": "harisharavindhan123",
        "role": "owner",
        "name": "Harish Aravindhan",
        "owner_name": "Harish Aravindhan"
    },
}

# Page configuration
st.set_page_config(
    page_title="CRM AI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
def load_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .sidebar-header {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Authentication functions
def authenticate_user(username, password):
    """Authenticate user with provided credentials"""
    if username in USERS and USERS[username]["password"] == password:
        return USERS[username]
    return None

def show_login():
    """Display login form"""
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; text-align: center; margin: 0;">
            CRM AI Dashboard
        </h1>
        <p style="color: white; text-align: center; margin: 0;">
            Please sign in to access your CRM dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            with st.form("login_form"):
                st.markdown("Login")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                if st.form_submit_button("Sign In", use_container_width=True):
                    user_info = authenticate_user(username, password)
                    if user_info:
                        st.session_state.user_info = user_info
                        st.session_state.authenticated = True
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Demo credentials
            with st.expander("Demo Credentials"):
                st.markdown("""
                **Admin Account:**
                - Username: `admin`
                - Password: `admin123`
                
                **Owner Account:**
                - Username: `RajaMurugavelu`
                - Password: `rajamurugavelu123`
                """)

def show_dashboard():
    """Display main dashboard"""
    user_info = st.session_state.user_info
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1 style="color: white; margin: 0;">CRM AI Dashboard</h1>
        <p style="color: white; margin: 0;">
            Welcome, {user_info.get('name', 'User')} | Role: {user_info.get('role', 'Unknown').title()}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-header">
            <h3>User Info</h3>
            <p><strong>Name:</strong> {user_info.get('name', 'Unknown')}</p>
            <p><strong>Role:</strong> {user_info.get('role', 'Unknown').title()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Logout button
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        # CRM Connection Status
        st.markdown("CRM Status")
        try:
            connection_status, message = test_connection()
            if connection_status:
                st.success(message)
            else:
                st.error(message)
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
        
        # Refresh Data button
        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.success("Data refreshed!")
            st.rerun()
        
        # Show AI status
        show_ai_status()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Leads", "Deals", "Tasks", "Notes"])
    
    # Get CRM data
    owner_name = user_info.get('owner_name', 'All')
    
    try:
        with st.spinner("Loading CRM data..."):
            crm_data = get_crm_summary(owner_name)
    except Exception as e:
        st.error(f"Error loading CRM data: {str(e)}")
        crm_data = {
            "leads": [],
            "deals": [],
            "tasks": [],
            "notes": [],
            "summary": {
                "total_leads": 0,
                "total_deals": 0,
                "total_tasks": 0,
                "total_notes": 0,
                "total_deal_value": 0,
                "closed_deals": 0,
                "closed_deal_value": 0
            }
        }
    
    # Dashboard Tab
    with tab1:
        show_dashboard_tab(crm_data, user_info)
    
    # Leads Tab
    with tab2:
        show_leads_tab(crm_data.get('leads', []), user_info)
    
    # Deals Tab
    with tab3:
        show_deals_tab(crm_data.get('deals', []), user_info)
    
    # Tasks Tab
    with tab4:
        show_tasks_tab(crm_data.get('tasks', []), user_info)
    
    # Notes Tab
    with tab5:
        show_notes_tab(crm_data.get('notes', []), user_info)

def show_dashboard_tab(crm_data, user_info):
    """Display dashboard overview"""
    summary = crm_data.get('summary', {})
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    print("Summary Data:", summary) 

    with col1:
        st.metric("Total Leads", summary.get('total_leads', 0))
    
    with col2:
        st.metric("Total Deals", summary.get('total_deals', 0))
    
    with col3:
        st.metric("Total Tasks", summary.get('total_tasks', 0))
    
    with col4:
        st.metric("Total Notes", summary.get('total_notes', 0))
    
    # Deal Value Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Deal Value", f"${summary.get('total_deal_value', 0):,.2f}")
    
    with col2:
        st.metric("Closed Deals", summary.get('closed_deals', 0))
    
    with col3:
        st.metric("Closed Deal Value", f"${summary.get('closed_deal_value', 0):,.2f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Deal Stage Distribution
        deals = crm_data.get('deals', [])
        if deals:
            stage_counts = {}
            for deal in deals:
                stage = deal.get('Stage', 'Unknown')
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
            
            fig = px.pie(
                values=list(stage_counts.values()),
                names=list(stage_counts.keys()),
                title="Deal Stage Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Lead Status Distribution
        leads = crm_data.get('leads', [])
        if leads:
            status_counts = {}
            for lead in leads:
                status = lead.get('Lead Status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            fig = px.bar(
                x=list(status_counts.keys()),
                y=list(status_counts.values()),
                title="Lead Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # AI Chat Interface
    st.markdown("AI Assistant")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your CRM data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_ai_response(prompt, crm_data, user_info)
                st.markdown(response)
        
        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def show_leads_tab(leads, user_info):
    """Display leads data"""
    st.markdown("Leads Management")
    
    if not leads:
        st.info("No leads found for your account.")
        return
    
    # Filter controls
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All"] + list(set(lead.get('Lead Status', 'Unknown') for lead in leads))
        )
    
    with col2:
        search_term = st.text_input("Search leads", placeholder="Enter lead name or company...")
    
    # Filter leads
    filtered_leads = leads
    if status_filter != "All":
        filtered_leads = [lead for lead in filtered_leads if lead.get('Lead Status') == status_filter]
    
    if search_term:
        filtered_leads = [
            lead for lead in filtered_leads 
            if search_term.lower() in lead.get('Lead Name', '').lower() or 
               search_term.lower() in lead.get('Company', '').lower()
        ]
    
    # Display leads
    st.markdown(f"**Found {len(filtered_leads)} leads**")
    
    # Convert to DataFrame for display
    if filtered_leads:
        df = pd.DataFrame(filtered_leads)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No leads match your filters.")

def show_deals_tab(deals, user_info):
    """Display deals data"""
    st.markdown("Deals Management")
    
    if not deals:
        st.info("No deals found for your account.")
        return
    
    # Filter controls
    col1, col2 = st.columns(2)
    
    with col1:
        stage_filter = st.selectbox(
            "Filter by Stage",
            ["All"] + list(set(deal.get('Stage', 'Unknown') for deal in deals))
        )
    
    with col2:
        search_term = st.text_input("Search deals", placeholder="Enter deal name or account...")
    
    # Filter deals
    filtered_deals = deals
    if stage_filter != "All":
        filtered_deals = [deal for deal in filtered_deals if deal.get('Stage') == stage_filter]
    
    if search_term:
        filtered_deals = [
            deal for deal in filtered_deals 
            if search_term.lower() in deal.get('Deal Name', '').lower() or 
               search_term.lower() in deal.get('Account Name', '').lower()
        ]
    
    # Display deals
    st.markdown(f"**Found {len(filtered_deals)} deals**")
    
    # Convert to DataFrame for display
    if filtered_deals:
        df = pd.DataFrame(filtered_deals)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No deals match your filters.")

def show_tasks_tab(tasks, user_info):
    """Display tasks data"""
    st.markdown("Tasks Management")
    
    if not tasks:
        st.info("No tasks found for your account.")
        return
    
    # Filter controls
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All"] + list(set(task.get('Status', 'Unknown') for task in tasks))
        )
    
    with col2:
        search_term = st.text_input("Search tasks", placeholder="Enter task subject...")
    
    # Filter tasks
    filtered_tasks = tasks
    if status_filter != "All":
        filtered_tasks = [task for task in filtered_tasks if task.get('Status') == status_filter]
    
    if search_term:
        filtered_tasks = [
            task for task in filtered_tasks 
            if search_term.lower() in task.get('Task Subject', '').lower()
        ]
    
    # Display tasks
    st.markdown(f"**Found {len(filtered_tasks)} tasks**")
    
    # Convert to DataFrame for display
    if filtered_tasks:
        df = pd.DataFrame(filtered_tasks)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No tasks match your filters.")

def show_notes_tab(notes, user_info):
    """Display notes data"""
    st.markdown("Notes Management")
    
    if not notes:
        st.info("No notes found for your account.")
        return
    
    # Search control
    search_term = st.text_input("Search notes", placeholder="Enter note title or content...")
    
    # Filter notes
    filtered_notes = notes
    if search_term:
        filtered_notes = [
            note for note in filtered_notes 
            if search_term.lower() in note.get('Note Title', '').lower() or 
               search_term.lower() in note.get('Note Content', '').lower()
        ]
    
    # Display notes
    st.markdown(f"**Found {len(filtered_notes)} notes**")
    
    # Convert to DataFrame for display
    if filtered_notes:
        df = pd.DataFrame(filtered_notes)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No notes match your search.")

def main():
    """Main application function"""
    load_css()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    
    # Show login or dashboard
    if not st.session_state.authenticated:
        show_login()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()


