import os
import logging
from dotenv import load_dotenv
from groq import Groq

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
    """AI Chat Agent using Groq API"""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.system_prompt = """You are OptiSale AI, an intelligent sales assistant that helps with CRM data analysis and sales insights. 

Key capabilities:
- Analyze sales data, deals, leads, and tasks
- Provide actionable sales insights and recommendations
- Suggest follow-up actions based on CRM data
- Help with sales strategy and customer relationship management

When analyzing CRM data:
1. Focus on actionable insights
2. Identify potential opportunities
3. Suggest specific follow-up actions
4. Highlight urgent items that need attention
5. Provide clear, concise recommendations

Always be helpful, professional, and focused on driving sales results."""

    def generate_response(self, query, context=None):
        """Generate a response using the Groq AI"""
        if not self.groq_client:
            return " AI capabilities are currently unavailable. Please check your Groq API configuration."
        
        try:
            # Prepare the messages for the API call
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add context if provided (for CRM data analysis)
            if context:
                messages.append({
                    "role": "system", 
                    "content": f"Additional context: {context}"
                })
            
            # Add the user query
            messages.append({
                "role": "user", 
                "content": query
            })
            
            # Make the API request
            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",  # You can change this model as needed
                messages=messages,
                temperature=0.7,  # Adjust for creativity vs accuracy
                max_tokens=1024,  # Adjust as needed
                top_p=1,
                stream=False
            )
            
            # Extract and return the response
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return "I apologize, but I couldn't generate a proper response. Please try again."
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f" Sorry, I encountered an error while processing your request: {str(e)}"

    def analyze_crm_data(self, data_type, data, user_query):
        """Analyze CRM data and provide insights"""
        try:
            if not data:
                return f"No {data_type} data available for analysis."
            
            # Create context for CRM analysis
            context = f"""
            You are analyzing {data_type} data from a CRM system. 
            The user asked: "{user_query}"
            
            Based on this data, provide:
            1. Key insights and patterns
            2. Actionable recommendations
            3. Priority items that need immediate attention
            4. Suggested follow-up actions
            5. Opportunities for improvement
            
            Keep your response focused and actionable.
            """
            
            # Generate analysis
            analysis_query = f"Analyze this {data_type} data and provide insights: {str(data)[:1000]}..."  # Limit data size
            return self.generate_response(analysis_query, context)
            
        except Exception as e:
            logger.error(f"Error analyzing CRM data: {e}")
            return f"I encountered an error while analyzing the {data_type} data: {str(e)}"

def chat_with_ai(query, context=None):
    """Function to interact with the AI agent"""
    try:
        if not groq_client:
            return " AI service is not available. Please check your API configuration."
        
        agent = ChatAgent(groq_client)
        return agent.generate_response(query, context)
        
    except Exception as e:
        logger.error(f"Error in chat_with_ai: {e}")
        return f" Sorry, I encountered an error: {str(e)}"

def analyze_crm_data(data_type, data, user_query):
    """Analyze CRM data with AI insights"""
    try:
        if not groq_client:
            return " AI analysis is not available. Please check your API configuration."
        
        agent = ChatAgent(groq_client)
        return agent.analyze_crm_data(data_type, data, user_query)
        
    except Exception as e:
        logger.error(f"Error in analyze_crm_data: {e}")
        return f" Sorry, I encountered an error analyzing the data: {str(e)}"
