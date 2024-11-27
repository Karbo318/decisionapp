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
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["google_service_account"],
            scopes=SCOPE
        )
        
        client = gspread.authorize(credentials)
        sheet = client.open(SHEET_NAME).sheet1
        
        # Initialize the sheet with headers if it's empty
        if sheet.row_count <= 1:
            sheet.append_row(["Timestamp", "Comments", "Rating"])
            
        return sheet
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        return None

def load_feedback(sheet):
    """Load existing feedback from the sheet."""
    if sheet is None:
        return pd.DataFrame(columns=["Timestamp", "Comments", "Rating"])
    
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Ensure required columns exist
        required_columns = ["Timestamp", "Comments", "Rating"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
                
        return df
    except Exception as e:
        st.error(f"Failed to load feedback: {str(e)}")
        return pd.DataFrame(columns=["Timestamp", "Comments", "Rating"])

def save_feedback(sheet, comments, rating):
    """Save new feedback to the sheet."""
    if sheet is None:
        raise Exception("Sheet connection not established")
    
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, comments, rating])

def create_rating_chart(feedback_data):
    """Create a formatted bar chart for ratings in specified order."""
    try:
        if feedback_data.empty or "Rating" not in feedback_data.columns:
            st.warning("No rating data available for visualization")
            return
        
        # Define ratings in desired order (negative to positive)
        ordered_ratings = pd.CategoricalDtype(
            categories=["F**k No", "No", "Don't Care", "Uhhhh....Sure", "Most Definitely"],
            ordered=True
        )
        
        # Convert to categorical and get value counts
        counts = feedback_data["Rating"].astype(ordered_ratings).value_counts()
        
        # Create and display chart
        st.bar_chart(counts)
        
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")

def main():
    st.set_page_config(page_title="Team Sexy Decision Portal", page_icon="📋")
    
    st.title("🤝 Team Sexy Feedback")
    st.write("Sarah would like to rejoin the team. Your sexy feedback here will be used to \
             make a sexy collective decision about whether or not to let her. It's anonymous. So be honest, but preferably kind. \
             Kindness is sexy.")
    
    # Connect to Google Sheets
    sheet = connect_to_google_sheet()
    
    # Load existing feedback
    feedback_data = load_feedback(sheet)
    
    # Feedback form
    with st.form("feedback_form", clear_on_submit=True):
        comments = st.text_area(
            "Comments",
            placeholder="Write any comments here. This is optional.",
            help="Your feedback will be anonymous"
        )
        
        rating = st.radio(
            "How do you feel about Sarah returning?",
            options=["Oh Hell No!", "Nah", "I Really Don't Care", "Yeah! Sure!", "It Would Be My Dream Come True!"],
            horizontal=True
        )
        
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            try:
                save_feedback(sheet, comments, rating)
                st.success("Thank you! Your feedback has been recorded.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save feedback: {str(e)}")
    
    # Display feedback summary
    if not feedback_data.empty:
        st.write("### 📊 Feedback Summary")
        
        # Create and display the rating chart
        create_rating_chart(feedback_data)
        
        # Display statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Responses", len(feedback_data))
        with col2:
            if "Rating" in feedback_data.columns:
                positive_responses = len(feedback_data[feedback_data["Rating"].isin(["Yeah! Sure!", "It Would Be My Dream Come True!"])])
                if len(feedback_data) > 0:
                    positive_percentage = (positive_responses/len(feedback_data)*100)
                else:
                    positive_percentage = 0
                st.metric("Positive Responses", f"{positive_responses} ({positive_percentage:.1f}%)")
        
        # Display detailed feedback
        st.write("### 📝 Detailed Feedback")
        st.dataframe(
            feedback_data,
            use_container_width=True
        )

if __name__ == "__main__":
    main()