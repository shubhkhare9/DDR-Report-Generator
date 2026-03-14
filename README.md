# DDR Report Generator 🏗️

An AI-powered system that reads **Inspection Reports** and **Thermal Reports** and automatically generates a structured **Detailed Diagnostic Report (DDR)** — ready to share with clients.

Built for waterproofing & structural repair firms.

---

## 📁 Project Structure

```
ddr_system/
├── app.py              ← Streamlit UI (main entry point)
├── extractor.py        ← PDF text + image extraction (PyMuPDF)
├── ddr_generator.py    ← Claude API multimodal DDR generation
├── report_builder.py   ← Word (.docx) + PDF output builder
├── requirements.txt    ← Python dependencies
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Clone / download the project
```bash
cd ddr_system
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get an Anthropic API Key
- Go to https://console.anthropic.com
- Create an API key
- You'll enter it in the app's sidebar

---

## 🚀 Run the App

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## 📋 How to Use

1. **Enter your Anthropic API key** in the sidebar
2. **Upload Inspection Report PDF** (site photos, checklists, observations)
3. **Upload Thermal Report PDF** (thermal camera images + temperature data)
4. Click **🚀 Generate DDR Report**
5. Wait ~30–60 seconds for Claude to process
6. **Preview** the report in the browser
7. **Download** as Word (.docx) or PDF

---

## 📊 DDR Report Sections Generated

| # | Section |
|---|---------|
| 1 | Property Issue Summary |
| 2 | Area-wise Observations (with images) |
| 3 | Probable Root Cause |
| 4 | Severity Assessment (High / Medium / Low) |
| 5 | Recommended Actions (Immediate / Short-term / Long-term) |
| 6 | Additional Notes |
| 7 | Missing or Unclear Information |

---

## 🔧 Technical Stack

| Component | Technology |
|-----------|------------|
| UI | Streamlit |
| PDF Extraction | PyMuPDF (fitz) |
| AI Model | Claude claude-opus-4-5 (Anthropic) |
| Word Output | python-docx |
| PDF Output | ReportLab |

---

## ⚠️ Rules the System Follows

- ❌ Never invents facts not in the documents
- 📝 Writes "Not Available" for missing data
- ⚡ Mentions conflicts between inspection and thermal data
- 🖼️ Places images in their correct sections
- 🗣️ Uses simple, client-friendly language

---

## 📌 Limitations

- API key is required (not included)
- Processing time: ~30–60 seconds (depends on document size)
- Very large PDFs (100+ pages) may need chunking
- Image quality depends on original PDF resolution

---

## 🔮 Future Improvements

- Auto-detect area names from images using vision
- Multi-language DDR output
- Custom branding / logo in reports
- Historical report comparison
- WhatsApp / email delivery integration
