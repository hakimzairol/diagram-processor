# pages/3_📊_Mind_Map_Dashboard.py
import streamlit as st
import pandas as pd
import db_manager

st.set_page_config(page_title="Mind Map Dashboard", page_icon="📊", layout="wide")
st.title("📊 Mind Map Dashboard")
st.markdown("View and filter data from all Mind Map & List sessions.")

# --- Helper function to get data from all schemas ---
def get_all_mindmap_data_from_all_schemas() -> list[dict]:
    """Fetches all data from all mind map schemas and adds a 'session' column."""
    all_data = []
    session_schemas = db_manager.get_all_mindmap_sessions()
    for schema in session_schemas:
        schema_data = db_manager.get_mindmap_data_from_schema(schema)
        for row in schema_data:
            row['session'] = schema # Add the session name to each row
            all_data.append(row)
    return all_data

# --- Sidebar Filters ---
st.sidebar.header("Filters")
# --- THIS IS THE FIX ---
# We add "All Sessions" to the beginning of the list
session_list = ["All Sessions"] + db_manager.get_all_mindmap_sessions()

if not session_list or len(session_list) == 1:
    st.info("No Mind Map data has been saved yet. Please use the 'Mind Map Processor' first.")
    st.stop()

selected_session = st.sidebar.selectbox("Select a Session:", options=session_list)

# --- Session Management (Only show for specific sessions) ---
if selected_session != "All Sessions":
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚠️ Delete This Session"):
        st.warning(f"This will permanently delete the session '{selected_session}' and all its data.")
        confirmation_text = st.text_input("Confirm by typing session name:", key="del_mm_confirm")
        if st.button("DELETE PERMANENTLY", disabled=(confirmation_text != selected_session)):
            if db_manager.delete_mindmap_session_schema(selected_session):
                st.success(f"Session '{selected_session}' was deleted!"); st.rerun()
            else:
                st.error("Error deleting session.")

# --- Load and Display Data ---
# --- THIS IS THE NEW LOGIC ---
if selected_session == "All Sessions":
    st.markdown("### Displaying Data for: `All Sessions`")
    data = get_all_mindmap_data_from_all_schemas()
else:
    st.markdown(f"### Data for Session: `{selected_session}`")
    data = db_manager.get_mindmap_data_from_schema(selected_session)

if not data:
    st.warning(f"No data found for selection.")
else:
    df = pd.DataFrame(data)
    
    # Display the dataframe. If 'All Sessions' is selected, it will have the 'session' column.
    st.dataframe(df, use_container_width=True)

    # --- Simple Chart ---
    st.markdown("---")
    st.markdown("#### Category Counts")
    if 'category_name' in df.columns:
        st.bar_chart(df['category_name'].value_counts())