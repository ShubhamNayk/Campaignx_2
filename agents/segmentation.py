import json
import streamlit as st
from groq import Groq
from langfuse import observe

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

@observe()
def segmentation_agent(brief, sample_customer_data):
    """Generates dynamic Python scoring logic to rank customers."""
    system_prompt = f"""
    You are an expert Data Segmentation AI.
    Read the marketing brief and write a Python expression to score a customer from 0 to 100.
    Higher scores mean the customer is a better fit for the campaign.
    
    Here is ONE sample customer dictionary to show you the keys available:
    {json.dumps(sample_customer_data)}
    
    RULES:
    1. Assume the dictionary variable is named `c`.
    2. Write ONLY a valid single-line Python expression that evaluates to an integer/float.
    3. Example: 100 if c.get('age', 0) >= 60 and c.get('gender') == 'F' else (50 if c.get('age', 0) >= 60 else 0)
    4. Return JSON format: {{"scoring_logic": "your python expression here", "strategy": "why you wrote this"}}
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Brief: {brief}"}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

@observe()
def rank_and_select_customers(logic, all_customers, limit=1000):
    """
    Evaluates the AI's logic against the database, ranks the customers, 
    and logs the final target list to Langfuse for auditing.
    """
    scored_customers = []
    for c in all_customers:
        try:
            score = eval(logic, {"c": c})
            scored_customers.append((score, c["customer_id"]))
        except Exception:
            scored_customers.append((0, c["customer_id"]))
    
    # Sort highest score to lowest
    scored_customers.sort(key=lambda x: x[0], reverse=True)
    
    # Slice the top 'limit' most affected people
    top_ids = [cid for score, cid in scored_customers[:limit]]
    
    # Returning this sends the final array of IDs straight to Langfuse!
    return top_ids