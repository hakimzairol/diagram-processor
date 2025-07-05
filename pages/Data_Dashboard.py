# pages/2_📊_Data_Dashboard.py

import streamlit as st
import pandas as pd
import db_manager # Import our database functions

st.set_page_config(
    page_title="Data Dashboard",
    page_icon="📊",
    layout="wide" # Use wide layout for better data display
)

st.title("📊 Data Dashboard")
st.markdown("View, filter and export data from all sessions.")

# --- Sidebar Filters ---
st.sidebar.header("Filters")

session_list = db_manager.get_all_session_schemas()
session_list.insert(0, "All Sessions")

selected_session = st.sidebar.selectbox(
    "Select a Session:",
    options=session_list
)

# --- Load Data Based on Selection ---
if selected_session == "All Sessions":
    data = db_manager.get_all_data_from_all_schemas()
else:
    data = db_manager.get_data_from_schema(selected_session)

# --- Main Page Display ---
if not data:
    st.warning("No data found for the selected session. Process a diagram first on the 'Processor' page!")
else:
    # Convert list of dicts to a Pandas DataFrame for powerful manipulation
    df = pd.DataFrame(data)

    # --- NEW: KPI Metrics Section ---
    st.markdown("---")
    st.markdown("##### At-a-Glance Summary")
    
    # Create columns for the metrics
    col1, col2, col3 = st.columns(3)
    
    # Metric 1: Total Items in the filtered view
    col1.metric("Total Items", value=len(df))
    
    # Metric 2: Number of unique categories in the filtered view
    col2.metric("Unique Categories", value=df['category_name'].nunique())
    
    # Metric 3: Number of sessions being viewed
    # If 'All Sessions' is selected, count unique sessions, otherwise it's just 1
    if 'session' in df.columns:
        num_sessions = df['session'].nunique()
    else:
        num_sessions = 1 # Only one session is being viewed
    col3.metric("Sessions Viewed", value=num_sessions)

    st.markdown("---")


    # --- Interactive Data Table with Advanced Filtering ---
    st.markdown("##### Detailed Data View")

    # Sidebar filter for category, based on the *currently loaded* data
    category_list = ["All Categories"] + sorted(df['category_name'].unique())
    selected_category = st.sidebar.selectbox(
        "Filter by Category:",
        options=category_list
    )

    if selected_category != "All Categories":
        df_filtered = df[df['category_name'] == selected_category]
    else:
        df_filtered = df # No category filter applied

    # Display the filtered dataframe
    st.dataframe(df_filtered)

    st.markdown("---")

    # --- Data Export (operates on the filtered data) ---
    st.subheader("📥 Export Data")
    st.write("Download the filtered data table above as a CSV file.")

    @st.cache_data # Cache the conversion to make it faster
    def convert_df_to_csv(df_to_convert):
        return df_to_convert.to_csv(index=False).encode('utf-8')

    csv = convert_df_to_csv(df_filtered)

    st.download_button(
       label="Download as CSV",
       data=csv,
       file_name=f"{selected_session}_data.csv",
       mime="text/csv",
    )

    # --- Simple Visualizations (operates on the filtered data) ---
    st.markdown("---")
    st.subheader("📊 Visual Insights")

    if not df_filtered.empty:
        # Create a bar chart of item counts per category
        st.write("Item Count by Category")
        category_counts = df_filtered['category_name'].value_counts()
        st.bar_chart(category_counts)
    else:
        st.info("No data to visualize for the current filter.")