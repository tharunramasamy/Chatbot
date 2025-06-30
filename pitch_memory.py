import os
import logging
from dotenv import load_dotenv
from groq import Groq
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the Groq API client
try:
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    logger.info("Groq client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {e}")
    groq_client = None

class ChatAgent:
    """Enhanced AI Chat Agent using Groq API"""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.system_prompt = """You are OptiSale AI, an intelligent sales assistant and CRM expert. You help sales teams optimize their performance through data-driven insights.

Core Capabilities:
- Analyze CRM data (deals, leads, tasks) and provide actionable insights
- Identify sales opportunities and potential risks
- Suggest specific follow-up actions and strategies
- Provide sales forecasting and performance analysis
- Recommend process improvements and best practices

Analysis Framework:
When analyzing data, always consider:
1. **Performance Metrics**: Conversion rates, deal sizes, cycle times
2. **Opportunity Identification**: High-value prospects, warm leads, closing deals
3. **Risk Assessment**: Stalled deals, overdue tasks, unassigned leads
4. **Action Items**: Specific, time-bound recommendations
5. **Strategic Insights**: Patterns, trends, and optimization opportunities

Communication Style:
- Be conversational yet professional
- Use emojis to make responses engaging
- Provide specific, actionable recommendations
- Include relevant metrics and data points
- Ask clarifying questions when needed

Always focus on driving sales results and improving team performance."""

    def generate_response(self, query, context=None):
        """Generate an enhanced response using the Groq AI"""
        if not self.groq_client:
            return "🚫 AI capabilities are currently unavailable. Please check your Groq API configuration."
        
        try:
            # Prepare the messages for the API call
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add context if provided (for CRM data analysis)
            if context:
                messages.append({
                    "role": "system", 
                    "content": f"📊 CRM Data Context: {context}"
                })
            
            # Add the user query
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Make the API request with enhanced parameters
            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                temperature=0.7,
                max_tokens=1500,  # Increased for more detailed responses
                top_p=0.9,
                stream=False
            )
            
            # Extract and return the response
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return "🤔 I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"⚠️ I encountered an error while processing your request: {str(e)}"

    def analyze_crm_data(self, data_type, data, user_query):
        """Enhanced CRM data analysis with structured insights"""
        try:
            if not data or "Error" in str(data):
                return f"📭 No {data_type} data available for analysis. Please check your CRM connection."
            
            # Enhanced context for CRM analysis
            analysis_prompt = f"""
**CRM Data Analysis Request**

**Data Type**: {data_type}
**User Query**: "{user_query}"

**Instructions**:
Analyze the provided {data_type} data and provide:

1. **Key Performance Insights**
   - Current status and trends
   - Performance by owner/team member
   - Conversion rates and success metrics

2. **Opportunity Identification**
   - High-priority items requiring attention
   - Potential upselling/cross-selling opportunities
   - Warm prospects ready for follow-up

3. **Risk Assessment**
   - Stalled or at-risk items
   - Overdue tasks or activities
   - Unassigned or neglected records

4. **Action Recommendations**
   - Specific next steps for each team member
   - Priority items to focus on today/this week
   - Process improvements to implement

5. **Data Quality Insights**
   - Missing information that should be filled
   - Data consistency issues
   - Recommendations for better data hygiene

Please provide specific, actionable insights that will help the sales team improve performance.
"""
            
            # Prepare data summary for analysis
            data_summary = self._prepare_data_summary(data_type, data)
            
            return self.generate_response(
                analysis_prompt + f"\n\n**Data Summary**: {data_summary}",
                f"Analyzing {data_type} data for actionable sales insights"
            )
            
        except Exception as e:
            logger.error(f"Error analyzing CRM data: {e}")
            return f"⚠️ I encountered an error while analyzing the {data_type} data: {str(e)}"

    def _prepare_data_summary(self, data_type, data):
        """Prepare a structured summary of the CRM data"""
        try:
            if isinstance(data, dict):
                summary = f"**{data_type.title()} Overview:**\n"
                total_records = sum(len(records) for records in data.values() if isinstance(records, list))
                summary += f"- Total Records: {total_records}\n"
                summary += f"- Owners/Assignees: {len(data)}\n\n"
                
                # Owner breakdown
                summary += "**By Owner:**\n"
                for owner, records in data.items():
                    if isinstance(records, list):
                        summary += f"- {owner}: {len(records)} {data_type.lower()}\n"
                        
                        # Add sample record details for context
                        if records and len(records) > 0:
                            sample = records[0]
                            if data_type.lower() == "deals":
                                summary += f"  Sample: {sample.get('Deal Name', 'N/A')} - {sample.get('Stage', 'N/A')}\n"
                            elif data_type.lower() == "leads":
                                summary += f"  Sample: {sample.get('Lead Name', 'N/A')} - {sample.get('Lead Status', 'N/A')}\n"
                            elif data_type.lower() == "tasks":
                                summary += f"  Sample: {sample.get('Task Subject', 'N/A')} - {sample.get('Status', 'N/A')}\n"
                
                return summary[:1000]  # Limit summary length
            else:
                return f"Data format: {type(data)}, Content preview: {str(data)[:200]}..."
                
        except Exception as e:
            logger.error(f"Error preparing data summary: {e}")
            return f"Data preview: {str(data)[:200]}..."

    def get_sales_insights(self, deals_data, leads_data, tasks_data):
        """Generate comprehensive sales insights from all CRM data"""
        try:
            insight_prompt = """
**Comprehensive Sales Performance Analysis**

Please analyze the complete CRM dataset and provide:

1. **Overall Sales Performance**
   - Pipeline health and velocity
   - Conversion rates across the funnel
   - Revenue trends and forecasting

2. **Team Performance Analysis**
   - Top performers and their success factors
   - Areas where team members need support
   - Workload distribution and balance

3. **Strategic Recommendations**
   - Immediate actions to boost performance
   - Process improvements to implement
   - Training or resource needs identified

4. **Predictive Insights**
   - Deals likely to close this quarter
   - Leads ready for promotion to opportunities
   - Resource allocation recommendations

Provide specific, actionable recommendations that will drive results.
"""
            
            # Combine all data for comprehensive analysis
            combined_context = f"""
Deals Data: {str(deals_data)[:800]}...
Leads Data: {str(leads_data)[:800]}...
Tasks Data: {str(tasks_data)[:800]}...
"""
            
            return self.generate_response(insight_prompt, combined_context)
            
        except Exception as e:
            logger.error(f"Error generating sales insights: {e}")
            return f"⚠️ Error generating comprehensive insights: {str(e)}"

# Enhanced standalone functions
def chat_with_ai(query, context=None):
    """Enhanced function to interact with the AI agent"""
    try:
        if not groq_client:
            return "🚫 AI service is not available. Please check your Groq API configuration."
        
        agent = ChatAgent(groq_client)
        return agent.generate_response(query, context)
        
    except Exception as e:
        logger.error(f"Error in chat_with_ai: {e}")
        return f"⚠️ Sorry, I encountered an error: {str(e)}"

def analyze_crm_data(data_type, data, user_query):
    """Enhanced CRM data analysis with AI insights"""
    try:
        if not groq_client:
            return "🚫 AI analysis is not available. Please check your Groq API configuration."
        
        agent = ChatAgent(groq_client)
        return agent.analyze_crm_data(data_type, data, user_query)
        
    except Exception as e:
        logger.error(f"Error in analyze_crm_data: {e}")
        return f"⚠️ Sorry, I encountered an error analyzing the data: {str(e)}"

def get_comprehensive_insights(deals_data, leads_data, tasks_data):
    """Get comprehensive sales insights from all CRM data"""
    try:
        if not groq_client:
            return "🚫 AI insights are not available. Please check your Groq API configuration."
        
        agent = ChatAgent(groq_client)
        return agent.get_sales_insights(deals_data, leads_data, tasks_data)
        
    except Exception as e:
        logger.error(f"Error getting comprehensive insights: {e}")
        return f"⚠️ Error generating insights: {str(e)}"