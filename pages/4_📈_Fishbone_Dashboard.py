# pages/4_📈_Fishbone_Dashboard.py
import streamlit as st
import pandas as pd
import db_manager

# --- Page Configuration ---
st.set_page_config(
    page_title="Fishbone Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Fishbone Analysis Dashboard")
st.markdown("---")

# --- Helper function to fetch data ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def get_fishbone_data(session_name):
    """Fetches all fishbone data for a specific session."""
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
    st.info("No Fishbone data has been saved yet. Please process a diagram on the 'Fishbone Processor' page first.")
    st.stop()

selected_session = st.sidebar.selectbox(
    "Select a Session to View:",
    options=all_sessions
)

# --- Load and display data ---
if selected_session:
    df = get_fishbone_data(selected_session)
    
    if df.empty:
        st.warning(f"No data found for session '{selected_session}'.")
    else:
        st.header(f"Analysis for Session: `{selected_session}`")
        
        # Display KPIs
        st.markdown("#### Key Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Details Logged", value=len(df))
        col2.metric("Unique Main Causes", value=df['main_cause'].nunique())
        col3.metric("Unique Sub-Causes", value=df['sub_cause'].nunique())
        
        st.markdown("---")
        
        # Add more filters
        st.sidebar.markdown("---")
        main_cause_list = ["All"] + sorted(df['main_cause'].unique())
        selected_main_cause = st.sidebar.selectbox("Filter by Main Cause:", main_cause_list)
        
        if selected_main_cause != "All":
            df_filtered = df[df['main_cause'] == selected_main_cause]
        else:
            df_filtered = df.copy()

        sub_cause_list = ["All"] + sorted(df_filtered['sub_cause'].unique())
        selected_sub_cause = st.sidebar.selectbox("Filter by Sub-Cause:", sub_cause_list)
        
        if selected_sub_cause != "All":
            df_filtered = df_filtered[df_filtered['sub_cause'] == selected_sub_cause]
            
        # Display Data Table
        st.markdown("#### Detailed Data View")
        st.dataframe(df_filtered)
        
        # Display Charts
        st.markdown("---")
        st.markdown("#### Visual Insights")
        
        if not df_filtered.empty:
            st.write("**Count of Details per Main Cause**")
            main_cause_counts = df['main_cause'].value_counts()
            st.bar_chart(main_cause_counts)
            
            st.write("**Count of Details per Sub-Cause (for selected Main Cause)**")
            if selected_main_cause != "All":
                 sub_cause_counts = df_filtered['sub_cause'].value_counts()
                 st.bar_chart(sub_cause_counts)
            else:
                 st.info("Select a specific Main Cause from the sidebar to see this chart.")
        else:
            st.info("No data to visualize for the current filter.")