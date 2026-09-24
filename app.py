import os
import streamlit as st
from pypdf import PdfReader
from crewai import Agent, Task, Crew, LLM

# ==============================================================================
# 1. PAGE CONFIGURATION & PRIVACY NOTICE
# ==============================================================================
st.set_page_config(
    page_title="Resume Review Agent",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Resume Review Agent")
st.write("Compare your resume against a target job description for unbiased, evidence-based feedback.")

st.info(
    "🔒 **Privacy Notice:** Your uploaded resume and job description are processed strictly in-memory "
    "to generate your analysis and are sent securely to the configured Groq LLM provider. "
    "No data is permanently stored, logged, or saved to any database."
)

# ==============================================================================
# 2. CONFIGURATION & SECRETS MANAGEMENT
# ==============================================================================
groq_api_key = st.secrets.get("GROQ_API_KEY")
groq_model = st.secrets.get("GROQ_MODEL", "groq/openai/gpt-oss-120b")

if not groq_api_key:
    st.error(
        "⚠️ **Missing API Key:** `GROQ_API_KEY` was not found in Streamlit Secrets.\n\n"
        "Please add it to `.streamlit/secrets.toml` locally or in the Streamlit Cloud Settings."
    )
    st.stop()

# Set environment variable for internal LiteLLM resolution
os.environ["GROQ_API_KEY"] = groq_api_key

# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================
def extract_text_from_pdf(uploaded_file) -> tuple[str | None, str | None]:
    """
    Extracts text from an uploaded PDF file using pypdf.
    Returns (extracted_text, error_message).
    """
    try:
        reader = PdfReader(uploaded_file)
        if len(reader.pages) == 0:
            return None, "The uploaded PDF contains no pages."
        
        extracted_text = ""
        for index, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n"
        
        cleaned_text = extracted_text.strip()
        if not cleaned_text:
            return None, (
                "Could not extract readable text from the PDF. The file may be a scanned image "
                "or contain non-selectable text. Please paste your resume text manually."
            )
            
        return cleaned_text, None

    except Exception as exc:
        return None, f"Failed to parse PDF file: {str(exc)}"

# ==============================================================================
# 4. USER INPUT SECTION
# ==============================================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Candidate Resume")
    input_type = st.radio("Resume Source:", ["Paste Text", "Upload PDF"], horizontal=True)
    
    resume_text = ""
    if input_type == "Paste Text":
        resume_text = st.text_area(
            "Paste Resume Text:",
            height=300,
            placeholder="Paste your full resume text here..."
        )
    else:
        uploaded_pdf = st.file_uploader("Upload PDF Resume:", type=["pdf"])
        if uploaded_pdf is not None:
            parsed_text, pdf_err = extract_text_from_pdf(uploaded_pdf)
            if pdf_err:
                st.error(f"❌ {pdf_err}")
            else:
                resume_text = parsed_text
                st.success("✅ PDF text successfully extracted.")

with col2:
    st.subheader("2. Target Job Description")
    job_description = st.text_area(
        "Paste Job Description:",
        height=365,
        placeholder="Paste the target job description and requirements here..."
    )

# ==============================================================================
# 5. CREWAI AGENT & TASK EXECUTION
# ==============================================================================
st.markdown("---")
run_analysis = st.button("🚀 Analyze Resume Match", type="primary", use_container_width=True)

if run_analysis:
    if not resume_text.strip():
        st.warning("⚠️ Please provide a candidate resume (via text paste or PDF upload) before running the analysis.")
        st.stop()

    if not job_description.strip():
        st.warning("⚠️ Please provide a target job description before running the analysis.")
        st.stop()

    try:
        with st.spinner("🤖 Agent analyzing resume against job description..."):
            
            # Initialize LLM backend via Groq
            llm = LLM(
                model=groq_model,
                api_key=groq_api_key,
                temperature=0.1
            )

            # Single Resume Review Agent
            auditor_agent = Agent(
                role="Executive Resume Auditor & Recruiter",
                goal=(
                    "Evaluate candidate resumes against target job descriptions with extreme accuracy "
                    "and provide actionable feedback without hallucinating unmentioned skills or experience."
                ),
                backstory=(
                    "You are a hyper-rigorous Executive Recruiter and Resume Auditor with 15+ years of experience. "
                    "Your primary rule is strict factual adherence: you NEVER assume, infer, or fabricate qualifications, "
                    "certifications, tools, employment history, degrees, or experience that are not explicitly stated in the resume. "
                    "If a requirement is missing or unclear, you explicitly mark it as 'Unknown / Not Demonstrated'."
                ),
                allow_delegation=False,
                verbose=False,
                llm=llm
            )

            # Structured Output Evaluation Task
            audit_task = Task(
                description=(
                    "Perform an objective gap analysis comparing the candidate's Resume against the Target Job Description.\n\n"
                    "=== CANDIDATE RESUME ===\n{resume_text}\n\n"
                    "=== TARGET JOB DESCRIPTION ===\n{job_description}\n\n"
                    "STRICT ACCURACY RULES:\n"
                    "1. Rely ONLY on explicit evidence present in the supplied resume.\n"
                    "2. NEVER invent, extrapolate, or assume experience, degrees, projects, achievements, or skills.\n"
                    "3. If a requirement is not clearly supported by the resume, classify it under 'Unclear / Not Demonstrated' "
                    "or 'Missing Requirements'.\n\n"
                    "Produce a structured review containing exact heading titles in Markdown format:\n"
                    "### 1. Match Summary\n"
                    "- Overall Fit Score (0-100%)\n"
                    "- Concise high-level summary of alignment\n\n"
                    "### 2. Skills Found\n"
                    "- Bullet points of required skills explicitly matching the resume\n\n"
                    "### 3. Missing Requirements\n"
                    "- Bullet points of hard requirements in the job description completely absent from the resume\n\n"
                    "### 4. Unclear / Not Demonstrated\n"
                    "- Requirements where evidence is weak, vague, or cannot be fully confirmed\n\n"
                    "### 5. Experience Gaps\n"
                    "- Gaps in required years of experience, leadership scope, or industry domain exposure\n\n"
                    "### 6. Education / Qualification Gaps\n"
                    "- Missing or non-matching degrees, certifications, or licenses\n\n"
                    "### 7. Resume Improvements\n"
                    "- Specific wording, structure, and formatting edits to better highlight matching evidence\n\n"
                    "### 8. Keywords to Consider\n"
                    "- Missing ATS keywords from the job description to weave in (if truthfully possessed)\n\n"
                    "### 9. Priority Action Plan\n"
                    "- Numbered step-by-step priority actions the candidate should take before applying"
                ),
                expected_output="A structured Markdown review adhering strictly to the 9 required section headings.",
                agent=auditor_agent
            )

            # Execute via single-agent Crew
            crew = Crew(
                agents=[auditor_agent],
                tasks=[audit_task]
            )

            result = crew.kickoff(inputs={
                "resume_text": resume_text,
                "job_description": job_description
            })

            st.success("✅ Analysis Complete!")
            st.markdown(result.raw)

    except Exception as exc:
        err_msg = str(exc).lower()
        if "429" in err_msg or "rate_limit" in err_msg:
            st.error("⏳ **Rate Limit Exceeded:** Groq API rate limit reached. Please wait a minute and try again.")
        elif "401" in err_msg or "authentication" in err_msg or "invalid api key" in err_msg:
            st.error("🔑 **Authentication Error:** Invalid Groq API Key. Please verify your secret key in Streamlit.")
        elif "timeout" in err_msg:
            st.error("⌛ **Timeout Error:** The LLM request timed out. Please retry in a few moments.")
        else:
            st.error(f"❌ **An unexpected error occurred:** {str(exc)}")
