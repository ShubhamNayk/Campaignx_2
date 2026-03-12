import requests
import json
import streamlit as st
from langfuse import observe

HACKATHON_API_KEY = st.secrets["HACKATHON_API_KEY"]

API_DOCS = """
API Documentation for CampaignX:
1. Get Cohort: GET https://campaignx.inxiteout.ai/api/v1/get_customer_cohort. Headers: X-API-Key.
2. Send Campaign: POST https://campaignx.inxiteout.ai/api/v1/send_campaign. Headers: X-API-Key, Content-Type: application/json. Payload requires: "subject", "body", "list_customer_ids", "send_time" (format: DD:MM:YY HH:MM:SS).
3. Get Report: GET https://campaignx.inxiteout.ai/api/v1/get_report?campaign_id=<id>. Headers: X-API-Key.
"""

@observe()
def dynamic_api_executor(llm_client, intent, payload_data=None):
    """The LLM reads the API docs and formulates the request dynamically."""
    system_prompt = f"""
    You are an API Execution Agent. 
    Read the following API documentation:
    {API_DOCS}
    
    Based on the user's intent, formulate the exact HTTP request required.
    Return ONLY a JSON object with:
    "url": the endpoint
    "method": "GET" or "POST"
    "headers": dictionary of headers (Include Content-Type if POST)
    "json_payload": dictionary of the body (if POST) or null
    """
    
    # TOKEN LIMIT FIX: Hide the massive array from the LLM
    safe_payload = None
    if payload_data:
        safe_payload = payload_data.copy()
        if "list_customer_ids" in safe_payload:
            safe_payload["list_customer_ids"] = ["ID_1", "ID_2", "...[TRUNCATED]"]
    
    user_prompt = f"Intent: {intent}\nAvailable Data: {json.dumps(safe_payload) if safe_payload else 'None'}"
    
    response = llm_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    request_details = json.loads(response.choices[0].message.content)
    
    headers = request_details.get("headers", {})
    headers["X-API-Key"] = HACKATHON_API_KEY
    
    method = request_details.get("method", "GET").upper()
    url = request_details.get("url")
    payload = request_details.get("json_payload")
    
    # TOKEN LIMIT FIX: Restore the massive array before sending to the real API
    if method == "POST" and payload and payload_data and "list_customer_ids" in payload_data:
        payload["list_customer_ids"] = payload_data["list_customer_ids"]
    
    if method == "GET":
        api_resp = requests.get(url, headers=headers)
    elif method == "POST":
        api_resp = requests.post(url, headers=headers, json=payload)
    else:
        return {"error": "Invalid method"}
        
    return api_resp.json() if api_resp.status_code == 200 else {"error": api_resp.text}