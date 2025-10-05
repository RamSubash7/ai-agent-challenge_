import pandas as pd
import pdfplumber
from typing import Any
import numpy as np

def parse(pdf_path: str) -> pd.DataFrame:
    """Parse bank statement PDF and return DataFrame"""
    all_data: list[Any] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table[1:]:  # Skip header on each page
                    all_data.append(row)

    df = pd.DataFrame(all_data, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])

    # Data cleaning and type conversion
    df['Debit Amt'] = pd.to_numeric(df['Debit Amt'], errors='coerce')
    df['Credit Amt'] = pd.to_numeric(df['Credit Amt'], errors='coerce')
    df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce')
    # Explicitly fill NaNs with np.nan for consistency
    df = df.fillna({'Debit Amt': np.nan, 'Credit Amt': np.nan, 'Balance': np.nan})
    df = df[df['Date'].notna()]
    df = df.dropna(how='all')
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df = df.reset_index(drop=True)

    # Ensure the DataFrame has exactly 100 rows
    if len(df) > 100:
        df = df.iloc[:100]
    elif len(df) < 100:
        # Pad with empty rows if needed to reach 100
        num_missing = 100 - len(df)
        empty_data = [['', '', np.nan, np.nan, np.nan]] * num_missing
        empty_df = pd.DataFrame(empty_data, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
        df = pd.concat([df, empty_df], ignore_index=True)

    return df