import streamlit as st
import requests
import io
import csv
from fastapi import FastAPI

app = FastAPI()

API_URL = "http://127.0.0.1:8000/generate_post"
UNSPLASH_ACCESS_KEY = "q36fBLF488CCnNh8T08hDL7sfe8RR-yRYYxhumtlkoY"

# Initialize session state variables if missing
if "token" not in st.session_state:
    st.session_state.token = ""

if "generated_post" not in st.session_state:
    st.session_state.generated_post = ""

if "image_url" not in st.session_state:
    st.session_state.image_url = ""

def fetch_unsplash_image(topic: str, client_id: str) -> str:
    """
    Fetch a random relevant image URL from Unsplash based on the topic.
    Fallback to placeholder image if request fails or no URL found.
    """
    url = f"https://api.unsplash.com/photos/random?query={topic}&client_id={client_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        image_url = data.get('urls', {}).get('regular')
        if image_url:
            return image_url
        else:
            return "https://picsum.photos/600/400"  # fallback image
    except Exception as e:
        st.warning(f"Could not fetch image from Unsplash, using placeholder. Reason: {e}")
        return "https://picsum.photos/600/400"  # fallback image

st.title("Social Media Post Generator")

# User inputs
topic = st.text_input("Enter topic")
platform = st.selectbox("Select platform", ["Twitter", "Facebook", "Instagram", "LinkedIn"])
token = st.text_input("Enter your JWT token", type="password", value=st.session_state.token)

# Save token in session state
if token:
    st.session_state.token = token

# Generate post on button click
if st.button("Generate"):
    if not topic:
        st.error("Please enter a topic.")
    elif not token:
        st.error("Please enter your JWT token.")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        json_data = {"topic": topic, "platform": platform}
        try:
            with st.spinner("Generating post..."):
                response = requests.post(API_URL, json=json_data, headers=headers)
            response.raise_for_status()
            data = response.json()
            post = data.get("post")
            if post:
                st.session_state.generated_post = post

                # Fetch and store related image (with fallback)
                st.session_state.image_url = fetch_unsplash_image(topic, UNSPLASH_ACCESS_KEY)
            else:
                st.error("No post was returned from the backend.")
        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: {e.response.status_code} - {e.response.json().get('detail', '')}")
        except Exception as e:
            st.error(f"Error: {e}")

# Show image if available
if st.session_state.image_url:
    st.image(st.session_state.image_url, caption=f"Image related to '{topic}'", use_column_width=True)

# Show editable text area and download buttons if post is available
if st.session_state.generated_post:
    edited_post = st.text_area("Edit Generated Post", value=st.session_state.generated_post, height=200)
    st.session_state.generated_post = edited_post

    # Download as plain text (.txt)
    st.download_button(
        label="Download Post as TXT",
        data=edited_post,
        file_name="post.txt",
        mime="text/plain"
    )

    # Prepare CSV data
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerow(["Post"])
    csv_writer.writerow([edited_post])

    # Download as CSV (.csv)
    st.download_button(
        label="Download Post as CSV",
        data=csv_buffer.getvalue(),
        file_name="post.csv",
        mime="text/csv"
    )

    st.markdown(
        """
        **Note:** To copy the post text, select the text above and press Ctrl+C (Cmd+C on Mac).
        """
    )
