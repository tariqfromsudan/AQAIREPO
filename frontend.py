import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import time
import json

st.set_page_config(page_title="Document Ingestion", page_icon="📄")
st.title("AI Document Processing")

# Securely load credentials for both local and cloud environments
if "STORAGE_CONNECTION_STRING" in st.secrets:
    CONNECTION_STRING = st.secrets["STORAGE_CONNECTION_STRING"]
else:
    CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
    
UPLOAD_CONTAINER = "useruploads"
RESULTS_CONTAINER = "processedresults"

def upload_to_azure(file_name, file_bytes):
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=UPLOAD_CONTAINER, blob=file_name)
    blob_client.upload_blob(file_bytes, overwrite=True)

def wait_for_result(file_name, timeout=60):
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    json_filename = f"{file_name}.json"
    blob_client = blob_service_client.get_blob_client(container=RESULTS_CONTAINER, blob=json_filename)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            download_stream = blob_client.download_blob()
            return json.loads(download_stream.readall())
        except Exception:
            time.sleep(2)
    return None

uploaded_file = st.file_uploader("Upload a file", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    if st.button("Process Document"):
        with st.spinner("Extracting text and generating JSON payload..."):
            bytes_data = uploaded_file.getvalue()
            upload_to_azure(uploaded_file.name, bytes_data)
            
            result_json = wait_for_result(uploaded_file.name, timeout=300)
            
            if result_json:
                st.success("Pipeline execution complete.")
                st.subheader("Transcription Preview")
                st.write(result_json["transcription"])
                
                st.download_button(
                    label="Download JSON for Model Training",
                    file_name=f"{uploaded_file.name}.json",
                    mime="application/json",
                    data=json.dumps(result_json, indent=4)
                )
            else:
                st.error("The request timed out. Please verify backend execution.") 