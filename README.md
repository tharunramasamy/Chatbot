# **README – Sales Support Chatbot**

**Project Title:**
Sales Enablement Chatbot Using Python and Large Language Model

**Developed By:**
Tharunbalaaje R, Data Analyst , OptiSol Business Solutions

---

## **Project Overview**

This chatbot was developed to assist the Business Development Representatives (BDRs) in improving their workflow efficiency. It enables BDRs to quickly retrieve information about client follow-ups, pending proposals, past interactions, and common queries, without the need to manually search through documents or CRM systems. The chatbot leverages Python, an LLM (Large Language Model), and the LangChain framework to provide natural language responses that are accurate and contextually relevant.

---

## **Key Features**

* Responds to frequently asked questions (FAQs) related to proposals, meetings, follow-ups, and sales resources
* Integrated with internal proposal and follow-up data sources via Pandas and CSV/Excel
* Uses GPT-based Large Language Model for high-quality, human-like responses
* Supports quick retrieval of pending proposal status and contact history
* Generates draft emails or follow-up messages on request
* Front-end built with Streamlit for a simple, web-based interface
* Secured with role-based authentication to protect sensitive data

---

## **File Structure**

```
Chatbot/
│
├── app.py
├── pitch_memeory.py
├── test.py
├── zoho_utiles.py 
├── data/
│   ├── proposals.csv
│   ├── followups.csv
│
├── requirements.txt
└── README.md
```
app.py: This is the main Streamlit application that launches the chatbot interface and handles user interactions through the web interface.

pitch_memory.py: Contains code to manage the chatbot’s memory, including secure handling of API keys for Groq and OpenAI, as well as logic to store or recall conversation context across multiple user sessions.

test.py: A simple testing script for validating chatbot queries, data extraction functions, and ensuring the LLM prompts respond as expected before deployment.

zoho_utiles.py: Provides utility functions to connect to Zoho CRM, allowing the chatbot to fetch and update live proposal data and follow-up details directly from the CRM system.
---

## **How to Run**

1. **Set up your environment**

   * Install Python 3.10+
   * Install dependencies:

     ```bash
     pip install -r requirements.txt
     ```

2. **Launch the chatbot**

   ```bash
   streamlit run chatbot_app.py
   ```

3. The chatbot interface will open in your browser at `http://localhost:8501`, where you can start asking queries.

---

## **Usage**

* Type a question in natural language, for example:
  *“Show me my pending proposals for this week”*
  or
  *“When was my last follow-up with Client ABC?”*

* The chatbot will process the query, retrieve relevant data, and generate an appropriate response using the language model.

---

## **Security Note**

This chatbot is designed for internal BDR use only. Please ensure that proposal and client data files are stored securely and that role-based permissions are properly configured if deployed to production.

---

## **Contact**

For questions, feedback, or contributions, please reach out to \ OptiSol sales 
