import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import plotly.express as px
import re
import fitz

st.title("ClariFunds-Lite: NGO Receipt Analyzer")
st.write("Upload a single-page image or a PDF (first page only for demo reliability).")

uploaded_file = st.file_uploader("Upload NGO Receipt (Image/PDF)", type=["jpg", "jpeg", "png", "bmp", "pdf"])

def simple_parse(ocr_text):
    data = []
    total = None
    skip_keywords = ['bill', 'date', 'organisation', 'organization', 'description', 'amount', 'category', 'name', 'cost', 'page', 'inr']
    for line in ocr_text.split('\n'):
        original = line
        line = line.strip()
        if not line:
            continue
        has_number = re.search(r'\d', line)
        if not has_number:
            continue
        lower = line.lower()
        if any(x in lower for x in skip_keywords):
            continue
        match = re.match(r'(.+?)\s+(\d+)$', line)
        if match:
            desc, amt = match.groups()
            if 'total' in desc.lower():
                try:
                    total = float(amt)
                except:
                    total = None
                continue
            data.append( (desc.strip(), float(amt)) )
            continue
        # If line is "Total 1234"
        if line.lower().startswith("total"):
            nums = re.findall(r'\d+', line)
            if nums:
                try:
                    total = float(nums[-1])
                except:
                    total = None
            continue
    return data, total

if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            image = Image.open(pd.io.common.BytesIO(img_bytes))
            st.image(image, caption="PDF (First Page) Preview", use_column_width=True)
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Image Preview", use_column_width=True)
        st.info("Best accuracy is with clean, one-line per item receipts (like LaTeX PDFs/images).")
        ocr_text = pytesseract.image_to_string(image)
        st.code(ocr_text)
        data, total = simple_parse(ocr_text)
        df = pd.DataFrame(data, columns=['Category','Amount'])
        if df.empty:
            st.warning("No items detected. Try experimenting with a more clearly printed image.")
        else:
            st.write(df)
            if total:
                st.success(f"Reported Total: ₹{total:,.2f}; Sum of items: ₹{df['Amount'].sum():,.2f}")
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Expense", f"₹{df['Amount'].sum():,.2f}")
            col2.metric("Max Expense", f"₹{df['Amount'].max():,.2f}")
            col3.metric("Min Expense", f"₹{df['Amount'].min():,.2f}")
            col4.metric("Top Category", df.loc[df['Amount'].idxmax(),'Category'])
            # Bar Chart
            st.subheader("Bar Chart")
            st.plotly_chart(px.bar(df, x='Category', y='Amount', labels={'Amount':'INR'}), use_container_width=True)
            # Treemap Chart
            st.subheader("Treemap")
            st.plotly_chart(px.treemap(df, path=['Category'], values='Amount', color='Amount', color_continuous_scale='Viridis'), use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

st.caption("Demo: For multi-page PDFs, only the first page is processed for stability. For full multi-page features, run locally with higher resources.")
