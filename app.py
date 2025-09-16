import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import matplotlib.pyplot as plt
import re

expense_keywords = {
    'office': 'Check office supply expenses for savings opportunities.',
    'travel': 'Plan travel in advance to reduce costs.',
    'program': 'Review program spending for budget alignment.',
    'food': 'Bulk purchases may reduce food costs.',
    'supplies': 'Consider local vendors for better rates.',
    'misc': 'Audit miscellaneous expenses for unnecessary costs.'
}

st.title("ClariFunds-Lite: NGO Receipt Analyzer")
st.write("Upload your NGO’s expense receipt to auto-categorize and visualize spend for transparent reporting.")

uploaded_file = st.file_uploader("Upload Receipt Image", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Receipt Preview", use_column_width=True)
    st.divider()

    ocr_text = pytesseract.image_to_string(image)
    st.subheader("Detected Text (OCR)")
    st.code(ocr_text, language='text')

    # Simple keyword match for categories
    data = []
    lines = ocr_text.split('\n')
    found_recommendation = ""
    for line in lines:
        for cat in expense_keywords:
            if cat in line.lower():
                nums = re.findall(r"\d+\.\d+|\d+", line)
                if nums:
                    amount = float(nums[-1])
                    data.append({'Category': cat.title(), 'Amount': amount})
                    # First found category gets the recommendation
                    if not found_recommendation:
                        found_recommendation = expense_keywords[cat]
    if not data:
        st.info("No recognizable expense categories found in this receipt. Please upload a clearer bill with visible category names like 'office', 'travel', etc.")
        df = pd.DataFrame([{'Category': 'Unknown', 'Amount': 0.0}])
    else:
        df = pd.DataFrame(data)
        st.subheader("Expense Categories")
        st.write(df)

        st.subheader("Visual Breakdown")
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

        st.subheader("Recommendation")
        st.write(found_recommendation if found_recommendation else "Expenses detected. Keep tracking for better fund management.")

st.caption("Developed using Streamlit and OCR for NGO transparency.")

# requirements.txt
# streamlit
# pillow
# pytesseract
# pandas
# matplotlib
