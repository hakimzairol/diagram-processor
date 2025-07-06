import streamlit as st
import db_manager
import gemini_client
import re
from PIL import Image

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
    page_title="Diagram Processor",
    page_icon="🐟",
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
    st.title("Diagram Processor")
    st.markdown("Upload an image of a diagram to extract and categorize its items.")

    # ADD THIS EXPANDER
    with st.expander("📖 Need help? Click here for instructions!"):
        st.markdown("""
            **This tool helps you extract and categorize items from a fishbone diagram image.**

            **How to use it:**
            1.  **Enter a Session Name:** Give your session a unique name (e.g., `Q1 Brainstorm`). This groups all diagrams from that session together.
            2.  **Upload an Image:** Upload a `.jpg` or `.png` file of your diagram.
            3.  **Analyze & Categorize:** Click "Analyze Image". The AI will extract the text. On the next screen, you can correct any errors and assign a category to each item.
            4.  **View Your Data:** Go to the "Data Dashboard" page from the sidebar to see all your saved data!
        """)
    
    st.session_state.session_name = st.text_input(
        "1. Enter a name for this session (e.g., 'Q1 Marketing 2024')",
        value=st.session_state.session_name
    )

    uploaded_image = st.file_uploader("2. Upload your team's image:", type=['jpg', 'jpeg', 'png'])

    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption='Uploaded Diagram', use_column_width=True)

    if st.button("Analyze Image", type="primary", use_container_width=True):
        if not st.session_state.session_name:
            st.error("⚠️ Please enter a session name.")
        elif not uploaded_image:
            st.error("⚠️ Please upload an image.")
        else:
            with st.spinner("Processing... This may take a moment."):
                session_schema = db_manager.sanitize_name(st.session_state.session_name)
                if not db_manager.setup_session_schema_and_table(session_schema):
                    st.error(f"❌ Failed to set up database schema '{session_schema}'. Check DB connection.")
                    st.stop()

                image_bytes = uploaded_image.getvalue()
                b64_image = gemini_client.base64.b64encode(image_bytes).decode("utf-8")
                extracted_info = gemini_client.extract_from_image(b64_image, "prompt.txt")

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

    # --- Editable Header ---
    st.markdown("##### Categorization Details")
    col1, col2, col3 = st.columns(3)
    st.session_state.activity_name = col1.text_input("Activity Name", value=st.session_state.activity_name)
    st.session_state.group_name = col2.text_input("Group Name", value=st.session_state.group_name)
    col3.text_input("Session Schema", value=schema, disabled=True)
    st.markdown("---")

    # --- The Main Form with Card Layout ---
    existing_cats = db_manager.fetch_distinct_category_names(schema)
    new_cat_option = "-- Add New Category --"
    category_options = [new_cat_option] + sorted(existing_cats)

    with st.form("category_form"):
        user_inputs = []
        st.markdown("###### Items to Categorize")
        
        for i, item in enumerate(items_to_process):
            with st.container(border=True):
                original_description = item.get('description', 'No description found')
                
                # --- LAYOUT FIX: Adjusted column widths and hiding labels ---
                col_check, col_desc, col_cat = st.columns([0.5, 4, 3]) # Gave checkbox less, but enough, space
                
                with col_check:
                    # Hide the "Include" label for a cleaner look
                    include_item = st.checkbox(
                        "Include", 
                        value=True, 
                        key=f"include_{i}", 
                        label_visibility="collapsed" # THIS HIDES THE TEXT
                    )

                with col_desc:
                    edited_description = st.text_input(
                        "Description", 
                        value=original_description, 
                        key=f"desc_{i}",
                        label_visibility="collapsed"
                    )

                with col_cat:
                    choice = st.selectbox(
                        "Category", 
                        options=category_options, 
                        key=f"choice_{i}", 
                        label_visibility="collapsed"
                    )

                    final_category = ""
                    if choice == new_cat_option:
                        new_cat_input = st.text_input("Enter new category name:", key=f"new_cat_{i}")
                        final_category = new_cat_input.strip()
                    else:
                        final_category = choice
                    
                user_inputs.append({
                    'include': include_item, 
                    'description': edited_description, 
                    'category': final_category
                })
        
        st.markdown("")
        submitted = st.form_submit_button("💾 Save All Categories to Database", use_container_width=True)

    if submitted:
        # Get the latest values from the UI fields
        group_name_to_save = st.session_state.group_name
        activity_name_to_save = st.session_state.activity_name

        # --- NEW VALIDATION STEP ---
        # Check if the group name provided by the user contains at least one digit.
        if not any(char.isdigit() for char in group_name_to_save):
            st.error(f"⚠️ Validation Error: The 'Group Name' must contain a number (e.g., 'GRP 1'). Please correct it.")
            # st.stop() is a powerful command that halts the script here.
            st.stop()

        # --- Filter the list to only include items the user wants ---
        items_to_save = [item for item in user_inputs if item['include']]

        # Validation now only runs on the items to be saved.
        is_valid = all(item['description'] and item['category'] for item in items_to_save)

        if not items_to_save:
            st.warning("⚠️ No items were selected to be saved.")
        elif not is_valid:
            st.warning("⚠️ For all included items, please ensure a description and category are filled.")
        else:
            with st.spinner("Saving data..."):
                # We can now safely get the number, knowing the validation passed.
                kumpulan_no = get_kumpulan_number(group_name_to_save)

                # --- The final data to be inserted is now based on the filtered list ---
                final_data_to_insert = [
                    {
                        'group_no': kumpulan_no,
                        'description': item['description'],
                        'category_name': item['category']
                    }
                    for item in items_to_save
                ]

                records_inserted = db_manager.insert_diagram_data(
                    final_data_to_insert, schema, activity_name_to_save
                )

                if records_inserted > 0:
                    db_manager.create_category_views(schema)
                    st.success(f"✅ Success! {records_inserted} records were saved.")
                    st.balloons()
                elif len(final_data_to_insert) == 0:
                     st.info("No items were marked to be saved to the database.")
                else:
                    st.error("❌ No records were inserted. An error occurred.")
    
    if st.button("Process Another Image"):
        reset_to_setup()
        st.rerun()
