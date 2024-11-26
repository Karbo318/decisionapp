import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Read the service account JSON from environment variable
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# Google Sheets configuration
SHEET_NAME = "Decisiondata"

# Connect to Google Sheets

# Set up the connection to Google Sheets
def connect_to_google_sheet():
    # Ensure the credentials are stored as a JSON string in your environment variable
    credentials_json = os.getenv("GOOGLE_SHEET_CREDENTIALS_JSON")
    
    # Convert the JSON string into a dictionary
    creds_dict = json.loads(credentials_json)
    
    # Use the credentials dictionary
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    
    # Authorize with gspread
    client = gspread.authorize(creds)
    
    # Open the sheet by name
    return client.open("Decisiondata").sheet1 


# Load feedback data
def load_feedback(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Save new feedback to Google Sheets
def save_feedback(sheet, comments, rating):
    sheet.append_row([comments, rating])

# Connect to the sheet
sheet = connect_to_google_sheet()

# Load existing feedback
try:
    feedback_data = load_feedback(sheet)
except Exception:
    feedback_data = pd.DataFrame(columns=["Comments", "Rating"])

# Streamlit app
st.set_page_config(page_title="Feedback App")

st.title("Team Member Feedback")
st.write("Provide your anonymous feedback on whether the former team member should rejoin the team.")

# Feedback form
with st.form("feedback_form"):
    comments = st.text_area("Any comments?", placeholder="Write your feedback here...")
    rating = st.radio("How do you feel about this team member returning?",
                      options=["Hell No", "No", "I Don't Care", "Sure", "Definitely"])
    submitted = st.form_submit_button("Submit Feedback")
    
    if submitted:
        save_feedback(sheet, comments, rating)
        st.success("Your feedback has been recorded. Thank you!")
        st.experimental_rerun()

# Display feedback summary
if not feedback_data.empty:
    st.write("### Feedback Summary:")
    st.bar_chart(feedback_data["Rating"].value_counts())
    st.write("Detailed Feedback:")
    st.dataframe(feedback_data)


