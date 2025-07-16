import os
import streamlit as st
from groq import Groq
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleAI:
    """Groq Generative AI integration for CRM chatbot (keeps original class name for compatibility)."""

    def __init__(self):
        """Initialize Groq client"""
        self.client = None
        # Default Groq model – ultra-fast 8B Llama
        self.model = "llama-3.1-8b-instant"
        self._initialize_client()

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _initialize_client(self):
        """Instantiate a Groq client from env variable GROQ_API_KEY"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.warning("GROQ_API_KEY environment variable not found")
                st.warning("Groq API key not configured. AI features will be limited.")
                return

            # Initialise Groq client
            self.client = Groq(api_key=api_key)
            logger.info("Groq client initialised successfully")
        except Exception as e:
            logger.error(f"Failed to initialise Groq client: {str(e)}")
            st.error(f"Failed to initialise Groq AI: {str(e)}")
            self.client = None

    def _chat_complete(self, messages: list[dict]) -> str:
        """Small wrapper around chat.completions.create"""
        try:
            if not self.client:
                return "Sorry, I'm currently unable to connect to the AI service. Please check your API configuration."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                top_p=1,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq completion error: {str(e)}")
            return "I apologise, but I encountered an error while processing your request. Please try again."

    def _create_context(self, crm_data: dict, user_info: dict) -> dict:
        """Create context from CRM data (unchanged from original implementation)."""
        context = {
            'user_name': user_info.get('name', 'User'),
            'user_role': user_info.get('role', 'owner'),
            'total_leads': len(crm_data.get('leads', [])),
            'total_deals': len(crm_data.get('deals', [])),
            'total_tasks': len(crm_data.get('tasks', [])),
            'total_notes': len(crm_data.get('notes', [])),
        }
        # Summary stats
        summary = crm_data.get('summary', {})
        context.update({
            'total_deal_value': summary.get('total_deal_value', 0),
            'closed_deals': summary.get('closed_deals', 0),
            'closed_deal_value': summary.get('closed_deal_value', 0)
        })
        # Recent items
        if crm_data.get('leads'):
            context['recent_leads'] = crm_data['leads'][:3]
        if crm_data.get('deals'):
            context['recent_deals'] = crm_data['deals'][:3]
        if crm_data.get('tasks'):
            context['recent_tasks'] = crm_data['tasks'][:3]
        return context

    def _create_prompt(self, user_message: str, context: dict) -> list[dict]:
        """Build chat messages list for Groq model"""
        system_prompt = f"""
You are a helpful CRM AI assistant for {context['user_name']}. You have access to their CRM data and can help them with insights and suggestions.

User Information:
- Name: {context['user_name']}
- Role: {context['user_role']}

Current CRM Data Summary:
- Total Leads: {context['total_leads']}
- Total Deals: {context['total_deals']}
- Total Tasks: {context['total_tasks']}
- Total Notes: {context['total_notes']}
- Total Deal Value: ${context.get('total_deal_value', 0):,.2f}
- Closed Deals: {context.get('closed_deals', 0)}
- Closed Deal Value: ${context.get('closed_deal_value', 0):,.2f}

Instructions:
- Be conversational and helpful.
- Provide specific insights when possible.
- If asked about data you don't have access to, explain what you can see.
- Offer actionable recommendations.
- Keep responses concise but informative.
- Use emojis appropriately to make responses engaging.
- Focus on the user's specific data and context.
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

    # ------------------------------------------------------------------
    # Public interface – mirrors original GoogleAI methods
    # ------------------------------------------------------------------
    def generate_response(self, user_message: str, crm_data: dict, user_info: dict) -> str:
        context = self._create_context(crm_data, user_info)
        messages = self._create_prompt(user_message, context)
        return self._chat_complete(messages)

    def generate_summary(self, crm_data: dict, user_info: dict) -> str:
        context = self._create_context(crm_data, user_info)
        prompt = [
            {"role": "system", "content": "You are an AI assistant that summarises CRM data for busy professionals."},
            {"role": "user", "content": f"Please provide a concise but actionable summary based on the following metrics: {context}"},
        ]
        return self._chat_complete(prompt)

    def generate_insights(self, crm_data: dict, user_info: dict, focus_area: str | None = None) -> str:
        context = self._create_context(crm_data, user_info)
        focus = f" Focus specifically on: {focus_area}." if focus_area else ""
        prompt = [
            {"role": "system", "content": "You are a CRM analyst providing insights."},
            {"role": "user", "content": f"Analyse this CRM context and highlight opportunities, challenges, and recommended actions.{focus}\nContext: {context}"},
        ]
        return self._chat_complete(prompt)

    def generate_recommendations(self, crm_data: dict, user_info: dict, goal: str | None = None) -> str:
        context = self._create_context(crm_data, user_info)
        goal_text = f"The user's goal is: {goal}." if goal else ""
        prompt = [
            {"role": "system", "content": "You are a CRM consultant offering actionable recommendations."},
            {"role": "user", "content": f"{goal_text} Based on the following CRM data, provide specific recommendations to improve performance: {context}"},
        ]
        return self._chat_complete(prompt)

    def test_connection(self) -> tuple[bool, str]:
        """Quick ping to verify API connectivity"""
        try:
            if not self.client:
                return False, "Client not initialised"
            test_messages = [
                {"role": "system", "content": "You are a connection tester."},
                {"role": "user", "content": "Respond with 'Connection successful'"},
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=test_messages,
                max_tokens=5,
                temperature=0
            )
            if "Connection successful" in response.choices[0].message.content:
                return True, "✅ Connection successful"
            return True, "✅ Connection established"
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False, f"❌ Connection failed: {str(e)}"


# ------------------------------------------------------------------
# Streamlit-level convenience wrappers (kept for compatibility)
# ------------------------------------------------------------------
@st.cache_resource
def get_ai_client():
    return GoogleAI()


def initialize_ai():
    return get_ai_client()


def show_ai_status():
    ai = get_ai_client()
    with st.sidebar:
        st.markdown("### ⚡ Groq AI Status")
        if ai.client:
            st.success("✅ AI Connected (Groq)")
            if st.button("Test AI Connection"):
                with st.spinner("Testing connection..."):
                    success, message = ai.test_connection()
                    st.success(message) if success else st.error(message)
        else:
            st.error("❌ AI Disconnected")
            st.markdown("⚠️ Check your GROQ_API_KEY in environment variables")


def get_ai_response(user_message: str, crm_data: dict, user_info: dict) -> str:
    return get_ai_client().generate_response(user_message, crm_data, user_info)


def get_ai_summary(crm_data: dict, user_info: dict) -> str:
    return get_ai_client().generate_summary(crm_data, user_info)


def get_ai_insights(crm_data: dict, user_info: dict, focus: str | None = None) -> str:
    return get_ai_client().generate_insights(crm_data, user_info, focus)


def get_ai_recommendations(crm_data: dict, user_info: dict, goal: str | None = None) -> str:
    return get_ai_client().generate_recommendations(crm_data, user_info, goal)