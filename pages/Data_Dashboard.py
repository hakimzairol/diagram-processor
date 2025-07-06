import streamlit as st
import pandas as pd
import db_manager # Import our database functions

st.set_page_config(
    page_title="Data Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Data Dashboard")
st.markdown("View, filter and export data from all sessions.")

# --- Sidebar Filters ---
st.sidebar.header("Filters")

session_list = db_manager.get_all_session_schemas()
session_list.insert(0, "All Sessions")

selected_session = st.sidebar.selectbox(
    "Select a Session:",
    options=session_list,
    key='session_selector' # Add a key to help with state
)

# ==============================================================================
#                      NEW: SESSION MANAGEMENT SECTION
# ==============================================================================
# This section only appears when a specific session is selected.
if selected_session != "All Sessions":
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Session Management")

    # Use an expander to hide the dangerous delete functionality
    with st.sidebar.expander("⚠️ Delete This Session"):
        st.warning(f"This will permanently delete the session '{selected_session}' and all its data. This action cannot be undone.")

        # Confirmation text input to prevent accidental clicks
        st.info("To confirm, please type the session name exactly as it appears above and click the button.")
        confirmation_text = st.text_input("Confirm session name:", key="delete_confirmation")

        # The final delete button is disabled until the user types the correct name
        if st.button("DELETE PERMANENTLY", disabled=(confirmation_text != selected_session)):
            with st.spinner("Deleting session..."):
                success = db_manager.delete_session_schema(selected_session)

                if success:
                    # Use st.experimental_rerun() to refresh the page and update the session list
                    st.success(f"Session '{selected_session}' was deleted!")
                    st.rerun()
                else:
                    st.error("An error occurred while trying to delete the session.")

# ==============================================================================
#                      EXISTING DATA DISPLAY LOGIC
# ==============================================================================
# --- Load Data Based on Selection ---
if selected_session == "All Sessions":
    data = db_manager.get_all_data_from_all_schemas()
else:
    data = db_manager.get_data_from_schema(selected_session)

# --- Main Page Display ---
if not data:
    st.warning("No data found for the selected session. Process a diagram first on the 'Processor' page!")
else:
    df = pd.DataFrame(data)
    st.markdown("---")
    st.markdown("##### At-a-Glance Summary")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Items", value=len(df))
    col2.metric("Unique Categories", value=df['category_name'].nunique())
    
    if 'session' in df.columns:
        num_sessions = df['session'].nunique()
    else:
        num_sessions = 1 if selected_session != "All Sessions" else 0
    col3.metric("Sessions Viewed", value=num_sessions)

    st.markdown("---")
    st.markdown("##### Detailed Data View")

    category_list = ["All Categories"] + sorted(df['category_name'].unique())
    selected_category = st.sidebar.selectbox(
        "Filter by Category:",
        options=category_list
    )

    if selected_category != "All Categories":
        df_filtered = df[df['category_name'] == selected_category]
    else:
        df_filtered = df

    st.dataframe(df_filtered)
    st.markdown("---")
    st.subheader("📥 Export Data")
    st.write("Download the filtered data table above as a CSV file.")

    @st.cache_data
    def convert_df_to_csv(df_to_convert):
        return df_to_convert.to_csv(index=False).encode('utf-8')

    csv = convert_df_to_csv(df_filtered)
    st.download_button(
       label="Download as CSV",
       data=csv,
       file_name=f"{selected_session}_data.csv",
       mime="text/csv",
    )

    st.markdown("---")
    st.subheader("📊 Visual Insights")
    if not df_filtered.empty:
        st.write("Item Count by Category")
        category_counts = df_filtered['category_name'].value_counts()
        st.bar_chart(category_counts)
    else:
        st.info("No data to visualize for the current filter.")
