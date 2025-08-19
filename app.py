import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
from zoho_crm import get_crm_summary, test_connection
from google_ai import get_ai_response, get_ai_summary

# ---- Configuration ----
load_dotenv()
USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "Admin User", "owner_name": "All"},
    "RajaMurugavelu": {"password": "rajamurugavelu123", "role": "owner", "name": "Raja Murugavelu", "owner_name": "Raja Murugavelu"},
    "KumaranV": {"password": "kumaranv123", "role": "owner", "name": "Kumaran V", "owner_name": "Kumaran V"},
    "SoniyaM": {"password": "soniyam123", "role": "owner", "name": "Soniya M", "owner_name": "Soniya M"},
    "DineshKumar": {"password": "dineshkumar123", "role": "owner", "name": "Dinesh Kumar", "owner_name": "Dinesh Kumar"},
    "Presales": {"password": "presales123", "role": "owner", "name": "Presales", "owner_name": "Presales"},
    "VishnuBhagavath": {"password": "vishnubhagavath123", "role": "owner", "name": "Vishnu Bhagavath", "owner_name": "Vishnu Bhagavath"},
    "ManojR": {"password": "manojr123", "role": "owner", "name": "Manoj R", "owner_name": "Manoj R"},
    "PraveenMuthumasaran": {"password": "praveenmuthumasaran123", "role": "owner", "name": "Praveen Muthumasaran", "owner_name": "Praveen Muthumasaran"},
    "RamKumar": {"password": "ramkumar123", "role": "owner", "name": "Ram Kumar", "owner_name": "Ram Kumar"},
    "HarishAravindhan": {"password": "harisharavindhan123", "role": "owner", "name": "Harish Aravindhan", "owner_name": "Harish Aravindhan"},
    "SteffinaD": {"password": "steffinad123", "role": "owner", "name": "Steffina D", "owner_name": "Steffina D"}
}

st.set_page_config(page_title="OptiAI Dashboard", layout="wide", initial_sidebar_state="expanded")

def show_sidebar(user_info):
    st.sidebar.markdown("<h1 style='font-size:48px;color:#06b6d4;text-align:center;'>OptiAI</h1>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='font-size:18px;color:#374151;'>👤 <b>{user_info.get('name','User')}</b></p>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='color:#6b7280;'>Role: <b>{user_info.get('role', '').title()}</b></p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.pop("authenticated", None)
        st.session_state.pop("user_info", None)
        st.session_state.pop("crm_data", None)
        st.session_state.pop("chat_history", None)
        st.rerun()

def authenticate_user(username, password):
    user = USERS.get(username)
    return user if user and user["password"] == password else None

def show_login():
    st.markdown("<h2 style='text-align:center;color:#06b6d4;'>Welcome to OptiAI CRM Dashboard</h2>", unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user = authenticate_user(username, password)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["user_info"] = user
                st.success(f"Welcome {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    show_login()
    st.stop()

user_info = st.session_state["user_info"]
show_sidebar(user_info)

def filter_items(items, key, owner_name, is_admin):
    if is_admin or owner_name == "All":
        return items
    return [item for item in items if item.get(key) == owner_name]

# ---- Tabs ----
tabs = st.tabs(["🤖 AI Chatbox", "📊 CRM Dashboard"])

# ---- AI Chatbot Tab ----
with tabs[0]:
    st.markdown("<h2 style='color:#06b6d4;'>OptiAI Chatbox</h2>", unsafe_allow_html=True)
    st.info("Chat directly with your CRM AI assistant. Ask anything about your data, deals, leads, notes, or get insights and recommendations!")
    if "crm_data" not in st.session_state:
        with st.spinner("Connecting to CRM..."):
            connection_ok, msg = test_connection()
            if not connection_ok:
                st.error(f"CRM Connection Error: {msg}")
                st.stop()
            else:
                owner_name = user_info.get("owner_name", "All")
                st.session_state.crm_data = get_crm_summary(owner_name)
    crm_data = st.session_state.crm_data

    is_admin = user_info.get("role", "").lower() == "admin"
    owner_name = user_info.get("owner_name", "All")
    deals = filter_items(crm_data.get("deals", []), "Deal Owner", owner_name, is_admin)
    leads = filter_items(crm_data.get("leads", []), "Lead Owner", owner_name, is_admin)
    tasks = filter_items(crm_data.get("tasks", []), "Task Owner", owner_name, is_admin)
    notes = filter_items(crm_data.get("notes", []), "Note Owner", owner_name, is_admin)

    filtered_crm_data = dict(crm_data)
    filtered_crm_data["deals"] = deals
    filtered_crm_data["leads"] = leads
    filtered_crm_data["tasks"] = tasks
    filtered_crm_data["notes"] = notes

    chat_history = st.session_state.get("chat_history", [])
    for role, message in chat_history:
        if role == "user":
            st.markdown(f"<div style='background:#dbeafe;padding:10px;border-radius:8px;text-align:right;margin-bottom:4px;'>{message}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#e7f5e6;padding:10px;border-radius:8px;margin-bottom:4px;'>{message}</div>", unsafe_allow_html=True)
    user_msg = st.text_input("Type your question for OptiAI...", key="chat_input")
    if st.button("Send", use_container_width=True):
        if user_msg:
            chat_history.append(("user", user_msg))
            st.session_state.chat_history = chat_history
            with st.spinner("OptiAI is thinking..."):
                ai_resp = get_ai_response(user_msg, filtered_crm_data, user_info)
            chat_history.append(("ai", ai_resp))
            st.session_state.chat_history = chat_history
            st.rerun()
    st.markdown("---")
    if st.button("Clear Chat History"):
        st.session_state["chat_history"] = []
        st.rerun()

# ---- Dashboard Tab ----
with tabs[1]:
    st.markdown("<h2 style='color:#06b6d4;'>📊 CRM Dashboard</h2>", unsafe_allow_html=True)
    st.write("All CRM data in a single powerful dashboard.")

    crm_data = st.session_state.crm_data
    is_admin = user_info.get("role", "").lower() == "admin"
    owner_name = user_info.get("owner_name", "All")
    deals = filter_items(crm_data.get("deals", []), "Deal Owner", owner_name, is_admin)
    leads = filter_items(crm_data.get("leads", []), "Lead Owner", owner_name, is_admin)
    tasks = filter_items(crm_data.get("tasks", []), "Task Owner", owner_name, is_admin)
    notes = filter_items(crm_data.get("notes", []), "Note Owner", owner_name, is_admin)

    closed_stage_keys = ["won", "closedwon", "closed_won", "closed won"]
    def is_closed_won(stage_val):
        if not isinstance(stage_val, str):
            return False
        cleaned = stage_val.replace(" ", "").replace("_", "").lower()
        return cleaned in closed_stage_keys or cleaned == "won"
    closed_deals_df = pd.DataFrame([d for d in deals if is_closed_won(str(d.get("Stage", "")))]) if deals else pd.DataFrame([])
    closed_deals_count = closed_deals_df.shape[0]
    closed_deal_value = closed_deals_df["Amount"].apply(lambda x: x if x is not None else 0).sum() if "Amount" in closed_deals_df.columns else 0

    total_deal_value = sum((d.get('Amount') or 0) for d in deals)  # <<< FIXED LINE

    metrics = [
        ("Total Deals", len(deals), "💼"),
        ("Total Leads", len(leads), "🧑‍💻"),
        ("Total Tasks", len(tasks), "📋"),
        ("Total Notes", len(notes), "🗒️"),
        ("Deal Value (₹)", f"{total_deal_value:,.2f}", "💰"),
        ("Closed/Won Deals", closed_deals_count, "✅"),
        ("Closed Deal Value (₹)", f"{closed_deal_value:,.2f}", "🏆"),
    ]
    cols = st.columns(4)
    for i, (label, val, icon) in enumerate(metrics):
        with cols[i % 4]:
            st.markdown(f"<div style='background:#e0f2fe;padding:16px;border-radius:12px;text-align:center;margin-bottom:8px;'>\
                <span style='font-size:32px;'>{icon}</span><br>\
                <span style='color:#0369a1;font-size:18px;'>{label}</span><br>\
                <span style='font-size:24px;font-weight:bold;color:#0e7490;'>{val}</span>\
                </div>", unsafe_allow_html=True)

    # --- Deals Table & Visualization ---
    st.markdown("### All Deals Table")
    if deals:
        df_deals = pd.DataFrame(deals)
        st.dataframe(df_deals[["Deal Name", "Deal Owner", "Account Name", "Amount", "Stage", "Tags", "Closing Date"]].fillna(""), hide_index=True)
        deal_stages = df_deals["Stage"].value_counts().reset_index()
        deal_stages.columns = ["Stage", "count"]
        fig_stage = px.pie(deal_stages, names="Stage", values="count", title="Deals by Stage")
        st.plotly_chart(fig_stage, use_container_width=True)
        owner_amount = df_deals.groupby("Deal Owner")["Amount"].sum().reset_index()
        fig_owner = px.bar(owner_amount, x="Deal Owner", y="Amount", color="Deal Owner", title="Deal Value by Owner")
        st.plotly_chart(fig_owner, use_container_width=True)
        st.markdown("#### Won/Closed Deals (includes 'Won' or 'Closed Won')")
        if closed_deals_df.shape[0] > 0:
            st.dataframe(closed_deals_df[["Deal Name", "Deal Owner", "Amount", "Stage", "Tags", "Closing Date"]].fillna(""), hide_index=True)
        else:
            st.info("No Won/Closed deals found.")
    else:
        st.info("No deals found.")

    st.markdown("### All Leads Table")
    if leads:
        df_leads = pd.DataFrame(leads)
        st.dataframe(df_leads[["Lead Name", "Lead Owner", "Company", "Email", "Phone", "Lead Status", "Lead Source", "Tags"]].fillna(""), hide_index=True)
        lead_status = df_leads["Lead Status"].value_counts().reset_index()
        lead_status.columns = ["Lead Status", "count"]
        fig_leads = px.bar(lead_status, x="Lead Status", y="count", color="Lead Status", text="count", title="Leads by Status")
        st.plotly_chart(fig_leads, use_container_width=True)
    else:
        st.info("No leads found.")

    st.markdown("### All Tasks Table")
    if tasks:
        df_tasks = pd.DataFrame(tasks)
        st.dataframe(df_tasks[["Task Subject", "Task Owner", "Status", "Priority", "Due Date", "Related To", "Start Date"]].fillna(""), hide_index=True)
    else:
        st.info("No tasks found.")

    st.markdown("### All Notes Table")
    if notes:
        df_notes = pd.DataFrame(notes)
        show_cols = ["Note Title", "Note Content", "Note Owner", "Created By", "Parent Module", "Parent Record", "Created Time"]
        st.dataframe(df_notes[show_cols].fillna(""), hide_index=True)
    else:
        st.info("No notes found.")

    st.markdown("### Tags Used in Deals & Leads")
    deal_tags_list = [tag for d in deals for tag in d.get("Tags", []) if tag]
    lead_tags_list = [tag for l in leads for tag in l.get("Tags", []) if tag]
    all_tags = pd.Series(deal_tags_list + lead_tags_list)
    if not all_tags.empty:
        tag_counts = all_tags.value_counts()
        fig_tags = px.bar(tag_counts, x=tag_counts.index, y=tag_counts.values, title="Tag Usage in Deals & Leads")
        st.plotly_chart(fig_tags, use_container_width=True)
        st.write("Top Tags:", ', '.join([str(tag) for tag in tag_counts.index[:10]]))
    else:
        st.info("No tags found in deals or leads.")