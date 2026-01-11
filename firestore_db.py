import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

@st.cache_resource
def get_db():
   
    if not firebase_admin._apps:
        
        if "firebase_key" in st.secrets:
           
            cred_info = dict(st.secrets["firebase_key"])
            cred = credentials.Certificate(cred_info)
        else:
           
            cred = credentials.Certificate("firebase-key.json")
            
        firebase_admin.initialize_app(cred)

    return firestore.client()