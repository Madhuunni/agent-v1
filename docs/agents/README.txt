Agent documentation index
=========================

This directory explains the local multi-agent Selenium automation framework one agent at a time.

Files:
- observer.txt: Converts the raw user prompt and local context into structured facts.
- planner.txt: Chooses and validates the ordered agent sequence.
- requirement.txt: Converts the task into ordered Selenium requirements.
- dom.txt: Reads the browser DOM for the target URL.
- locator.txt: Maps requirement steps to concrete Selenium locators.
- test_plan.txt: Converts requirements and locators into executable test steps.
- code_generator.txt: Renders a Selenium Python script from the test plan.
- code_validator.txt: Checks generated Python syntax/safety before execution.
- executor.txt: Runs the generated Selenium script and records logs/screenshots.
- debug.txt: Classifies execution failures and recommends retry strategy.
- report.txt: Builds the final Markdown report.
- fine_tuning.txt: Explains how to modify prompts, schemas, fallbacks, and code for fine tuning.

How the whole system runs
-------------------------
The graph always starts with observer_agent, then planner_agent, then a router. The planner fills pending_agents with the dynamic sequence. The router pops one pending agent at a time into current_agent. Each specialist returns a partial state update, and the graph routes back through the router until report_agent sets stop=true.

Shared input/output convention
------------------------------
Every agent exposes a run(state: dict) -> dict function. The input is the shared LangGraph state, and the output is a partial dictionary merged into that state. Most LLM-backed agents call invoke_json(schema, system_prompt, payload, fallback), so their intended output is controlled by a Pydantic schema and a deterministic fallback.
