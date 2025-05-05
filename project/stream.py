import streamlit as st
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

# Function to load and process data with caching for performance
@st.cache_data
def load_data(selected_files, selected_folder_path, selected_year):
    """Load and process financial data from selected CSV files"""
    data = pd.DataFrame()

    for file in selected_files:
        file_path = os.path.join(selected_folder_path, file)
        df = pd.read_csv(file_path)

        # Process dates and filter by selected year range
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        df = df.loc[f'{selected_year[0]}-01-01':f'{selected_year[1]}-12-31']

        # Add filename (without extension) and calculate daily returns
        df['File'] = os.path.splitext(file)[0]
        df['daily_return'] = df['Close'].pct_change() * 100

        data = pd.concat([data, df])

    return data

def calculate_monthly_stats(data):
    """Calculate monthly statistics (returns, volatility, volume)"""
    monthly_stats = data.groupby(['File', pd.Grouper(freq='ME')]).agg({
        'daily_return': ['mean', 'std'],
        'Volume': 'mean'
    })
    monthly_stats.columns = ['monthly_mean', 'monthly_volatility', 'monthly_volume']
    return monthly_stats.reset_index()

def get_file_description(selected_file, symbols_meta_df):
    """Get security description from metadata"""
    file_name = os.path.splitext(selected_file)[0]
    description_row = symbols_meta_df[symbols_meta_df['NASDAQ Symbol'] == file_name]
    return description_row['Security Name'].values[0] if not description_row.empty else "Description not available"

def get_available_years(data_folder):
    """Determine the available date range across all data files"""
    min_year = 2100
    max_year = 1900

    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if file.endswith('.csv'):
                try:
                    df = pd.read_csv(os.path.join(root, file))
                    df['Date'] = pd.to_datetime(df['Date'])
                    year_min = df['Date'].min().year
                    year_max = df['Date'].max().year
                    min_year = min(min_year, year_min)
                    max_year = max(max_year, year_max)
                except:
                    continue

    return (max(min_year, 1990), min(max_year, datetime.now().year))  # Apply reasonable limits

# Dashboard configuration
st.set_page_config(page_title="Financial Dashboard", layout="wide")
st.title("📊 Explore the Financial Markets")
st.markdown("""
This interactive dashboard provides comprehensive visual analysis of financial market data, enabling users to explore and compare key performance metrics across multiple securities.
""")

# File paths configuration
data_folder = "C:\\Users\\stebr\\Financial Market\\data"
symbols_meta_path = os.path.join(data_folder, "symbols_valid_meta.csv")

# Load metadata
try:
    symbols_meta_df = pd.read_csv(symbols_meta_path)
except Exception as e:
    st.error(f"Error loading metadata: {str(e)}")
    st.stop()

# Determine available time range
min_year, max_year = get_available_years(data_folder)

# Sidebar interface
with st.sidebar:
    st.header("Settings")

    # Folder selection
    subfolders = [f.name for f in os.scandir(data_folder) if f.is_dir()]
    selected_folder = st.radio("Select financial instrument", subfolders)

    # File selection (hide .csv extension in UI)
    selected_folder_path = os.path.join(data_folder, selected_folder)
    files = [f.name for f in os.scandir(selected_folder_path) if f.is_file() and f.name.endswith('.csv')]
    display_names = [os.path.splitext(f)[0] for f in files]
    selected_indices = st.multiselect("Select asset/s", display_names)
    selected_files = [f"{name}.csv" for name in selected_indices]  # Add extension back for processing

    # Year range selection
    selected_year = st.slider("Time period", min_year, max_year, (max(min_year, max_year - 5), max_year))

    # Analysis type selection
    chart_type = st.selectbox("Analysis type", [
        "Returns",
        "Returns and Volatility",
        "Volume",
        "Volatility",
        "Return and Volume"
    ])

# Main dashboard content
if selected_files:
    try:
        # Load and process data
        data = load_data(selected_files, selected_folder_path, selected_year)
        monthly_data = calculate_monthly_stats(data)

        # Display asset descriptions
        st.subheader("Asset Descriptions")
        for file in selected_files:
            desc = get_file_description(file, symbols_meta_df)
            st.write(f"**{os.path.splitext(file)[0]}**: {desc}")

        # Visualization section
        st.subheader(f"{chart_type} Analysis")

        # Configuration for different chart types
        chart_configs = {
            "Returns": {
                "plot": px.line,
                "x": "Date",
                "y": "monthly_mean",
                "labels": {"monthly_mean": "Monthly Return (%)"}
            },
            "Returns and Volatility": {
                "plot": px.scatter,
                "x": "monthly_mean",
                "y": "monthly_volatility",
                "size": "monthly_volume",
                "labels": {
                    "monthly_mean": "Monthly Return (%)",
                    "monthly_volatility": "Volatility (%)"
                }
            },
            "Volatility": {
                "plot": px.area,
                "x": "Date",
                "y": "monthly_volatility",
                "labels": {"monthly_volatility": "Volatility (%)"}
            },
            "Volume": {
                "plot": px.bar,
                "x": "Date",
                "y": "monthly_volume",
                "labels": {"monthly_volume": "Monthly Volume"}
            },
            "Return and Volume": {
                "plot": px.scatter,
                "x": "monthly_volume",
                "y": "monthly_mean",
                "labels": {
                    "monthly_volume": "Volume",
                    "monthly_mean": "Return (%)"
                }
            }
        }

        # Create and display the selected chart
        config = chart_configs[chart_type]
        fig = config["plot"](
            monthly_data,
            x=config["x"],
            y=config["y"],
            color="File",
            **{k: v for k, v in config.items() if k not in ["plot", "x", "y"]}
        )

        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Analysis explanations
        explanations = {
            "Returns": """
            **Average Return**: The mean of observed returns over a specific period.  
            - Useful for assessing potential profitability
            - Higher values indicate better historical performance
            """,
            "Returns and Volatility": """
            **Returns vs Volatility**: Shows the relationship between risk and return.
            - Typically, higher returns are associated with higher volatility
            - Look for assets that offer higher returns with lower volatility (top-left quadrant)
            """,
            "Volatility": """
            **Volatility**: Measures how much the returns vary over time.
            - Higher volatility means higher risk
            - Useful for assessing the stability of returns
            """,
            "Volume": """
            **Trading Volume**: The number of shares traded during a period.
            - High volume confirms price trends
            - Sudden volume spikes may indicate upcoming price movements
            """,
            "Return and Volume": """
            **Return vs Volume**: Examines how trading activity relates to returns.
            - High volume with positive returns suggests strong buyer interest
            - High volume with negative returns suggests strong selling pressure
            """
        }

        st.subheader("Analysis Explanation")
        st.write(explanations[chart_type])

    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
else:
    st.warning("Please select at least one asset to analyze")