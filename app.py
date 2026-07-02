"""
VetApp – AI-Powered Veterinary Scan Evaluation Dashboard
=========================================================
A single-page Streamlit application that lets veterinarians upload
digital scans (X-rays, ultrasounds) and receive a standardized
AI-generated evaluation report via the Gemini API.
"""

import io
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
MODEL_ID = "gemini-2.5-flash"

ACCEPTED_TYPES = ["png", "jpg", "jpeg"]

SYSTEM_INSTRUCTION = """
You are VetScan AI, a board-certified veterinary radiologist assistant.
When given a veterinary diagnostic image (X-ray, ultrasound, etc.), you
MUST return your analysis in the **exact** Markdown structure below.
Do NOT deviate from this format. Every section header must appear even
if you write "No significant findings" under it.

---

## 🩻 Patient / Scan Demographics
*(Describe the species, approximate body region, imaging modality, and
projection/orientation that you can infer from the image. If something
cannot be determined, state "Unable to determine from image.")*

## 🔍 Primary Radiographic Findings
Evaluate and report on each of the following:
- **Bone integrity** – fractures, periosteal reactions, lytic/blastic lesions
- **Joint spaces** – width, symmetry, osteophytes, subluxation
- **Soft tissue** – swelling, masses, calcifications
- **Foreign objects** – presence, location, material density

## 📋 Secondary Observations & Anomalies
*(Any incidental or secondary findings not covered above.)*

## 🧠 Preliminary Diagnostic Intent Summary
*(A concise 2-4 sentence interpretive summary integrating the above
findings into one or more differential diagnoses ranked by likelihood.)*

## ✅ Recommended Next Steps / Confirmatory Tests
*(List concrete follow-up actions: additional views, CT/MRI, lab work,
surgical consult, etc.)*

---

End every report with the exact line:
> ⚠️ **Disclaimer:** This AI-generated report is a preliminary screening
> aid and does **not** replace the professional judgment of a licensed
> veterinarian.
"""

# ──────────────────────────────────────────────
# Gemini Client (cached so we don't recreate)
# ──────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_gemini_client() -> genai.Client:
    """Return a reusable Gemini client."""
    return genai.Client(api_key=GEMINI_API_KEY)


def analyse_image(image_bytes: bytes, mime_type: str) -> str:
    """Send the uploaded scan to Gemini and return the markdown report."""
    client = get_gemini_client()

    # Open a PIL Image – the google-genai SDK accepts PIL images natively
    pil_image = Image.open(io.BytesIO(image_bytes))

    prompt_text = (
        "Analyse this veterinary diagnostic image and "
        "produce the standardized evaluation report."
    )

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[pil_image, prompt_text],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,       # deterministic clinical tone
            max_output_tokens=4096,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "The model returned an empty response. "
            "Please try again or upload a different image."
        )
    return response.text


# ──────────────────────────────────────────────
# Page config & custom CSS
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="VetApp · AI Scan Evaluator",
    page_icon="🐾",
    layout="wide",
)

# Inject custom styles for a polished, clinical look
st.markdown(
    """
    <style>
    /* ---------- global ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ---------- hero banner ---------- */
    .hero {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 1.5rem;
        text-align: center;
        color: #ffffff;
    }
    .hero h1 {
        font-size: 2.4rem;
        font-weight: 700;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.5px;
    }
    .hero p {
        font-size: 1.05rem;
        opacity: 0.85;
        margin: 0;
    }

    /* ---------- disclaimer ---------- */
    .disclaimer {
        background: linear-gradient(90deg, #fff3cd 0%, #fff8e1 100%);
        border-left: 5px solid #ffb300;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        font-size: 0.92rem;
        color: #664d03;
        margin-bottom: 1.5rem;
    }
    .disclaimer strong {
        color: #b8860b;
    }

    /* ---------- upload card ---------- */
    .upload-card {
        background: #f8fafc;
        border: 2px dashed #cbd5e1;
        border-radius: 14px;
        padding: 2rem;
        text-align: center;
        transition: border-color 0.3s;
    }
    .upload-card:hover {
        border-color: #2c5364;
    }

    /* ---------- report card ---------- */
    .report-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 2rem 2.5rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    }

    /* ---------- footer ---------- */
    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding-bottom: 1rem;
    }

    /* streamlit uploader override */
    [data-testid="stFileUploader"] {
        max-width: 520px;
        margin: 0 auto;
    }

    /* hide default streamlit menu & footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Hero Banner
# ──────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <h1>🐾 VetApp</h1>
        <p>AI-Powered Veterinary Scan Evaluation Dashboard</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Medical Disclaimer
# ──────────────────────────────────────────────
st.markdown(
    """
    <div class="disclaimer">
        <strong>⚕️ Medical Disclaimer:</strong>
        This tool is an AI-powered preliminary screening assistant and
        does <u>not</u> replace a licensed veterinarian's professional
        judgment. All AI-generated findings must be reviewed and
        confirmed by a qualified veterinary professional before any
        clinical action is taken.
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Two-column layout: Upload | Preview
# ──────────────────────────────────────────────
col_upload, col_preview = st.columns([1, 1], gap="large")

with col_upload:
    st.subheader("📤 Upload Diagnostic Scan")
    uploaded_file = st.file_uploader(
        "Drag & drop or browse for an image",
        type=ACCEPTED_TYPES,
        help="Accepted formats: PNG, JPG, JPEG",
    )
    analyse_btn = st.button(
        "🔬  Analyse Scan",
        use_container_width=True,
        disabled=uploaded_file is None,
        type="primary",
    )

with col_preview:
    st.subheader("🖼️ Scan Preview")
    if uploaded_file is not None:
        try:
            preview_image = Image.open(uploaded_file)
            st.image(preview_image, use_container_width=True)
        except Exception:
            st.error("⚠️ The uploaded file could not be rendered as an image.")
    else:
        st.info("Upload a scan on the left to see a preview here.")

# ──────────────────────────────────────────────
# Analysis
# ──────────────────────────────────────────────
if analyse_btn and uploaded_file is not None:
    # Reset file pointer and read bytes
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()

    # Validate the image with Pillow
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()  # raises if corrupt
    except Exception:
        st.error(
            "🚫 **Corrupt or invalid image file.** "
            "Please upload a valid PNG or JPEG scan."
        )
        st.stop()

    # Determine MIME type
    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
    mime_type = mime_map.get(extension, "image/png")

    # Call Gemini
    st.divider()
    st.subheader("📝 AI Evaluation Report")

    with st.spinner("Analysing scan with Gemini AI — this may take a moment …"):
        try:
            report_md = analyse_image(raw_bytes, mime_type)
        except Exception as exc:
            st.error(
                f"🚫 **API Error:** {exc}\n\n"
                "Please check your network connection and try again."
            )
            st.stop()

    # Render the report inside a styled card
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown(report_md)
    st.markdown("</div>", unsafe_allow_html=True)

    # Download button for the report
    st.download_button(
        label="💾  Download Report (.md)",
        data=report_md,
        file_name="vetscan_report.md",
        mime="text/markdown",
    )

# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown(
    '<div class="footer">VetApp © 2026 · Built with Streamlit & Google Gemini</div>',
    unsafe_allow_html=True,
)
