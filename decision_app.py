import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account

# Constants
SHEET_NAME = "Decisiondata"
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def connect_to_google_sheet():
    """Connect to Google Sheets using service account credentials."""
    try:
        # Load credentials directly from streamlit secrets
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["google_service_account"],
            scopes=SCOPE
        )
        
        client = gspread.authorize(credentials)
        sheet = client.open(SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        return None

def load_feedback(sheet):
    """Load existing feedback from the sheet."""
    if sheet is None:
        return pd.DataFrame(columns=["Comments", "Rating"])
    
    try:
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to load feedback: {str(e)}")
        return pd.DataFrame(columns=["Comments", "Rating"])

def save_feedback(sheet, comments, rating):
    """Save new feedback to the sheet."""
    if sheet is None:
        raise Exception("Sheet connection not established")
    
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, comments, rating])

def main():
    st.set_page_config(page_title="Team Member Feedback", page_icon="📋")
    
    st.title("🤝 Team Member Feedback")
    st.write("Provide your anonymous feedback on whether the former team member should rejoin the team.")
    
    # Connect to Google Sheets
    sheet = connect_to_google_sheet()
    
    # Load existing feedback
    feedback_data = load_feedback(sheet)
    
    # Feedback form
    with st.form("feedback_form", clear_on_submit=True):
        comments = st.text_area(
            "Comments",
            placeholder="Write your feedback here...",
            help="Your feedback will be anonymous"
        )
        
        rating = st.radio(
            "How do you feel about this team member returning?",
            options=["Hell No", "No", "I Don't Care", "Sure", "Definitely"],
            horizontal=True
        )
        
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            try:
                save_feedback(sheet, comments, rating)
                st.success("Thank you! Your feedback has been recorded.")
                # Use rerun to refresh the page and show updated data
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to save feedback: {str(e)}")
    
    # Display feedback summary
    if not feedback_data.empty:
        st.write("### 📊 Feedback Summary")
        
        # Create a bar chart of ratings
        rating_counts = feedback_data["Rating"].value_counts()
        st.bar_chart(rating_counts)
        
        # Display statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Responses", len(feedback_data))
        with col2:
            positive_responses = len(feedback_data[feedback_data["Rating"].isin(["Sure", "Definitely"])])
            st.metric("Positive Responses", f"{positive_responses} ({(positive_responses/len(feedback_data)*100):.1f}%)")
        
        # Display detailed feedback
        st.write("### 📝 Detailed Feedback")
        st.dataframe(
            feedback_data.sort_values(by="Timestamp", ascending=False),
            use_container_width=True
        )

if __name__ == "__main__":
    main()