
import streamlit as st
import requests
import database

API = "http://127.0.0.1:8000"

SUPPORTED_FILES = ["pdf", "docx", "pptx", "xlsx", "csv", "txt"]


def error_text(r, default):
    try:
        return r.json().get("detail", default)
    except ValueError:
        return default + ": " + r.text[:200]


st.set_page_config(page_title="DocMind", layout="wide")
database.init_db()

st.title("DocMind: Ask your document")


# Initialize chat
if "chat_id" not in st.session_state:
    st.session_state.chat_id = database.create_chat()

if "messages" not in st.session_state:
    st.session_state.messages = database.get_messages(
        st.session_state.chat_id
    )

if "mode_selector" not in st.session_state:
    st.session_state.mode_selector = "Document Mode"


# Handle a clicked suggestion before creating the mode selector
if "next_question_mode" in st.session_state:
    st.session_state.mode_selector = st.session_state.pop(
        "next_question_mode"
    )


# SIDEBAR
with st.sidebar:

    st.header("DocMind")

    # Upload document
    st.subheader("Upload document")

    uploaded = st.file_uploader(
        "Choose a document",
        type=SUPPORTED_FILES,
        key="document_uploader"
    )

    if uploaded and st.button(
        "Process document",
        key="process_document",
        use_container_width=True
    ):
        with st.spinner("Reading and indexing your document..."):
            try:
                response = requests.post(
                    f"{API}/upload",
                    files={
                        "file": (
                            uploaded.name,
                            uploaded.getvalue()
                        )
                    },
                    timeout=300
                )

                if response.ok:
                    st.success(response.json()["message"])

                    st.session_state.chat_id = database.create_chat(
                        uploaded.name
                    )
                    st.session_state.messages = []
                    st.session_state.mode_selector = "Document Mode"
                    st.rerun()
                else:
                    st.error(error_text(response, "Upload failed"))

            except requests.RequestException as e:
                st.error(f"Backend connection error: {e}")

    st.divider()

    # New chat
    if st.button(
        "+ New Chat",
        key="new_chat_button",
        use_container_width=True
    ):
        st.session_state.chat_id = database.create_chat()
        st.session_state.messages = []
        st.session_state.mode_selector = "Document Mode"
        st.rerun()

    st.divider()

    # Recent history
    st.subheader("Recent")

    chats = [
        chat for chat in database.get_chats()
        if chat["title"].strip() != "New Chat"
    ]

    def show_chat_item(chat):

        col1, col2 = st.columns([7, 1])

        with col1:
            if st.button(
                chat["title"],
                key=f"chat_{chat['id']}",
                use_container_width=True
            ):
                st.session_state.chat_id = chat["id"]
                st.session_state.messages = database.get_messages(
                    chat["id"]
                )
                st.rerun()

        with col2:
            with st.popover("⋯"):
                if st.button(
                    "Delete Chat",
                    key=f"delete_{chat['id']}"
                ):
                    database.delete_chat(chat["id"])

                    if st.session_state.chat_id == chat["id"]:
                        st.session_state.chat_id = database.create_chat()
                        st.session_state.messages = []

                    st.rerun()

    for chat in chats[:3]:
        show_chat_item(chat)

    if len(chats) > 3:
        with st.expander("View all chats"):
            for chat in chats[3:]:
                show_chat_item(chat)

    st.divider()

    # Delete history
    with st.expander("Delete History"):

        st.warning("This will delete all conversations.")

        confirm = st.checkbox(
            "I want to delete all history",
            key="confirm_delete"
        )

        if st.button(
            "Delete All History",
            disabled=not confirm,
            key="delete_all"
        ):
            database.delete_all_chats()
            st.session_state.chat_id = database.create_chat()
            st.session_state.messages = []
            st.rerun()


# MODE SELECTOR
st.radio(
    "Choose your mode",
    ["Document Mode", "General AI Mode"],
    horizontal=True,
    key="mode_selector"
)

current_mode = st.session_state.mode_selector

if current_mode == "Document Mode":
    st.caption("Ask questions about your uploaded document.")
else:
    st.caption("Ask general questions and learn about anything.")


# DISPLAY CHAT HISTORY
for message_index, message in enumerate(st.session_state.messages):

    with st.chat_message(message["role"]):

        st.write(message["content"])

        sources = message.get("sources", [])

        if sources:
            with st.expander(f"Sources ({len(sources)})"):

                for source in sources:
                    location = source.get(
                        "location",
                        f"Page {source.get('page', 1)}"
                    )

                    st.caption(location)
                    st.write(source["text"])

        suggestions = message.get("suggestions", {})

        if isinstance(suggestions, dict):

            document_questions = suggestions.get(
                "document_questions", []
            )

            general_questions = suggestions.get(
                "general_questions", []
            )

            if document_questions:
                st.markdown("**Related to your document**")

                for i, item in enumerate(document_questions):

                    if st.button(
                        item,
                        key=f"doc_suggestion_{message_index}_{i}"
                    ):
                        st.session_state.next_question = item
                        st.session_state.next_question_mode = "Document Mode"
                        st.rerun()

            if general_questions:
                st.markdown("**Explore more with AI**")

                for i, item in enumerate(general_questions):

                    if st.button(
                        item,
                        key=f"general_suggestion_{message_index}_{i}"
                    ):
                        st.session_state.next_question = item
                        st.session_state.next_question_mode = "General AI Mode"
                        st.rerun()

        elif isinstance(suggestions, list) and suggestions:
            for i, item in enumerate(suggestions):
                if st.button(
                    item,
                    key=f"old_suggestion_{message_index}_{i}"
                ):
                    st.session_state.next_question = item
                    st.session_state.next_question_mode = "Document Mode"
                    st.rerun()


# CHAT INPUT
# Always display the typing bar
typed_question = st.chat_input("Ask DocMind anything...")

suggested_question = st.session_state.pop(
    "next_question", None
)

question = suggested_question or typed_question


# PROCESS QUESTION
if question:

    history = [
        {
            "role": message["role"],
            "content": message["content"]
        }
        for message in st.session_state.messages
    ]

    mode = (
        "general"
        if current_mode == "General AI Mode"
        else "document"
    )

    database.save_message(
        st.session_state.chat_id,
        "user",
        question
    )

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        with st.spinner("DocMind is thinking..."):

            try:
                response = requests.post(
                    f"{API}/ask",
                    json={
                        "question": question,
                        "history": history,
                        "mode": mode
                    },
                    timeout=120
                )

                if response.ok:

                    data = response.json()

                    answer_text = data["answer"]
                    sources = data.get("sources", [])
                    suggestions = data.get("suggestions", {})

                    st.write(answer_text)

                    if sources:
                        with st.expander(
                            f"Sources ({len(sources)})"
                        ):
                            for source in sources:
                                location = source.get(
                                    "location",
                                    f"Page {source.get('page', 1)}"
                                )
                                st.caption(location)
                                st.write(source["text"])

                    database.save_message(
                        st.session_state.chat_id,
                        "assistant",
                        answer_text,
                        sources,
                        suggestions
                    )

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer_text,
                        "sources": sources,
                        "suggestions": suggestions
                    })

                    # Display document suggestions
                    if isinstance(suggestions, dict):

                        document_questions = suggestions.get(
                            "document_questions", []
                        )

                        general_questions = suggestions.get(
                            "general_questions", []
                        )

                        if document_questions:
                            st.markdown("**Related to your document**")

                            for i, item in enumerate(document_questions):
                                if st.button(
                                    item,
                                    key=f"new_doc_{len(st.session_state.messages)}_{i}"
                                ):
                                    st.session_state.next_question = item
                                    st.session_state.next_question_mode = "Document Mode"
                                    st.rerun()

                        if general_questions:
                            st.markdown("**Explore more with AI**")

                            for i, item in enumerate(general_questions):
                                if st.button(
                                    item,
                                    key=f"new_general_{len(st.session_state.messages)}_{i}"
                                ):
                                    st.session_state.next_question = item
                                    st.session_state.next_question_mode = "General AI Mode"
                                    st.rerun()

                else:
                    st.error(error_text(response, "Something went wrong"))

            except requests.RequestException as e:
                st.error(f"Could not connect to backend: {e}")
