import os
import shutil
import contextlib
import pandas as pd
import yfinance as yf
from os.path import join

# --- CONFIGURATION ---
offset = 0                  # Start index for downloading symbols
limit = 3000                # Max number of symbols to download (None for all)
period = '10y'              # Historical data period
base_folder = 'Data'        # Base folder to store data

# --- LOAD SYMBOL LIST FROM NASDAQ ---
nasdaq_url = "http://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
data = pd.read_csv(nasdaq_url, sep='|')

# Filter out test issues
data_clean = data[data['Test Issue'] == 'N']
symbols = data_clean['NASDAQ Symbol'].tolist()
print(f'Total number of tradable symbols = {len(symbols)}')

# --- DOWNLOAD HISTORICAL DATA FOR EACH SYMBOL ---
valid_flags = [False] * len(symbols)  # Track which symbols downloaded successfully

# Define download range
end = min(offset + (limit or len(symbols)), len(symbols))

# Suppress verbose yfinance output
with open(os.devnull, 'w') as devnull:
    with contextlib.redirect_stdout(devnull):
        for i in range(offset, end):
            symbol = symbols[i]
            df = yf.download(symbol, period=period)
            if df.empty:
                continue
            valid_flags[i] = True
            df.to_csv(join(base_folder, f'{symbol}.csv'))

print(f'Total number of valid symbols downloaded = {sum(valid_flags)}')

# --- SAVE METADATA OF VALID SYMBOLS ---
valid_data = data_clean[valid_flags]
valid_data.to_csv(join(base_folder, 'symbols_valid_meta.csv'), index=False)

# --- CLASSIFY SYMBOLS AS ETFs OR STOCKS ---
etf_symbols = valid_data[valid_data['ETF'] == 'Y']['NASDAQ Symbol'].tolist()
stock_symbols = valid_data[valid_data['ETF'] == 'N']['NASDAQ Symbol'].tolist()

# --- MOVE FILES TO SUBFOLDERS ---
def move_symbols(symbols, destination):
    os.makedirs(destination, exist_ok=True)  # Ensure destination folder exists
    for symbol in symbols:
        filename = f'{symbol}.csv'
        src_path = join(base_folder, filename)
        dst_path = join(destination, filename)
        if os.path.exists(src_path):  # Ensure file exists before moving
            shutil.move(src_path, dst_path)

move_symbols(etf_symbols, join(base_folder, 'etfs'))
move_symbols(stock_symbols, join(base_folder, 'stocks'))
