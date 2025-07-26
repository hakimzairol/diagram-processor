# pages/1_🧠_Mind_Map_Processor.py

import streamlit as st
import db_manager
import gemini_client
import re
from PIL import Image
import json # Make sure json is imported

# --- Helper Functions ---
def get_kumpulan_number(group_name_str: str) -> int:
    """Extracts the integer group number from a string, with a fallback."""
    if group_name_str:
        match = re.search(r'\d+', group_name_str)
        if match:
            return int(match.group(0))
    return 0 # Default to 0 if no number found

# --- Page Configuration ---
st.set_page_config(
    page_title="Mind Map Processor",
    page_icon="🧠",
    layout="centered"
)

# --- Initialize Session State ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'setup'
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = {}
if 'session_name' not in st.session_state:
    st.session_state.session_name = ""

def reset_to_setup():
    """Clears the state and returns to the initial setup screen."""
    st.session_state.stage = 'setup'
    st.session_state.extracted_data = {}
    for key in ['activity_name', 'group_name']:
        if key in st.session_state:
            del st.session_state[key]

# ==============================================================================
#                             STAGE 1: SETUP & ANALYSIS
# ==============================================================================
if st.session_state.stage == 'setup':
    st.title("🧠 Mind Map Processor")
    st.markdown("Upload a simple list or mind map to extract and categorize items.")

    st.session_name = st.text_input(
        "Enter a name for this session (e.g., 'Q1 Marketing 2024')",
        value=st.session_state.session_name
    )
    uploaded_image = st.file_uploader("Upload your team's image:", type=['jpg', 'jpeg', 'png'])

    if uploaded_image:
        st.image(Image.open(uploaded_image), caption='Uploaded Diagram', use_column_width=True)

    if st.button("Analyze Image", type="primary", use_container_width=True):
        if not st.session_state.session_name:
            st.error("⚠️ Please enter a session name.")
        elif not uploaded_image:
            st.error("⚠️ Please upload an image.")
        else:
            with st.spinner("Processing... This may take a moment."):
                session_schema = db_manager.sanitize_name(st.session_state.session_name)
                
                # --- THIS IS THE FIX ---
                # Call the correct setup function for the Mind Map tool
                if not db_manager.setup_mindmap_schema(session_schema):
                    st.error(f"❌ Failed to set up database schema '{session_schema}'. Check DB connection.")
                    st.stop()

                image_bytes = uploaded_image.getvalue()
                # The old tool uses the original prompt.txt
                json_string = gemini_client.get_gemini_response(image_bytes, "prompt.txt")

                try:
                    extracted_info = json.loads(json_string)
                except json.JSONDecodeError:
                    st.error("❌ Extraction failed. The AI returned invalid JSON. Try a clearer image.")
                    st.text_area("AI Raw Output:", json_string, height=150)
                    st.stop()

                if not extracted_info or 'items' not in extracted_info:
                    st.error("❌ Extraction failed. The AI could not find structured data. Try another image.")
                    st.json(extracted_info)
                    st.stop()

                st.session_state.extracted_data = {
                    "session_schema": session_schema,
                    "info": extracted_info,
                }
                st.session_state.stage = 'categorize'
                st.rerun()

# ==============================================================================
#                             STAGE 2: CATEGORIZATION
# ==============================================================================
elif st.session_state.stage == 'categorize':
    st.title("✍️ Assign Categories")

    data = st.session_state.extracted_data
    info = data['info']
    schema = data['session_schema']
    items_to_process = info.get('items', [])

    if 'activity_name' not in st.session_state:
        st.session_state.activity_name = info.get('activity_name', 'N/A')
    if 'group_name' not in st.session_state:
        st.session_state.group_name = info.get('group_name', 'N/A')

    st.markdown("##### Categorization Details")
    col1, col2, col3 = st.columns(3)
    st.session_state.activity_name = col1.text_input("Activity Name", value=st.session_state.activity_name)
    st.session_state.group_name = col2.text_input("Group Name", value=st.session_state.group_name)
    col3.text_input("Session Schema", value=schema, disabled=True)
    st.markdown("---")

    # This part of the UI remains the same as it was working well
    with st.form("category_form"):
        # ... (rest of the form logic is unchanged)
        user_inputs = []
        st.markdown("###### Items to Categorize")
        
        for i, item in enumerate(items_to_process):
            with st.container(border=True):
                original_description = item.get('description', 'No description found')
                col_check, col_desc, col_cat = st.columns([0.5, 4, 3])
                with col_check:
                    include_item = st.checkbox("Include", value=True, key=f"include_{i}", label_visibility="collapsed")
                with col_desc:
                    edited_description = st.text_input("Description", value=original_description, key=f"desc_{i}", label_visibility="collapsed")
                with col_cat:
                    # In a real app, you might fetch existing categories for this schema
                    # For now, let's keep it simple
                    final_category = st.text_input("Category", key=f"cat_{i}", label_visibility="collapsed")
                user_inputs.append({'include': include_item, 'description': edited_description, 'category': final_category})
        
        st.markdown("")
        submitted = st.form_submit_button("💾 Save All Categories to Database", use_container_width=True)

    if submitted:
        group_name_to_save = st.session_state.group_name
        activity_name_to_save = st.session_state.activity_name

        if not any(char.isdigit() for char in group_name_to_save):
            st.error("⚠️ Validation Error: The 'Group Name' must contain a number (e.g., 'GRP 1'). Please correct it.")
            st.stop()

        items_to_save = [item for item in user_inputs if item['include']]
        is_valid = all(item['description'] and item['category'] for item in items_to_save)

        if not items_to_save:
            st.warning("⚠️ No items were selected to be saved.")
        elif not is_valid:
            st.warning("⚠️ For all included items, please ensure a description and category are filled.")
        else:
            with st.spinner("Saving data..."):
                kumpulan_no = get_kumpulan_number(group_name_to_save)
                final_data_to_insert = [{'group_no': kumpulan_no, 'description': item['description'], 'category_name': item['category']} for item in items_to_save]
                
                # --- THIS IS THE SECOND FIX ---
                # Call the correct insert function for the Mind Map tool
                records_inserted = db_manager.insert_mindmap_data(final_data_to_insert, schema, activity_name_to_save)

                if records_inserted > 0:
                    st.success(f"✅ Success! {records_inserted} records were saved.")
                    st.balloons()
                else:
                    st.error("❌ No records were inserted. An error occurred.")
    
    if st.button("Process Another Image"):
        reset_to_setup()
        st.rerun()