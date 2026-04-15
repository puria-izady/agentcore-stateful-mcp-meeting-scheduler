# Stateful MCP Meeting Scheduler on Amazon Bedrock AgentCore

A small, tangible example of a stateful MCP server built with FastMCP and deployed to Amazon Bedrock AgentCore.

This sample uses a meeting scheduler because it makes the three stateful MCP client capabilities immediately obvious:

- **elicitation** for missing structured input
- **progress notifications** while the workflow runs
- **sampling** to draft the final invite

## Repository layout

- `app/StatefulMeetingDemo/main.py` - FastMCP server
- `local_runtime_test.py` - local client that exercises the stateful flow
- `remote_runtime_test.py` - SigV4-signed client for a deployed AgentCore runtime
- `agentcore/agentcore.json` - AgentCore runtime config
- `agentcore/aws-targets.json` - deployment target template

## What was validated

This sample was tested in two modes:

1. locally against `http://localhost:8000/mcp`
2. remotely against a deployed AgentCore runtime in `us-east-1`

Both paths successfully exercised:

- `ctx.elicit(...)`
- `ctx.report_progress(...)`
- `ctx.sample(...)`

## Prerequisites

- Python 3.10+
- Node.js 20+
- AWS CLI configured
- Docker available
- `agentcore` CLI installed

## Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastmcp mcp pydantic boto3
```

## Run locally

Start the MCP server:

```bash
cd app/StatefulMeetingDemo
python main.py
```

In another shell, from the project root, run:

```bash
python local_runtime_test.py
```

You should see:

- five elicitation prompts answered by the client
- progress updates from 25% to 100%
- a sampling request
- a final meeting summary with a generated invite draft

## Configure AWS targets

Before deploying, replace the placeholder values in `agentcore/aws-targets.json` with your own AWS account and region.

Example:

```json
[
  {
    "name": "default",
    "description": "Personal sandbox",
    "account": "123456789012",
    "region": "us-east-1"
  }
]
```

## Deploy to AgentCore

From the project root:

```bash
agentcore validate
agentcore package
cd agentcore/cdk && npm install && cd ../..
agentcore deploy --target default --yes --verbose
```

Check the deployed runtime:

```bash
agentcore status --target default
```

## Test the deployed runtime

Export your AWS settings and the AgentCore invoke URL:

```bash
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
export AGENTCORE_RUNTIME_URL='https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/<encoded-runtime-arn>/invocations'
```

Then run:

```bash
python remote_runtime_test.py
```

This client signs requests with SigV4 using `boto3`, then exercises the same elicitation, progress, and sampling flow against the hosted runtime.

## The one switch that matters

The critical server-side change is enabling stateful HTTP mode:

```python
mcp.run(
    transport="streamable-http",
    host="0.0.0.0",
    port=8000,
    stateless_http=False,
)
```

Without that, you still have an MCP server, but not one that can carry the interaction across a session the way this demo does.

## Notes

- The hosted AgentCore endpoint requires authenticated requests. A plain unsigned HTTP client is not enough for remote testing.
- If you scaffolded the project with `--skip-install`, you need to install the CDK dependencies before deploying.
- Generated build artifacts, logs, deployment state, and local caches are intentionally ignored in `.gitignore` so the repo stays clean.
