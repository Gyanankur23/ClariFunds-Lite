# ClariFunds-Lite NGO Receipt Analyzer

SIH 2025 Internal Submission 

ClariFunds-Lite is an AI-powered web app designed for NGOs to automatically extract, structure, and analyze expenses from receipts in image or multi-page PDF formats. Developed for Smart India Hackathon 2025 by Team NexaAudit, it brings transparency and efficiency to financial reporting with modern OCR and data visualization tools.

---

## Features

- **Multi-page PDF & Image Upload:** Handles both types for real-world compatibility.
- **Automated Receipt Parsing:** Extracts each line item, ignoring headers and totals.
- **Per-Bill (Per-Page) Analytics:** Each page analyzed separately for clear NGO-wise breakdown.
- **Visual Dashboards:** Bar chart, treemap, and KPIs (total, max, min, top category) per upload.
- **User-Friendly Streamlit Interface:** No coding needed for users.

---

## How It Works

1. **Upload Receipts:** 
   - Drag & drop images (JPG/PNG) or multi-page PDFs.
2. **Automated Extraction:** 
   - The app uses Tesseract OCR and robust parsing to scan each page for line items.
3. **Visual Analysis:** 
   - For each page, view an instant table of categorized expenses, summary KPIs, and interactive expense breakdown charts.
4. **Transparency & Compliance:** 
   - Download data or screenshots for easy reporting and audits.

---

## Technologies Used

- **Python 3**
- **Streamlit** (dashboard and file handling)
- **PyMuPDF** (PDF image conversion)
- **Pillow** (image manipulation)
- **pytesseract** (OCR)
- **plotly** (interactive charts)

---

## Demo

<img src="app_homepage_screenshot.png" width="350">

1. **Home Screen:** Upload your receipts.
2. **Preview & Analysis:** Each receipt page produces its own summary like below:
<img src="kpi_and_charts_example.png" width="600">

---

## Installation

1. Clone this repository.
2. Install requirements:

pip install -r requirements.txt

- Make sure **Tesseract OCR** is installed on your system and in PATH.

3. Run the app:

streamlit run app.py


---

## Example Use Case

- Track monthly spend across multiple projects by uploading all bills as a single PDF.
- Receive per-bill and project-wise breakdowns with no manual data entry.

---

## Limitations & Future Work

- Best results with clear, tabular receipts and moderate file sizes.
- Extreme PDF/image sizes may exceed memory limits on cloud deployment.
- Future: In-app CSV export, manual correction of extraction, and advanced AI parsing.

---

## Team

**Team NexaAudit**  
Smart India Hackathon 2025  
(Contact: [Add GitHub/LinkedIn/email as desired])

---

## Acknowledgements

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Streamlit](https://streamlit.io/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [Plotly](https://plotly.com/python/)

---

### For SIH, please see `/SIH2025-IDEA-Presentation-Format.pdf` for the original proposal and slide deck.

