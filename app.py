import streamlit as st
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from zoho_utils import get_deals, get_leads, get_tasks, get_summary_stats
from pitch_memory import chat_with_ai, analyze_crm_data
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the .env file
load_dotenv()

# Page Configuration and Styling
st.set_page_config(
    page_title="OptiSale.AI - Intelligent Sales Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .chat-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .user-message {
        background: #667eea;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        text-align: right;
    }
    .ai-message {
        background: white;
        color: #333;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
    }
    .owner-filter {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

USERS = {
    # Admin users (full access)
    "admin": {"password": "admin123", "role": "admin", "name": "Admin User", "owner_name": None},
    "demo": {"password": "demo123", "role": "admin", "name": "Demo User", "owner_name": None},
    
    # Owner users (restricted to own data)
    "RajaMurugavelu": {"password": "rajamurugavelu123", "role": "owner", "name": "Raja Murugavelu", "owner_name": "Raja Murugavelu"},
    "KumaranV": {"password": "kumaranv123", "role": "owner", "name": "Kumaran V", "owner_name": "Kumaran V"},
    "SoniyaM": {"password": "soniyam123", "role": "owner", "name": "Soniya M", "owner_name": "Soniya M"},
    "DineshKumar": {"password": "dineshkumar123", "role": "owner", "name": "Dinesh Kumar", "owner_name": "Dinesh Kumar"},
    "Presales": {"password": "presales123", "role": "owner", "name": "Presales", "owner_name": "Presales"},
    "VishnuBhagavath": {"password": "vishnubhagavath123", "role": "owner", "name": "Vishnu Bhagavath", "owner_name": "Vishnu Bhagavath"},
    "ManojR": {"password": "manojr123", "role": "owner", "name": "Manoj R", "owner_name": "Manoj R"},
    "PraveenMuthumaaran": {"password": "praveenmuthumasaran123", "role": "owner", "name": "Praveen Muthumasaran", "owner_name": "Praveen Muthumasaran"},
    "RamKumar": {"password": "ramkumar123", "role": "owner", "name": "Ram Kumar", "owner_name": "Ram Kumar"},
    "HarishAravindhan": {"password": "harisharavindhan123", "role": "owner", "name": "Harish Aravindhan", "owner_name": "Harish Aravindhan"}
}

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "authenticated": False,
        "user": None,
        "chat_history": [],
        "selected_owner": "All"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_logout():
    """Display logout button in sidebar"""
    with st.sidebar:
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.chat_history = []
            st.rerun()

def show_login():
    """Enhanced login form"""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 OptiSale.AI</h1>
        <p>Your AI-powered CRM companion for smarter sales insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Login to Your Dashboard")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_button = st.form_submit_button("Login", use_container_width=True)
            
            if login_button:
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.user = username
                    st.success(f"Welcome, {USERS[username]['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        st.info("💡 **Demo Credentials:**\n- Username: demo\n- Password: demo123")

def filter_data_by_ownership(data, user_info):
    """Filter data based on user role and ownership"""
    if not data or "Error" in str(data):
        return data
    
    # Admin users see all data
    if user_info["role"] == "admin":
        return data
    
    # Owner users see only their own data
    owner_name = user_info["owner_name"]
    if not owner_name:
        return {"No Data": []}
    
    # Filter data to show only records owned by the current user
    filtered_data = {}
    if isinstance(data, dict):
        for owner, records in data.items():
            if owner == owner_name:
                filtered_data[owner] = records
    
    return filtered_data if filtered_data else {"No Data": []}

def get_user_specific_data():
    """Get data filtered by current user's ownership"""
    user_info = USERS[st.session_state.user]
    
    # Fetch all data
    deals_data = get_deals()
    leads_data = get_leads()
    tasks_data = get_tasks()
    
    # Filter based on user role
    filtered_deals = filter_data_by_ownership(deals_data, user_info)
    filtered_leads = filter_data_by_ownership(leads_data, user_info)
    filtered_tasks = filter_data_by_ownership(tasks_data, user_info)
    
    return filtered_deals, filtered_leads, filtered_tasks

def show_dashboard():
    """Enhanced dashboard with ownership filtering"""
    user_info = USERS[st.session_state.user]
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🚀 OptiSale.AI Dashboard</h1>
        <p>Get intelligent insights about your CRM data</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="owner-filter">
        <h3>Welcome, <strong>{user_info['name']}</strong>!</h3>
        <p><strong>Role:</strong> {user_info['role'].title()}</p>
        {f"<p><strong>Viewing data for:</strong> {user_info['owner_name']}</p>" if user_info['role'] == 'owner' else "<p><strong>Access Level:</strong> All Data (Admin)</p>"}
    </div>
    """, unsafe_allow_html=True)

    # Get filtered data
    deals_data, leads_data, tasks_data = get_user_specific_data()
    
    # Summary Statistics
    st.markdown("## 📊 Performance Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_deals = sum(len(records) for records in deals_data.values()) if deals_data else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>🤝 Total Deals</h3>
            <h2 style="color: #667eea;">{total_deals}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_leads = sum(len(records) for records in leads_data.values()) if leads_data else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 Total Leads</h3>
            <h2 style="color: #667eea;">{total_leads}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_tasks = sum(len(records) for records in tasks_data.values()) if tasks_data else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ Total Tasks</h3>
            <h2 style="color: #667eea;">{total_tasks}</h2>
        </div>
        """, unsafe_allow_html=True)

    # Tabs for different data views
    tab1, tab2, tab3, tab4 = st.tabs(["💼 Deals", "👥 Leads", "✅ Tasks", "🤖 AI Assistant"])
    
    with tab1:
        show_deals_section(deals_data)
    
    with tab2:
        show_leads_section(leads_data)
    
    with tab3:
        show_tasks_section(tasks_data)
    
    with tab4:
        show_ai_chat_section(deals_data, leads_data, tasks_data)

def show_deals_section(deals_data):
    """Display deals data with filtering"""
    st.markdown("### 💼 Your Deals")
    
    if not deals_data or "Error" in str(deals_data):
        st.warning("No deals data available or error fetching data.")
        return
    
    if "No Data" in deals_data:
        st.info("No deals assigned to you.")
        return
    
    for owner, deals in deals_data.items():
        if deals:
            st.markdown(f"#### 👤 {owner} ({len(deals)} deals)")
            
            deals_df = pd.DataFrame(deals)
            st.dataframe(deals_df, use_container_width=True)
            
            # Export option
            csv = deals_df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download {owner}'s Deals",
                data=csv,
                file_name=f"{owner}_deals.csv",
                mime="text/csv"
            )

def show_leads_section(leads_data):
    """Display leads data with filtering"""
    st.markdown("### 👥 Your Leads")
    
    if not leads_data or "Error" in str(leads_data):
        st.warning("No leads data available or error fetching data.")
        return
    
    if "No Data" in leads_data:
        st.info("No leads assigned to you.")
        return
    
    for owner, leads in leads_data.items():
        if leads:
            st.markdown(f"#### 👤 {owner} ({len(leads)} leads)")
            
            leads_df = pd.DataFrame(leads)
            st.dataframe(leads_df, use_container_width=True)
            
            # Export option
            csv = leads_df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download {owner}'s Leads",
                data=csv,
                file_name=f"{owner}_leads.csv",
                mime="text/csv"
            )

def show_tasks_section(tasks_data):
    """Display tasks data with filtering"""
    st.markdown("### ✅ Your Tasks")
    
    if not tasks_data or "Error" in str(tasks_data):
        st.warning("No tasks data available or error fetching data.")
        return
    
    if "No Data" in tasks_data:
        st.info("No tasks assigned to you.")
        return
    
    for owner, tasks in tasks_data.items():
        if tasks:
            st.markdown(f"#### 👤 {owner} ({len(tasks)} tasks)")
            
            tasks_df = pd.DataFrame(tasks)
            st.dataframe(tasks_df, use_container_width=True)
            
            # Export option
            csv = tasks_df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download {owner}'s Tasks",
                data=csv,
                file_name=f"{owner}_tasks.csv",
                mime="text/csv"
            )

def show_ai_chat_section(deals_data, leads_data, tasks_data):
    """Enhanced AI Chat Assistant with user-specific data"""
    user_info = USERS[st.session_state.user]
    
    st.markdown("### 🤖 AI Sales Assistant")
    st.markdown(f"**AI insights for:** {user_info['name']} ({user_info['role'].title()})")
    
    # Chat History Display
    st.markdown("#### 💬 Chat History")
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)
    
    # Chat Input
    st.markdown("#### 💭 Ask Your AI Assistant")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask about your deals, leads, or tasks:",
            placeholder="e.g., 'What deals should I focus on today?' or 'Analyze my lead conversion rate'"
        )
    
    with col2:
        send_button = st.button("Send 🚀", use_container_width=True)
    
    # Quick Action Buttons
    st.markdown("#### ⚡ Quick Actions")
    quick_actions = st.columns(4)
    
    with quick_actions[0]:
        if st.button("📈 Analyze My Deals"):
            user_input = "Analyze my deals and provide insights on what I should focus on"
            send_button = True
    
    with quick_actions[1]:
        if st.button("🎯 Lead Opportunities"):
            user_input = "What are my best lead opportunities right now?"
            send_button = True
    
    with quick_actions[2]:
        if st.button("⏰ Urgent Tasks"):
            user_input = "What urgent tasks do I need to complete?"
            send_button = True
    
    with quick_actions[3]:
        if st.button("💡 Sales Tips"):
            user_input = "Give me actionable sales tips based on my current pipeline"
            send_button = True
    
    # Process chat input
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Generate AI response based on user's filtered data only
        with st.spinner("🤖 AI is analyzing your data..."):
            try:
                # Create context from user's filtered data
                context_data = {
                    "deals": deals_data,
                    "leads": leads_data, 
                    "tasks": tasks_data,
                    "user_name": user_info['name'],
                    "user_role": user_info['role']
                }
                
                # Get AI response with user-specific context
                ai_response = analyze_crm_data("comprehensive", context_data, user_input)
                
                # Add AI response to history
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                
                st.rerun()
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

def main():
    """Main application function"""
    init_session_state()
    
    if not st.session_state.authenticated:
        show_login()
    else:
        show_logout()
        show_dashboard()

if __name__ == "__main__":
    main()