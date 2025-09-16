import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import plotly.express as px
import re
import fitz

st.title("ClariFunds-Lite: NGO Receipt Analyzer")
st.write("Upload an image or multi-page PDF. Each NGO bill (each page) will be analyzed separately.")

uploaded_file = st.file_uploader("Upload NGO Receipt (Image/PDF)", type=["jpg", "jpeg", "png", "bmp", "pdf"])

def simple_parse(ocr_text):
    data = []
    total = None
    skip_keywords = ['bill', 'date', 'organisation', 'organization', 'description', 'amount', 'category', 'name', 'cost', 'page', 'inr']
    for line in ocr_text.split('\n'):
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
        # Line is "Total 1234"
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
        per_page_results = []
        if uploaded_file.type == "application/pdf":
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page_number in range(doc.page_count):
                page = doc.load_page(page_number)
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                image = Image.open(pd.io.common.BytesIO(img_bytes))
                st.image(image, caption=f"Page {page_number+1} Preview", use_column_width=True)
                ocr_text = pytesseract.image_to_string(image)
                data, total = simple_parse(ocr_text)
                per_page_results.append({
                    'page': page_number+1,
                    'df': pd.DataFrame(data, columns=['Category','Amount']),
                    'total': total
                })
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Image Preview", use_column_width=True)
            ocr_text = pytesseract.image_to_string(image)
            data, total = simple_parse(ocr_text)
            per_page_results.append({
                'page': 1,
                'df': pd.DataFrame(data, columns=['Category','Amount']),
                'total': total
            })

        # Show analysis for each page separately
        for page_result in per_page_results:
            page_num = page_result['page']
            df = page_result['df']
            st.markdown(f"---\n## NGO Expense Analysis: Page {page_num}")
            if df.empty:
                st.warning("No items detected on this bill!")
                continue
            st.write(df)
            if page_result['total']:
                st.success(f"Reported Total: ₹{page_result['total']:,.2f}, Sum of items: ₹{df['Amount'].sum():,.2f}")
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

st.caption("Every NGO bill is analyzed separately for transparent, bill-specific insights. Multi-page PDFs supported!")
