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
        if sheet.row_count <= 1:  # Only header row or empty
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
        
        # Debug info
        st.write("Debug - DataFrame Columns:", df.columns.tolist())
        
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
    """Create a formatted bar chart for ratings."""
    try:
        if feedback_data.empty or "Rating" not in feedback_data.columns:
            st.warning("No rating data available for visualization")
            return
        
        # Remove any empty ratings
        feedback_data = feedback_data[feedback_data["Rating"].notna()]
        
        if feedback_data.empty:
            st.warning("No valid ratings found")
            return
        
        # Create rating counts with all possible options
        all_ratings = ["Hell No", "No", "I Don't Care", "Sure", "Definitely"]
        rating_counts = pd.Series(0, index=all_ratings)
        actual_counts = feedback_data["Rating"].value_counts()
        rating_counts.update(actual_counts)
        
        # Create the chart
        chart_data = pd.DataFrame({
            "Rating": rating_counts.index,
            "Count": rating_counts.values
        })
        
        st.bar_chart(
            chart_data.set_index("Rating"),
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")

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
                positive_responses = len(feedback_data[feedback_data["Rating"].isin(["Sure", "Definitely"])])
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