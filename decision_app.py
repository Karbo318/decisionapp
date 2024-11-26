import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets configuration
SHEET_NAME = "Decisiondata"

# Connect to Google Sheets
def connect_to_google_sheet():
    # Load credentials from Streamlit secrets
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["google_service_account"],
        scope=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    # Authorize with gspread
    client = gspread.authorize(creds)
    # Open the sheet by name
    return client.open(SHEET_NAME).sheet1

# Load feedback data
def load_feedback(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Save new feedback to Google Sheets
def save_feedback(sheet, comments, rating):
    sheet.append_row([comments, rating])

# Streamlit app
st.set_page_config(page_title="Feedback App")

st.title("Team Member Feedback")
st.write("Provide your anonymous feedback on whether the former team member should rejoin the team.")

# Connect to the sheet
try:
    sheet = connect_to_google_sheet()
    # Load existing feedback
    feedback_data = load_feedback(sheet)
except Exception:
    st.error("Unable to connect to Google Sheets. Please check your configuration.")
    feedback_data = pd.DataFrame(columns=["Comments", "Rating"])

# Feedback form
with st.form("feedback_form"):
    comments = st.text_area("Any comments?", placeholder="Write your feedback here...")
    rating = st.radio("How do you feel about this team member returning?",
                      options=["Hell No", "No", "I Don't Care", "Sure", "Definitely"])
    submitted = st.form_submit_button("Submit Feedback")
    
    if submitted:
        try:
            save_feedback(sheet, comments, rating)
            st.success("Your feedback has been recorded. Thank you!")
            st.experimental_rerun()
        except Exception:
            st.error("Failed to save feedback. Please try again later.")

# Display feedback summary
if not feedback_data.empty:
    st.write("### Feedback Summary:")
    st.bar_chart(feedback_data["Rating"].value_counts())
    st.write("Detailed Feedback:")
    st.dataframe(feedback_data)
