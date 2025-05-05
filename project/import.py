# Configuration parameters
offset = 0  # Starting index for symbol download
limit = 30  # Exact number of valid files we want to obtain
period = '10y'  # Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max

import pandas as pd
import yfinance as yf
import os
import shutil
from pathlib import Path

# Create necessary directories
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)  # Create main data directory if it doesn't exist
(data_dir / 'etfs').mkdir(exist_ok=True)  # ETF subdirectory
(data_dir / 'stocks').mkdir(exist_ok=True)  # Stocks subdirectory


# Download and filter symbols
def get_valid_symbols():
    # Download NASDAQ traded symbols list
    url = "http://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
    data = pd.read_csv(url, sep='|')
    data_clean = data[data['Test Issue'] == 'N']  # Filter out test issues
    data_clean.to_csv(data_dir / 'symbols_valid_meta.csv', index=False)  # Save filtered list
    return data_clean


data_clean = get_valid_symbols()
symbols = data_clean['NASDAQ Symbol'].tolist()  # Convert symbols to list
print(f'Total number of symbols traded = {len(symbols)}')  # Print total count


# Download historical data until we reach the limit of valid files
def download_history(symbols, offset=0, limit=None, period='10y'):
    if limit is None:
        limit = len(symbols)  # Default to all symbols if no limit specified

    valid_symbols = []  # Store successfully downloaded symbols
    i = offset  # Start from offset index

    # Loop until we reach our limit or end of symbols list
    while len(valid_symbols) < limit and i < len(symbols):
        s = symbols[i]
        try:
            # Attempt to download historical data
            data = yf.download(s, period=period, progress=False)
            if not data.empty:  # Only save if we got valid data
                data.to_csv(data_dir / f'{s}.csv')
                valid_symbols.append(s)
                print(f'Downloaded {s} ({len(valid_symbols)}/{limit})')  # Progress tracking
        except Exception as e:
            print(f'Error downloading {s}: {str(e)}')  # Error handling
        i += 1  # Move to next symbol

    print(f'Total number of valid symbols downloaded = {len(valid_symbols)}')
    return valid_symbols


valid_symbols = download_history(symbols, offset, limit, period)  # Execute download


# Organize downloaded files into appropriate folders
def organize_files(valid_data):
    # Separate ETFs and stocks from the valid data
    etfs = valid_data[valid_data['ETF'] == 'Y']['NASDAQ Symbol'].tolist()
    stocks = valid_data[valid_data['ETF'] == 'N']['NASDAQ Symbol'].tolist()

    # Move ETF files to etfs subdirectory
    for s in etfs:
        src = data_dir / f'{s}.csv'
        if src.exists():
            shutil.move(src, data_dir / 'etfs' / f'{s}.csv')

    # Move stock files to stocks subdirectory
    for s in stocks:
        src = data_dir / f'{s}.csv'
        if src.exists():
            shutil.move(src, data_dir / 'stocks' / f'{s}.csv')


# Filter the clean data to only include symbols we successfully downloaded
valid_data = data_clean[data_clean['NASDAQ Symbol'].isin(valid_symbols)]
organize_files(valid_data)  # Execute file organization