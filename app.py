import streamlit as st
import requests
import io
import csv

# ✅ Backend API
API_BASE_URL = "https://post-generator-2.onrender.com"
UNSPLASH_ACCESS_KEY = "q36fBLF488CCnNh8T08hDL7sfe8RR-yRYYxhumtlkoY"

# ✅ Initialize session state
st.session_state.setdefault("token", "")
st.session_state.setdefault("generated_post", "")
st.session_state.setdefault("image_url", "")
st.session_state.setdefault("is_logged_in", False)

# ✅ API calls
def signup(username, password):
    try:
        return requests.post(f"{API_BASE_URL}/signup", json={"username": username, "password": password})
    except Exception as e:
        st.error(f"Signup API error: {e}")
        return None

def login(username, password):
    try:
        return requests.post(f"{API_BASE_URL}/token", data={"username": username, "password": password})
    except Exception as e:
        st.error(f"Login API error: {e}")
        return None

def fetch_unsplash_image(topic, client_id):
    url = f"https://api.unsplash.com/photos/random?query={topic}&client_id={client_id}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json().get("urls", {}).get("regular", "https://picsum.photos/600/400")
    except Exception as e:
        st.warning(f"Image fetch failed: {e}")
        return "https://picsum.photos/600/400"

# ✅ UI: App Title
st.title("📝 Social Media Post Generator")

# ✅ UI: Auth Section
with st.expander("🔐 Signup or Login"):
    auth_tab = st.radio("Choose Action", ["Login", "Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if auth_tab == "Signup":
        if st.button("Sign Up"):
            res = signup(username, password)
            if res and res.status_code == 201:
                st.success("✅ Signup successful. Please log in.")
            elif res:
                st.error(f"Signup failed: {res.json().get('detail', res.text)}")
    else:
        if st.button("Login"):
            res = login(username, password)
            if res and res.status_code == 200:
                st.session_state.token = res.json().get("access_token")
                st.session_state.is_logged_in = True
                st.success("✅ Login successful!")
            elif res:
                st.error(f"Login failed: {res.json().get('detail', res.text)}")

# ✅ Stop if not logged in
if not st.session_state.token:
    st.warning("Please login to use the generator.")
    st.stop()

# ✅ Post Generation Inputs
topic = st.text_input("📌 Enter a topic")
platform = st.selectbox("📱 Select platform", ["Facebook", "Twitter", "Instagram", "LinkedIn"])

if st.button("🚀 Generate Post"):
    if not topic:
        st.error("Please enter a topic.")
    else:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        data = {"topic": topic, "platform": platform}

        try:
            with st.spinner("Generating post..."):
                res = requests.post(f"{API_BASE_URL}/generate_post", json=data, headers=headers)
                res.raise_for_status()
                st.session_state.generated_post = res.json().get("post", "")
                st.session_state.image_url = fetch_unsplash_image(topic, UNSPLASH_ACCESS_KEY)
        except requests.exceptions.HTTPError as e:
            st.error(f"Error {e.response.status_code}: {e.response.json().get('detail', '')}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ✅ Show Generated Post
if st.session_state.generated_post:
    st.subheader("✏️ Generated Post")
    edited_post = st.text_area("You can edit it:", value=st.session_state.generated_post, height=200)
    st.session_state.generated_post = edited_post

    st.download_button("⬇️ Download as TXT", data=edited_post, file_name="post.txt", mime="text/plain")

    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow(["Post"])
    writer.writerow([edited_post])
    st.download_button("⬇️ Download as CSV", data=csv_buf.getvalue(), file_name="post.csv", mime="text/csv")

    st.markdown("💡 To copy: select the text above and press `Ctrl+C` (or `Cmd+C` on Mac).")

# ✅ Show Image
if st.session_state.image_url:
    st.image(st.session_state.image_url, caption=f"Image for '{topic}'", use_column_width=True)
