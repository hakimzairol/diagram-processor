# pages/4_📈_Fishbone_Dashboard.py
import streamlit as st
import pandas as pd
import db_manager

st.set_page_config(page_title="Fishbone Dashboard", page_icon="📈", layout="wide")
st.title("📈 Fishbone Analysis Dashboard")
st.markdown("---")

@st.cache_data(ttl=600)
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

st.sidebar.header("Dashboard Filters")
all_sessions = db_manager.get_all_fishbone_sessions()

if not all_sessions:
    st.info("No Fishbone data has been saved yet. Process a diagram on the 'Fishbone Processor' page first.")
    st.stop()

selected_session = st.sidebar.selectbox("Select a Session to View:", options=all_sessions)

if selected_session:
    df = get_fishbone_data(selected_session)
    
    if df.empty:
        st.warning(f"No data found for session '{selected_session}'.")
    else:
        st.header(f"Analysis for Session: `{selected_session}`")
        
        # Replace empty strings with a more descriptive placeholder for metrics
        df_metrics = df.replace('', 'N/A')
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Details Logged", value=len(df_metrics))
        col2.metric("Unique Main Causes", value=df_metrics['main_cause'].nunique())
        col3.metric("Unique Sub-Causes", value=df_metrics['sub_cause'].nunique())
        
        st.markdown("---")
        
        st.sidebar.markdown("---")
        # --- FIX FOR THE TYPEERROR ---
        # Filter out empty/None values before sorting and creating the filter list
        main_cause_options = sorted([cause for cause in df['main_cause'].unique() if cause])
        selected_main_cause = st.sidebar.selectbox("Filter by Main Cause:", ["All"] + main_cause_options)
        
        if selected_main_cause != "All":
            df_filtered = df[df['main_cause'] == selected_main_cause]
        else:
            df_filtered = df.copy()

        # --- FIX FOR THE TYPEERROR ---
        sub_cause_options = sorted([cause for cause in df_filtered['sub_cause'].unique() if cause])
        selected_sub_cause = st.sidebar.selectbox("Filter by Sub-Cause:", ["All"] + sub_cause_options)
        
        if selected_sub_cause != "All":
            df_filtered = df_filtered[df_filtered['sub_cause'] == selected_sub_cause]
            
        st.markdown("#### Detailed Data View")
        st.dataframe(df_filtered, use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### Visual Insights")
        
        if not df_filtered.empty:
            st.write("**Count of Details per Main Cause**")
            # Use the cleaned df_metrics for counting to handle 'N/A' correctly
            main_cause_counts = df_metrics[df_metrics['main_cause'] != 'N/A']['main_cause'].value_counts()
            st.bar_chart(main_cause_counts)
        else:
            st.info("No data to visualize for the current filter.")