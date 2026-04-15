# StatefulMeetingDemo

Internal FastMCP application for the `agentcore-stateful-mcp-meeting-scheduler` sample.

This app exposes a single stateful MCP workflow that demonstrates:

- elicitation for missing structured inputs
- progress updates during execution
- sampling for invite generation

## Run locally

```bash
python main.py
```

The server starts on port `8000` using Streamable HTTP with `stateless_http=False`.

## Main entrypoint

- `main.py` contains the complete meeting scheduler server implementation

For full setup, deployment, and testing instructions, use the repository root `README.md`.
