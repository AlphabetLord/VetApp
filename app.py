import streamlit as st
import io
import json
import re
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types
from fpdf import FPDF

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="VetScan AI – Radiology Copilot",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# TIMEZONE
# ══════════════════════════════════════════════════════════════════════════════
IST = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> datetime:
    """Return the current time in IST."""
    return datetime.now(IST)


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Global ───────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Sidebar ──────────────────────────── */
div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
    border-right: 1px solid #e2e8f0 !important;
}
div[data-testid="stSidebar"] .stMarkdown h3 {
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b !important;
    font-weight: 700 !important;
    margin-top: 20px !important;
}

/* ── App Header ───────────────────────── */
.app-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    color: #ffffff;
    position: relative;
    overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.app-header h1 {
    font-size: 26px; font-weight: 900; letter-spacing: -0.03em; margin: 0;
    position: relative; z-index: 1;
}
.app-header p {
    font-size: 13px; opacity: 0.7; margin: 4px 0 0 0;
    position: relative; z-index: 1;
}
.header-badge {
    display: inline-block;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    backdrop-filter: blur(8px);
    color: #c7d2fe; font-family: monospace;
    font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
    padding: 5px 12px; border-radius: 6px;
}

/* ── Cards ─────────────────────────────── */
.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* ── Context summary table ─────────────── */
.ctx-table {
    width: 100%; border-collapse: collapse; font-size: 13px;
}
.ctx-table td {
    padding: 7px 14px; border-bottom: 1px solid #f1f5f9;
}
.ctx-table td:first-child {
    font-weight: 600; color: #475569; width: 35%; white-space: nowrap;
}

/* ── Buttons ───────────────────────────── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(79,70,229,0.25) !important;
}

/* ── Tabs ──────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    background: #ffffff;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #e2e8f0;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600 !important; font-size: 13px !important;
    color: #64748b !important; border-radius: 8px !important;
    padding: 10px 20px !important;
}
.stTabs [aria-selected="true"] {
    color: #4f46e5 !important; background: #eef2ff !important;
    border-bottom-color: transparent !important;
}

/* ── Report document styling (on-screen) ─ */
.report-doc {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    padding: 36px 40px;
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 13px;
    line-height: 1.85;
    color: #1e293b;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}

/* Markdown h2 inside report → section banners */
[data-testid="stMarkdownContainer"] h2 {
    background: linear-gradient(135deg, #1e1b4b 0%, #3730a3 100%);
    color: #ffffff !important;
    padding: 11px 22px;
    border-radius: 8px;
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 28px 0 14px 0;
}

/* Markdown h3 → subsection accent */
[data-testid="stMarkdownContainer"] h3 {
    border-left: 4px solid #4f46e5;
    padding: 6px 0 6px 14px;
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    color: #312e81 !important;
    margin: 18px 0 8px 0;
}

/* Bullet / list styling inside report-doc */
.report-doc ul, .report-doc ol {
    padding-left: 22px;
    margin: 6px 0;
}
.report-doc li {
    margin-bottom: 4px;
}

/* ── Archive cards ─────────────────────── */
.archive-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-top: 10px;
    transition: border-color 0.2s;
}
.archive-card:hover { border-color: #a5b4fc; }

/* ── Disclaimer ────────────────────────── */
.disclaimer {
    background: #fef3c7; border-left: 4px solid #f59e0b;
    border-radius: 0 8px 8px 0;
    padding: 10px 16px; font-size: 12px; color: #92400e;
    margin: 12px 0;
}

/* ── Misc ──────────────────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATA PERSISTENCE – JSON files in ./data/ survive app restarts
# ══════════════════════════════════════════════════════════════════════════════
DATA_DIR = Path(__file__).resolve().parent / "data"


def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(filename: str, default):
    """Load a JSON file from DATA_DIR; return *default* on any failure."""
    path = DATA_DIR / filename
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return default
    return default


def save_json(filename: str, data):
    """Write *data* as formatted JSON to DATA_DIR."""
    _ensure_dir()
    (DATA_DIR / filename).write_text(
        json.dumps(data, indent=2, default=str), encoding="utf-8"
    )


def persist():
    """Flush current session state to disk."""
    save_json("clinicians.json", st.session_state["clinicians"])
    save_json("patients.json", st.session_state["patients"])
    save_json("reports.json", st.session_state["reports"])


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE – hydrate from disk on first run
# ══════════════════════════════════════════════════════════════════════════════
if "clinicians" not in st.session_state:
    st.session_state["clinicians"] = load_json(
        "clinicians.json", ["Dr. Sharma, DVM", "Dr. Vance, BVSc", "Dr. Al-Jamil, DVM"]
    )
if "patients" not in st.session_state:
    st.session_state["patients"] = load_json("patients.json", {})
if "reports" not in st.session_state:
    st.session_state["reports"] = load_json("reports.json", [])
if "selected_clinician" not in st.session_state:
    st.session_state["selected_clinician"] = st.session_state["clinicians"][0]
if "selected_patient_id" not in st.session_state:
    st.session_state["selected_patient_id"] = None

# ══════════════════════════════════════════════════════════════════════════════
# GEMINI CLIENT (cached across reruns)
# ══════════════════════════════════════════════════════════════════════════════
MODEL_ID = "gemini-2.5-flash"
ENGINE_LABEL = "Gemini 2.5 Flash"


@st.cache_resource(show_spinner=False)
def get_gemini_client() -> genai.Client:
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


# ══════════════════════════════════════════════════════════════════════════════
# DEFAULT SYSTEM INSTRUCTION – Radiographic Reporting Standard
# ══════════════════════════════════════════════════════════════════════════════
DEFAULT_SYSTEM_INSTRUCTION = """## RADIOGRAPHIC REPORTING STANDARD

The final report must follow the conventions of consultant-level radiology reporting.

Every conclusion must be traceable to objective imaging observations.

Never infer pathology before thoroughly describing morphology.

Diagnostic reasoning should progress through the following hierarchy:

*Image Features -> Radiographic Pattern -> Pathophysiologic Interpretation -> Differential Diagnosis -> Most Likely Explanation*

Never reverse this sequence.

---

### IMAGE FEATURE ANALYSIS

Before considering disease processes, characterize every abnormality using formal radiographic descriptors appropriate to the imaging modality.

Describe, where applicable:

- Exact anatomical location
- Organ or tissue compartment
- Laterality
- Number of abnormalities
- Distribution (focal, multifocal, diffuse, segmental, lobar, generalized)
- Shape
- Size (absolute measurements whenever possible)
- Volume
- Margin characteristics (well-defined, poorly defined, irregular, spiculated, encapsulated)
- Internal architecture
- Density / attenuation / echogenicity / signal intensity
- Enhancement characteristics
- Mineralization or calcification
- Presence of cavitation
- Internal septations
- Fat content
- Fluid content
- Gas content
- Tissue composition
- Relationship to adjacent anatomical structures
- Degree of mass effect
- Compression of neighbouring structures
- Evidence of invasion
- Evidence of obstruction
- Evidence of displacement
- Secondary reactive changes
- Associated inflammatory changes
- Associated vascular changes
- Associated lymph node abnormalities

No pathological interpretation should occur before this descriptive analysis.

---

### RADIOGRAPHIC PATTERN ANALYSIS

After morphology has been fully described, classify the dominant imaging pattern.

Possible examples include:

- Mass lesion
- Diffuse infiltrative process
- Nodular disease
- Cystic process
- Obstructive pattern
- Vascular abnormality
- Degenerative change
- Traumatic injury
- Infectious pattern
- Inflammatory pattern
- Neoplastic pattern
- Fibrotic change
- Ischaemic process
- Congenital anomaly
- Post-operative appearance

Explain precisely which imaging characteristics support the selected pattern.

---

### PATHOPHYSIOLOGIC REASONING

Interpret how the observed imaging features may relate to underlying biological processes.

Examples include:

- Cellular proliferation
- Tissue necrosis
- Oedema
- Haemorrhage
- Fibrosis
- Mineralization
- Inflammation
- Infection
- Vascular compromise
- Mechanical obstruction
- Degeneration
- Tissue remodelling
- Healing response

Differentiate direct observations from biological inference.

---

### DIFFERENTIAL DIAGNOSIS

Construct a ranked differential diagnosis.

For every differential include:

- Supporting imaging features
- Features arguing against the diagnosis
- Expected clinical correlation
- Expected laboratory correlation
- Expected progression
- Recommended confirmatory investigation
- Level of diagnostic confidence

---

### INTERNAL CONSISTENCY REVIEW

Before producing the final report perform an internal audit.

Verify that:

- Every conclusion is supported by imaging evidence.
- No diagnosis contradicts another finding.
- No anatomical region has been omitted.
- No critical abnormality has been ignored.
- No incidental finding has been overlooked.
- The overall interpretation is internally coherent.

---

### REPORT LANGUAGE

Use concise consultant-level radiology language.

Avoid speculative wording unless uncertainty is explicitly discussed.

Avoid unnecessary adjectives.

Avoid repetition.

State objective findings before interpretation.

Use accepted radiological terminology.

Separate: Findings, Impression, Differential diagnosis, Recommendations. Never combine them.

---

### FINAL REPORT FORMAT

The final report should be presented in the following order:

**1. Examination**
- Imaging modality, protocol, technical adequacy, image quality, limitations and comparison studies.

**2. Findings**
- Comprehensive anatomical review.
- Objective radiographic observations only.
- Organized by anatomical system or region.
- Include normal structures where clinically relevant.
- Describe all incidental findings separately.
- Use bullet points to organize sub-findings within each anatomical system.

**3. Impression**
- Concise synthesis of the most clinically significant findings.
- Prioritize abnormalities by likely clinical importance.
- Explain the radiographic pattern leading to the impression.
- Clearly distinguish confirmed observations from inferred interpretations.
- Use a numbered list for multiple impression items.

**4. Differential Diagnosis**
- Ranked differential diagnoses with justification.
- Supporting and opposing imaging evidence for each.
- Diagnostic confidence (High / Moderate / Low) with rationale.
- Use bullet points for each differential entry.

**5. Limitations**
- Technical limitations.
- Imaging artefacts.
- Missing clinical information.
- Factors reducing diagnostic certainty.

**6. Comparison**
- Compare with prior imaging when available.
- Describe interval progression, regression, stability or new findings.
- Quantify changes wherever feasible.

**7. Recommendations**
- Appropriate additional imaging, laboratory correlation, specialist referral or follow-up where justified.
- Clearly distinguish urgent from routine recommendations.
- Never recommend treatment or make definitive clinical management decisions.
- Use a numbered list.

The completed report should resemble the quality, structure and analytical depth expected from an experienced consultant radiologist, with every inference transparently supported by objective imaging evidence and accompanied by explicit acknowledgment of uncertainty where appropriate.

---

OUTPUT FORMATTING RULES:
- Use Markdown. Use ## for each numbered section header (e.g. ## 1. Examination). Use ### for subsections.
- Use bullet points (- ) to organize sub-information within each section.
- Use numbered lists (1. 2. 3.) for Impressions and Recommendations.
- Use **bold** for key terms and diagnostic entities.
- Do NOT use emojis.
- Maintain an objective, professional clinical tone throughout.
"""

# Initialise the editable prompt in session state
if "active_prompt" not in st.session_state:
    st.session_state["active_prompt"] = DEFAULT_SYSTEM_INSTRUCTION


# ══════════════════════════════════════════════════════════════════════════════
# PDF GENERATION – formal radiology report in Arial
# ══════════════════════════════════════════════════════════════════════════════
class RadiologyPDF(FPDF):
    """Custom PDF matching the clinical radiology report design."""

    BLUE = (41, 65, 148)
    LIGHT_BG = (245, 247, 250)
    BORDER_GRAY = (200, 210, 220)
    TEXT_DARK = (30, 30, 50)
    TEXT_MID = (80, 90, 110)

    def header(self):
        # Blue banner
        self.set_fill_color(*self.BLUE)
        self.rect(0, 0, 210, 20, "F")
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(255, 255, 255)
        self.set_xy(0, 3)
        self.cell(210, 14, "Radiology Report", align="C")
        self.ln(22)

    def footer(self):
        self.set_y(-22)
        self.set_draw_color(*self.BORDER_GRAY)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.TEXT_MID)
        self.multi_cell(
            0, 3.5,
            "This AI-generated report is a preliminary screening aid and does not replace "
            "the professional judgement of a licensed veterinarian. All findings must be "
            "reviewed and confirmed by a qualified clinician before clinical action is taken.",
            align="C",
        )

    def section_header(self, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.TEXT_DARK)
        self.set_fill_color(*self.LIGHT_BG)
        self.cell(0, 8, title, ln=True, fill=True)
        self.set_draw_color(*self.BORDER_GRAY)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def meta_row(self, label: str, value: str):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.TEXT_MID)
        self.cell(45, 6, label)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.TEXT_DARK)
        self.cell(50, 6, value)

    def body_text(self, text: str):
        """Render a block of markdown-ish text into the PDF."""
        self.set_text_color(*self.TEXT_DARK)
        lines = text.split("\n")
        for raw_line in lines:
            line = raw_line.rstrip()

            # Skip empty lines (add small spacing)
            if not line.strip():
                self.ln(2)
                continue

            # ## Section header
            if line.startswith("## "):
                self.section_header(line[3:].strip())
                continue

            # ### Subsection header
            if line.startswith("### "):
                self.ln(2)
                self.set_font("Helvetica", "B", 10)
                self.set_text_color(*self.BLUE)
                self.cell(0, 6, line[4:].strip(), ln=True)
                self.set_text_color(*self.TEXT_DARK)
                self.ln(1)
                continue

            # Bullet point (- or * or •)
            if re.match(r"^\s*[-*\u2022]\s+", line):
                clean = re.sub(r"^\s*[-*\u2022]\s+", "", line)
                clean = clean.replace("**", "")
                self.set_font("Helvetica", "", 9)
                x_start = self.get_x()
                self.cell(8, 5, "")
                self.cell(4, 5, "-")
                self.multi_cell(0, 5, clean.strip())
                continue

            # Numbered list (1. 2. etc.)
            m = re.match(r"^(\d+)\.\s+(.*)", line)
            if m:
                num, content = m.group(1), m.group(2)
                content = content.replace("**", "")
                self.set_font("Helvetica", "", 9)
                self.cell(8, 5, "")
                self.set_font("Helvetica", "B", 9)
                self.cell(8, 5, f"{num}.")
                self.set_font("Helvetica", "", 9)
                self.multi_cell(0, 5, content.strip())
                continue

            # Regular paragraph text
            clean = line.replace("**", "").replace("*", "").strip()
            if clean:
                self.set_font("Helvetica", "", 9)
                self.multi_cell(0, 5, clean)


def _sanitize(text: str) -> str:
    """Replace common Unicode characters unsupported by Helvetica/Arial."""
    return (
        text
        .replace("\u2022", "-")   # •
        .replace("\u2014", "-")   # —
        .replace("\u2013", "-")   # –
        .replace("\u2018", "'")   # '
        .replace("\u2019", "'")   # '
        .replace("\u201c", '"')   # "
        .replace("\u201d", '"')   # "
        .replace("\u2026", "...")  # …
        .replace("\u2192", "->")  # →
        .replace("\u00b7", "-")   # ·
    )


def generate_report_pdf(report: dict, patient: dict) -> bytes:
    """Build a formal radiology PDF and return bytes."""
    pdf = RadiologyPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # ── Patient Information table ──
    pdf.section_header("Patient Information")
    pdf.meta_row("Name:", _sanitize(patient.get("name", "—")))
    pdf.meta_row("Species / Breed:", _sanitize(f"{patient.get('species','—')} / {patient.get('breed','—')}"))
    pdf.ln(5)
    pdf.meta_row("Age / Sex:", _sanitize(f"{patient.get('age','—')} / {patient.get('sex','—')}"))
    pdf.meta_row("Weight:", f"{patient.get('weight','—')} kg")
    pdf.ln(5)
    pdf.meta_row("Owner:", _sanitize(patient.get("owner", "—")))
    pdf.meta_row("Medical Record:", patient.get("id", "—"))
    pdf.ln(5)
    pdf.meta_row("Referring Clinician:", _sanitize(report.get("clinician", "—")))
    pdf.meta_row("Date of Study:", report.get("timestamp", "—"))
    pdf.ln(3)

    # ── Clinical History ──
    pdf.section_header("Clinical History")
    pdf.set_font("Helvetica", "", 9)
    history_text = _sanitize(
        f"{patient.get('condition', '')}. {patient.get('history', '')}".strip(". ")
    )
    pdf.multi_cell(0, 5, history_text if history_text else "No clinical history provided.")
    pdf.ln(2)

    # ── Technique ──
    pdf.section_header("Technique")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0, 5,
        _sanitize(
            f"{report.get('modality','—')}, {report.get('projection','—')} views, "
            f"{report.get('region','—')} region. Obtained according to departmental protocol."
        ),
    )
    pdf.ln(2)

    # ── AI Report Body (sanitized) ──
    pdf.body_text(_sanitize(report.get("content", "")))

    # ── Signature block ──
    pdf.ln(8)
    pdf.set_draw_color(*RadiologyPDF.BORDER_GRAY)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*RadiologyPDF.TEXT_MID)
    pdf.cell(45, 6, "Attending Clinician:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*RadiologyPDF.TEXT_DARK)
    pdf.cell(60, 6, report.get("clinician", "—"))
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*RadiologyPDF.TEXT_MID)
    pdf.cell(30, 6, "Report Date:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*RadiologyPDF.TEXT_DARK)
    pdf.cell(0, 6, report.get("timestamp", "—"), ln=True)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*RadiologyPDF.TEXT_MID)
    pdf.cell(45, 6, "AI Engine:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*RadiologyPDF.TEXT_DARK)
    pdf.cell(60, 6, report.get("engine_used", "—"))
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*RadiologyPDF.TEXT_MID)
    pdf.cell(30, 6, "Report ID:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*RadiologyPDF.TEXT_DARK)
    pdf.cell(0, 6, report.get("id", "—"), ln=True)

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### Clinician Registry")

    active_folder = st.selectbox(
        "Active Clinician",
        options=st.session_state["clinicians"],
        key="sidebar_clinician_select",
    )
    st.session_state["selected_clinician"] = active_folder

    new_clinician = st.text_input("Add Clinician", placeholder="e.g. Dr. Brooks, DVM")
    if st.button("Register", use_container_width=True):
        if new_clinician and new_clinician not in st.session_state["clinicians"]:
            st.session_state["clinicians"].append(new_clinician)
            persist()
            st.success("Clinician added.")
            st.rerun()

    st.markdown("---")
    st.markdown("### System Status")
    report_count = len(st.session_state["reports"])
    st.progress(min(report_count / 300, 1.0))
    st.caption(f"{report_count} / 300 reports stored")

    st.markdown("---")
    st.markdown("### Data Management")
    if st.button("Clear All Data", use_container_width=True, type="secondary"):
        st.session_state["patients"] = {}
        st.session_state["reports"] = []
        st.session_state["selected_patient_id"] = None
        persist()
        st.toast("All patient and report data cleared.")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
_now_str = now_ist().strftime("%d %b %Y, %I:%M %p IST")
st.markdown(f"""
<div class="app-header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1>VetScan AI <span style="font-weight:400; color:#a5b4fc;">Radiology Copilot</span></h1>
            <p>Veterinary diagnostic image analysis powered by {ENGINE_LABEL}</p>
        </div>
        <div style="text-align:right;">
            <span class="header-badge">SYSTEM ONLINE</span><br/>
            <span style="font-size:11px; opacity:0.6; color:#cbd5e1;">{_now_str}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_patients, tab_analysis, tab_archive = st.tabs([
    "Patients",
    "Image Analysis",
    "Report Archive",
])

# ─────────────────────────────────────────
# TAB 1 – PATIENTS
# ─────────────────────────────────────────
with tab_patients:
    col_intake, col_records = st.columns([1, 2])

    with col_intake:
        st.markdown("#### New Patient")
        with st.form("intake_form", clear_on_submit=True):
            p_name = st.text_input("Patient Name", placeholder="e.g. Stella")
            col_s, col_b = st.columns(2)
            with col_s:
                p_species = st.selectbox("Species", [
                    "Canine", "Feline", "Equine", "Avian",
                    "Reptile", "Exotic / Other",
                ])
            with col_b:
                p_breed = st.text_input("Breed", placeholder="e.g. Rottweiler")
            col_a, col_sx, col_w = st.columns(3)
            with col_a:
                p_age = st.text_input("Age", placeholder="e.g. 3 years")
            with col_sx:
                p_sex = st.selectbox("Sex", [
                    "Male Intact", "Male Neutered",
                    "Female Intact", "Female Spayed",
                ])
            with col_w:
                p_weight = st.number_input("Weight (kg)", 0.0, 1000.0, 10.0, 0.1)
            p_owner = st.text_input("Owner Name", placeholder="e.g. Mr. Shah")
            p_condition = st.text_input("Primary Complaint", placeholder="e.g. Acute hind-limb lameness")
            p_history = st.text_area("Relevant History", placeholder="e.g. Suspected trauma 48 h ago, pain on palpation of right stifle")

            submitted = st.form_submit_button("Save Patient", use_container_width=True)
            if submitted:
                if p_name and p_species:
                    ts = now_ist()
                    pid = f"PT-{ts.strftime('%y%m%d%H%M%S')}"
                    st.session_state["patients"][pid] = {
                        "id": pid,
                        "name": p_name,
                        "species": p_species,
                        "breed": p_breed,
                        "age": p_age,
                        "sex": p_sex,
                        "weight": p_weight,
                        "owner": p_owner,
                        "condition": p_condition,
                        "history": p_history,
                        "clinician": st.session_state["selected_clinician"],
                        "created": ts.strftime("%Y-%m-%d %H:%M"),
                    }
                    persist()
                    st.success(f"Patient {pid} saved.")
                    st.rerun()
                else:
                    st.error("Patient Name and Species are required.")

    with col_records:
        # Clinician filter with "All" option
        view_options = ["All Clinicians"] + st.session_state["clinicians"]
        view_filter = st.selectbox(
            "View patients for",
            options=view_options,
            index=view_options.index(st.session_state["selected_clinician"])
            if st.session_state["selected_clinician"] in view_options else 0,
            key="patient_view_filter",
        )

        if view_filter == "All Clinicians":
            f_patients = dict(st.session_state["patients"])
            st.markdown("#### All Patient Records")
        else:
            f_patients = {
                k: v for k, v in st.session_state["patients"].items()
                if v["clinician"] == view_filter
            }
            st.markdown(f"#### Patient Records — {view_filter}")

        if not f_patients:
            st.info("No patients registered yet.")
        else:
            for pid, pt in list(f_patients.items()):
                with st.expander(f"{pt['name']}  —  {pt.get('species','')}/{pt.get('breed','')}  ({pid})", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        mn = st.text_input("Name", value=pt["name"], key=f"n_{pid}")
                        mb = st.text_input("Breed", value=pt.get("breed", ""), key=f"b_{pid}")
                    with col2:
                        mw = st.number_input("Weight (kg)", value=float(pt.get("weight", 0)), key=f"w_{pid}")
                        mc = st.text_input("Primary Complaint", value=pt.get("condition", ""), key=f"c_{pid}")
                    with col3:
                        mh = st.text_area("History", value=pt.get("history", ""), key=f"h_{pid}")

                    bcol1, bcol2 = st.columns(2)
                    with bcol1:
                        if st.button("Update Patient", key=f"upd_{pid}", use_container_width=True):
                            st.session_state["patients"][pid].update({
                                "name": mn, "breed": mb, "weight": mw,
                                "condition": mc, "history": mh,
                            })
                            persist()
                            st.toast("Patient updated.")
                            st.rerun()
                    with bcol2:
                        if st.button("Select for Analysis", key=f"sel_{pid}", type="primary", use_container_width=True):
                            st.session_state["selected_patient_id"] = pid
                            st.success(f"Selected {pt['name']}. Go to the Image Analysis tab.")

# ─────────────────────────────────────────
# TAB 2 – IMAGE ANALYSIS
# ─────────────────────────────────────────
with tab_analysis:
    target_pid = st.session_state["selected_patient_id"]
    if not target_pid or target_pid not in st.session_state["patients"]:
        st.warning("Select a patient in the Patients tab first.")
    else:
        active_pt = st.session_state["patients"][target_pid]

        # ── Patient context summary ──
        st.markdown(f"""
        <div class="card">
            <p style="margin:0 0 8px 0; font-size:11px; text-transform:uppercase;
                      font-weight:700; color:#64748b; letter-spacing:0.1em;">
                Active Patient Context
            </p>
            <table class="ctx-table">
                <tr><td>Patient</td><td>{active_pt['name']} ({active_pt['id']})</td></tr>
                <tr><td>Species / Breed</td><td>{active_pt.get('species','—')} / {active_pt.get('breed','—')}</td></tr>
                <tr><td>Age / Sex</td><td>{active_pt.get('age','—')} / {active_pt.get('sex','—')}</td></tr>
                <tr><td>Weight</td><td>{active_pt.get('weight','—')} kg</td></tr>
                <tr><td>Owner</td><td>{active_pt.get('owner','—')}</td></tr>
                <tr><td>Primary Complaint</td><td>{active_pt.get('condition','—')}</td></tr>
                <tr><td>History</td><td>{active_pt.get('history','—')}</td></tr>
                <tr><td>Attending Clinician</td><td>{active_pt.get('clinician','—')}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 2])

        with col_left:
            # ── Scan Upload ──
            st.markdown("#### Upload Scan")
            uploaded_scan = st.file_uploader(
                "Diagnostic image", type=["png", "jpg", "jpeg"],
                label_visibility="collapsed",
            )
            if uploaded_scan:
                st.image(uploaded_scan, caption="Uploaded scan preview", use_container_width=True)

            st.markdown("---")

            # ── Structured Clinical Context ──
            st.markdown("#### Clinical Context")

            scan_modality = st.selectbox("Imaging Modality", [
                "Digital Radiography (X-Ray)",
                "Computed Tomography (CT)",
                "Ultrasonography (US)",
                "MRI",
            ])
            scan_region = st.selectbox("Body Region", [
                "Thorax", "Abdomen", "Pelvis", "Skull / Head",
                "Cervical Spine", "Thoracolumbar Spine", "Forelimb",
                "Hindlimb", "Whole Body", "Other",
            ])
            scan_projection = st.text_input(
                "Projection / View",
                value="Lateral and Ventrodorsal",
            )
            clinical_indication = st.text_input(
                "Clinical Indication",
                placeholder="e.g. Rule out fracture of right femur",
            )
            current_medications = st.text_input(
                "Current Medications",
                placeholder="e.g. Meloxicam 0.1 mg/kg PO SID",
            )
            prior_imaging = st.checkbox("Prior imaging available for comparison")
            prior_details = ""
            if prior_imaging:
                prior_details = st.text_input(
                    "Prior Imaging Details",
                    placeholder="e.g. Radiograph 2025-11-20 — right stifle, no fracture seen",
                )
            specific_focus = st.text_area(
                "Specific Focus / Additional Instructions",
                placeholder="e.g. Evaluate distal margins of third metatarsal",
            )

        with col_right:
            st.markdown(f"#### Analysis Engine — {ENGINE_LABEL}")

            # ── Editable System Prompt ──
            with st.expander("System Prompt (editable)", expanded=False):
                edited_prompt = st.text_area(
                    "Modify the system instruction sent to the AI. Changes persist for this session.",
                    value=st.session_state["active_prompt"],
                    height=400,
                    key="prompt_editor",
                    label_visibility="collapsed",
                )
                pcol1, pcol2 = st.columns(2)
                with pcol1:
                    if st.button("Apply Changes", use_container_width=True, key="apply_prompt"):
                        st.session_state["active_prompt"] = edited_prompt
                        st.toast("System prompt updated for this session.")
                        st.rerun()
                with pcol2:
                    if st.button("Reset to Default", use_container_width=True, key="reset_prompt"):
                        st.session_state["active_prompt"] = DEFAULT_SYSTEM_INSTRUCTION
                        st.toast("System prompt reset to default.")
                        st.rerun()

            st.markdown(
                '<div class="disclaimer">'
                '<strong>Disclaimer:</strong> This tool is an AI-powered preliminary '
                'screening assistant and does <u>not</u> replace a licensed veterinarian\'s '
                'professional judgement. All findings must be confirmed by a qualified clinician.'
                '</div>',
                unsafe_allow_html=True,
            )

            run_btn = st.button(
                "Run Analysis",
                type="primary",
                use_container_width=True,
                disabled=(uploaded_scan is None),
            )

            if run_btn:
                with st.spinner("Analysing image — this may take a moment..."):
                    try:
                        client = get_gemini_client()
                        uploaded_scan.seek(0)
                        pil_image = Image.open(uploaded_scan)

                        # Build structured context prompt
                        context_prompt = f"""PATIENT DEMOGRAPHICS:
- Name: {active_pt['name']}
- Species: {active_pt.get('species', '—')}
- Breed: {active_pt.get('breed', '—')}
- Age: {active_pt.get('age', 'Not recorded')}
- Sex: {active_pt.get('sex', 'Not recorded')}
- Weight: {active_pt.get('weight', '—')} kg

CLINICAL INFORMATION:
- Primary Complaint: {active_pt.get('condition', '—')}
- Clinical Indication: {clinical_indication if clinical_indication else active_pt.get('condition', '—')}
- Relevant History: {active_pt.get('history', 'None provided')}
- Current Medications: {current_medications if current_medications else 'None recorded'}

IMAGING PARAMETERS:
- Modality: {scan_modality}
- Body Region: {scan_region}
- Projection / View: {scan_projection}
- Prior Imaging Available: {'Yes — ' + prior_details if prior_imaging and prior_details else 'No'}

SPECIFIC FOCUS:
{specific_focus if specific_focus else 'Standard comprehensive evaluation — no specific focus override.'}

Analyse the attached diagnostic image and produce the standardized radiographic report per the system directive."""

                        # Use the active (potentially edited) system prompt
                        active_system_prompt = st.session_state["active_prompt"]

                        response = client.models.generate_content(
                            model=MODEL_ID,
                            contents=[pil_image, context_prompt],
                            config=types.GenerateContentConfig(
                                system_instruction=active_system_prompt,
                                temperature=0.3,
                                max_output_tokens=8192,
                            ),
                        )

                        if not response.text:
                            raise RuntimeError("The model returned an empty response.")

                        generation_output = response.text

                    except Exception as exc:
                        st.error(
                            f"**API Error:** {exc}\n\n"
                            "Check your API key in `.streamlit/secrets.toml` and try again."
                        )
                        st.stop()

                    # Save report with correct IST timestamp
                    ts = now_ist()
                    report_id = f"RPT-{ts.strftime('%y%m%d-%H%M%S')}"
                    new_report = {
                        "id": report_id,
                        "patient_id": active_pt["id"],
                        "patient_name": active_pt["name"],
                        "species": active_pt.get("species", "—"),
                        "breed": active_pt.get("breed", "—"),
                        "clinician": active_pt["clinician"],
                        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S IST"),
                        "modality": scan_modality,
                        "region": scan_region,
                        "projection": scan_projection,
                        "engine_used": ENGINE_LABEL,
                        "content": generation_output,
                    }
                    st.session_state["reports"].append(new_report)
                    persist()
                    st.success(f"Report {report_id} generated and saved.")

            # ── Render latest report for this patient ──
            pt_reports = [
                r for r in st.session_state["reports"]
                if r["patient_id"] == active_pt["id"]
            ]
            if pt_reports:
                latest = pt_reports[-1]
                st.markdown("---")
                st.markdown(f"#### Report: {latest['id']}  —  {latest['timestamp']}")

                # Report rendered with clinical document styling
                st.markdown('<div class="report-doc">', unsafe_allow_html=True)
                st.markdown(latest["content"])
                st.markdown('</div>', unsafe_allow_html=True)

                # ── Downloads ──
                st.markdown("#### Export Report")
                col_d1, col_d2 = st.columns(2)

                with col_d1:
                    st.download_button(
                        label="Download Markdown (.md)",
                        data=latest["content"].encode("utf-8"),
                        file_name=f"{active_pt['name'].replace(' ','_')}_{latest['id']}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with col_d2:
                    pdf_bytes = generate_report_pdf(latest, active_pt)
                    st.download_button(
                        label="Download PDF (.pdf)",
                        data=pdf_bytes,
                        file_name=f"{active_pt['name'].replace(' ','_')}_{latest['id']}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

# ─────────────────────────────────────────
# TAB 3 – REPORT ARCHIVE
# ─────────────────────────────────────────
with tab_archive:
    st.markdown("#### Report Archive")

    if not st.session_state["reports"]:
        st.info("No reports have been generated yet.")
    else:
        search_q = st.text_input(
            "Search reports",
            placeholder="Filter by patient name, clinician, modality, or report ID...",
        )

        filtered = []
        for r in st.session_state["reports"]:
            pool = f"{r['id']} {r['patient_name']} {r['clinician']} {r['modality']} {r['engine_used']}".lower()
            if search_q.lower() in pool:
                filtered.append(r)

        st.caption(f"Showing {len(filtered)} of {len(st.session_state['reports'])} reports")

        for rec in reversed(filtered):
            with st.container():
                st.markdown(f"""
                <div class="archive-card">
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <span style="font-weight:800; font-size:13px; color:#4f46e5;">{rec['id']}</span>
                        <span style="font-size:11px; color:#64748b; font-family:monospace;">{rec['timestamp']}</span>
                    </div>
                    <div style="margin-top:6px; font-size:12px; color:#334155;">
                        <b>Patient:</b> {rec['patient_name']} &nbsp;|&nbsp;
                        <b>Clinician:</b> {rec['clinician']} &nbsp;|&nbsp;
                        <b>Modality:</b> {rec['modality']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                with st.expander(f"View Report — {rec['id']}", expanded=False):
                    st.markdown('<div class="report-doc">', unsafe_allow_html=True)
                    st.markdown(rec["content"])
                    st.markdown('</div>', unsafe_allow_html=True)

                    # PDF download from archive
                    pt_data = st.session_state["patients"].get(rec["patient_id"], {
                        "name": rec["patient_name"], "id": rec["patient_id"],
                    })
                    arc_pdf = generate_report_pdf(rec, pt_data)
                    st.download_button(
                        label="Download PDF",
                        data=arc_pdf,
                        file_name=f"{rec['patient_name'].replace(' ','_')}_{rec['id']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{rec['id']}",
                        use_container_width=True,
                    )
                    if st.button("Delete Report", key=f"del_{rec['id']}", type="secondary", use_container_width=True):
                        st.session_state["reports"].remove(rec)
                        persist()
                        st.toast("Report deleted.")
                        st.rerun()
