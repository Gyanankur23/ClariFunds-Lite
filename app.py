import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import plotly.express as px
import re
import time
import fitz  # PyMuPDF

st.title("ClariFunds-Lite: NGO Receipt Analyzer")
st.write(
    "Upload multi-page NGO expense PDFs or images. The app analyzes each page separately providing detailed insights."
)

uploaded_file = st.file_uploader("Upload NGO Receipt Image(s) or PDF", type=["jpg", "jpeg", "png", "bmp", "pdf"])

def extract_table_data(ocr_text):
    """
    Extracts category and amount pairs from OCR text for a single table.
    Separates out total amount line.
    Ignores bill no, date, organization, and header lines.
    """
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    data = []
    total_amount = None
    
    ignore_keywords = [
        'description', 'amount', 'expense', 'item', 'value', 'purpose',
        'category', 'name', 'cost', 'bill no', 'date', 'organisation', 
        'organization', 'inr', 'no.', 'total', 'gst', 'tax', 'subtotal'
    ]
    
    for line in lines:
        lower = line.lower()
        if any(word in lower for word in ignore_keywords):
            # Catch total separately
            if 'total' in lower:
                possible_amounts = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', line.replace(',', ''))
                if possible_amounts:
                    try:
                        total_amount = float(possible_amounts[-1].replace(',', ''))
                    except:
                        pass
            continue
        
        # Extract last number as amount
        possible_amounts = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', line.replace(',', ''))
        if possible_amounts:
            try:
                amount = float(possible_amounts[-1].replace(',', ''))
                # Description is line without the last number
                index = line.rfind(possible_amounts[-1])
                category = line[:index].strip()
                if category == '':
                    # Possible multiline description: skip for simplicity, or try previous line approach
                    continue
                data.append((category, amount))
            except:
                continue
                
    return data, total_amount

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        st.write(f"Processing {doc.page_count} pages...")
    else:
        doc = None

    all_tables = []

    if doc:
        with st.spinner("AI is analyzing all pages..."):
            time.sleep(5)
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                image = Image.open(pd.io.common.BytesIO(img_bytes))
                st.image(image, caption=f"Page {page_num+1} Preview", use_column_width=True)
                ocr_text = pytesseract.image_to_string(image)
                table_data, total = extract_table_data(ocr_text)
                all_tables.append({'data': table_data, 'total': total, 'page': page_num + 1})
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image Preview", use_column_width=True)
        with st.spinner("AI is analyzing the image..."):
            time.sleep(3)
            ocr_text = pytesseract.image_to_string(image)
            table_data, total = extract_table_data(ocr_text)
            all_tables.append({'data': table_data, 'total': total, 'page': 1})

    # For each table (page), show details separately with charts
    for table in all_tables:
        st.markdown(f"---\n## Page {table['page']} Expense Breakdown")
        df = pd.DataFrame(table['data'], columns=['Category', 'Amount'])

        if df.empty:
            st.warning("No expense data found on this page.")
            continue

        st.write(df)

        # Show total if detected
        if table['total'] is not None:
            st.write(f"**Reported total:** ₹{table['total']:,.2f}")
            scraped_total = df['Amount'].sum()
            st.write(f"**Sum of extracted items:** ₹{scraped_total:,.2f}")
            if abs(scraped_total - table['total']) > 1:
                st.warning("Discrepancy detected between reported total and sum of extracted items.")

        # KPI cards
        total_exp = df['Amount'].sum()
        max_exp = df['Amount'].max()
        min_exp = df['Amount'].min()
        top_cat = df.loc[df['Amount'].idxmax(), 'Category']

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Expense", f"₹{total_exp:,.2f}")
        c2.metric("Maximum Expense", f"₹{max_exp:,.2f}")
        c3.metric("Minimum Expense", f"₹{min_exp:,.2f}")
        c4.metric("Top Category", top_cat)

        # Bar chart
        st.subheader("Expenses by Category - Bar Chart")
        bar_fig = px.bar(df, x='Category', y='Amount', title="Expense Comparison", labels={'Amount':'INR'})
        st.plotly_chart(bar_fig, use_container_width=True)

        # Treemap with amount labels
        st.subheader("Expenses Proportion - Treemap")
        treemap_fig = px.treemap(df, path=['Category'], values='Amount', title='Expense Distribution',
                                 color='Amount', color_continuous_scale='Viridis',
                                 hover_data={'Amount':':,.2f'})
        st.plotly_chart(treemap_fig, use_container_width=True)

        st.subheader("Recommendation")
        st.write(f"Top spend category: **{top_cat}** with ₹{max_exp:,.2f}. Verify alignment with budget plans.")

st.caption("Developed for NGOs: Multi-page, reliable, visual expense analytics.")
