"""
AI Agent that generates custom bank statement parsers
"""
import os
import sys
import argparse
import pandas as pd
import importlib.util
from pathlib import Path
from typing import Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Choose your LLM provider (uncomment one)
# Option 1: Anthropic Claude
# from anthropic import Anthropic
# client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Option 2: Google Gemini
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')


def call_llm(prompt: str) -> str:
    """Call LLM and return generated text"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"LLM Error: {e}")
        sys.exit(1)


def peek_pdf_structure(pdf_path: str) -> str:
    """Quick analysis of PDF structure"""
    import pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text_sample = page.extract_text()[:500]
            tables = page.extract_tables()
            structure = (
                f"PDF has {len(pdf.pages)} page(s)\n"
                f"First page text sample:\n{text_sample}\n"
                f"Number of tables detected: {len(tables)}\n"
            )
            if tables:
                structure += f"First table has {len(tables[0])} rows"
            return structure
    except Exception as e:
        return f"Could not analyze PDF: {e}"


def build_prompt(pdf_path: str, csv_path: str, 
                 previous_code: Optional[str] = None,
                 error_msg: Optional[str] = None,
                 attempt: int = 1) -> str:
    """Build prompt for LLM to generate parser"""
    
    # Read expected output
    expected_df = pd.read_csv(csv_path)
    pdf_structure = peek_pdf_structure(pdf_path)
    
    prompt = f"""You are a Python coding expert. Write a complete Python parser function.

TASK: Create a function `parse(pdf_path)` that extracts bank statement data from PDF.

PDF STRUCTURE:
{pdf_structure}

IMPORTANT: This PDF has MULTIPLE PAGES with DUPLICATE HEADERS on each page. 
You MUST skip the header row on each page individually to avoid duplicate headers in your final data.

REQUIRED OUTPUT SCHEMA:
Columns: {expected_df.columns.tolist()}
Data types: {expected_df.dtypes.to_dict()}
Expected rows: {len(expected_df)} (EXACTLY this many rows, no more, no less)

SAMPLE EXPECTED OUTPUT (first 3 rows):
{expected_df.head(3).to_string()}

REQUIREMENTS:
1. Function signature: def parse(pdf_path: str) -> pd.DataFrame
2. Use pdfplumber library to extract tables
3. Return pandas DataFrame matching the schema EXACTLY
4. Column names must match exactly: {expected_df.columns.tolist()}
5. Handle data type conversions (dates, numbers)
6. Clean the data (remove nulls, strip whitespace)
7. Include proper imports at the top
8. CRITICAL: Process each page separately and skip headers on each page to avoid duplicates

RECOMMENDED APPROACH:
```python
for page in pdf.pages:
    table = page.extract_table()
    if table:
        for row in table[1:]:  # Skip header on each page
            all_data.append(row)
```

CODE TEMPLATE:
```python
import pandas as pd
import pdfplumber
from typing import Any

def parse(pdf_path: str) -> pd.DataFrame:
    '''Parse bank statement PDF and return DataFrame'''
    # Your code here
    pass
```
"""

    # Add error correction context
    if previous_code and error_msg:
        prompt += f"""

❌ PREVIOUS ATTEMPT {attempt-1} FAILED WITH ERROR:
{error_msg}

PREVIOUS CODE THAT FAILED:
```python
{previous_code}
```

INSTRUCTIONS FOR FIX:
- Analyze the error above carefully
- If you get "Shape mismatch" with more rows than expected, you're likely including duplicate headers from multiple PDF pages
- Process each page individually: for page in pdf.pages: ... for row in table[1:]: ...
- If you get "DataFrames not exactly equal" check for NaN vs 0.0 issues - use float('nan') for empty values, not 0.0
- Make sure column names match EXACTLY
- Ensure data types are correct
- The PDF has multiple pages with headers on each page - skip them all
- Test your logic mentally before responding

NOW WRITE THE CORRECTED CODE:
"""
    
    prompt += """

CRITICAL: Return ONLY the Python code, nothing else. No explanations, no markdown.
Start directly with 'import' statements.
"""
    
    return prompt


def save_parser(code: str, bank: str) -> str:
    """Save generated parser code to file"""
    parser_dir = Path("custom_parser")
    parser_dir.mkdir(exist_ok=True)
    parser_path = parser_dir / f"{bank}_parser.py"
    with open(parser_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print("-"*40)
    print(f"[INFO] Parser saved to: {parser_path}")
    print("-"*40)
    return str(parser_path)


    # ...existing code...
def import_parser(parser_path: str):
    spec = importlib.util.spec_from_file_location("custom_parser", parser_path)
    parser_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser_module)
    return parser_module

def test_parser(parser_path: str, pdf_path: str, expected_df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """Test if generated parser produces correct output"""
    try:
        parser_module = import_parser(parser_path)
        print("-"*40)
        print(f"[TEST] Running parse function for: {pdf_path}")
        actual_df = parser_module.parse(pdf_path)
        if not isinstance(actual_df, pd.DataFrame):
            return False, f"parse() returned {type(actual_df)}, expected DataFrame"
        if list(actual_df.columns) != list(expected_df.columns):
            return False, f"Column mismatch!\nExpected: {list(expected_df.columns)}\nGot: {list(actual_df.columns)}"
        if actual_df.shape != expected_df.shape:
            return False, f"Shape mismatch!\nExpected: {expected_df.shape} (rows, cols)\nGot: {actual_df.shape}"
        if expected_df.equals(actual_df):
            print("Perfect match!")
            return True, None
        error_details = (
            f"DataFrames not exactly equal. Differences found:\n"
            f"Expected first row:\n{expected_df.iloc[0].to_dict()}\n"
            f"Actual first row:\n{actual_df.iloc[0].to_dict()}\n"
            f"Expected dtypes:\n{expected_df.dtypes.to_dict()}\n"
            f"Actual dtypes:\n{actual_df.dtypes.to_dict()}\n"
        )
        return False, error_details
    except Exception as e:
        import traceback
        error_msg = (
            f"Code execution error: {type(e).__name__}\n{str(e)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )
        return False, error_msg


def agent_loop(bank: str, max_attempts: int = 3) -> bool:
    """
    Main agent loop: generate -> test -> self-correct
    """
    pdf_path = f"data/{bank}/{bank}_sample.pdf"
    csv_path = f"data/{bank}/{bank}_sample.csv"
    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        return False
    if not Path(csv_path).exists():
        print(f"CSV not found: {csv_path}")
        return False
    print("="*60)
    print(f"[AGENT] Starting agent for bank: {bank.upper()}")
    print(f"[DATA] PDF: {pdf_path}")
    print(f"[DATA] CSV: {csv_path}")
    expected_df = pd.read_csv(csv_path)
    print(f"[DATA] Expected output: {expected_df.shape[0]} rows, {expected_df.shape[1]} columns")
    print("="*60)
    previous_code = None
    error_msg = None
    for attempt in range(1, max_attempts + 1):
        print("-"*60)
        print(f"[AGENT] ATTEMPT {attempt}/{max_attempts}")
        print("-"*60)
        prompt = build_prompt(
            pdf_path=pdf_path,
            csv_path=csv_path,
            previous_code=previous_code,
            error_msg=error_msg,
            attempt=attempt
        )
        print(f"[LLM] Generating parser code...")
        generated_code = call_llm(prompt)
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0]
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0]
        generated_code = generated_code.strip()
        print(f"[LLM] Generated {len(generated_code)} characters of code")
        parser_path = save_parser(generated_code, bank)
        print(f"[TEST] Testing generated parser...")
        success, error_msg = test_parser(parser_path, pdf_path, expected_df)
        if success:
            print("="*60)
            print(f"[RESULT] SUCCESS on attempt {attempt}!")
            print(f"[RESULT] Parser saved to: {parser_path}")
            print("="*60)
            return True
        else:
            print("-"*40)
            print(f"[RESULT] Attempt {attempt} failed:")
            print(error_msg)
            previous_code = generated_code
            if attempt < max_attempts:
                print(f"[AGENT] Will retry with error feedback...")
    print("="*60)
    print(f"[RESULT] Failed after {max_attempts} attempts")
    print("="*60)
    return False


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="AI Agent that generates bank statement parsers")
    parser.add_argument("--target", type=str, required=True, help="Bank name (e.g., icici, sbi)")
    parser.add_argument("--max-attempts", type=int, default=3, help="Maximum correction attempts (default: 3)")
    args = parser.parse_args()
    success = agent_loop(args.target, args.max_attempts)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()