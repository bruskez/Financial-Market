import os
import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def process_file(self, file_path):
        try:
            df = pd.read_csv(file_path)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Gestione eventuali errori di formato
            return df
        except Exception as e:
            print(f"Errore durante la lettura del file {file_path}: {e}")
            return None

    def save_to_csv(self, df, file_path):
        try:
            df.to_csv(file_path, index=False)
        except Exception as e:
            print(f"Errore durante il salvataggio del file {file_path}: {e}")

    def calculate_monthly_stats(self, df):
        df['daily_return'] = df['Adj Close'].pct_change() * 100
        df['Period'] = df['Date'].dt.to_period('M')

        grouped = df.groupby('Period')
        df['monthly_mean'] = grouped['daily_return'].transform('mean')
        df['volatility'] = grouped['daily_return'].transform(lambda x: np.std(x))
        df['Vol_month_mean'] = grouped['Volume'].transform('mean')

        df.drop(columns='Period', inplace=True)
        return df

    def process_data(self):
        for filename in os.listdir(self.folder_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(self.folder_path, filename)
                df = self.process_file(file_path)
                if df is not None:
                    df = self.calculate_monthly_stats(df)
                    self.save_to_csv(df, file_path)
                    print(f"✅ File elaborato: {filename}")
                else:
                    print(f"❌ Errore durante l'elaborazione di {filename}")

if __name__ == "__main__":
    folder_path_etf = 'C:\\Users\\stebr\\Financial Market\\data\\etfs'
    folder_path_stock = 'C:\\Users\\stebr\\Financial Market\\data\\stocks'

    processor = DataProcessor(folder_path_etf)
    processor.process_data()

    processor = DataProcessor(folder_path_stock)
    processor.process_data()
