import streamlit as st
from groq import Groq
from langfuse import observe
from tools import dynamic_api_executor

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

@observe()
def execution_agent(subject, body, customer_ids, send_time):
    intent = "Schedule an email campaign"
    payload_data = {
        "subject": subject,
        "body": body,
        "list_customer_ids": customer_ids,
        "send_time": send_time
    }
    return dynamic_api_executor(client, intent, payload_data)