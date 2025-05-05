import os
import pandas as pd
import numpy as np


class FinancialDataProcessor:
    def __init__(self, folder_path):
        """Initialize the financial data processor with the folder path containing CSV files"""
        self.folder_path = folder_path

    def process_all_files(self):
        """Process all CSV files in the specified folder"""
        for filename in os.listdir(self.folder_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(self.folder_path, filename)
                try:
                    # Process each file and save the results
                    df = self._process_single_file(file_path)
                    self._save_file(df, file_path)
                    print(f"Successfully processed file: {filename}")
                except Exception as e:
                    print(f"Error processing file {filename}: {str(e)}")

    def _process_single_file(self, file_path):
        """Process a single CSV file and calculate financial metrics"""
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Convert Date column to datetime and calculate daily returns
        df['Date'] = pd.to_datetime(df['Date'])
        df['daily_return'] = df['Close'].pct_change() * 100  # Percentage daily returns

        # Group by month for monthly calculations
        monthly = df.groupby(df['Date'].dt.to_period("M"))

        # Calculate monthly metrics:
        # 1. Mean return for each month
        df['monthly_mean_return'] = monthly['daily_return'].transform('mean')

        # 2. Monthly volatility (standard deviation of returns)
        df['monthly_volatility'] = monthly['daily_return'].transform('std')

        # 3. Average trading volume for each month
        df['monthly_avg_volume'] = monthly['Volume'].transform('mean')

        return df

    def _save_file(self, df, file_path):
        """Save the processed DataFrame back to CSV"""
        df.to_csv(file_path, index=False)


if __name__ == "__main__":
    # Process both ETFs and Stocks folders
    etf_processor = FinancialDataProcessor('data/etfs')
    etf_processor.process_all_files()

    stock_processor = FinancialDataProcessor('data/stocks')
    stock_processor.process_all_files()