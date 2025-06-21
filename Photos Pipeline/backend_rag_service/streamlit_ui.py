import streamlit as st
import requests

st.set_page_config(page_title="SecurePhotos Search", layout="wide")
st.title("🔍 Semantic Image Search (Qdrant)")

query = st.text_input("Enter your query:", placeholder="e.g. a majestic white lion roaring")

if st.button("Search") and query.strip():
    with st.spinner("Searching images..."):
        response = requests.post("http://localhost:8000/query", json={"query": query.strip()})
        if response.status_code == 200:
            results = response.json()
            st.subheader("Top Matching Image Results")
            for res in results["image_results"]:
                st.markdown(f"**URL:** {res['image_url']}")
                st.markdown(f"**Summary:** {res['summary']}")
                st.markdown("---")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
