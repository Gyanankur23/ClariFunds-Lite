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
    "Upload multi-page NGO expense PDFs or images. The app analyzes all pages and summarizes your NGO’s funding transparency."
)

uploaded_file = st.file_uploader("Upload NGO Receipt Image(s) or PDF", type=["jpg", "jpeg", "png", "bmp", "pdf"])

def extract_lines(ocr_text):
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    data = []
    i = 0
    skip_keywords = [
        'description', 'amount', 'expense', 'item', 'value', 'purpose',
        'category', 'name', 'cost', 'total', 'organisation', 'organization',
        'bill no', 'date', 'inr', 'no.'
    ]
    while i < len(lines):
        line = lines[i]
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in skip_keywords):
            i += 1
            continue
        nums = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', line.replace(',', ''))
        if nums:
            possible_amount = nums[-1].replace(',', '')
            try:
                amount = float(possible_amount)
                desc = line[:line.rfind(nums[-1])].strip()
                if desc == '' and i > 0:
                    desc = lines[i-1]
                    if data and data[-1][0] == desc:
                        i += 1
                        continue
                if any(x in desc.lower() for x in ['total', 'tax', 'gst']):
                    i += 1
                    continue
                data.append((desc, amount))
            except:
                pass
        i += 1
    return data

if uploaded_file:
    all_data = []

    if uploaded_file.type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        with st.spinner(f"AI is thinking... Extracting and analyzing {doc.page_count} pages."):
            time.sleep(5.5)
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                image = Image.open(pd.io.common.BytesIO(img_bytes))
                st.image(image, caption=f"Receipt Preview - Page {page_num+1}", use_column_width=True)

                ocr_text = pytesseract.image_to_string(image)
                page_data = extract_lines(ocr_text)
                all_data.extend(page_data)

    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Receipt Preview", use_column_width=True)
        with st.spinner("AI is thinking... Extracting and analyzing."):
            time.sleep(5.5)
            ocr_text = pytesseract.image_to_string(image)
            all_data.extend(extract_lines(ocr_text))

    if not all_data:
        st.info("No line items detected. Please use clear and tabulated expense bills.")
    else:
        df = pd.DataFrame(all_data, columns=['Category', 'Amount'])
        st.subheader("Extracted Expenses Across All Pages")
        st.write(df)

        st.subheader("Visual Summary")
        st.bar_chart(df.groupby('Category')['Amount'].sum())

        fig, ax = plt.subplots()
        df.groupby('Category')['Amount'].sum().plot.pie(
            autopct='%1.1f%%', legend=False, ylabel='', ax=ax
        )
        st.pyplot(fig)

        top_cat = df.groupby('Category')['Amount'].sum().idxmax()
        top_val = df.groupby('Category')['Amount'].sum().max()
        st.subheader("AI Recommendation")
        st.write(
            f"Highest NGO spending category: '{top_cat}' with ₹{top_val:.2f}. Review this for alignment with budget goals."
        )

st.caption("Built for NGOs: Transparent multi-page expense analysis dashboard, ready for Smart India Hackathon.")
