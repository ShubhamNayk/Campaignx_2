import streamlit as st
import os

def setup_langfuse():
    """Initializes Langfuse environment variables from Streamlit secrets."""
    os.environ["LANGFUSE_PUBLIC_KEY"] = st.secrets["LANGFUSE_PUBLIC_KEY"]
    os.environ["LANGFUSE_SECRET_KEY"] = st.secrets["LANGFUSE_SECRET_KEY"]
    os.environ["LANGFUSE_HOST"] = st.secrets.get("LANGFUSE_HOST", "https://cloud.langfuse.com")