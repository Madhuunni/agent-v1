from __future__ import annotations
from app.graph.builder import build_graph
from app.graph.state import initial_state

if __name__ == '__main__':
    prompt = 'Generate Selenium test plan for login page at http://localhost:4200 and verify dashboard after login.'
    result = build_graph().invoke(initial_state(prompt))
    print(result.get('final_report'))
