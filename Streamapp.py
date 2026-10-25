import streamlit as st
from openai import OpenAI
import httpx

# 1. App Page Configuration
st.set_page_config(page_title="Free OpenRouter Chatbot", page_icon="🤖")
st.title("🤖 Free OpenRouter Assistant")

# 2. Sidebar for Secure Key Entry
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter OpenRouter API Key", type="password", help="Get a free key from openrouter.ai")
    st.markdown("[Get a Free OpenRouter API Key](https://openrouter.ai/)")
    
    # Using an alternative ultra-stable free model ID
    st.info("Using Free Model: meta-llama/llama-3.3-70b-instruct:free")

# 3. Initialize chat history session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Display historical chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Handle User Input
if prompt := st.chat_input("What is on your mind?"):
    if not api_key:
        st.info("Please add your OpenRouter API key in the sidebar to continue.")
        st.stop()
        
    # Append and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 6. Call OpenRouter API & Stream Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # FIX: Explicitly configure HTTPX client with custom timeouts to prevent networking dropouts
            http_client = httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0))
            
            # Point the client to OpenRouter's endpoints with MANDATORY platform tracking headers
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                http_client=http_client,
                default_headers={
                    "HTTP-Referer": "http://localhost:8501", # Required by OpenRouter
                    "X-Title": "Local Streamlit Test App"      # Required by OpenRouter
                }
            )
            
            # FIX: Switched to a highly stable free model tier endpoint
            response = client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True
            )
            
            # FIX: Robust token streaming check to eliminate formatting crashes
            for chunk in response:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_response += delta.content
                        message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            # Capture the exact network message if it still breaks
            st.error(f"Network Connection Failed: {str(e)}")
            st.info("💡 If you are behind a corporate proxy or VPN, try disabling it, or check your internet connection.")
