# pages/1_🧠_Mind_Map_Processor.py
import streamlit as st
import db_manager
import gemini_client
import re
from PIL import Image
import json

def get_kumpulan_number(group_name_str: str) -> int:
    if group_name_str:
        match = re.search(r'\d+', group_name_str)
        if match: return int(match.group(0))
    return 0

st.set_page_config(page_title="Mind Map Processor", page_icon="🧠", layout="centered")

# --- State Management ---
if 'stage' not in st.session_state: st.session_state.stage = 'setup'
if 'extracted_data' not in st.session_state: st.session_state.extracted_data = {}

def reset_to_setup():
    st.session_state.stage = 'setup'
    st.session_state.extracted_data = {}
    for key in ['activity_name', 'group_name', 'session_name']:
        if key in st.session_state: del st.session_state[key]

# --- STAGE 1: SETUP ---
if st.session_state.stage == 'setup':
    st.title("🧠 Mind Map & List Processor")
    st.markdown("Upload a simple list or mind map to extract and categorize items.")
    
    session_name = st.text_input("Enter a name for this session (e.g., 'Q1_Marketing_2024')")
    uploaded_image = st.file_uploader("Upload your image:", type=['jpg', 'jpeg', 'png'])

    if uploaded_image: st.image(Image.open(uploaded_image), caption='Uploaded Diagram')

    if st.button("Analyze Image", type="primary", use_container_width=True):
        if not session_name or not uploaded_image:
            st.warning("⚠️ Please provide a session name and upload an image.")
        else:
            with st.spinner("Processing..."):
                if not db_manager.setup_mindmap_schema(session_name):
                    st.error(f"❌ Failed to set up database schema '{session_name}'. Check DB connection.")
                else:
                    image_bytes = uploaded_image.getvalue()
                    json_string = gemini_client.get_gemini_response(image_bytes, "prompt.txt")
                    try:
                        extracted_info = json.loads(json_string)
                        if 'items' not in extracted_info: raise ValueError("Missing 'items' key in AI response")
                        st.session_state.extracted_data = {"session_schema": db_manager.sanitize_name(session_name), "info": extracted_info}
                        st.session_state.stage = 'categorize'
                        st.rerun()
                    except (json.JSONDecodeError, ValueError) as e:
                        st.error(f"❌ AI Extraction Failed: {e}. Try a clearer image.")
                        st.code(json_string, language='json')

# --- STAGE 2: CATEGORIZATION ---
elif st.session_state.stage == 'categorize':
    st.title("✍️ Assign Categories")
    data = st.session_state.extracted_data
    info = data.get('info', {})
    schema = data.get('session_schema')
    items = info.get('items', [])
    
    # Header Information
    st.session_state.activity_name = st.text_input("Activity Name", info.get('activity_name', 'N/A'))
    st.session_state.group_name = st.text_input("Group Name", info.get('group_name', 'N/A'))
    
    # Form for editing and categorizing
    with st.form("category_form"):
        st.markdown("---")
        st.markdown("###### Items to Categorize")
        
        # This list will hold the data for each row in the form
        processed_items = []
        
        for i, item in enumerate(items):
            with st.container(border=True):
                col1, col2 = st.columns(2)
                # Get the description from the AI
                desc = col1.text_input("Description", value=item.get('description', ''), key=f"desc_{i}")
                # Provide a simple text box for the category
                cat = col2.text_input("Category", key=f"cat_{i}")
                processed_items.append({'description': desc, 'category': cat})
        
        submitted = st.form_submit_button("💾 Save All to Database", use_container_width=True)

    if submitted:
        # Validate that all fields are filled
        if not all(item['description'] and item['category'] for item in processed_items):
            st.warning("⚠️ Please fill in all descriptions and categories before saving.")
        else:
            with st.spinner("Saving..."):
                kumpulan_no = get_kumpulan_number(st.session_state.group_name)
                # Prepare data for insertion
                data_to_insert = [
                    {'group_no': kumpulan_no, 'description': item['description'], 'category_name': item['category']}
                    for item in processed_items
                ]
                # Call the correct insert function
                records_inserted = db_manager.insert_mindmap_data(data_to_insert, schema, st.session_state.activity_name)
                
                if records_inserted > 0:
                    st.success(f"✅ Success! {records_inserted} records saved.")
                    st.balloons()
                    reset_to_setup() # Reset the state for the next use
                    st.rerun()
                else:
                    st.error("❌ No records were inserted. An error occurred.")

    if st.button("❌ Start Over"):
        reset_to_setup()
        st.rerun()