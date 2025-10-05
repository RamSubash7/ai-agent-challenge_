### Bank Statement Parser Agent

An autonomous agent that generates custom PDF bank statement parsers using an LLM, validates them against ground-truth CSVs, and self-refines until tests pass.

---

### Architecture Overview

```mermaid
flowchart TD
    A[CLI: agent.py] -->|parse args, load API key| B[BankParserAgent]
    B --> C[Analyze Documents]
    C -->|pdfplumber / PyPDF2| C1[Extract PDF Text <br/> Tables]
    C -->|pandas| C2[Load CSV Ground Truth]
    C1 --> D
    C2 --> D
    D[Generate Parser Code <br/>(Gemini)] --> E[Write Parser File <br/> custom_parsers/{bank}_parser.py]
    E --> F[Run Parser Test]
    F -->|compare with CSV| G{Pass?}
    G -- Yes --> H[Finalize <br/>(Add header, report success)]
    G -- No --> I[Fix Parser Code <br/>(LLM with error context)]
    I --> E
```

---

### Key Features

- Autonomous loop: Generate → Test → Fix (configurable retries)
- Deterministic output: DataFrame matches expected CSV schema and formatting
- Uses `pdfplumber`/`PyPDF2` for PDF extraction; `pandas` for data shaping
- Writes parsers to `custom_parsers/<bank>_parser.py`
- Helpful CLI with clear error messages

---

### Repository Structure

- `agent.py`: CLI and `BankParserAgent` implementation
- `custom_parsers/`: Generated parsers (created at runtime)
- `data/`: Sample inputs
  - `icici/`
    - `icici_sample.pdf`
    - `icici_sample.csv`
- `requirements.txt`: Python dependencies
- `setup.py`: Packaging metadata

---

### Prerequisites

- Python 3.11+
- A Google Gemini API key
  - Set `GEMINI_API_KEY` or pass `--api-key` to the CLI

---

### Setup

1) Clone and enter the project
```bash
git clone <your-repo-url>
cd ai-agent-challenge-ram
```

2) Create and activate a virtual environment
- macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```
- Windows PowerShell
```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
```

3) Install dependencies
```bash
pip install -r requirements.txt
```

4) Provide API key
- Option A: Environment variable
  - macOS/Linux
    ```bash
    export GEMINI_API_KEY="<your_api_key>"
    ```
  - Windows PowerShell
    ```powershell
    setx GEMINI_API_KEY "<your_api_key>"
    $Env:GEMINI_API_KEY = "<your_api_key>"  # current session
    ```
- Option B: Pass via CLI `--api-key`

---

### Usage

- Show help
```bash
python agent.py --help
```

- Generate a parser for ICICI
```bash
python agent.py --target icici --api-key <your_api_key>
```

Expected effects
- Reads: `data/icici/icici_sample.pdf`, `data/icici/icici_sample.csv`
- Writes: `custom_parsers/icici_parser.py`

Exit codes
- `0`: Success (parser passed checks)
- `1`: Failure (missing inputs/API key or tests failed)

---

### How It Works

1) Analyze
- Extracts PDF text/tables using `pdfplumber` (preferred) with `PyPDF2` fallback
- Loads CSV ground-truth with `pandas` to establish schema and sample rows

2) Generate Parser Code
- Prompts Gemini with PDF excerpts, expected columns/dtypes, and sample rows
- Requests a `parse(pdf_path: str) -> pd.DataFrame` function
- Enforces correct columns, types, date parsing, and error handling

3) Write Parser
- Writes generated code to `custom_parsers/<bank>_parser.py`

4) Test Parser
- Runs a temporary script that imports `parse()` and compares its DataFrame output to the CSV
- Normalizes dates and indices before equality checks

5) Fix Loop
- Sends failing output and stack traces back to the LLM to refine the parser
- Retries until pass or max retries are reached

---

### Troubleshooting

- Missing API key
  - Message: "Please provide Gemini API key via --api-key or GEMINI_API_KEY env var"
  - Fix: Set env var or pass `--api-key`

- Missing sample files
  - Messages like: `PDF not found: data/<bank>/<bank>_sample.pdf` or `CSV not found: ...`
  - Fix: Provide files in `data/<bank>/` with expected names

- Optional dependencies at import time
  - `agent.py` defers heavy imports so `--help` works without full setup
  - For actual generation, ensure: `google-generativeai`, `langgraph`, `pdfplumber`, `PyPDF2`, `python-dotenv`

- Windows path issues
  - Run from the project root
  - Activate venv using PowerShell: `./venv/Scripts/Activate.ps1`

---

### Extending to a New Bank

1) Add sample files
- `data/<bank>/<bank>_sample.pdf`
- `data/<bank>/<bank>_sample.csv`

2) Run the agent
```bash
python agent.py --target <bank>
```

3) Inspect generated parser
- `custom_parsers/<bank>_parser.py`

4) Validate manually or with tests by comparing the DataFrame to your CSV

---

### Security & Privacy

- Only processes sample data provided by you
- Review generated code before production use
- Consider redacting sensitive data from PDFs

---

### License

MIT License

---

### Acknowledgements

- `pdfplumber`, `PyPDF2` for PDF extraction
- Google Gemini for code generation
- `pandas` for data processing
