# %% [markdown]
# ## IMPORT DATA

# %%
import os
import shutil
import contextlib
import pandas as pd
import yfinance as yf

# Parametri
offset = 0
limit = 3000
period = '10y'
output_dir = 'Data'

# Carica i simboli dal file ufficiale NASDAQ
data = pd.read_csv("http://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt", sep='|')
data_clean = data[data['Test Issue'] == 'N']
symbols = data_clean['NASDAQ Symbol'].tolist()
print(f'Total number of symbols traded = {len(symbols)}')

# Crea directory di output se non esiste
os.makedirs(output_dir, exist_ok=True)
data.to_csv(os.path.join(output_dir, 'symbols_valid_meta.csv'), index=False)

# Scarica dati da Yahoo Finance
%%time
limit = limit or len(symbols)
end = min(offset + limit, len(symbols))
is_valid = [False] * len(symbols)

with open(os.devnull, 'w') as devnull:
    with contextlib.redirect_stdout(devnull):
        for i in range(offset, end):
            s = symbols[i]
            df = yf.download(s, period=period)
            if df.empty:
                continue
            is_valid[i] = True
            df.to_csv(f'{output_dir}/{s}.csv')

print(f'Total number of valid symbols downloaded = {sum(is_valid)}')

# Filtra simboli validi
valid_data = data_clean[is_valid]
valid_data.to_csv('symbols_valid_meta.csv', index=False)

# Separa ETF e Azioni
etfs = valid_data[valid_data['ETF'] == 'Y']['NASDAQ Symbol'].tolist()
stocks = valid_data[valid_data['ETF'] == 'N']['NASDAQ Symbol'].tolist()

# Crea sottocartelle per ETF e Stocks
os.makedirs(f'{output_dir}/etfs', exist_ok=True)
os.makedirs(f'{output_dir}/stocks', exist_ok=True)

# Sposta file nelle rispettive directory
def move_symbols(symbols, dest):
    for s in symbols:
        src = os.path.join(output_dir, f'{s}.csv')
        dst = os.path.join(dest, f'{s}.csv')
        if os.path.isfile(src):
            shutil.move(src, dst)

move_symbols(etfs, f'{output_dir}/etfs')
move_symbols(stocks, f'{output_dir}/stocks')
