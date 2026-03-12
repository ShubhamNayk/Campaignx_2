import json
import streamlit as st
from groq import Groq
from langfuse import observe

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

@observe()
def content_generation_agent(brief, feedback=""):
    system_prompt = f"""
    You are an expert Email Marketing Copywriter.
    STRICT RULES:
    1. The email body MUST contain this exact URL: https://superbfsi.com/xdeposit/explore/
    2. Use emojis appropriately.
    3. Use markdown for font variations (**bold**, *italics*).
    4. Provide ONLY a valid JSON output with "subject_line", "email_body", and "strategy_reasoning".
    {feedback}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Brief: {brief}"}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


@observe()
def optimizer_agent_bulk(brief, original_subject, open_rate, click_rate, human_guidance=""):
    """
    Generates 5 completely different optimized email variants in one call.
    Returns a list of 5 dicts: [{subject_line, email_body, strategy_reasoning, variant_label}]
    """
    system_prompt = f"""
    You are an expert Campaign Optimizer Agent.
    Previous campaign data:
    - Brief: {brief}
    - Previous Subject: {original_subject}
    - Open Rate: {open_rate}%
    - Click Rate: {click_rate}%
    - Human Directive: "{human_guidance if human_guidance else 'Improve metrics autonomously.'}"

    Generate exactly 5 COMPLETELY DIFFERENT email variants. Each must use a distinct copywriting strategy:
    Variant 1: Urgency & Scarcity
    Variant 2: Curiosity & Mystery
    Variant 3: Social Proof & Trust
    Variant 4: Personal & Emotional
    Variant 5: Data-Driven & Logical

    STRICT RULES:
    1. Every email body MUST contain: https://superbfsi.com/xdeposit/explore/
    2. Use emojis and markdown (**bold**, *italics*).
    3. Return ONLY valid JSON in this exact format:
    {{
      "variants": [
        {{"variant_label": "Urgency & Scarcity", "subject_line": "...", "email_body": "...", "strategy_reasoning": "..."}},
        {{"variant_label": "Curiosity & Mystery", "subject_line": "...", "email_body": "...", "strategy_reasoning": "..."}},
        {{"variant_label": "Social Proof & Trust", "subject_line": "...", "email_body": "...", "strategy_reasoning": "..."}},
        {{"variant_label": "Personal & Emotional", "subject_line": "...", "email_body": "...", "strategy_reasoning": "..."}},
        {{"variant_label": "Data-Driven & Logical", "subject_line": "...", "email_body": "...", "strategy_reasoning": "..."}}
      ]
    }}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.9,
        response_format={"type": "json_object"}
    )
    data = json.loads(response.choices[0].message.content)
    return data.get("variants", [])
