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
    "Upload your NGO’s expense receipt (image or PDF) to auto-extract, analyze, and visualize expenses—optimized for your LaTeX bill format."
)

uploaded_file = st.file_uploader("Upload NGO Receipt Image or PDF", type=["jpg", "jpeg", "png", "bmp", "pdf"])

image = None

def extract_lines(ocr_text):
    """
    Parses OCR text to extract (description, amount) pairs from your LaTeX-style bills.
    Tries to handle cases where amount is on a separate line below description.
    Ignores headers, totals, and empty lines.
    """
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip() != '']
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
        
        # Skip header/meta lines
        if any(keyword in lower_line for keyword in skip_keywords):
            i += 1
            continue
        
        # Try to find amount in current line
        nums = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', line.replace(',', ''))
        if nums:
            # If amount in line, split description and amount
            possible_amount = nums[-1].replace(',', '')
            try:
                amount = float(possible_amount)
                description = line[:line.rfind(nums[-1])].strip()
                if description == '':
                    # If description empty, check previous line (likely description)
                    if i > 0:
                        description = lines[i-1]
                        # Prevent duplicate if previous line already used
                        if data and data[-1][0] == description:
                            i += 1
                            continue
                # Avoid counting totals or taxes
                if any(x in description.lower() for x in ['total', 'tax', 'gst']):
                    i += 1
                    continue
                data.append((description, amount))
            except:
                pass
            i += 1
        else:
            # If no amount in line, check next line for amount
            if i + 1 < len(lines):
                next_line = lines[i+1]
                nums_next = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', next_line.replace(',', ''))
                if nums_next:
                    possible_amount = nums_next[-1].replace(',', '')
                    try:
                        amount = float(possible_amount)
                        description = line
                        if any(x in description.lower() for x in ['total', 'tax', 'gst']):
                            i += 2
                            continue
                        data.append((description, amount))
                        i += 2
                        continue
                    except:
                        pass
            i += 1
    return data


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

    data = extract_lines(ocr_text)

    if not data:
        st.info("No line items detected. Please use a clean, tabular expense bill image/PDF (like the provided LaTeX bills).")
    else:
        df = pd.DataFrame(data, columns=['Category', 'Amount'])
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

        top_cat = df.sort_values('Amount', ascending=False).iloc[0]
        st.subheader("AI Recommendation")
        st.write(
            f"Highest NGO spend: '{top_cat['Category']}'. Confirm alignment with funding priorities."
        )

st.caption("Built for NGOs: Optimized for clear tabular receipts like LaTeX-generated bills, enabling transparent fund analysis.")
