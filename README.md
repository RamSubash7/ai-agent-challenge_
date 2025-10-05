# AI Agent Challenge

Welcome to the AI Agent Challenge repository! This project is designed to showcase and develop intelligent agent solutions.

## Features

- Modular agent architecture
- Extensible design for custom tasks
- Example agents and environments

## How to Run (5 Steps)

1. **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/ai-agent-challenge-ram.git
    cd ai-agent-challenge-ram
    ```

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Activate your Python environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4. **Run the agent to generate a parser**
    ```bash
    python agent.py --target icici
    ```

5. **Run tests to validate the parser**
    ```bash
    pytest test_parser.py -v
    ```

---

## Agent Diagram

The agent operates in a self-correcting loop: it plans the parser logic, generates code using an LLM, runs tests to validate the output, and refines its approach up to three times if errors are detected. This autonomous cycle ensures the generated parser matches the expected CSV schema and passes all tests, requiring no manual tweaks for new bank statements.

## Folder Structure

- `agents/` - Agent implementations
- `environments/` - Simulation environments
- `main.py` - Entry point

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

This project is licensed under the MIT License.