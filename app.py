import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import plotly.express as px
import re
import time
import fitz  # PyMuPDF

st.title("ClariFunds-Lite: NGO Expense Analyzer")
st.write("Upload multi-page PDFs or images to analyze NGO expense reports accurately.")

uploaded_file = st.file_uploader("Upload NGO Receipt (Image/PDF)", type=["jpg", "jpeg", "png", "bmp", "pdf"])

def extract_data_from_text(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    data = []
    skip_keywords = ['total', 'gst', 'tax', 'subtotal', 'amount payable', 'amount due', 'balance']
    i = 0

    while i < len(lines):
        line = lines[i]
        # skip known header or footer lines
        if any(skip in line.lower() for skip in skip_keywords):
            i += 1
            continue

        # Find numbers in current line
        nums = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', line.replace(',', ''))

        if nums:
            # The last number is treated as amount
            amount_str = nums[-1]
            try:
                amount = float(amount_str)
            except:
                i += 1
                continue

            # Extract description
            # Assume description is everything before the last occurrence of amount
            idx = line.rfind(amount_str)
            desc = line[:idx].strip()
            if not desc and i > 0:
                # Sometimes description is above in previous line (multi-line cells)
                desc = lines[i - 1]
                # don't double count if last entry
                if data and data[-1][0] == desc:
                    i += 1
                    continue

            # Add only non-empty descriptions
            if desc:
                data.append((desc, amount))
        i += 1
    return data

if uploaded_file:
    all_data = []

    if uploaded_file.type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        with st.spinner(f"Processing {doc.page_count} pages..."):
            time.sleep(3)  # Simulated delay
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                image = Image.open(pd.io.common.BytesIO(img_bytes))
                st.image(image, caption=f"Page {page_num +1} Preview", use_column_width=True)

                text = pytesseract.image_to_string(image)
                page_data = extract_data_from_text(text)
                all_data.extend(page_data)
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image Preview", use_column_width=True)
        with st.spinner("Processing image..."):
            time.sleep(2)
            text = pytesseract.image_to_string(image)
            all_data.extend(extract_data_from_text(text))

    if not all_data:
        st.warning("No valid expense items detected. Please check the receipt quality.")
    else:
        df = pd.DataFrame(all_data, columns=['Category', 'Amount'])
        st.subheader("Extracted Expenses")
        st.write(df)

        total_expense = df['Amount'].sum()
        max_expense = df['Amount'].max()
        min_expense = df['Amount'].min()
        top_category = df.loc[df['Amount'].idxmax(), 'Category']

        # Display cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Expense", f"₹{total_expense:,.2f}")
        col2.metric("Highest Expense", f"₹{max_expense:,.2f}")
        col3.metric("Lowest Expense", f"₹{min_expense:,.2f}")
        col4.metric("Top Category", top_category)

        # Bar chart
        st.subheader("Expense Breakdown - Bar Chart")
        bar_fig = px.bar(df.groupby('Category', as_index=False).sum(), x='Category', y='Amount',
                         labels={'Amount': 'Amount (INR)'},
                         title='Expenses per Category')
        st.plotly_chart(bar_fig, use_container_width=True)

        # Treemap for better visualization of many categories
        st.subheader("Expense Distribution - Treemap")
        tree_fig = px.treemap(df.groupby('Category', as_index=False).sum(),
                              path=['Category'], values='Amount', color='Amount',
                              color_continuous_scale='Blues',
                              title='Proportion of Expenses')
        st.plotly_chart(tree_fig, use_container_width=True)

        # Recommendation
        st.subheader("Recommendation")
        st.write(f"The largest expense is in the '{top_category}' category "
                 f"at ₹{max_expense:,.2f}. Review this for budget alignment.")

st.caption("Built for NGOs: Accurate multi-page expense analysis for transparency and compliance.")

