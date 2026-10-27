import streamlit as st
from src.shark_crew.crew import pitch
from dotenv import load_dotenv
load_dotenv()

st.title("Welcome to Shark Tank!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Tell us whats your idea..."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("The sharks are reviewing your pitch..."):
            
            # (Run your crew here and get crew_result)
            crew_result = pitch(prompt)

            # 3. Render the output inside a styled Markdown container/box
            st.markdown("### 🦈 Shark Panel Verdict")
            
            # If crew_result has structured task outputs, display them cleanly
            if hasattr(crew_result, "tasks_output") and len(crew_result.tasks_output) > 0:
                for idx, task_output in enumerate(crew_result.tasks_output):
                    # Use containers or expanders for each shark's output
                    with st.container(border=True):
                        st.markdown(task_output.raw)
            else:
                # Fallback to general string output
                with st.container(border=True):
                    st.markdown(str(crew_result))