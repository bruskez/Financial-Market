import pandas as pd
import os
import glob
from pathlib import Path

# Path to the main data folder
folder_path = 'C:\\Users\\stebr\\Financial Market\\data'

# Find all .csv files including subdirectories (recursive search)
csv_files = glob.glob(os.path.join(folder_path, '**', '*.csv'), recursive=True)

for file_path in csv_files:
    try:
        # Read CSV file while skipping the first 3 rows (no header)
        df = pd.read_csv(file_path, skiprows=3, header=None)

        # Assign standard column names to the DataFrame
        df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']

        # Convert Date column to datetime format for better time series handling
        df['Date'] = pd.to_datetime(df['Date'])

        # Save the processed DataFrame back to the same file (overwrite original)
        df.to_csv(file_path, index=False)

        print(f'File processed successfully: {file_path}')

    except Exception as e:
        print(f'Error processing file {file_path}: {e}')