import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

@st.cache_resource
def get_db():
    # Check if app is already initialized to avoid "App already exists" error
    if not firebase_admin._apps:
        # HACKATHON MODE: Try to load from Secrets first (for Deployment)
        if "firebase_key" in st.secrets:
            # Create a credential object from the secrets dictionary
            # You must paste the content of json into Streamlit Cloud secrets
            cred_info = dict(st.secrets["firebase_key"])
            cred = credentials.Certificate(cred_info)
        else:
            # LOCAL MODE: Fallback to file for local testing
            cred = credentials.Certificate("firebase-key.json")
            
        firebase_admin.initialize_app(cred)

    return firestore.client()