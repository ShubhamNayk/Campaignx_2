import streamlit as st
from groq import Groq
from langfuse import observe, get_client
from tools import dynamic_api_executor

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

@observe()
def reporting_agent(campaign_id):
    """Fetches the report and cleanly logs the open/click rates directly into Langfuse!"""
    intent = f"Get the campaign report for campaign_id: {campaign_id}"
    report = dynamic_api_executor(client, intent)
    
    if "data" in report and len(report["data"]) > 0:
        data = report["data"]
        total = len(data)
        opens = sum(1 for r in data if r.get("EO") == "Y")
        clicks = sum(1 for r in data if r.get("EC") == "Y")
        open_rate = (opens/total)*100
        click_rate = (clicks/total)*100
        
        # --- THE LANGFUSE V3 MAGIC ---
        langfuse = get_client()
        langfuse.update_current_span(
            metadata={
                "Total Sent": total,
                "Total Opens": opens,
                "Total Clicks": clicks,
                "Open Rate (%)": round(open_rate, 1),
                "Click Rate (%)": round(click_rate, 1)
            }
        )
        
    return report