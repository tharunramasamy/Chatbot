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
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #d62728;
        --background-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Custom styling for the app */
    .main-header {
        background: var(--background-gradient);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
    }

    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .user-message {
        background: var(--primary-color);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .ai-message {
        background: white;
        color: #333;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        margin-right: 20%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 3px solid var(--secondary-color);
    }

    .data-table {
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .sidebar .stButton > button {
        width: 100%;
        background: var(--background-gradient);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        padding: 0 20px;
    }

    .stTabs [aria-selected="true"] {
        background: var(--background-gradient);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "Admin User"},
    "Manoj R": {"password": "manoj123", "role": "owner", "name": "Manoj R"},
    "demo": {"password": "demo123", "role": "user", "name": "Demo User"}
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
        <h1>OptiSale.AI</h1>
        <h3>Intelligent Sales Assistant</h3>
        <p>Your AI-powered CRM companion for smarter sales insights</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown("### Secure Login")
            with st.form("login_form"):
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.form_submit_button("Login", use_container_width=True):
                        if username in USERS and USERS[username]["password"] == password:
                            st.session_state.authenticated = True
                            st.session_state.user = USERS[username]
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")

                with col_b:
                    st.form_submit_button("Demo Info", use_container_width=True)

            with st.expander("Demo Credentials"):
                st.code("Username: demo\nPassword: demo123")

def create_metric_card(title, value, delta=None, delta_color="normal"):
    """Create a styled metric card"""
    delta_html = ""
    if delta:
        color = "green" if delta_color == "normal" else "red"
        delta_html = f'<div style="color: {color}; font-size: 0.8rem;">△ {delta}</div>'

    return f"""
    <div class="metric-card">
        <h4 style="margin: 0; color: var(--primary-color);">{title}</h4>
        <h2 style="margin: 0.5rem 0; color: #333;">{value}</h2>
        {delta_html}
    </div>
    """

def display_data_table(data, title, key_prefix):
    """Display data in an enhanced table format"""
    if not data or "Error" in data:
        st.warning(f"No {title.lower()} data available or error occurred")
        return

    st.markdown(f"{title} Overview")

    # Owner selection filter
    owners = list(data.keys())
    selected_owner = st.selectbox(f"Filter by Owner ({title})", ["All"] + owners, key=f"{key_prefix}_owner")

    # Display data based on selection
    if selected_owner == "All":
        for owner, items in data.items():
            if items:  # Only show if there are items
                with st.expander(f"👤 {owner} ({len(items)} {title.lower()})"):
                    df = pd.DataFrame(items)
                    st.dataframe(df, use_container_width=True)
    else:
        if selected_owner in data and data[selected_owner]:
            st.markdown(f"#### 👤 {selected_owner}")
            df = pd.DataFrame(data[selected_owner])
            st.dataframe(df, use_container_width=True)

            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label=f"Download {title} Data",
                data=csv,
                file_name=f"{title.lower()}_{selected_owner.replace(' ', '_')}.csv",
                mime="text/csv"
            )
        else:
            st.info(f"No {title.lower()} found for {selected_owner}")

def create_owner_distribution_chart(data, title):
    """Create a pie chart showing distribution by owner"""
    if not data or "Error" in data:
        return None

    owner_counts = {owner: len(items) for owner, items in data.items()}

    if owner_counts:
        fig = px.pie(
            values=list(owner_counts.values()),
            names=list(owner_counts.keys()),
            title=f"{title} Distribution by Owner"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    return None

def enhanced_chat_interface():
    """Enhanced chatbot interface with better styling"""
    st.markdown("""
    <div class="main-header">
        <h2>AI Sales Assistant</h2>
        <p>Get intelligent insights about your CRM data</p>
    </div>
    """, unsafe_allow_html=True)

    # Chat history display
    chat_container = st.container()

    with chat_container:
        if st.session_state.chat_history:
            for i, (user_msg, ai_msg) in enumerate(st.session_state.chat_history):
                st.markdown(f"""
                <div class="chat-container">
                    <div class="user-message">
                        <strong>You:</strong> {user_msg}
                    </div>
                    <div class="ai-message">
                        <strong>🤖 OptiSale AI:</strong> {ai_msg}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="chat-container">
                <div class="ai-message">
                    <strong>OptiSale AI:</strong> Hello! I'm your intelligent sales assistant. 
                    I can help you analyze your CRM data, provide insights about deals, leads, and tasks. 
                    What would you like to know?
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Chat input
    st.markdown("Ask me anything about your sales data:")

    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("", placeholder="E.g., 'Show me lead conversion insights' or 'What deals need attention?'", key="chat_input")
    with col2:
        send_button = st.button("📤 Send", use_container_width=True)

    # Quick action buttons
    st.markdown("####  Quick Actions:")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Analyze Deals", use_container_width=True):
            user_input = "Analyze my deals data and provide insights"
            send_button = True

    with col2:
        if st.button("Lead Insights", use_container_width=True):
            user_input = "Give me insights about leads performance"
            send_button = True

    with col3:
        if st.button("Task Analysis", use_container_width=True):
            user_input = "Analyze my tasks and priorities"
            send_button = True

    with col4:
        if st.button("Sales Tips", use_container_width=True):
            user_input = "Give me sales strategy recommendations"
            send_button = True

    # Process chat input
    if send_button and user_input:
        with st.spinner("Thinking..."):
            # Get relevant CRM data based on query
            context = ""
            if any(word in user_input.lower() for word in ["deal", "deals"]):
                deals = get_deals()
                context += f"Deals data: {str(deals)[:500]}..."

            if any(word in user_input.lower() for word in ["lead", "leads"]):
                leads = get_leads()
                context += f"Leads data: {str(leads)[:500]}..."

            if any(word in user_input.lower() for word in ["task", "tasks"]):
                tasks = get_tasks()
                context += f"Tasks data: {str(tasks)[:500]}..."

            # Get AI response
            ai_response = chat_with_ai(user_input, context)

            # Add to chat history
            st.session_state.chat_history.append((user_input, ai_response))
            st.rerun()

def main_interface():
    """Enhanced main application interface"""
    # Sidebar
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h2> OptiSale.AI</h2>
        <p>Welcome, <strong>{}</strong>!</p>
    </div>
    """.format(st.session_state.user['name']), unsafe_allow_html=True)

    st.sidebar.markdown("---")

    if st.sidebar.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.sidebar.button("New Chat", key="new_chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    show_logout()

    # Main content with enhanced tabs
    tab2, tab1 = st.tabs(["AI Assistant", "Dashboard"])

    # Dashboard Tab
    with tab1:
        st.markdown("""
        <div class="main-header">
            <h1>Sales Dashboard</h1>
            <p>Comprehensive overview of your CRM performance</p>
        </div>
        """, unsafe_allow_html=True)

        # Load data with caching
        @st.cache_data(ttl=300)  # Cache for 5 minutes
        def load_crm_data():
            return {
                'deals': get_deals(),
                'leads': get_leads(), 
                'tasks': get_tasks(),
                'stats': get_summary_stats()
            }

        with st.spinner("Loading CRM data..."):
            crm_data = load_crm_data()

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            deals_count = crm_data['stats'].get('total_deals', 0)
            st.markdown(create_metric_card(" Total Deals", deals_count), unsafe_allow_html=True)

        with col2:
            leads_count = crm_data['stats'].get('total_leads', 0)
            st.markdown(create_metric_card(" Total Leads", leads_count), unsafe_allow_html=True)

        with col3:
            tasks_count = crm_data['stats'].get('total_tasks', 0)
            st.markdown(create_metric_card(" Total Tasks", tasks_count), unsafe_allow_html=True)

        with col4:
            total_owners = len(set(
                list(crm_data['stats'].get('deals_by_owner', {}).keys()) +
                list(crm_data['stats'].get('leads_by_owner', {}).keys()) +
                list(crm_data['stats'].get('tasks_by_owner', {}).keys())
            ))
            st.markdown(create_metric_card(" Active Owners", total_owners), unsafe_allow_html=True)

        # Charts row
        if crm_data['deals'] and "Error" not in crm_data['deals']:
            col1, col2 = st.columns(2)

            with col1:
                deals_chart = create_owner_distribution_chart(crm_data['deals'], "Deals")
                if deals_chart:
                    st.plotly_chart(deals_chart, use_container_width=True)

            with col2:
                leads_chart = create_owner_distribution_chart(crm_data['leads'], "Leads")
                if leads_chart:
                    st.plotly_chart(leads_chart, use_container_width=True)

        # Data tables
        st.markdown("---")

        # Enhanced data display
        data_tab1, data_tab2, data_tab3 = st.tabs([" Deals", " Leads", " Tasks"])

        with data_tab1:
            display_data_table(crm_data['deals'], "Deals", "deals")

        with data_tab2:
            display_data_table(crm_data['leads'], "Leads", "leads")

        with data_tab3:
            display_data_table(crm_data['tasks'], "Tasks", "tasks")

    # AI Assistant Tab
    with tab2:
        enhanced_chat_interface()

def main():
    """Main application entry point"""
    init_session_state()

    if not st.session_state.authenticated:
        show_login()
    else:
        main_interface()

if __name__ == "__main__":
    main()