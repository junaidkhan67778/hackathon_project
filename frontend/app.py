import streamlit as st
import requests
import json
import time
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Insurance Coverage Assistant",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Sophisticated CSS styling with subtle colors
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main container */
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    /* Header section */
    .header-section {
        text-align: center;
        margin-bottom: 3rem;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        color: white;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
    }
    
    .header-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .header-subtitle {
        font-size: 1.1rem;
        font-weight: 300;
        opacity: 0.95;
        margin-top: 0.5rem;
    }
    
    /* Card styling */
    .card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(15, 23, 42, 0.12);
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .section-description {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    
    /* File upload styling */
    .stFileUploader > div > div {
        border: 2px dashed #cbd5e1 !important;
        border-radius: 12px !important;
        background: #f8fafc !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader > div > div:hover {
        border-color: #667eea !important;
        background: #f1f5f9 !important;
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        padding: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        background: #fefefe !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Result cards */
    .result-covered {
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
        border: 1px solid #bbf7d0;
        border-left: 4px solid #10b981;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
    }
    
    .result-not-covered {
        background: linear-gradient(135deg, #fef2f2 0%, #fefefe 100%);
        border: 1px solid #fecaca;
        border-left: 4px solid #ef4444;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
    }
    
    .result-review {
        background: linear-gradient(135deg, #fffbeb 0%, #fefce8 100%);
        border: 1px solid #fde68a;
        border-left: 4px solid #f59e0b;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);
    }
    
    .result-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .result-text {
        font-size: 1rem;
        line-height: 1.6;
        margin-bottom: 1rem;
        color: #374151;
    }
    
    .confidence-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(8px);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        color: #374151;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Success/Error messages */
    .success-message {
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
        border: 1px solid #bbf7d0;
        color: #065f46;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-weight: 500;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .error-message {
        background: linear-gradient(135deg, #fef2f2 0%, #fefefe 100%);
        border: 1px solid #fecaca;
        color: #991b1b;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-weight: 500;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .processing-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #bae6fd;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.1);
    }
    
    .processing-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #0c4a6e;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    
    .processing-text {
        color: #075985;
        font-size: 1rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 3rem 2rem;
        color: #64748b;
        border-top: 1px solid #e2e8f0;
        margin-top: 4rem;
        background: white;
        border-radius: 16px;
    }
    
    .footer-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.5rem;
    }
    
    .footer-text {
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .footer-small {
        font-size: 0.875rem;
        color: #94a3b8;
    }
    
    /* ── Readable text inside the query text-area ─────────────── */
    .stTextArea textarea{
        color:#334155 !important;                /* dark slate */
    }
    
    .stTextArea textarea::placeholder{
        color:#94a3b8 !important;                /* slate-400 */
        opacity:1 !important;                    /* ensure full opacity */
    }
    
    .result-text{
        font-size:0.95rem !important;
        max-width:640px;
        color:#334155 !important;                /* same dark slate */
    }
</style>
""", unsafe_allow_html=True)

# Backend URL
BACKEND_URL = "https://hackathon-project-backend-m1qe.onrender.com"

# Header
st.markdown("""
<div class="header-section">
    <div class="header-title">🛡️ Insurance Coverage Assistant</div>
    <div class="header-subtitle">AI-powered policy analysis for instant coverage decisions</div>
</div>
""", unsafe_allow_html=True)

# Document Upload Section
st.markdown("""
<div class="card">
    <div class="section-header">
        📄 Upload Policy Document
    </div>
    <div class="section-description">
        Upload your insurance policy document to enable personalized coverage analysis. 
        Supported formats include PDF and DOCX files up to 10MB.
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "",
    type=['pdf', 'docx'],
    help="Upload your insurance policy document for analysis",
    label_visibility="collapsed"
)

if uploaded_file is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📤 Process Document", key="upload_btn"):
            with st.spinner(""):
                st.markdown("""
                <div class="processing-card">
                    <div class="processing-title">
                        🔄 Processing Document
                    </div>
                    <div class="processing-text">
                        Analyzing your policy document and creating searchable sections...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{BACKEND_URL}/upload-document", files=files, timeout=60)
                    
                    if response.status_code == 200:
                        st.markdown("""
                        <div class="success-message">
                            ✅ Document processed successfully! You can now ask coverage questions.
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.markdown("""
                        <div class="error-message">
                            ❌ Processing failed. Please try again or contact support.
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.markdown("""
                    <div class="error-message">
                        🔧 Service temporarily unavailable. Please try again in a moment.
                    </div>
                    """, unsafe_allow_html=True)

# Query Section
st.markdown("""
<div class="card">
    <div class="section-header">
        💬 Ask About Coverage
    </div>
    <div class="section-description">
        Enter your coverage question below. Our AI will analyze your policy and provide 
        an instant decision with detailed reasoning.
    </div>
</div>
""", unsafe_allow_html=True)

query = st.text_area(
    "",
    height=120,
    placeholder="Enter your coverage question...\n\nExample: Does my policy cover emergency medical evacuation during international travel?",
    label_visibility="collapsed",
    key="query_input"
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    submit_clicked = st.button("🔍 Analyze Coverage", type="primary", key="analyze_btn")

if submit_clicked:
    if not query.strip():
        st.markdown("""
        <div class="error-message">
            ⚠️ Please enter your coverage question before analyzing.
        </div>
        """, unsafe_allow_html=True)
    else:
        with st.spinner(""):
            st.markdown("""
            <div class="processing-card">
                <div class="processing-title">
                    🤔 Analyzing Coverage
                </div>
                <div class="processing-text">
                    Our AI is reviewing your policy documents and analyzing your question...
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                response = requests.post(
                    f"{BACKEND_URL}/process-claim",
                    json={"query": query.strip()},
                    timeout=120  # Increased timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    decision = result.get('decision', 'UNKNOWN')
                    explanation = result.get('justification', 'Analysis not available')
                    confidence = result.get('confidence_score', 0)
                    
                    if decision == 'COVERED':
                        st.markdown(f"""
                        <div class="result-covered">
                            <div class="result-title">✅ COVERED</div>
                            <div class="result-text">{explanation}</div>
                            <div class="confidence-badge">Confidence: {confidence*100:.0f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    elif decision == 'NOT COVERED':
                        st.markdown(f"""
                        <div class="result-not-covered">
                            <div class="result-title">❌ NOT COVERED</div>
                            <div class="result-text">{explanation}</div>
                            <div class="confidence-badge">Confidence: {confidence*100:.0f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        st.markdown(f"""
                        <div class="result-review">
                            <div class="result-title">⚠️ REQUIRES REVIEW</div>
                            <div class="result-text">{explanation}</div>
                            <div class="result-text">
                                <strong>Recommendation:</strong> Please contact your insurance provider 
                                for clarification on this coverage scenario.
                            </div>
                            <div class="confidence-badge">Confidence: {confidence*100:.0f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                else:
                    st.markdown("""
                    <div class="error-message">
                        🔧 Analysis service temporarily unavailable. Please try again.
                    </div>
                    """, unsafe_allow_html=True)
                    
            except requests.exceptions.Timeout:
                st.markdown("""
                <div class="error-message">
                    ⏱️ Analysis is taking longer than expected. Please try a simpler question.
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                st.markdown("""
                <div class="error-message">
                    🔧 Service temporarily unavailable. Please try again in a moment.
                </div>
                """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <div class="footer-title">🔒 Your Privacy & Security</div>
    <div class="footer-text">
        All documents and queries are processed securely using enterprise-grade encryption. 
        We do not store your personal information or share your data with third parties.
    </div>
    <div class="footer-small">
        Insurance Coverage Assistant • Powered by Advanced AI<br>
        For official policy interpretation, please consult your insurance provider
    </div>
</div>
""", unsafe_allow_html=True)
