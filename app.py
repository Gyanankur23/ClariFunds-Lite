import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import matplotlib.pyplot as plt
import re

st.title("ClariFunds-Lite: Universal Receipt Analyzer")
st.write(
    "Upload any expense bill (not limited to specific keywords). "
    "The tool extracts line items and amounts to provide a useful dashboard."
)

uploaded_file = st.file_uploader("Upload Receipt Image", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Receipt Preview", use_column_width=True)
    st.divider()

    ocr_text = pytesseract.image_to_string(image)
    st.subheader("Detected Text (OCR)")
    st.code(ocr_text, language='text')

    data = []
    lines = ocr_text.split('\n')
    for line in lines:
        # Look for any number (amount) in each line
        nums = re.findall(r"\d+\.\d+|\d+", line)
        if nums:
            # Use text before the first number as category
            parts = re.split(r"\d+\.\d+|\d+", line, maxsplit=1)
            cat = parts[0].strip() if parts[0].strip() else "Other"
            try:
                amount = float(nums[-1])
                # Clean up category: only take simple words, avoid "Total"/"GST"/"Tax" lines if preferred
                if cat.lower() in ["total", "tax", "gst"]:
                    continue
                data.append({'Category': cat.title(), 'Amount': amount})
            except:
                continue
    if not data:
        st.info(
            "No line items with amounts found. Try with a different or clearer bill image."
        )
        df = pd.DataFrame([{'Category': 'Unknown', 'Amount': 0.0}])
    else:
        df = pd.DataFrame(data)
        st.subheader("Expense Breakdown")
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

        # Simple recommendation: Point out top category
        top_cat = df.sort_values('Amount', ascending=False).iloc[0]
        st.subheader("Recommendation")
        st.write(
            f"Most spent on '{top_cat['Category']}'. Review regular high expenses for smarter fund use."
        )

st.caption(
    "Works on any retail, grocery, or service bill for instant dashboard insight."
)
