# 📋 Resume Review Agent

A minimal, reliable, single-agent AI application built with **CrewAI**, **Streamlit**, and **Groq** that compares resumes against target job descriptions and provides structured gap analysis without hallucinating unstated qualifications.

## 🌟 Key Features
- **Strict Accuracy Rule:** Evaluates candidates solely on explicit evidence provided in the resume. Unmentioned qualifications are categorized as missing or non-demonstrated.
- **Dual Input Methods:** Supports direct text pasting or uploading PDF resumes (`pypdf`).
- **Structured 9-Part Analysis:** Provides Match Summary, Skills Found, Missing Requirements, Experience Gaps, Education Gaps, Resume Improvements, Keywords, and an Action Plan.
- **In-Memory Privacy:** Inputs are processed in-memory and are never written to disk or saved in databases.

## 🛠️ Local Development Setup

### 1. Clone or Extract Project
Extract `resume-review-agent.zip` and open the directory:
```bash
cd resume-review-agent
```

### 2. Create Python 3.11 Environment
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Local Secrets
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add your Groq API key:
```toml
GROQ_API_KEY = "gsk_your_actual_groq_api_key_here"
GROQ_MODEL = "groq/openai/gpt-oss-120b"
```

### 5. Launch the Application
```bash
streamlit run app.py
```

## 🔒 Privacy Notice
No resume or job description content is stored permanently by this application. Data is transferred securely to Groq APIs purely for model evaluation and discarded from memory upon completion.
