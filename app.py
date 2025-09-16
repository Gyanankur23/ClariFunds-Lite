import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import plotly.express as px
import re
import time
import fitz  # PyMuPDF for PDF

st.title("ClariFunds-Lite: NGO Receipt Analyzer")
st.write("Upload multi-page PDFs or images for precise expense analysis.")

uploaded_file = st.file_uploader("Upload NGO Receipt (Image/PDF)", type=["jpg", "jpeg", "png", "bmp", "pdf"])

def parse_lines(lines):
    """
    Parse lines to extract expense rows, ignoring headers, totals, footer lines.
    Handles multi-line descriptions if split.
    """
    data = []
    total_amount = None
    skip_keywords = ['total', 'gst', 'tax', 'subtotal', 'amount payable', 'amount due']
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        lc = line.lower()
        # Skip headers or footer summaries
        if any(k in lc for k in skip_keywords):
            # If "total", parse for total if line includes a number
            if 'total' in lc:
                nums = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', line.replace(',', ''))
                if nums:
                    try:
                        total_amount = float(nums[-1].replace(',', ''))
                    except:
                        total_amount = None
            i += 1
            continue
        # Look for a line with a number clue
        nums = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', line.replace(',', ''))
        if nums:
            amount_str = nums[-1].replace(',', '')
            try:
                amount = float(amount_str)
            except:
                i += 1
                continue
            # The description is line content before amount
            desc_candidate = line[:line.rfind(nums[-1])].strip()
            # If description is empty or looks like a total, check previous line
            if not desc_candidate and i > 0:
                desc_candidate = lines[i - 1]
                # Avoid duplicate entry if previous line was description
                if data and data[-1][0] == desc_candidate:
                    i += 1
                    continue
            # Skip if description is total or footer
            if any(k in desc_candidate.lower() for k in skip_keywords):
                i += 1
                continue
            data.append((desc_candidate, amount))
        else:
            # Check if next line is just an amount; merge lines
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                nums_next = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', next_line.replace(',', ''))
                if nums_next:
                    try:
                        amount = float(nums_next[-1].replace(',', ''))
                        desc_candidate = line
                        if not any(k in desc_candidate.lower() for k in skip_keywords):
                            data.append((desc_candidate, amount))
                        i += 2
                        continue
                    except:
                        pass
            i += 1
    return data, total_amount

# Process file
if uploaded_file:
    page_data_list = []
    if uploaded_file.type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        with st.spinner(f"Processing {doc.page_count} pages..."):
            time.sleep(3)
            for p in range(doc.page_count):
                page = doc.load_page(p)
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                image = Image.open(pd.io.common.BytesIO(img_bytes))
                ocr_text = pytesseract.image_to_string(image)
                lines = [line for line in ocr_text.split('\n')]
                data, total = parse_lines(lines)
                page_data_list.append({'page': p+1, 'data': data, 'total': total})
                st.image(image, caption=f"Page {p+1} preview", use_column_width=True)
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image Preview", use_column_width=True)
        with st.spinner("Extracting data from image..."):
            time.sleep(3)
            ocr_text = pytesseract.image_to_string(image)
            lines = [line for line in ocr_text.split('\n')]
            data, total = parse_lines(lines)
            page_data_list = [{'page': 1, 'data': data, 'total': total}]

    # Show previews and detailed analysis per page
    for page_info in page_data_list:
        page_num = page_info['page']
        df = pd.DataFrame(page_info['data'], columns=['Category', 'Amount'])
        st.markdown(f"## Page {page_num} Expense Details")
        if df.empty:
            st.warning("No expense entries found on this page.")
            continue
        st.write(df)

        # Show total in report
        if page_info['total'] is not None:
            sum_items = df['Amount'].sum()
            st.write(f"Reported Total: ₹{page_info['total']:,.2f} | Sum of Items: ₹{sum_items:,.2f}")
            if abs(sum_items - page_info['total']) > 1:
                st.warning("Discrepancy between sum and reported total detected.")

        # KPIs as cards
        total_exp = df['Amount'].sum()
        max_exp = df['Amount'].max()
        min_exp = df['Amount'].min()
        top_cat = df.loc[df['Amount'].idxmax(), 'Category']
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Expense", f"₹{total_exp:,.2f}")
        col2.metric("Max Expense", f"₹{max_exp:,.2f}")
        col3.metric("Min Expense", f"₹{min_exp:,.2f}")
        col4.metric("Top Category", top_cat)

        # Visualization: Bar
        st.subheader("Expenses by Category - Bar Chart")
        fig_bar = px.bar(df, x='Category', y='Amount', labels={'Amount':'INR'})
        st.plotly_chart(fig_bar, use_container_width=True)

        # Visualization: Treemap
        st.subheader("Expenses Distribution - Treemap")
        fig_tree = px.treemap(df, path=['Category'], values='Amount',
                              color='Amount', color_continuous_scale='Viridis',
                              title='Expense Share')
        st.plotly_chart(fig_tree, use_container_width=True)

