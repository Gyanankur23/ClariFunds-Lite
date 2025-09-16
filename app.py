import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import io
import re

st.set_page_config(page_title="ClariFunds-Lite Dashboard", layout="wide")

st.title("ClariFunds-Lite: NGO Receipt Analyzer")
st.write("Upload a receipt image. The AI will extract, categorize, and visualize expenses in seconds.")

# Upload Button
uploaded_file = st.file_uploader("Upload Receipt", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    col1, col2 = st.columns([1, 2])
    with col1:
        image = Image.open(uploaded_file)
        st.image(image, caption='Receipt Preview', use_column_width=True)

    # OCR Extraction
    text = pytesseract.image_to_string(image)
    
    # Basic Expense Extraction
    categories = ['office', 'travel', 'program', 'food', 'supplies', 'misc']
    lines = text.split('\n')
    data = []
    for line in lines:
        for cat in categories:
            if cat in line.lower():
                amount = None
                if '₹' in line:
                    try:
                        amount = float(line.split('₹')[-1].strip().split()[0].replace(',', ''))
                    except:
                        amount = None
                else:
                    nums = re.findall(r"\d+\.\d+|\d+", line)
                    if nums:
                        amount = float(nums[-1])
                if amount:
                    data.append({'Category': cat.title(), 'Amount': amount})
    if not data:
        # If not found, put total
        nums = re.findall(r"\d+\.\d+|\d+", text)
        if nums:
            data = [{'Category': 'Total', 'Amount': float(nums[-1])}]
        else:
            data = [{'Category': 'Unknown', 'Amount': 0.0}]
    df = pd.DataFrame(data)

    with col2:
        st.subheader("Expense Breakdown")
        st.dataframe(df, use_container_width=True)

        # Charts
        st.subheader("Visual Summary")
        st.bar_chart(df.set_index('Category')['Amount'])
        st.write("")  # Spacer
        st.pyplot(df.set_index('Category').plot.pie(y='Amount', autopct='%1.1f%%', legend=False, ylabel='').get_figure())

        # Recommendation
        st.subheader("AI Recommendation")
        if df['Amount'].sum() == 0:
            st.write("No clear expense amounts found. Try another image with clearer text and visible numbers.")
        elif 'Total' in df['Category'].values or 'Unknown' in df['Category'].values:
            st.write("Check receipt clarity or try specifying expense categories for better recommendations.")
        else:
            top_cat = df.sort_values('Amount', ascending=False).iloc[0]
            st.write(f"Highest spending is in '{top_cat['Category']}'. Consider reviewing and optimizing this category for better fund management.")

else:
    st.info("Please upload a clear receipt image (jpg, jpeg, or png) to begin analysis.")

