import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import matplotlib.pyplot as plt
import re
import time
from difflib import get_close_matches

# NGO-focused reference categories
ref_categories = [
    "Office Supplies", "Travel", "Program", "Food", "Staff", "Utilities",
    "Stationery", "Transport", "Accommodation", "Workshop", "Training", "Misc"
]
fuzzy_threshold = 0.7  # Can be tuned

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
            # Extract first non-numeric word(s) before the number as category guess
            parts = re.split(r"\d+\.\d+|\d+", line, maxsplit=1)
            raw_cat = parts[0].strip() if parts[0].strip() else "Other"
            try:
                amount = float(nums[-1])
                # Fuzzy match raw_cat with ref_categories
                match = get_close_matches(raw_cat, ref_categories, n=1, cutoff=fuzzy_threshold)
                if match:
                    cat = match[0]
                else:
                    cat = raw_cat.title() if raw_cat.lower() not in ["total", "tax", "gst"] else "Other"
                if cat in ["Total", "Tax", "Gst", "Other"] and raw_cat.lower() in ["total", "tax", "gst"]:
                    continue  # skip total/tax/gst lines
                data.append({'Line': line.strip(), 'Category': cat, 'Amount': amount})
            except:
                continue

    if not data:
        st.info(
            "No line items with clear amounts found. Please upload a clearer NGO expense receipt."
        )
        df = pd.DataFrame([{'Line': '', 'Category': 'Unknown', 'Amount': 0.0}])
    else:
        df = pd.DataFrame(data)
        st.subheader("Auto-Categorized Expenses")
        st.write(df[['Line', 'Category', 'Amount']])

        # User Correction UI
        st.subheader("Review and Correct Categories (if needed)")
        edit_df = df.copy()
        for i, row in edit_df.iterrows():
            default_cat = row['Category']
            new_cat = st.selectbox(
                f"Edit category for: '{row['Line']}' (amount: {row['Amount']})",
                options=ref_categories + ["Other"],
                index=ref_categories.index(default_cat) if default_cat in ref_categories else len(ref_categories),
                key=f"cat_select_{i}"
            )
            edit_df.at[i, "Category"] = new_cat

        # Dashboard Visualization
        dashboard_df = edit_df.groupby('Category', as_index=False)['Amount'].sum()
        dashboard_df = dashboard_df[dashboard_df['Amount'] > 0]

        st.subheader("Visual Summary")
        st.bar_chart(dashboard_df.set_index('Category')['Amount'])
        fig, ax = plt.subplots()
        dashboard_df.set_index('Category').plot.pie(
            y='Amount',
            autopct='%1.1f%%',
            legend=False,
            ylabel='',
            ax=ax
        )
        st.pyplot(fig)

        # Short, NGO-centric recommendation
        if not dashboard_df.empty:
            top_cat = dashboard_df.sort_values('Amount', ascending=False).iloc[0]
            st.subheader("AI Recommendation")
            st.write(
                f"Most NGO funds spent on '{top_cat['Category']}'. Ensure this aligns with your budget and reporting requirements."
            )

st.caption("Built for NGOs: Simple, transparent, and instant expense analysis dashboard.")

