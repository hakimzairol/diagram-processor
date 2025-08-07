# pages/4_📈_Fishbone_Dashboard.py
import streamlit as st
import pandas as pd
import db_manager

st.set_page_config(page_title="Fishbone Dashboard", page_icon="📈", layout="wide")
st.title("📈 Fishbone Analysis Dashboard")
st.markdown("---")

# This is a helper function to get data from the database. It's good practice.
@st.cache_data(ttl=600) # Cache the data for 10 minutes to make the app faster
def get_fishbone_data(session_name):
    conn = None
    try:
        conn = db_manager.psycopg2.connect(**db_manager.config.DB_PARAMS)
        query = "SELECT * FROM fishbone_data WHERE session_name = %s ORDER BY main_cause, sub_cause;"
        df = pd.read_sql_query(query, conn, params=(session_name,))
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

# --- Sidebar Filters ---
st.sidebar.header("Dashboard Filters")
all_sessions = db_manager.get_all_fishbone_sessions()

if not all_sessions:
    st.info("No Fishbone data has been saved yet. Process a diagram on the 'Fishbone Processor' page first.")
    st.stop()

selected_session = st.sidebar.selectbox("Select a Session to View:", options=all_sessions)

# --- Main Page Logic ---
if selected_session:
    # Get the main data for the selected session
    df = get_fishbone_data(selected_session)
    
    if df.empty:
        st.warning(f"No data found for session '{selected_session}'.")
    else:
        # Display the main header
        st.header(f"Analysis for Session: `{selected_session}`")
        
        # <<< --- THIS IS THE NEW PART YOU ASKED ABOUT --- >>>
        # 1. Fetch the comment from the new 'fishbone_sessions' table.
        comment = db_manager.get_fishbone_session_comment(selected_session)
        # 2. If a comment exists, display it inside an expander.
        if comment:
            with st.expander("📝 Show Session Comments"):
                st.info(comment)
        # <<< --- END OF NEW PART --- >>>
        
        # This is the existing code for Key Metrics
        df_metrics = df.replace('', 'N/A')
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Details Logged", value=len(df_metrics))
        col2.metric("Unique Main Causes", value=df_metrics['main_cause'].nunique())
        col3.metric("Unique Sub-Causes", value=df_metrics['sub_cause'].nunique())
        
        st.markdown("---")
        
        # This is the existing code for the sidebar filters
        st.sidebar.markdown("---")
        main_cause_options = sorted([cause for cause in df['main_cause'].unique() if cause])
        selected_main_cause = st.sidebar.selectbox("Filter by Main Cause:", ["All"] + main_cause_options)
        
        if selected_main_cause != "All":
            df_filtered = df[df['main_cause'] == selected_main_cause]
        else:
            df_filtered = df.copy()

        sub_cause_options = sorted([cause for cause in df_filtered['sub_cause'].unique() if cause])
        selected_sub_cause = st.sidebar.selectbox("Filter by Sub-Cause:", ["All"] + sub_cause_options)
        
        if selected_sub_cause != "All":
            df_filtered = df_filtered[df_filtered['sub_cause'] == selected_sub_cause]
            
        # This is the existing code to show the data table and charts
        st.markdown("#### Detailed Data View")
        st.dataframe(df_filtered, use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### Visual Insights")
        
        if not df_filtered.empty:
            st.write("**Count of Details per Main Cause**")
            main_cause_counts = df_metrics[df_metrics['main_cause'] != 'N/A']['main_cause'].value_counts()
            st.bar_chart(main_cause_counts)
        else:
            st.info("No data to visualize for the current filter.")