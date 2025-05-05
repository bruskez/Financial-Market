import streamlit as st
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configurazione iniziale
st.set_page_config(page_title="Financial Dashboard", layout="wide")


# Funzione per caricare e processare i dati
@st.cache_data
def load_data(selected_files, selected_folder_path, selected_year):
    data = pd.DataFrame()

    for file in selected_files:
        try:
            file_path = os.path.join(selected_folder_path, file)
            df = pd.read_csv(file_path)

            # Conversione e filtraggio date
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            df = df.loc[f'{selected_year[0]}-01-01':f'{selected_year[1]}-12-31']

            # Calcolo metriche
            df['daily_return'] = df['Close'].pct_change() * 100
            monthly_group = df.resample('ME')  # ME per frequenza mensile (end of month)

            df['monthly_mean'] = monthly_group['daily_return'].transform('mean')
            df['monthly_volatility'] = monthly_group['daily_return'].transform('std')
            df['monthly_volume'] = monthly_group['Volume'].transform('mean')

            df['File'] = file  # Aggiungi nome file
            data = pd.concat([data, df])

        except Exception as e:
            st.warning(f"Error processing {file}: {str(e)}")

    return data


# UI Layout
st.title("📊 Your First Financial Analysis Dashboard")
st.markdown("""
    <style>
    .small-font { font-size:18px !important; }
    </style>
    <p class="small-font">This dashboard provides a visual analysis of financial data, including Returns, Volatility, and Volume for selected securities </p>
    """, unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    data_folder = "data"

    try:
        subfolders = [f.name for f in os.scandir(data_folder) if f.is_dir()]
        selected_folder = st.radio("📂 Instrument Type", subfolders)
        selected_folder_path = os.path.join(data_folder, selected_folder)
        files = [f.name for f in os.scandir(selected_folder_path) if f.is_file() and f.name.endswith('.csv')]

        if not files:
            st.error("No CSV files found in selected folder")
            st.stop()

        selected_files = st.multiselect("🔍 Select Securities", files)

        if not selected_files:
            st.warning("Please select at least one security")
            st.stop()

        start_year, end_year = 2013, datetime.now().year
        selected_year = st.slider("📅 Time Period", start_year, end_year, (start_year, end_year))

        chart_type = st.selectbox("📈 Analysis Type", [
            "Returns",
            "Returns and Volatility",
            "Volume",
            "Volatility"
        ])

    except Exception as e:
        st.error(f"Initialization error: {str(e)}")
        st.stop()

# Main content
try:
    data = load_data(selected_files, selected_folder_path, selected_year)

    if data.empty:
        st.warning("No data available for selected period")
        st.stop()

    # Monthly aggregated data
    monthly_data = data.groupby(['File', pd.Grouper(freq='ME')]).mean().reset_index()

    # Visualizations
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader(f"{chart_type} Analysis")

        if chart_type == "Returns":
            fig = px.line(monthly_data, x='Date', y='monthly_mean', color='File',
                          labels={'monthly_mean': 'Monthly Return (%)'})
            fig.update_traces(line_width=2.5)

        elif chart_type == "Returns and Volatility":
            fig = px.scatter(monthly_data, x='monthly_mean', y='monthly_volatility',
                             color='File', size='monthly_volume',
                             labels={'monthly_mean': 'Return (%)',
                                     'monthly_volatility': 'Volatility'})

        elif chart_type == "Volatility":
            fig = px.area(monthly_data, x='Date', y='monthly_volatility', color='File',
                          labels={'monthly_volatility': 'Volatility'})

        elif chart_type == "Volume":
            fig = px.bar(monthly_data, x='Date', y='monthly_volume', color='File',
                         labels={'monthly_volume': 'Volume'})

        fig.update_layout(height=500, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Statistics")
        st.dataframe(monthly_data.groupby('File').agg({
            'monthly_mean': ['mean', 'std'],
            'monthly_volume': 'mean'
        }).rename(columns={
            'monthly_mean': 'Return',
            'monthly_volume': 'Volume'
        }).style.format("{:.2f}"))

except Exception as e:
    st.error(f"Processing error: {str(e)}")