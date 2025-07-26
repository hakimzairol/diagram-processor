# pages/2_🐠_Fishbone_Processor.py

import streamlit as st
import pandas as pd
import json
import db_manager
import gemini_client

# --- Page Configuration ---
st.set_page_config(
    page_title="Fishbone Processor",
    page_icon="🐠",
    layout="wide"
)

st.title("🐠 Fishbone Diagram Processor")
st.markdown("---")

# --- Initialize Database Table ---
# This runs once and ensures the table exists before we do anything else.
db_manager.create_fishbone_table_if_not_exists()

# --- State Management ---
def initialize_state():
    """Initializes the session state variables."""
    if 'fishbone_stage' not in st.session_state:
        st.session_state.fishbone_stage = 'setup'
    if 'fishbone_ai_data' not in st.session_state:
        st.session_state.fishbone_ai_data = None
    if 'fishbone_editable_df' not in st.session_state:
        st.session_state.fishbone_editable_df = None

def reset_to_setup():
    """Resets the state to the beginning."""
    st.session_state.fishbone_stage = 'setup'
    st.session_state.fishbone_ai_data = None
    st.session_state.fishbone_editable_df = None

initialize_state()

# --- Helper Function ---
def flatten_ai_data(ai_data):
    """Converts the nested JSON from the AI into a flat list for the data editor."""
    flat_list = []
    # We add a check for 'causes' to prevent errors if the AI returns a different structure
    if 'causes' not in ai_data:
        return []
        
    for cause_group in ai_data.get('causes', []):
        main_cause = cause_group.get('main_cause')
        for sub_group in cause_group.get('sub_causes', []):
            sub_cause = sub_group.get('sub_cause')
            for detail in sub_group.get('details', []):
                flat_list.append({
                    'main_cause': main_cause,
                    'sub_cause': sub_cause,
                    'detail': detail
                })
    return flat_list

# ==============================================================================
#                                 STAGE 1: SETUP
# ==============================================================================
if st.session_state.fishbone_stage == 'setup':
    st.header("Step 1: Upload Your Diagram")
    
    # We'll use a unique session name for the fishbone data
    # Let's retrieve this from the AI data later instead of asking upfront
    
    with st.form("setup_form_fishbone"):
        session_name = st.text_input("Enter a unique Session Name for this diagram:",
                                     help="E.g., 'ucam_marketing_q1_2024'. This will be the unique identifier.")
        uploaded_file = st.file_uploader("Upload your Fishbone Diagram image", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("🧠 Process with AI")

    if submitted and uploaded_file and session_name:
        with st.spinner("The AI is analyzing your diagram... this may take a moment."):
            try:
                image_bytes = uploaded_file.getvalue()
                json_string = gemini_client.get_gemini_response(image_bytes, 'prompt_fishbone.txt')
                ai_data = json.loads(json_string)
                
                # Store the user-provided session name
                st.session_state.fishbone_session_name = session_name
                st.session_state.fishbone_ai_data = ai_data
                st.session_state.fishbone_stage = 'verify'
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred during AI processing: {e}")
                st.error("The AI may have returned an invalid format. Please try again with a clearer image.")

# ==============================================================================
#                               STAGE 2: VERIFY & EDIT
# ==============================================================================
elif st.session_state.fishbone_stage == 'verify':
    st.header("Step 2: Verify and Correct the Extracted Data")
    st.info("The AI has extracted the data below. Please review, edit, add, or delete rows as needed.")

    ai_data = st.session_state.fishbone_ai_data
    
    st.subheader("Overall Diagram Information")
    col1, col2 = st.columns(2)
    problem_statement = col1.text_input("Problem Statement", value=ai_data.get('problem_statement', ''))
    group_name = col2.text_input("Group/Client Name (Optional)", value=ai_data.get('group_name', ''))

    if st.session_state.fishbone_editable_df is None:
        flat_data = flatten_ai_data(ai_data)
        st.session_state.fishbone_editable_df = pd.DataFrame(flat_data)

    df = st.session_state.fishbone_editable_df
    
    main_cause_options = pd.unique(df['main_cause'].dropna()).tolist() if 'main_cause' in df.columns else []
    sub_cause_options = pd.unique(df['sub_cause'].dropna()).tolist() if 'sub_cause' in df.columns else []

    st.subheader("Causal Details")
    st.write("Use the table below to edit details and re-assign causes. You can add and delete rows.")
    
    edited_df = st.data_editor(
        df,
        column_config={
            "main_cause": st.column_config.SelectboxColumn("Main Cause", options=main_cause_options, required=True),
            "sub_cause": st.column_config.SelectboxColumn("Sub Cause", options=sub_cause_options, required=True),
            "detail": st.column_config.TextColumn("Detail", required=True),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor_fishbone"
    )
    
    st.markdown("---")

    col_save, col_reset = st.columns(2)
    if col_save.button("💾 Save All Verified Data to Database", type="primary", use_container_width=True):
        verified_data_list = edited_df.to_dict('records')
        
        with st.spinner("Saving to database..."):
            records_inserted = db_manager.insert_fishbone_data(
                session_name=st.session_state.fishbone_session_name,
                problem_statement=problem_statement,
                group_name=group_name,
                verified_data=verified_data_list
            )
            
            if records_inserted > 0:
                st.session_state.fishbone_stage = 'saved'
                st.rerun()
            else:
                st.error("Failed to save data. Please check the logs.")

    if col_reset.button("❌ Start Over", use_container_width=True):
        reset_to_setup()
        st.rerun()

# ==============================================================================
#                                 STAGE 3: SAVED
# ==============================================================================
elif st.session_state.fishbone_stage == 'saved':
    st.success("✅ Success! All data has been saved to the database.")
    st.balloons()
    
    st.write("You can now view this data in the 'Fishbone Dashboard' or process another diagram.")
    
    if st.button("Process Another Diagram"):
        reset_to_setup()
        st.rerun()