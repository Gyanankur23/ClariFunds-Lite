import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import matplotlib.pyplot as plt
import re
import time

st.title("ClariFunds-Lite: NGO Receipt Analyzer")
st.write(
    "Upload your NGO’s expense receipt to instantly auto-categorize and visualize spend for transparent fund reporting and compliance."
)

uploaded_file = st.file_uploader("Upload NGO Receipt Image", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Receipt Preview", use_column_width=True)
    st.divider()

    # AI thinking animation
    with st.spinner("AI is thinking... Extracting and analyzing expenses."):
        time.sleep(5.5)  # Simulate thinking delay (5–6 seconds)
        ocr_text = pytesseract.image_to_string(image)

    st.subheader("Detected Text (OCR)")
    st.code(ocr_text, language='text')

    data = []
    lines = ocr_text.split('\n')
    for line in lines:
        nums = re.findall(r"\d+\.\d+|\d+", line)
        if nums:
            # Extract first non-numeric word(s) before the number as category
            parts = re.split(r"\d+\.\d+|\d+", line, maxsplit=1)
            cat = parts[0].strip() if parts[0].strip() else "Other"
            try:
                amount = float(nums[-1])
                if cat.lower() in ["total", "tax", "gst"]:
                    continue
                data.append({'Category': cat.title(), 'Amount': amount})
            except:
                continue

    if not data:
        st.info(
            "No line items with clear amounts found. Please upload a clearer NGO expense receipt."
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

        # Short, NGO-centric recommendation
        top_cat = df.sort_values('Amount', ascending=False).iloc[0]
        st.subheader("AI Recommendation")
        st.write(
            f"Most NGO funds spent on '{top_cat['Category']}'. Ensure this aligns with your budget plan and reporting requirements."
        )

st.caption("Built for NGOs: Simple, transparent, and instant expense analysis dashboard.")
