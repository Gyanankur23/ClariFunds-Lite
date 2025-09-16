import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import matplotlib.pyplot as plt
import re
import time

import fitz  # PyMuPDF for PDF support

st.title("ClariFunds-Lite: NGO Receipt Analyzer")
st.write(
    "Upload your NGO’s expense receipt (image or PDF) to auto-categorize and visualize spend for transparent fund reporting and compliance."
)

uploaded_file = st.file_uploader("Upload NGO Receipt Image or PDF", type=["jpg", "jpeg", "png", "bmp", "pdf"])

image = None

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        # Extract first page of PDF to image
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        image = Image.open(pd.io.common.BytesIO(img_bytes))
        st.image(image, caption="Receipt Preview (First Page of PDF)", use_column_width=True)
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Receipt Preview", use_column_width=True)
    st.divider()

    with st.spinner("AI is thinking... Extracting and analyzing expenses."):
        time.sleep(5.5)
        ocr_text = pytesseract.image_to_string(image)

    st.subheader("Detected Text (OCR)")
    st.code(ocr_text, language='text')

    # Improved Table Parser for Clean LaTeX Bills
    data = []
    lines = ocr_text.split('\n')
    for line in lines:
        # Match: Description (words or spaces), then number (amount)
        match = re.match(r'(.+?)\s+(\d+)(?:\s*|$)', line.strip())
        if match:
            desc = match.group(1).strip()
            amt = match.group(2).strip()
            # Skip headers and totals
            if desc.lower() in ['description', 'amount (inr)', 'expense', 'item', 'value', 'purpose', 'category', 'name', 'cost', 'total', 'organisation', 'organization']:
                continue
            try:
                amount_f = float(amt.replace(',', ''))
                data.append({'Category': desc, 'Amount': amount_f})
            except ValueError:
                continue

    if not data:
        st.info("No line items detected as expected. Try with a cleanly formatted receipt image/PDF.")
        df = pd.DataFrame([{'Category': 'Unknown', 'Amount': 0.0}])
    else:
        df = pd.DataFrame(data)
        st.subheader("Extracted Expenses")
        st.write(df)

        st.subheader("Visual Summary")
        st.bar_chart(df.set_index('Category')['Amount'])
        fig, ax = plt.subplots()
        df.groupby('Category')['Amount'].sum().plot.pie(
            y='Amount',
            autopct='%1.1f%%',
            legend=False,
            ylabel='',
            ax=ax
        )
        st.pyplot(fig)

        if not df.empty:
            top_cat = df.sort_values('Amount', ascending=False).iloc[0]
            st.subheader("AI Recommendation")
            st.write(f"Highest NGO spend on '{top_cat['Category']}'. Ensure spending aligns with intended objectives and aid transparency.")

st.caption("Built for NGOs: Simple, transparent, and instant expense analysis dashboard.")

# requirements.txt should include: streamlit pillow pytesseract pandas matplotlib pymupdf
