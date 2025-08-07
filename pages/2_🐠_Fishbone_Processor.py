# pages/2_🐠_Fishbone_Processor.py
import streamlit as st
import pandas as pd
import json
import db_manager
import gemini_client

# --- Page Configuration ---
st.set_page_config(page_title="Fishbone Processor", page_icon="🐠", layout="wide")
st.title("🐠 Fishbone Diagram Processor")
st.markdown("---")

# Run all necessary table creation/migration functions at the start
db_manager.create_fishbone_table_if_not_exists()
db_manager.create_fishbone_sessions_table()
db_manager.add_comment_column_if_not_exists()


# --- State Management ---
def initialize_state():
    if 'fishbone_stage' not in st.session_state: st.session_state.fishbone_stage = 'setup'
    if 'fishbone_ai_data' not in st.session_state: st.session_state.fishbone_ai_data = None
    if 'fishbone_session_name' not in st.session_state: st.session_state.fishbone_session_name = ""

def reset_to_setup():
    st.session_state.fishbone_stage = 'setup'
    st.session_state.fishbone_ai_data = None
    st.session_state.fishbone_session_name = ""
    if 'fishbone_editable_df' in st.session_state: del st.session_state['fishbone_editable_df']

initialize_state()

# --- Helper Function ---
def flatten_ai_data(ai_data):
    flat_list = []
    if 'causes' not in ai_data: return []
    for cause_group in ai_data.get('causes', []):
        main_cause = cause_group.get('main_cause', '')
        sub_causes_list = cause_group.get('sub_causes', [{'sub_cause': '', 'details': cause_group.get('details', [])}])
        if not sub_causes_list: sub_causes_list = [{'sub_cause': '', 'details': cause_group.get('details', [])}]

        for sub_group in sub_causes_list:
            sub_cause = sub_group.get('sub_cause', '')
            for detail in sub_group.get('details', []):
                flat_list.append({'main_cause': main_cause, 'sub_cause': sub_cause, 'detail': detail})
    return flat_list

# --- STAGE 1: SETUP ---
if st.session_state.fishbone_stage == 'setup':
    st.header("Step 1: Upload Your Diagram")
    session_name = st.text_input("Enter a unique Session Name:", help="E.g., 'ucam_marketing_q1_2024'")
    uploaded_file = st.file_uploader("Upload your Fishbone Diagram image", type=["png", "jpg", "jpeg"])
    if st.button("🧠 Process with AI", disabled=(not session_name or not uploaded_file)):
        with st.spinner("The AI is analyzing your diagram..."):
            image_bytes = uploaded_file.getvalue()
            json_string = gemini_client.get_gemini_response(image_bytes, 'prompt_fishbone.txt')
            try:
                ai_data = json.loads(json_string)
                st.session_state.fishbone_session_name = session_name
                st.session_state.fishbone_ai_data = ai_data
                st.session_state.fishbone_stage = 'verify'
                st.rerun()
            except (json.JSONDecodeError, KeyError) as e:
                st.error(f"AI Extraction Failed. Error: {e}. The AI may have returned an invalid format.")
                st.code(json_string, language='json')

# --- STAGE 2: VERIFY & EDIT ---
elif st.session_state.fishbone_stage == 'verify':
    st.header("Step 2: Verify and Correct the Extracted Data")
    st.info("Double-click any cell to edit it. You can add or delete rows.")

    ai_data = st.session_state.fishbone_ai_data
    
    col1, col2 = st.columns(2)
    problem_statement = col1.text_input("Problem Statement", value=ai_data.get('problem_statement', ''))
    group_name = col2.text_input("Group/Client Name (Optional)", value=ai_data.get('group_name', ''))
    session_comments = st.text_area("Session Comments (Optional)", height=100)

    if 'fishbone_editable_df' not in st.session_state:
        df_temp = pd.DataFrame(flatten_ai_data(ai_data))
        df_temp = df_temp.fillna('')
        df_temp['row_comment'] = '' # Initialize the comment column
        st.session_state.fishbone_editable_df = df_temp
    
    st.subheader("Causal Details")
    
    edited_df = st.data_editor(
        st.session_state.fishbone_editable_df,
        column_config={
            "include": st.column_config.CheckboxColumn("Include?", default=True),
            "main_cause": st.column_config.TextColumn("Main Cause", required=True),
            "sub_cause": st.column_config.TextColumn("Sub Cause (Optional)"),
            "detail": st.column_config.TextColumn("Detail", required=True),
            "row_comment": st.column_config.TextColumn("Comment (Optional)")
        },
        num_rows="dynamic", use_container_width=True, key="data_editor_final"
    )
    st.session_state.fishbone_editable_df = edited_df
    
    st.markdown("---")

    col_save, col_reset = st.columns(2)
    if col_save.button("💾 Save All Verified Data", type="primary", use_container_width=True):
        df_to_save = edited_df[edited_df['include'] == True] if 'include' in edited_df else edited_df
        is_valid = all(row['main_cause'] and row['detail'] for index, row in df_to_save.iterrows())
        
        if not is_valid:
            st.warning("⚠️ For all included rows, please ensure 'Main Cause' and 'Detail' are filled.")
        else:
            with st.spinner("Saving data and comments..."):
                db_manager.save_fishbone_session_comment(st.session_state.fishbone_session_name, session_comments)
                records_to_insert = df_to_save.drop(columns=['include'], errors='ignore').to_dict('records')
                records_inserted = db_manager.insert_fishbone_data(
                    session_name=st.session_state.fishbone_session_name,
                    problem_statement=problem_statement, group_name=group_name,
                    verified_data=records_to_insert
                )
                if records_inserted > 0 or session_comments:
                    st.session_state.fishbone_stage = 'saved'
                    st.rerun()
                else:
                    st.error("❌ No records were saved to the database.")
    
    if col_reset.button("❌ Start Over", use_container_width=True):
        reset_to_setup(); st.rerun()

# --- STAGE 3: SAVED ---
elif st.session_state.fishbone_stage == 'saved':
    st.success("✅ Success! All data has been saved to the database.")
    st.balloons()
    st.write("You can now view this data in the 'Fishbone Dashboard' or process another diagram.")
    if st.button("Process Another Diagram"):
        reset_to_setup(); st.rerun()