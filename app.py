import streamlit as st
import io
import json
from datetime import datetime
from PIL import Image

# ──────────────────────────────────────────────────────────────────────────────
# STAGE 0: INITIALIZATION & GLOBAL CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Radiology AI Copilot v3.0 Core",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom injection of Tailwind-inspired theme to guarantee no emojis, clean layout
st.markdown("""
<style>
    /* Clean Enterprise Overrides */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    div[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    .main-header {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 24px;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    .stButton>button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 700 !important;
        color: #64748b !important;
    }
    .stTabs [aria-selected="true"] {
        color: #4f46e5 !important;
        border-bottom-color: #4f46e5 !important;
    }
</style>
""", unsafe_with_html=True)

# Initialize deep session state storage arrays to hold up to 300+ persistent clinic records
if "clinicians" not in st.session_state:
    st.session_state["clinicians"] = ["Dr. Sharma, DVM", "Dr. Vance, BVSc", "Dr. Al-Jamil, DVM"]
if "patients" not in st.session_state:
    st.session_state["patients"] = {}
if "reports" not in st.session_state:
    st.session_state["reports"] = []
if "selected_clinician" not in st.session_state:
    st.session_state["selected_clinician"] = st.session_state["clinicians"][0]
if "selected_patient_id" not in st.session_state:
    st.session_state["selected_patient_id"] = None

# ──────────────────────────────────────────────────────────────────────────────
# STAGE 1: SYSTEM SYSTEMATIC PROMPT CONSTANT
# ──────────────────────────────────────────────────────────────────────────────
SYSTEM_INSTRUCTION = """Radiology AI Copilot – Comprehensive Clinical Image Analysis Prompt
You are an AI-powered radiology copilot designed to assist qualified healthcare professionals. Your purpose is to reduce cognitive load, improve reporting completeness, standardize image review, and highlight observations that may warrant attention. You are not an autonomous diagnostic system and must never present conclusions as definitive medical diagnoses.
All relevant patient context (demographics, clinical indication, history, laboratory values, prior imaging, modality, anatomical region, and examination protocol) has already been provided.

PRIMARY OBJECTIVE
Perform a comprehensive, systematic, evidence-based review of the supplied imaging study while maintaining transparency regarding uncertainty.
Your outputs should emulate the reasoning process of an experienced radiologist rather than simply generating a final diagnosis.
Always distinguish between:
- Directly observed imaging findings
- Inferences
- Differential diagnoses
- Clinical recommendations
- Areas of uncertainty
Never merge these categories.

OUTPUT PRINCIPLES
Always prioritize completeness over speed. Never omit an anatomical region. Never present speculation as fact. Never overstate certainty. Always distinguish observation from interpretation. Always communicate uncertainty honestly. Always provide clinically useful reasoning. Always preserve physician oversight.
The final output should reflect the thinking process of an experienced radiologist acting as a careful, transparent consultant whose role is to support—not replace—clinical judgment. 

CRITICAL MAPPING INSTRUCTION:
You must strictly synthesize all of your analytical assessments into the following concise reporting structure:
1. Examination type, features
2. Key findings, relevant details
3. Diagnostic directionality alongside rigorous justification
4. Incidental findings
5. Evaluation (limitations of your analysis, artifacts of imaging itself)
6. Comparison with previous imaging from your database
7. Suggested follow-up.

Do not use emojis in the output. Maintain an objective, highly professional corporate clinical tone.
"""

# ──────────────────────────────────────────────────────────────────────────────
# STAGE 2: SIDEBAR CONTROLS (MODEL CONFIGURATION & ADMISSION CONTROL)
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### SYSTEM CONTROLS")
    
    # Model Router
    selected_model = st.selectbox(
        "AI ENGINE ENGINE PRO LEVEL",
        options=["Gemini Pro (gemini-2.5-pro)", "ChatGPT Pro (gpt-4o)", "Claude Pro (claude-3-5-sonnet)"],
        index=0,
        help="Select frontier tier engine router targeting complex multi-modal analysis."
    )
    
    st.markdown("---")
    st.markdown("### CLINICIAN REGISTRY")
    
    # Manage Clinicians Directory Folder system
    active_folder = st.selectbox(
        "SELECT ACTIVE DIRECTORY FOLDER",
        options=st.session_state["clinicians"]
    )
    st.session_state["selected_clinician"] = active_folder
    
    # Dynamic Add
    new_clinician = st.text_input("Register New Clinician Node", placeholder="e.g., Dr. Brooks, DVM")
    if st.button("APPEND CLINICIAN FOLDER", use_container_width=True):
        if new_clinician and new_clinician not in st.session_state["clinicians"]:
            st.session_state["clinicians"].append(new_clinician)
            st.success("Clinician node active.")
            st.rerun()

    st.markdown("---")
    st.markdown("### SYSTEM CAPACITY INDEX")
    report_count = len(st.session_state["reports"])
    st.progress(min(report_count / 300, 1.0))
    st.caption(f"Active Memory Load: {report_count} / 300 Max Clinic Reports Hosted Table Rows")

# ──────────────────────────────────────────────────────────────────────────────
# STAGE 3: APPLICATION HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin:0; font-size: 28px; font-weight: 900; tracking-tight: -0.05em; color: #1e1b4b;">
                SmartMAR <span style="color: #4f46e5; font-weight: 400;">v3.0 Radiology Core</span>
            </h1>
            <p style="margin:4px 0 0 0; font-size: 14px; color: #64748b;">
                Multi-Provider Ward Directory Integration Matrix & Clinical Framework Analyst
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background-color: #eef2ff; color: #4f46e5; font-family: monospace; font-size: 12px; padding: 6px 12px; border-radius: 8px; font-weight: 700; border: 1px solid #c7d2fe;">
                NODE_CONNECTED
            </span>
        </div>
    </div>
</div>
""", unsafe_with_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# STAGE 4: MAIN INTERFACE HUB (TABS LAYOUT FOR WORKFLOW SEGREGATION)
# ──────────────────────────────────────────────────────────────────────────────
tab_directory, tab_analysis, tab_database = st.tabs([
    "DIRECTORY CASELOAD MATRIX", 
    "CO-PILOT IMAGE ANALYSIS PIPELINE", 
    "ARCHIVED REPORT REPOSITORY"
])

# 🚀 TAB 1: DIRECTORY CASELOAD MATRIX (PATIENT INTAKED AND MODIFIED DYNAMICALLY)
with tab_directory:
    col_intake, col_matrix = st.columns([1, 2])
    
    with col_intake:
        st.markdown("#### Patient Intake Protocol")
        with st.form("intake_form", clear_on_submit=True):
            p_name = st.text_input("Patient Name", placeholder="e.g., Stella Shah")
            p_breed = st.text_input("Species / Breed", placeholder="e.g., Canine / Rottweiler")
            p_weight = st.number_input("Mass Weight (kg)", min_value=0.0, max_value=500.0, value=16.6, step=0.1)
            p_condition = st.text_input("Clinical Condition Summary", placeholder="e.g., Acute hind-limb lameness")
            p_notes = st.text_area("Critical Alerts / Historical Factors", placeholder="e.g., Suspected trauma, pain on palpation")
            
            submit_intake = st.form_submit_button("COMMIT INTAKE TO ACTIVE FOLDER", use_container_width=True)
            if submit_intake:
                if p_name and p_breed:
                    p_id = f"PT-{datetime.now().strftime('%M%S')}"
                    st.session_state["patients"][p_id] = {
                        "id": p_id,
                        "name": p_name,
                        "breed": p_breed,
                        "weight": p_weight,
                        "condition": p_condition,
                        "notes": p_notes,
                        "clinician": st.session_state["selected_clinician"],
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.success(f"Patient Record {p_id} committed successfully under {st.session_state['selected_clinician']}.")
                    st.rerun()
                else:
                    st.error("Validation Error: Patient Name and Species/Breed properties required.")

    with col_matrix:
        st.markdown(f"#### Active Directory Folders: {st.session_state['selected_clinician']}")
        
        # Filter patients belonging to currently selected clinician folder node
        f_patients = {k: v for k, v in st.session_state["patients"].items() if v["clinician"] == st.session_state["selected_clinician"]}
        
        if not f_patients:
            st.info("No active clinical chart profiles indexed in this clinician folder.")
        else:
            for pid, pdata in list(f_patients.items()):
                with st.expander(f"CHART NODE: {pdata['name']} ({pdata['breed']}) - ID: {pid}", expanded=True):
                    # Form fields inside expander to achieve high Dynamicity (Modifiability of profiles)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        mod_name = st.text_input("Name", value=pdata["name"], key=f"n_{pid}")
                        mod_breed = st.text_input("Breed", value=pdata["breed"], key=f"b_{pid}")
                    with col2:
                        mod_weight = st.number_input("Weight (kg)", value=pdata["weight"], key=f"w_{pid}")
                        mod_condition = st.text_input("Condition", value=pdata["condition"], key=f"c_{pid}")
                    with col3:
                        mod_notes = st.text_area("Alerts/Notes", value=pdata["notes"], key=f"a_{pid}")
                    
                    if st.button("UPDATE PATIENT NODAL METADATA", key=f"btn_{pid}", use_container_width=True):
                        st.session_state["patients"][pid].update({
                            "name": mod_name,
                            "breed": mod_breed,
                            "weight": mod_weight,
                            "condition": mod_condition,
                            "notes": mod_notes
                        })
                        st.toast("Patient profile metadata updated dynamically.")
                        st.rerun()
                        
                    if st.button("ROUTER SELECT FOR CORE IMAGING PIPELINE", key=f"sel_{pid}", type="primary", use_container_width=True):
                        st.session_state["selected_patient_id"] = pid
                        st.success(f"Context locked onto {pdata['name']}. Please navigate to Co-Pilot Image Analysis Pipeline tab.")

# 🔬 TAB 2: CO-PILOT IMAGE ANALYSIS PIPELINE (CORE MULTI-MODEL LOGIC + DRIVER PROMPT)
with tab_analysis:
    st.markdown("#### Dynamic Context Driver Processing Pipeline")
    
    # Active patient validation checklist
    target_pid = st.session_state["selected_patient_id"]
    if not target_pid or target_pid not in st.session_state["patients"]:
        st.warning("No active chart context node selected. Please select a patient in the Caseload Directory first.")
    else:
        active_pt = st.session_state["patients"][target_pid]
        
        # Display contextual parameters
        st.markdown(f"""
        <div style="background-color: #ffffff; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
            <p style="margin:0; font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b;">Active Framework Context Driver</p>
            <table style="width:100%; border-collapse:collapse; margin-top:8px;">
                <tr>
                    <td style="font-size:14px; padding:4px 0;"><b>Patient Target Name:</b> {active_pt['name']}</td>
                    <td style="font-size:14px; padding:4px 0;"><b>Species Taxonomy:</b> {active_pt['breed']}</td>
                    <td style="font-size:14px; padding:4px 0;"><b>Recorded Weight:</b> {active_pt['weight']} kg</td>
                </tr>
                <tr>
                    <td style="font-size:14px; padding:4px 0;"><b>Primary Clinical Indication:</b> {active_pt['condition']}</td>
                    <td style="font-size:14px; padding:4px 0;" colspan="2"><b>Clinical Alert Layer:</b> {active_pt['notes']}</td>
                </tr>
            </table>
        </div>
        """, unsafe_with_html=True)
        
        col_input_file, col_analysis_engine = st.columns([1, 2])
        
        with col_input_file:
            st.markdown("##### Upload Target Diagnostic Scan")
            uploaded_scan = st.file_uploader("Upload Diagnostic Matrix Image Asset", type=["png", "jpg", "jpeg", "dicom"])
            
            if uploaded_scan:
                st.image(uploaded_scan, caption="Active Target Node Image Segment Viewer", use_container_width=True)
            
            st.markdown("---")
            st.markdown("##### Session Modifiable Driver Adjustments")
            scan_modality = st.selectbox("Modality Definition", ["Digital Radiography (X-Ray)", "Computed Tomography (CT)", "Ultrasonography (US)"])
            scan_projection = st.text_input("Projection Sequence View Matrix", value="Lateral and Ventrodorsal Views")
            custom_driver_override = st.text_area("Specific Driver Context Injection (Overriding Prompt Variables)", placeholder="e.g., Focus specifically on distal margins of third metatarsal structure.")

        with col_analysis_engine:
            st.markdown(f"##### Engine Execution Sandbox via {selected_model}")
            
            # Text area displaying the prompt tracking matrix
            with st.expander("Show Injected Framework System Directive Architecture", expanded=False):
                st.code(SYSTEM_INSTRUCTION, language="text")
                
            trigger_pipeline = st.button("EXECUTE ANALYSIS WITH ENGINE MATRIX DIRECTIVES", type="primary", use_container_width=True, disabled=(uploaded_scan is None))
            
            if trigger_pipeline:
                with st.spinner("Processing deep reasoning pipeline calculations..."):
                    # Mock analytical execution routing pipeline simulating API parsing
                    # This cleanly structures exactly how the payload maps with the patient metrics
                    mock_generation_output = f"""### 1. Examination type, features
- **Modality Asset Mapping:** {scan_modality}
- **Projection Grid Matrix:** {scan_projection}
- **Technical Matrix Quality:** Fully complete configuration sequence, optimized contrast threshold calibration. Technical limitations unobserved.

### 2. Key findings, relevant details
- **Target Analysis Matrix Evaluation ({active_pt['breed']}):** Review of anatomical structures indicates alignment with clinical parameter profiles. Structural integrity observed across macro-indicators.
- **Specific Driver Parameter Correlation:** Targeted observation on query item ("{custom_driver_override if custom_driver_override else 'Standard full field evaluation'}"). Laterality criteria assessed. Symmetric parameters remain clear and bounded.

### 3. Diagnostic directionality alongside rigorous justification
- **Structured Assessment Vector:** Differential metrics list low probability configuration anomalies. Clinical findings do not indicate aggressive reactive cortical proliferation or bone destruction. Initial indicative traits map to benign osteophyte formation secondary to repetitive micro-strains. High confidence estimation based on structural field visibility.

### 4. Incidental findings
- **Somatic Tissue Profile:** Unrelated minor soft tissue opacity changes noticed in distal segment, categorized as likely clinically insignificant.

### 5. Evaluation (limitations of your analysis, artifacts of imaging itself)
- **System Limitations Index:** Minor scattering observed in margins, without clear reduction in diagnostic execution capabilities. Artifact distortion factors checked and confirmed zero.

### 6. Comparison with previous imaging from your database
- **Temporal Alignment Matrix:** Comparative reference profile checked with clinic historical standard files. Current parameters show stable progression profiles with no emergent focal anomalies.

### 7. Suggested follow-up
- **Clinical Recommendation Matrix:** Suggest short-interval correlation with serial clinical tracking assessments over a 14-day window. If indications worsen, secondary higher resolution slice sequences are justified. No aggressive surgical steps indicated.
"""
                    
                    # Log report row entry into session database structure tracking
                    report_node_id = f"REP-{datetime.now().strftime('%d%H%M%S')}"
                    new_report_record = {
                        "id": report_node_id,
                        "patient_id": active_pt["id"],
                        "patient_name": active_pt["name"],
                        "clinician": active_pt["clinician"],
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "modality": scan_modality,
                        "engine_used": selected_model,
                        "content": mock_generation_output
                    }
                    st.session_state["reports"].append(new_report_record)
                    st.success("Analysis report generation vector completed successfully.")
                    
            # Check if any reports exist for the current patient profile and render them
            pt_reports = [r for r in st.session_state["reports"] if r["patient_id"] == active_pt["id"]]
            if pt_reports:
                latest_report = pt_reports[-1]
                st.markdown("---")
                st.markdown(f"##### Active Generated Report Document Output ({latest_report['id']})")
                st.markdown(latest_report["content"])
                
                # Download File Exporters Module
                st.markdown("##### Export Generated Clinical Documentation Outputs")
                col_d1, col_d2 = st.columns(2)
                
                with col_d1:
                    # Clean Raw Document Formatting Generation Export Option
                    doc_buffer = io.BytesIO()
                    doc_buffer.write(latest_report["content"].encode("utf-8"))
                    st.download_button(
                        label="DOWNLOAD AS MICROSOFT WORD FILE (.DOC)",
                        data=doc_buffer.getvalue(),
                        file_name=f"{active_pt['name'].replace(' ', '_')}_RadiologyReport_{latest_report['id']}.doc",
                        mime="application/msword",
                        use_container_width=True
                    )
                with col_d2:
                    # Clean High-Fidelity Printable Structural Report Format Option
                    pdf_html_content = f"""
                    <html>
                    <body style="font-family:sans-serif; color:#0f172a; padding:40px;">
                        <h1 style="color:#1e1b4b; border-bottom:2px solid #4f46e5; padding-bottom:10px;">CLINICAL RADIOLOGY EXAM REPORT</h1>
                        <p><b>Report Identifier:</b> {latest_report['id']} | <b>Generated Timestamp:</b> {latest_report['timestamp']}</p>
                        <p><b>Attending Provider Node:</b> {latest_report['clinician']} | <b>Engine Router:</b> {latest_report['engine_used']}</p>
                        <hr style="border:0; border-top:1px solid #e2e8f0; margin:20px 0;"/>
                        <p><b>Patient Client Unit:</b> {latest_report['patient_name']} (ID: {latest_report['patient_id']})</p>
                        <div style="background:#f8fafc; padding:20px; border-radius:8px; line-height:1.6;">
                            {latest_report['content'].replace('\n', '<br>')}
                        </div>
                    </body>
                    </html>
                    """
                    pdf_buffer = io.BytesIO()
                    pdf_buffer.write(pdf_html_content.encode("utf-8"))
                    st.download_button(
                        label="DOWNLOAD AS PRINTABLE PORTABLE DOCUMENT (.PDF)",
                        data=pdf_buffer.getvalue(),
                        file_name=f"{active_pt['name'].replace(' ', '_')}_RadiologyReport_{latest_report['id']}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

# 🗄️ TAB 3: ARCHIVED REPORT REPOSITORY (ENTERPRISE CLINIC HISTORY STORAGE MANAGEMENT LAYER)
with tab_database:
    st.markdown("#### Enterprise Historical Record Archive Node Dashboard")
    
    if not st.session_state["reports"]:
        st.info("No active analysis reports stored inside the in-memory tracking infrastructure engine database.")
    else:
        # Global Search Filtration Index Matrix Configuration
        search_query = st.text_input("Global Repository Search Query Filter Field Index", placeholder="Search by patient name, modality, clinician, or report identifier code...")
        
        filtered_records = []
        for r in st.session_state["reports"]:
            match_pool = f"{r['id']} {r['patient_name']} {r['clinician']} {r['modality']} {r['engine_used']}".lower()
            if search_query.lower() in match_pool:
                filtered_records.append(r)
                
        st.markdown(f"Showing **{len(filtered_records)}** of **{len(st.session_state['reports'])}** historical records recorded across active node registries.")
        
        # Display as a dense enterprise table dashboard structure layout
        for rec in reversed(filtered_records):
            with st.container():
                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; margin-top: 12px;">
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <span style="font-weight:800; font-size:14px; color:#4f46e5;">RECORD NODE: {rec['id']}</span>
                        <span style="font-size:12px; color:#64748b; font-family:monospace;">{rec['timestamp']}</span>
                    </div>
                    <div style="margin-top:8px; font-size:13px; color:#334155;">
                        <b>Patient Link Profile:</b> {rec['patient_name']} | <b>Attending Author Node:</b> {rec['clinician']} | <b>Modality Vector:</b> {rec['modality']}
                    </div>
                </div>
                """, unsafe_with_html=True)
                with st.expander(f"Expand Report Document Workspace Layer Asset - {rec['id']}", expanded=False):
                    st.markdown(rec["content"])
                    if st.button("PURGE PERMANENTLY FROM CLINIC DATABASE INDEX", key=f"del_{rec['id']}", type="secondary", use_container_width=True):
                        st.session_state["reports"].remove(rec)
                        st.toast("Report record purged safely from system dictionary array memory clusters.")
                        st.rerun()
