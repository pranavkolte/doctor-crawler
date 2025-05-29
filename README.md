# doctor-crawler

## Setup and Run

### Using Virtual Environment
1. Create a virtual environment:
    ```bash
    python -m venv .venv
    ```
    Or use `uv`:
    ```bash
    uv sync
    ```

2. If using manual environment setup, install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application
1. Start Docker containers:
    ```bash
    docker compose up -d
    ```

2. Run the crawler:
    ```bash
    python main.py
    ```