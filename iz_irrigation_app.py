import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# TITLE
# -------------------------

st.title("Irrigation Scheduling Helper App")

st.write("""
This tool compares cumulative crop evapotranspiration (ET)
with accumulated water supply (rain + irrigation).
When depletion exceeds the threshold,
the system recommends irrigation to ensure healthy crops.
""")

# -------------------------
# FILE UPLOAD
# -------------------------

uploaded_file = st.file_uploader("Upload Weather CSV File", type=["csv"])

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    # Ensure numeric types
    df['ET_inches'] = df['ET_inches'].astype(float)
    df['Precipitation_inches'] = df['Precipitation_inches'].astype(float)

    # Generate Month and Day columns for selection (assuming daily data from index)
    # This is a simplified approach; for complex date handling, a 'Date' column in CSV is recommended.
    df['Day_Index'] = df.index
    # Approximate month and day within month for display purposes
    month_map = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    df['Month'] = ((df.index // 30) % 12) + 1 # Simple approximation for month number
    df['Day'] = (df.index % 30) + 1 # Simple approximation for day within month
    df['Month'] = df['Month'].map(month_map).fillna('Unknown') # Map to names

    # User Inputs
    irrigation_trigger = st.slider("Allowable Depletion (inches)", 0.5, 3.0, 1.0)
    irrigation_depth = st.slider("Irrigation Depth Applied (inches)", 0.5, 2.0, 1.0)

    # Initialize columns as floats
    df['Daily_I'] = 0.0
    df['ET_Cumul'] = 0.0
    df['cum_P_and_I'] = 0.0
    df['Depletion'] = 0.0

    cumulative_ET = 0.0
    cumulative_P_and_I_total = 0.0


    # -------------------------
    # IRRIGATION SIMULATION LOOP
    # -------------------------

    for i in range(len(df)):

        cumulative_ET += df.loc[i, 'ET_inches']
        df.loc[i, 'ET_Cumul'] = cumulative_ET

        cumulative_P_and_I_total += df.loc[i, 'Precipitation_inches']

        depletion = cumulative_ET - cumulative_P_and_I_total

        if depletion >= irrigation_trigger:
            irrigation_today = irrigation_depth
            cumulative_P_and_I_total += irrigation_today
            df.loc[i, 'Daily_I'] = irrigation_today
            depletion = cumulative_ET - cumulative_P_and_I_total

        df.loc[i, 'cum_P_and_I'] = cumulative_P_and_I_total
        df.loc[i, 'Depletion'] = depletion

    # -------------------------
    # RESULTS
    # -------------------------

    st.subheader("Season Summary")

    total_irrigation = df['Daily_I'].sum()
    irrigation_events = (df['Daily_I'] > 0).sum()

    st.write(f"Total Irrigation Applied: {total_irrigation:.2f} inches")
    st.write(f"Number of Irrigation Events: {irrigation_events}")

    # -------------------------
    # CHARTS
    # -------------------------

    st.subheader("Depletion Over Time")

    fig, ax = plt.subplots()
    ax.plot(df.index, df['Depletion'])
    ax.set_xlabel("Day")
    ax.set_ylabel("Soil Water Depletion (inches)")
    st.pyplot(fig)

    st.subheader("Daily Irrigation Events")

    fig2, ax2 = plt.subplots()
    ax2.bar(df.index, df['Daily_I'])
    ax2.set_xlabel("Day")
    ax2.set_ylabel("Irrigation Applied (inches)")
    st.pyplot(fig2)

    # -------------------------
    # CALENDAR TABLE
    # -------------------------

    st.subheader("Daily Irrigation Calendar")

    st.dataframe(df[['ET_inches', 'Precipitation_inches', 'Depletion', 'Daily_I', 'Month', 'Day']])

    # -------------------------
    # MONTH AND DAY SELECTION FOR DECISION
    # -------------------------

    st.subheader("Irrigation Decision for a Specific Day")

    # Ensure Month column is correctly ordered for selectbox (if using generated months)
    month_order = [m for m in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'] if m in df['Month'].unique()]
    if 'Unknown' in df['Month'].unique():
        month_order.append('Unknown') # Add 'Unknown' if it exists due to fillna

    selected_month = st.selectbox("Select a month:", month_order)
    filtered_df_by_month = df[df['Month'] == selected_month]

    # Sort days for better user experience
    unique_days = filtered_df_by_month['Day'].unique()
    unique_days.sort()
    selected_day = st.selectbox("Select a day:", unique_days)

    # Filter the dataframe for the selected date
    selected_day_data = filtered_df_by_month[filtered_df_by_month['Day'] == selected_day]

    if not selected_day_data.empty:
        selected_day_data_row = selected_day_data.iloc[0]
        st.write(f"For {selected_month} {selected_day}, the decision is to apply **{selected_day_data_row['Daily_I']:.2f}** inches of irrigation.")
        st.write(f"On this day, ET was: **{selected_day_data_row['ET_inches']:.2f}** inches, and precipitation was: **{selected_day_data_row['Precipitation_inches']:.2f}** inches.")
    else:
        st.write(f"No data available for {selected_month} {selected_day}.")

    # Re-display plots for context after selection if desired, or remove if redundant
    # st.pyplot(fig)
    # st.pyplot(fig2)
