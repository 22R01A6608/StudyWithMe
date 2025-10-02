
# app.py
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pypdf
import io
import pyperclip  # NEW: For copy to clipboard functionality (will simulate in Colab)

# Load environment variables from .env file
load_dotenv("key.env")

# --- Configuration ---
gemini_api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=gemini_api_key)
if not gemini_api_key:
    st.error("GEMINI_API_KEY not found. Please set it in a .env file or as an environment variable.")
    st.stop()

# Initialize the Generative Model
try:
    model = genai.GenerativeModel("gemini-pro-latest")
except Exception as e:
    st.error(f"Failed to initialize Gemini model. Please check your API key and network connection: {e}")
    st.stop()

# --- Helper Function to Extract Text from PDF ---
def extract_text_from_pdf(uploaded_file):
    pdf_reader = pypdf.PdfReader(uploaded_file)
    text_content = ""
    for page in pdf_reader.pages:
        text_content += page.extract_text() + "\n"
    return text_content

# --- Streamlit UI Layout ---
st.set_page_config(
    page_title="🧠 AI-Powered Study Buddy",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 AI-Powered Study Buddy")
st.markdown("Your intelligent companion for simplified learning, summaries, and quick quizzes!")

st.markdown("---")

# --- Function to display AI output with copy button and expander ---
def display_ai_output(output_text, label="AI Output", key_prefix="output"):
    if output_text:
        # NEW: Copy to clipboard functionality (simplified for Streamlit/Colab)
        # Streamlit doesn't have a native copy-to-clipboard widget yet.
        # This is a common workaround using st.text_area to allow easy copy-pasting.
        # For true one-click copy, JS would be needed, or community components.
        st.subheader(label)
        output_container = st.container()
        with output_container:
            st.text_area(
                "Copy to Clipboard:",
                value=output_text,
                height=150, # Adjusted height for visibility
                key=f"{key_prefix}_copy_area",
                help="Select the text above and press Ctrl+C (Cmd+C) to copy."
            )
            # NEW: Expander for long outputs
            with st.expander("Read Full Output"):
                st.markdown(output_text)
    else:
        st.info("AI output will appear here.")


# --- Feature 1: Explain a Concept ---
st.header("💡 Explain a Concept")
st.markdown("Enter any complex concept, and the AI will explain it in simple, easy-to-understand terms.")

# NEW: Use st.session_state for clearing inputs and outputs
if "explain_input" not in st.session_state:
    st.session_state.explain_input = ""
if "explain_output" not in st.session_state:
    st.session_state.explain_output = ""

st.subheader("Input") # NEW: Clearer label
concept_input = st.text_area(
    "What concept would you like to understand better?",
    value=st.session_state.explain_input, # Bind to session_state
    placeholder="e.g., Quantum Entanglement, Supply Chain Management, Photosynthesis",
    height=100,
    key="concept_area"
)

col_exp_1, col_exp_2 = st.columns([1, 0.15]) # NEW: Columns for buttons
with col_exp_1:
    if col_exp_1.button("Explain Concept", use_container_width=True):
        if concept_input:
            st.session_state.explain_input = concept_input # Save input to state
            with st.spinner("AI is thinking..."):
                prompt = f"Explain the following concept in simple terms for a student, focusing on clarity and easy understanding: {concept_input}"
                try:
                    response = model.generate_content(prompt)
                    st.session_state.explain_output = response.text # Save output to state
                except Exception as e:
                    st.error(f"Error generating explanation: {e}")
                    st.session_state.explain_output = f"Error: {e}"
        else:
            st.warning("Please enter a concept to explain.")
            st.session_state.explain_output = "" # Clear output if no input

with col_exp_2: # NEW: Clear button for explanation
    if col_exp_2.button("Clear", key="clear_explain"):
        st.session_state.explain_input = ""
        st.session_state.explain_output = ""
        st.experimental_rerun() # Rerun to clear text_area immediately

display_ai_output(st.session_state.explain_output, label="Explanation Output", key_prefix="explain") # NEW: Use helper function

st.markdown("---")

# --- Feature 2: Summarize Notes (Updated with PDF upload and Level 1 enhancements) ---
st.header("📝 Summarize Notes")
st.markdown("Paste your study notes below, or upload a PDF document, and the AI will provide a concise summary.")

if "summarize_input" not in st.session_state:
    st.session_state.summarize_input = ""
if "summarize_output" not in st.session_state:
    st.session_state.summarize_output = ""
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None


st.subheader("Input") # NEW: Clearer label
notes_input = st.text_area(
    "Paste your study notes here:",
    value=st.session_state.summarize_input, # Bind to session_state
    placeholder="e.g., [Paste a paragraph or two of your lecture notes]",
    height=200,
    key="notes_area"
)
# NEW: Character/Word Count
char_count = len(notes_input)
word_count = len(notes_input.split())
st.caption(f"Characters: {char_count} | Words: {word_count}")

st.markdown("--- OR ---")

uploaded_file = st.file_uploader("Upload a PDF document:", type=["pdf"], key="pdf_uploader")


col_sum_1, col_sum_2 = st.columns([1, 0.15]) # NEW: Columns for buttons
with col_sum_1:
    summarize_button = col_sum_1.button("Summarize Content", use_container_width=True)

with col_sum_2: # NEW: Clear button for summarization
    if col_sum_2.button("Clear", key="clear_summarize"):
        st.session_state.summarize_input = ""
        st.session_state.summarize_output = ""
        st.session_state.uploaded_file = None
        st.experimental_rerun() # Rerun to clear text_area and file_uploader

if summarize_button:
    content_to_summarize = ""
    if uploaded_file is not None:
        st.write("Processing PDF...")
        try:
            content_to_summarize = extract_text_from_pdf(uploaded_file)
            st.session_state.uploaded_file = uploaded_file # Save uploaded file to state
            if not content_to_summarize.strip():
                st.warning("Could not extract readable text from the PDF. Please try pasting notes directly.")
                st.session_state.summarize_output = "Error: Could not extract readable text from PDF."
                content_to_summarize = "" # Clear content to prevent sending empty prompt
        except Exception as e:
            st.error(f"Error reading PDF: {e}. Please ensure it's a valid PDF or try pasting text.")
            st.session_state.summarize_output = f"Error reading PDF: {e}"
            content_to_summarize = ""

    elif notes_input:
        content_to_summarize = notes_input
        st.session_state.summarize_input = notes_input # Save input to state

    if content_to_summarize:
        MAX_CHARS_FOR_GEMINI = 50000
        original_length = len(content_to_summarize)

        if original_length > MAX_CHARS_FOR_GEMINI:
            st.warning(
                f"Your input is very long ({original_length} characters). "
                f"Summarizing the first {MAX_CHARS_FOR_GEMINI} characters to fit AI limits. "
                "For very long documents, consider summarizing in chunks."
            )
            content_to_summarize = content_to_summarize[:MAX_CHARS_FOR_GEMINI]

        with st.spinner("AI is summarizing..."):
            prompt = f"Summarize the following study notes concisely, highlighting the main points and key takeaways. Aim for a summary that captures the essence of the notes: {content_to_summarize}"
            try:
                response = model.generate_content(prompt)
                st.session_state.summarize_output = response.text # Save output to state
            except Exception as e:
                st.error(f"Error generating summary: {e}")
                st.session_state.summarize_output = f"Error: {e}"
                st.exception(e)
    else:
        st.warning("Please paste notes or upload a PDF document to summarize.")
        st.session_state.summarize_output = "" # Clear output if no input

display_ai_output(st.session_state.summarize_output, label="Summary Output", key_prefix="summarize") # NEW: Use helper function

st.markdown("---")

# --- Feature 3: Generate Quizzes/Flashcards (Updated with Level 1 enhancements) ---
st.header("🎲 Generate Quizzes/Flashcards")
st.markdown("Get practice questions or flashcards on any topic to test your knowledge.")

if "quiz_topic_input" not in st.session_state:
    st.session_state.quiz_topic_input = ""
if "quiz_flashcard_output" not in st.session_state:
    st.session_state.quiz_flashcard_output = ""

st.subheader("Input") # NEW: Clearer label
quiz_topic_input = st.text_input(
    "Enter a topic for your quiz or flashcards:",
    value=st.session_state.quiz_topic_input, # Bind to session_state
    placeholder="e.g., Cell Biology, World War II, Calculus Integration",
    key="quiz_topic"
)

col_quiz_1, col_quiz_2, col_quiz_3 = st.columns([0.45, 0.45, 0.1]) # NEW: Columns for buttons
with col_quiz_1:
    if col_quiz_1.button("Generate Quiz", use_container_width=True):
        if quiz_topic_input:
            st.session_state.quiz_topic_input = quiz_topic_input # Save input to state
            with st.spinner("AI is creating a quiz..."):
                prompt = f"Generate a short quiz (3-4 questions) with answers on the topic of '{quiz_topic_input}'. Include various question types like multiple-choice, true/false, and short answer. Clearly label questions and answers."
                try:
                    response = model.generate_content(prompt)
                    st.session_state.quiz_flashcard_output = response.text # Save output to state
                except Exception as e:
                    st.error(f"Error generating quiz: {e}")
                    st.session_state.quiz_flashcard_output = f"Error: {e}"
        else:
            st.warning("Please enter a topic for the quiz.")
            st.session_state.quiz_flashcard_output = "" # Clear output if no input

with col_quiz_2:
    if col_quiz_2.button("Generate Flashcards", use_container_width=True):
        if quiz_topic_input:
            st.session_state.quiz_topic_input = quiz_topic_input # Save input to state
            with st.spinner("AI is making flashcards..."):
                prompt = f"""Generate 3-4 flashcards for studying '{quiz_topic_input}'. For each flashcard, provide a clear question/term on the "front" and its answer/definition on the "back". Format each flashcard clearly, for example:
                **Flashcard 1 - Front:** [Question]
                **Flashcard 1 - Back:** [Answer]"""
                try:
                    response = model.generate_content(prompt)
                    st.session_state.quiz_flashcard_output = response.text # Save output to state
                except Exception as e:
                    st.error(f"Error generating flashcards: {e}")
                    st.session_state.quiz_flashcard_output = f"Error: {e}"
        else:
            st.warning("Please enter a topic for flashcards.")
            st.session_state.quiz_flashcard_output = "" # Clear output if no input

with col_quiz_3: # NEW: Clear button for quiz/flashcards
    if col_quiz_3.button("Clear", key="clear_quiz"):
        st.session_state.quiz_topic_input = ""
        st.session_state.quiz_flashcard_output = ""
        st.experimental_rerun() # Rerun to clear text_input immediately

display_ai_output(st.session_state.quiz_flashcard_output, label="Quiz / Flashcard Output", key_prefix="quiz") # NEW: Use helper function

st.markdown("---")
st.caption("Powered by Google Gemini Pro and Streamlit")