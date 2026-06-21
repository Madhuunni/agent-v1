# Agentic AI Local

A local-first dynamic multi-agent framework for Selenium automation using Python, LangGraph, LangChain abstractions, Ollama/local LLM runtime, Pydantic v2, and Selenium. It never requires OpenAI, Anthropic, Gemini, Groq, or other cloud LLM APIs.

## Architecture

```text
User Prompt
  -> Observer Agent
  -> Planner Agent
  -> Plan Validator
  -> Router over pending_agents
  -> Dynamic Agent Execution
  -> Optional Debug / Retry
  -> Report Agent
```

## Observer phase
The observer detects the user goal, task type, URL, whether DOM inspection/code generation/execution/debugging are needed, existing generated files, run logs, and local memory.

## Planner phase
The planner emits strict structured plan data with a dynamic `agent_sequence`. The planner does not execute tools. Deterministic validation then checks allowed agents, dependencies, retry limits, and iteration limits.

## Dynamic agent sequence
The LangGraph graph is fixed, but the router reads `pending_agents`, pops the next agent, sets `current_agent`, and routes dynamically. This makes the execution path prompt-dependent rather than a hardcoded chain.

## Install

```bash
cd agentic_ai_local
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Install and start Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull qwen2.5-coder:7b
```

Configure `.env` with `OLLAMA_BASE_URL`, `LOCAL_LLM_MODEL`, `APP_USERNAME`, `APP_PASSWORD`, and `HEADLESS`.

## Run CLI

```bash
python -m app.cli run "Generate and run Selenium login test for http://localhost:4200" --max-retries 2 --headless true --verbose
```

## Example prompts
1. `Inspect page at http://localhost:4200 and list available buttons.`
2. `Generate Selenium test plan for login at http://localhost:4200.`
3. `Generate and run Selenium login test for http://localhost:4200.`
4. `Run the existing generated login test and fix it if it fails.`

## Example execution flow
A generate-and-run prompt typically plans:
`requirement_agent -> dom_agent -> locator_agent -> test_plan_agent -> code_generator_agent -> code_validator_agent -> executor_agent -> report_agent`.

## Add a new agent
1. Add a Pydantic schema if needed.
2. Create `app/agents/my_agent.py` with `run(state) -> dict`.
3. Add the agent name to `ALLOWED_AGENTS`.
4. Register it in `app/graph/nodes.py`.
5. Add validation dependency rules if needed.

## Add a new tool
Create a small deterministic module in `app/tools/`, keep execution separate from planning, and call it only from an agent.

## Safety limitations
The executor only runs files under `generated_tests/`. Safety checks reject destructive commands, hardcoded secrets, and cloud LLM provider references. Browser network access should be limited to the local app under test and localhost Ollama.

## Troubleshooting
- Ollama unavailable: run `ollama serve` and pull the configured model.
- Browser errors: install Chrome/Chromium and ensure webdriver-manager can download a compatible driver.
- Missing URL: include an `http://` or `https://` URL in Selenium/DOM prompts.
- Credentials: set `APP_USERNAME` and `APP_PASSWORD` in `.env`.
