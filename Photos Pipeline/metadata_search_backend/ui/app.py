import streamlit as st
import requests

st.set_page_config(page_title="📷 Metadata Search", layout="wide")
st.title("🔎 SecurePhotos: Metadata Search")

query = st.text_input("Enter your query:", placeholder="e.g. Photos taken in May 2023 by iPhone")

if st.button("Search") and query.strip():
    with st.spinner("Querying backend..."):
        response = requests.post("http://localhost:8000/metadata-query", json={"query": query})
        if response.status_code == 200:
            results = response.json()
            st.subheader("Top Results:")
            for img in results["matched_images"]:
                st.markdown(f"**URL:** {img['image_url']}")
                st.markdown(f"**Summary:** {img['summary']}")
                st.markdown("---")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
else:
    st.warning("Please enter a query to search for metadata.")
