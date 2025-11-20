# MCP Chat Application

A production-ready Streamlit and CLI-based chat interface that leverages the Model Context Protocol (MCP) to connect Google's Gemini LLM with various tools and servers.

## Features

- **Interactive Chat**: Clean Streamlit-based web interface and CLI option
- **Multi-Server Support**: Connects to multiple MCP servers simultaneously
  - **Expense Server**: Remote expense tracking server
  - **Manim Server**: Local Manim server for generating math animations
  - **Math Server**: Local math operations server (`server.py`)
- **Configuration-Driven**: YAML-based configuration with environment variable support
- **Comprehensive Logging**: Structured logging to files and console
- **Error Handling**: Robust error handling throughout the application
- **Tested**: Unit tests for all math operations
- **Gemini Integration**: Uses `langchain-google-genai` for conversational AI

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (optional, for running math server via fastmcp)
- A Google Gemini API Key

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory.

2. **Install Dependencies**:
   ```bash
   pip install streamlit langchain-google-genai langchain-mcp-adapters python-dotenv pyyaml fastmcp pytest
   ```

3. **Environment Setup**:
   Copy the example environment file and fill in your values:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
   
   Optionally, override default paths:
   ```env
   UV_PATH=/path/to/uv
   PYTHON_PATH=/path/to/python3
   MANIM_EXECUTABLE=/path/to/manim
   MATH_SERVER_PATH=/path/to/server.py
   MANIM_SERVER_PATH=/path/to/manim_server.py
   ```

4. **Configuration**:
   The `config.yaml` file defines server connections and application settings. You can:
   - Enable/disable servers by setting `enabled: true/false`
   - Modify server transport types and commands
   - Adjust LLM settings (model, temperature)
   - Configure logging levels

## Usage

### Running the Streamlit Chat Application

```bash
streamlit run app.py
```

The application will open in your default web browser. You can chat with the agent, which will use connected MCP tools to answer queries.

### Running the CLI Application

```bash
python client1.py
```

Or use it programmatically:
```python
from client1 import main
import asyncio

result = asyncio.run(main("What is 25 + 17?"))
print(result)
```

### Running the Local Math Server

To run the math server standalone (for testing):

```bash
python server.py
```

To use it within the chat app, enable it in `config.yaml`:
```yaml
servers:
  math:
    enabled: true
    # ... rest of configuration
```

## Testing

Run the test suite:

```bash
pytest test_server.py -v
```

This will test all mathematical operations provided by the server.

## Project Structure

```
mcp-server/
├── app.py              # Streamlit web interface
├── client1.py          # CLI interface
├── server.py           # Math MCP server
├── config.yaml         # Application configuration
├── config_loader.py    # Configuration loader utility
├── test_server.py      # Unit tests
├── .env                # Environment variables (not in git)
├── .env.example        # Example environment file
├── logs/               # Application logs
│   ├── mcp_chat.log
│   └── mcp_cli.log
├── README.md           # This file
├── LICENSE             # License file
└── pyproject.toml      # Python project metadata
```

## Configuration

### Server Configuration (`config.yaml`)

Servers are defined with the following structure:

```yaml
servers:
  server-name:
    enabled: true
    transport: stdio  # or streamable_http
    command: ${PYTHON_PATH:-python3}
    args:
      - /path/to/server.py
    env:
      ENV_VAR: value
```

Environment variables in the format `${VAR_NAME:-default}` are automatically expanded.

### Logging

Logs are written to:
- `logs/mcp_chat.log` (Streamlit app)
- `logs/mcp_cli.log` (CLI app)

Configure logging level in `config.yaml`:

```yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
```

## Troubleshooting

### FileNotFoundError for `uv` or `python3`

Update your `.env` file with the correct paths:
```env
UV_PATH=/Users/yourname/path/to/uv
PYTHON_PATH=/Users/yourname/path/to/python3
```

### GEMINI_API_KEY not found

Ensure your `.env` file contains:
```env
GEMINI_API_KEY=your_actual_api_key
```

### MCP Server Connection Errors

Check the logs in `logs/` directory for detailed error messages. Ensure:
- Server paths are correct in `.env`
- Servers are enabled in `config.yaml`
- Required dependencies are installed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

See LICENSE file for details.

## Author

MCP Chat Team
