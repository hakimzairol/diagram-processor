# Home.py
import streamlit as st

st.set_page_config(
    page_title="Diagram Processor Home",
    page_icon="🏠",
    layout="wide"
)

st.title("Welcome to the Diagram Processor Suite! 🏠")
st.markdown("---")

st.header("What would you like to do today?")
st.write("Please select a tool from the sidebar on the left.")

st.subheader("Here's a quick guide:")
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("#### 🧠 Mind Map Processor")
        st.write("Use this tool for simple lists or mind maps.")
        st.write("Ideal for extracting a flat list of items and assigning them to categories.")
        st.info("Your existing data is safe here!")

with col2:
    with st.container(border=True):
        st.markdown("#### 🐠 Fishbone Analyzer")
        st.write("Use this tool for complex Fishbone (Ishikawa) diagrams.")
        st.write("Designed to capture the relationship between main causes, sub-causes, and specific details.")
        st.success("✨ New Feature!")

st.markdown("---")
st.write("Developed with guidance from a helpful AI assistant.")