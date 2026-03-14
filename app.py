"""
app.py — DDR Report Generator (Streamlit UI)
Upload Inspection + Thermal PDFs → Claude AI generates DDR → Download as PDF & Word
"""
import streamlit as st
import os
import tempfile
import json
from extractor import extract_from_pdf
from ddr_generator import generate_ddr
from report_builder import build_word_report, build_pdf_report

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DDR Report Generator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1F497D;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #707070;
        margin-top: 0;
    }
    .section-header {
        background-color: #1F497D;
        color: white;
        padding: 8px 14px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 8px;
    }
    .area-card {
        background-color: #F5F7FB;
        border-left: 4px solid #C05000;
        padding: 10px 14px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    .severity-high { color: #C00000; font-weight: 700; }
    .severity-medium { color: #FF8C00; font-weight: 700; }
    .severity-low { color: #007000; font-weight: 700; }
    .stProgress > div > div > div > div { background-color: #1F497D; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # Auto-load API key from Streamlit secrets if deployed on Streamlit Cloud
    secret_api_key = ""
    try:
        secret_api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    if secret_api_key:
        api_key = secret_api_key
        st.success("🔑 API Key loaded automatically")
    else:
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Free API key from console.groq.com",
        )
    st.markdown("---")
    st.markdown("""
### 📌 How It Works
1. Upload both PDF documents
2. Click **Generate DDR**
3. AI extracts text + images
4. Claude generates all 7 sections
5. Download as PDF or Word

### 📋 DDR Sections
1. Property Issue Summary
2. Area-wise Observations
3. Probable Root Cause
4. Severity Assessment
5. Recommended Actions
6. Additional Notes
7. Missing / Unclear Info
""")
    st.markdown("---")
    st.caption("Powered by Groq — LLaMA 3.3 70B (100% Free)")


# ─────────────────────────────────────────────────────────────────────────────
# Main header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🏗️ DDR Report Generator</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">AI-powered Detailed Diagnostic Report for Waterproofing & Structural Inspections</p>',
    unsafe_allow_html=True,
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# File upload
# ─────────────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Inspection Report")
    st.caption("Upload the site inspection PDF (observations, photos, checklists)")
    inspection_file = st.file_uploader(
        "Inspection Report PDF",
        type=["pdf"],
        key="inspection",
        label_visibility="collapsed",
    )
    if inspection_file:
        st.success(f"✅ Loaded: **{inspection_file.name}**")

with col2:
    st.markdown("### 🌡️ Thermal Report")
    st.caption("Upload the thermal imaging PDF (temperature readings, thermal photos)")
    thermal_file = st.file_uploader(
        "Thermal Report PDF",
        type=["pdf"],
        key="thermal",
        label_visibility="collapsed",
    )
    if thermal_file:
        st.success(f"✅ Loaded: **{thermal_file.name}**")

st.markdown("")

# ─────────────────────────────────────────────────────────────────────────────
# Generate button
# ─────────────────────────────────────────────────────────────────────────────
generate_btn = st.button(
    "🚀 Generate DDR Report",
    type="primary",
    use_container_width=True,
    disabled=not (inspection_file and thermal_file and api_key),
)

if not api_key:
    st.info("🔑 Enter your Anthropic API key in the sidebar to enable generation.")
elif not inspection_file or not thermal_file:
    st.info("📄 Upload both PDF documents above to continue.")

# ─────────────────────────────────────────────────────────────────────────────
# Generation pipeline
# ─────────────────────────────────────────────────────────────────────────────
if generate_btn:
    progress = st.progress(0, text="Starting...")
    status = st.empty()

    try:
        # Step 1 — Save uploaded files to temp
        progress.progress(10, text="💾 Saving uploaded files...")
        tmpdir = tempfile.mkdtemp()
        inspection_path = os.path.join(tmpdir, "inspection.pdf")
        thermal_path = os.path.join(tmpdir, "thermal.pdf")

        inspection_file.seek(0)
        thermal_file.seek(0)

        with open(inspection_path, "wb") as f:
            f.write(inspection_file.read())
        with open(thermal_path, "wb") as f:
            f.write(thermal_file.read())

        # Step 2 — Extract inspection
        progress.progress(25, text="📋 Extracting Inspection Report (text + images)...")
        inspection_data = extract_from_pdf(inspection_path, "inspection")
        status.success(
            f"✅ Inspection Report: {inspection_data['total_pages']} pages, "
            f"{len(inspection_data['images'])} images extracted"
        )

        # Step 3 — Extract thermal
        progress.progress(40, text="🌡️ Extracting Thermal Report (text + thermal images)...")
        thermal_data = extract_from_pdf(thermal_path, "thermal")
        status.success(
            f"✅ Thermal Report: {thermal_data['total_pages']} pages, "
            f"{len(thermal_data['images'])} thermal images extracted"
        )

        # Step 4 — Generate DDR
        progress.progress(55, text="🤖 Sending to Groq AI (LLaMA 3.3 70B) for DDR generation (this may take 30–60 seconds)...")
        status.info("🧠 LLaMA is analysing all text and images from both documents...")

        ddr_content = generate_ddr(inspection_data, thermal_data, api_key)
        progress.progress(80, text="✍️ DDR generated — building formatted reports...")

        # Step 5 — Build Word
        status.info("📝 Building Word document...")
        word_path = build_word_report(ddr_content, inspection_data, thermal_data)

        # Step 6 — Build PDF
        status.info("📑 Building PDF document...")
        pdf_path = build_pdf_report(ddr_content, inspection_data, thermal_data)

        progress.progress(100, text="✅ Complete!")
        status.success("🎉 DDR Report Generated Successfully!")

        # ── Store in session state ────────────────────────────
        st.session_state["ddr_content"] = ddr_content
        st.session_state["word_path"] = word_path
        st.session_state["pdf_path"] = pdf_path

    except Exception as e:
        progress.empty()
        st.error(f"❌ An error occurred: {str(e)}")
        st.exception(e)


# ─────────────────────────────────────────────────────────────────────────────
# Display results
# ─────────────────────────────────────────────────────────────────────────────
if "ddr_content" in st.session_state:
    ddr = st.session_state["ddr_content"]
    word_path = st.session_state["word_path"]
    pdf_path = st.session_state["pdf_path"]

    st.markdown("---")
    st.markdown("## 📊 Generated DDR Report")

    # ── Download buttons ──────────────────────────────────────
    dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 2])
    with dl_col1:
        with open(word_path, "rb") as f:
            st.download_button(
                label="📄 Download Word (.docx)",
                data=f.read(),
                file_name="DDR_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
    with dl_col2:
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📑 Download PDF (.pdf)",
                data=f.read(),
                file_name="DDR_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    st.markdown("---")

    # ── Property Info ─────────────────────────────────────────
    prop = ddr.get("property_info", {})
    if prop:
        st.markdown("### 🏠 Property Information")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            st.metric("Property Type", prop.get("property_type", "N/A"))
            st.metric("Flat / Unit", prop.get("flat_number", "N/A"))
        with p_col2:
            st.metric("Floors", prop.get("floors", "N/A"))
            st.metric("Inspection Score", prop.get("inspection_score", "N/A"))
        with p_col3:
            st.metric("Inspected By", prop.get("inspected_by", "N/A"))
            st.metric("Inspection Date", prop.get("inspection_date", "N/A"))

    st.markdown("---")

    # ── All 7 sections ────────────────────────────────────────
    sections = ddr.get("sections", [])

    for sec in sections:
        sec_id = sec.get("id", "")
        title = sec.get("title", "Section")
        content = sec.get("content", "")

        with st.expander(f"📌 {title}", expanded=(sec_id in ["s1", "s2"])):

            if content:
                st.markdown(content)

            # ── Area-wise (s2) ────────────────────────────────
            if sec_id == "s2":
                for area in sec.get("areas", []):
                    st.markdown(
                        f'<div class="area-card">'
                        f'<b>📍 {area.get("area_name", "")}</b>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    a_col1, a_col2 = st.columns(2)
                    with a_col1:
                        st.markdown("**🔴 Problem (Negative Side)**")
                        st.info(area.get("negative_side", "Not Available"))
                        st.markdown("**🌡️ Thermal Finding**")
                        st.info(area.get("thermal_finding", "Not Available"))
                    with a_col2:
                        st.markdown("**🔵 Source (Positive Side)**")
                        st.warning(area.get("positive_side", "Not Available"))

            # ── Severity table (s4) ───────────────────────────
            elif sec_id == "s4":
                sev_rows = sec.get("severity_table", [])
                if sev_rows:
                    st.markdown("#### Severity Assessment Table")
                    for row in sev_rows:
                        sev = row.get("severity", "").strip().lower()
                        badge = (
                            "🔴" if "high" in sev
                            else "🟠" if "medium" in sev
                            else "🟢"
                        )
                        s_col1, s_col2, s_col3 = st.columns([3, 1.5, 5])
                        with s_col1:
                            st.markdown(f"**{row.get('area', '')}**")
                        with s_col2:
                            st.markdown(f"{badge} **{row.get('severity', '')}**")
                        with s_col3:
                            st.markdown(row.get("reasoning", ""))
                        st.divider()

            # ── Actions table (s5) ────────────────────────────
            elif sec_id == "s5":
                actions = sec.get("actions", [])
                if actions:
                    st.markdown("#### Recommended Actions")
                    for act in actions:
                        prio = act.get("priority", "").strip().lower()
                        badge = (
                            "🚨" if "immediate" in prio
                            else "⚠️" if "short" in prio
                            else "📅"
                        )
                        a_col1, a_col2, a_col3 = st.columns([2.5, 6, 2])
                        with a_col1:
                            st.markdown(f"**{act.get('area', '')}**")
                        with a_col2:
                            st.markdown(act.get("action", ""))
                        with a_col3:
                            st.markdown(f"{badge} **{act.get('priority', '')}**")
                        st.divider()

    # ── Raw JSON toggle ───────────────────────────────────────
    with st.expander("🔍 View Raw JSON (Developer View)", expanded=False):
        st.json(ddr)