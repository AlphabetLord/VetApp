import streamlit as st
import io
import json
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="VetScan AI – Radiology Copilot",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS – Tailwind-inspired clinical design system
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Inter:wght@400;500;600;700;800;900&display=swap');

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
    color: #c7d2fe; font-family: 'IBM Plex Mono', monospace;
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

/* ── Report document styling ───────────── */
.report-doc {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    padding: 36px 40px;
    font-family: 'IBM Plex Mono', 'Courier New', monospace !important;
    font-size: 12.5px;
    line-height: 1.85;
    color: #1e293b;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.report-doc h2, .report-doc h3 {
    font-family: 'Inter', sans-serif !important;
}

/* Markdown h2 inside report areas → section banners */
[data-testid="stMarkdownContainer"] h2 {
    background: linear-gradient(135deg, #1e1b4b 0%, #3730a3 100%);
    color: #ffffff !important;
    padding: 11px 22px;
    border-radius: 8px;
    font-family: 'Inter', sans-serif !important;
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
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    color: #312e81 !important;
    margin: 18px 0 8px 0;
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
# SYSTEM INSTRUCTION – Radiographic Reporting Standard
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_INSTRUCTION = """## RADIOGRAPHIC REPORTING STANDARD

The final report must follow the conventions of consultant-level radiology reporting.

Every conclusion must be traceable to objective imaging observations.

Never infer pathology before thoroughly describing morphology.

Diagnostic reasoning should progress through the following hierarchy:

*Image Features → Radiographic Pattern → Pathophysiologic Interpretation → Differential Diagnosis → Most Likely Explanation*

Never reverse this sequence.

---

### IMAGE FEATURE ANALYSIS

Before considering disease processes, characterize every abnormality using formal radiographic descriptors appropriate to the imaging modality.

Describe, where applicable:

•  Exact anatomical location
•  Organ or tissue compartment
•  Laterality
•  Number of abnormalities
•  Distribution (focal, multifocal, diffuse, segmental, lobar, generalized)
•  Shape
•  Size (absolute measurements whenever possible)
•  Volume
•  Margin characteristics (well-defined, poorly defined, irregular, spiculated, encapsulated)
•  Internal architecture
•  Density / attenuation / echogenicity / signal intensity
•  Enhancement characteristics
•  Mineralization or calcification
•  Presence of cavitation
•  Internal septations
•  Fat content
•  Fluid content
•  Gas content
•  Tissue composition
•  Relationship to adjacent anatomical structures
•  Degree of mass effect
•  Compression of neighbouring structures
•  Evidence of invasion
•  Evidence of obstruction
•  Evidence of displacement
•  Secondary reactive changes
•  Associated inflammatory changes
•  Associated vascular changes
•  Associated lymph node abnormalities

No pathological interpretation should occur before this descriptive analysis.

---

### RADIOGRAPHIC PATTERN ANALYSIS

After morphology has been fully described, classify the dominant imaging pattern.

Possible examples include:

•  Mass lesion
•  Diffuse infiltrative process
•  Nodular disease
•  Cystic process
•  Obstructive pattern
•  Vascular abnormality
•  Degenerative change
•  Traumatic injury
•  Infectious pattern
•  Inflammatory pattern
•  Neoplastic pattern
•  Fibrotic change
•  Ischaemic process
•  Congenital anomaly
•  Post-operative appearance

Explain precisely which imaging characteristics support the selected pattern.

---

### PATHOPHYSIOLOGIC REASONING

Interpret how the observed imaging features may relate to underlying biological processes.

Examples include:

•  Cellular proliferation
•  Tissue necrosis
•  Oedema
•  Haemorrhage
•  Fibrosis
•  Mineralization
•  Inflammation
•  Infection
•  Vascular compromise
•  Mechanical obstruction
•  Degeneration
•  Tissue remodelling
•  Healing response

Differentiate direct observations from biological inference.

---

### DIFFERENTIAL DIAGNOSIS

Construct a ranked differential diagnosis.

For every differential include:

Supporting imaging features

Features arguing against the diagnosis

Expected clinical correlation

Expected laboratory correlation

Expected progression

Recommended confirmatory investigation

Level of diagnostic confidence

---

### INTERNAL CONSISTENCY REVIEW

Before producing the final report perform an internal audit.

Verify that:

Every conclusion is supported by imaging evidence.

No diagnosis contradicts another finding.

No anatomical region has been omitted.

No critical abnormality has been ignored.

No incidental finding has been overlooked.

The overall interpretation is internally coherent.

---

### REPORT LANGUAGE

Use concise consultant-level radiology language.

Avoid speculative wording unless uncertainty is explicitly discussed.

Avoid unnecessary adjectives.

Avoid repetition.

State objective findings before interpretation.

Use accepted radiological terminology.

Separate:

Findings

Impression

Differential diagnosis

Recommendations

Never combine them.

---

### FINAL REPORT FORMAT

The final report should be presented in the following order:

*1. Examination*

•  Imaging modality, protocol, technical adequacy, image quality, limitations and comparison studies.

*2. Findings*

•  Comprehensive anatomical review.
•  Objective radiographic observations only.
•  Organized by anatomical system or region.
•  Include normal structures where clinically relevant.
•  Describe all incidental findings separately.

*3. Impression*

•  Concise synthesis of the most clinically significant findings.
•  Prioritize abnormalities by likely clinical importance.
•  Explain the radiographic pattern leading to the impression.
•  Clearly distinguish confirmed observations from inferred interpretations.

*4. Differential Diagnosis*

•  Ranked differential diagnoses with justification.
•  Supporting and opposing imaging evidence for each.
•  Diagnostic confidence (High / Moderate / Low) with rationale.

*5. Limitations*

•  Technical limitations.
•  Imaging artefacts.
•  Missing clinical information.
•  Factors reducing diagnostic certainty.

*6. Comparison*

•  Compare with prior imaging when available.
•  Describe interval progression, regression, stability or new findings.
•  Quantify changes wherever feasible.

*7. Recommendations*

•  Appropriate additional imaging, laboratory correlation, specialist referral or follow-up where justified.
•  Clearly distinguish urgent from routine recommendations.
•  Never recommend treatment or make definitive clinical management decisions.

The completed report should resemble the quality, structure and analytical depth expected from an experienced consultant radiologist, with every inference transparently supported by objective imaging evidence and accompanied by explicit acknowledgment of uncertainty where appropriate.

---

OUTPUT FORMATTING RULES:
- Use Markdown. Use ## for each numbered section header (e.g. ## 1. Examination). Use ### for subsections.
- Use bullet points for lists.
- Use **bold** for key terms and diagnostic entities.
- Do NOT use emojis.
- Maintain an objective, professional clinical tone throughout.
"""

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### Clinician Registry")

    active_folder = st.selectbox(
        "Active Clinician",
        options=st.session_state["clinicians"],
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
        persist()
        st.toast("All patient and report data cleared.")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1>VetScan AI <span style="font-weight:400; color:#a5b4fc;">Radiology Copilot</span></h1>
            <p>Veterinary diagnostic image analysis powered by Gemini 2.5 Flash</p>
        </div>
        <div><span class="header-badge">SYSTEM ONLINE</span></div>
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
                    pid = f"PT-{datetime.now().strftime('%y%m%d%H%M%S')}"
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
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    persist()
                    st.success(f"Patient {pid} saved.")
                    st.rerun()
                else:
                    st.error("Patient Name and Species are required.")

    with col_records:
        st.markdown(f"#### Patient Records — {st.session_state['selected_clinician']}")

        f_patients = {
            k: v for k, v in st.session_state["patients"].items()
            if v["clinician"] == st.session_state["selected_clinician"]
        }

        if not f_patients:
            st.info("No patients registered under this clinician yet.")
        else:
            for pid, pt in list(f_patients.items()):
                with st.expander(f"{pt['name']}  —  {pt['species']}/{pt['breed']}  ({pid})", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        mn = st.text_input("Name", value=pt["name"], key=f"n_{pid}")
                        mb = st.text_input("Breed", value=pt["breed"], key=f"b_{pid}")
                    with col2:
                        mw = st.number_input("Weight (kg)", value=pt["weight"], key=f"w_{pid}")
                        mc = st.text_input("Primary Complaint", value=pt["condition"], key=f"c_{pid}")
                    with col3:
                        mh = st.text_area("History", value=pt["history"], key=f"h_{pid}")

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
                <tr><td>Species / Breed</td><td>{active_pt['species']} / {active_pt['breed']}</td></tr>
                <tr><td>Age / Sex</td><td>{active_pt.get('age','—')} / {active_pt.get('sex','—')}</td></tr>
                <tr><td>Weight</td><td>{active_pt['weight']} kg</td></tr>
                <tr><td>Owner</td><td>{active_pt.get('owner','—')}</td></tr>
                <tr><td>Primary Complaint</td><td>{active_pt['condition']}</td></tr>
                <tr><td>History</td><td>{active_pt.get('history','—')}</td></tr>
                <tr><td>Attending Clinician</td><td>{active_pt['clinician']}</td></tr>
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

            with st.expander("View System Prompt", expanded=False):
                st.code(SYSTEM_INSTRUCTION, language="text")

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
                with st.spinner("Analysing image — this may take a moment…"):
                    try:
                        client = get_gemini_client()
                        uploaded_scan.seek(0)
                        pil_image = Image.open(uploaded_scan)

                        # Build structured context prompt
                        context_prompt = f"""PATIENT DEMOGRAPHICS:
- Name: {active_pt['name']}
- Species: {active_pt['species']}
- Breed: {active_pt['breed']}
- Age: {active_pt.get('age', 'Not recorded')}
- Sex: {active_pt.get('sex', 'Not recorded')}
- Weight: {active_pt['weight']} kg

CLINICAL INFORMATION:
- Primary Complaint: {active_pt['condition']}
- Clinical Indication: {clinical_indication if clinical_indication else active_pt['condition']}
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

                        response = client.models.generate_content(
                            model=MODEL_ID,
                            contents=[pil_image, context_prompt],
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION,
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

                    # Save report
                    report_id = f"RPT-{datetime.now().strftime('%y%m%d-%H%M%S')}"
                    new_report = {
                        "id": report_id,
                        "patient_id": active_pt["id"],
                        "patient_name": active_pt["name"],
                        "species": active_pt["species"],
                        "breed": active_pt["breed"],
                        "clinician": active_pt["clinician"],
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
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
                st.markdown(f"#### Report: {latest['id']}")

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
                    # Formal radiographic HTML report
                    nl = chr(10)
                    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Radiology Report – {latest['id']}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Inter:wght@400;600;700;800&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'IBM Plex Mono',monospace; color:#1e293b; background:#fff; padding:48px; font-size:12px; line-height:1.8; }}
  .rpt-header {{ border-bottom:3px solid #1e1b4b; padding-bottom:16px; margin-bottom:24px; }}
  .rpt-header h1 {{ font-family:'Inter',sans-serif; font-size:20px; font-weight:800; color:#1e1b4b; letter-spacing:-0.02em; }}
  .rpt-header p {{ font-size:11px; color:#64748b; margin-top:4px; }}
  .meta-table {{ width:100%; border-collapse:collapse; margin-bottom:28px; }}
  .meta-table td {{ padding:6px 14px; border:1px solid #e2e8f0; font-size:12px; }}
  .meta-table td:first-child {{ font-weight:600; background:#f8fafc; color:#475569; width:30%; }}
  .section-banner {{ background:linear-gradient(135deg,#1e1b4b,#3730a3); color:#fff; padding:8px 18px; border-radius:6px; font-family:'Inter',sans-serif; font-size:12px; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; margin:28px 0 12px 0; }}
  .report-body {{ white-space:pre-wrap; }}
  .footer {{ margin-top:40px; border-top:1px solid #e2e8f0; padding-top:12px; font-size:10px; color:#94a3b8; }}
</style>
</head>
<body>
<div class="rpt-header">
  <h1>VETERINARY RADIOLOGY REPORT</h1>
  <p>Generated by VetScan AI Radiology Copilot &middot; {latest['timestamp']}</p>
</div>
<table class="meta-table">
  <tr><td>Report ID</td><td>{latest['id']}</td></tr>
  <tr><td>Patient</td><td>{latest['patient_name']}</td></tr>
  <tr><td>Species / Breed</td><td>{latest.get('species','—')} / {latest.get('breed','—')}</td></tr>
  <tr><td>Attending Clinician</td><td>{latest['clinician']}</td></tr>
  <tr><td>Modality</td><td>{latest['modality']}</td></tr>
  <tr><td>Region</td><td>{latest.get('region','—')}</td></tr>
  <tr><td>Projection</td><td>{latest.get('projection','—')}</td></tr>
  <tr><td>AI Engine</td><td>{latest['engine_used']}</td></tr>
</table>
<div class="report-body">{latest['content'].replace(nl,'<br>')}</div>
<div class="footer">
  This AI-generated report is a preliminary screening aid and does not replace the professional judgement of a licensed veterinarian.
  All findings must be reviewed and confirmed by a qualified clinician before clinical action is taken.
</div>
</body>
</html>"""
                    st.download_button(
                        label="Download Report (.html)",
                        data=report_html.encode("utf-8"),
                        file_name=f"{active_pt['name'].replace(' ','_')}_{latest['id']}.html",
                        mime="text/html",
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
            placeholder="Filter by patient name, clinician, modality, or report ID…",
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
                        <span style="font-size:11px; color:#64748b; font-family:'IBM Plex Mono',monospace;">{rec['timestamp']}</span>
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
                    if st.button("Delete Report", key=f"del_{rec['id']}", type="secondary", use_container_width=True):
                        st.session_state["reports"].remove(rec)
                        persist()
                        st.toast("Report deleted.")
                        st.rerun()
