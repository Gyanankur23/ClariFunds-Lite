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
    "Upload your NGO’s expense receipt (image or PDF) to auto-extract, analyze, and visualize expenses—built for transparent fund reporting."
)

uploaded_file = st.file_uploader("Upload NGO Receipt Image or PDF", type=["jpg", "jpeg", "png", "bmp", "pdf"])

image = None

if uploaded_file:
    if uploaded_file.type == "application/pdf":
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

    # Parse only valid table lines; ignore Bill headers, date, org, etc.
    skip_keywords = [
        'description', 'amount (inr)', 'expense', 'item', 'value', 'purpose',
        'category', 'name', 'cost', 'total', 'organisation', 'organization',
        'bill no', 'date', '', 'amount'
    ]

    data = []
    lines = ocr_text.split('\n')
    for line in lines:
        # Match: Description, then amount (number) at end of line/table cell
        match = re.match(r'(.+?)\s+(\d+)(?:\s*|$)', line.strip())
        if match:
            cat = match.group(1).strip()
            amt = match.group(2).strip()
            # Exclude lines starting with known headings or meta fields
            lower_cat = cat.lower().replace(':','').strip()
            if any(keyword in lower_cat for keyword in skip_keywords):
                continue
            try:
                amount_f = float(amt.replace(',', ''))
                data.append({'Category': cat, 'Amount': amount_f})
            except ValueError:
                continue

    if not data:
        st.info("No line items detected. Please use a clean, tabular expense bill for best results.")
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
            st.write(
                f"Highest NGO spend: '{top_cat['Category']}'. Verify if this matches the intended funding priorities and optimize future use."
            )

st.caption("Built for NGOs: Accurate, transparent analysis and ready-to-present dashboard for Smart India Hackathon.")
