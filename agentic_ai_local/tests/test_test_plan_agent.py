from app.agents import test_plan_agent


def test_test_plan_fallback_filters_blank_locator_candidates():
    plan = test_plan_agent._fallback(
        {
            "name": "Login",
            "base_url": "http://localhost:4200/",
            "steps": [
                {"step_number": 1, "action": "navigate", "target_description": "app", "value": "http://localhost:4200/"},
                {"step_number": 2, "action": "type", "target_description": "email field", "value": "user@example.com"},
            ],
        },
        {
            "locators": [
                {
                    "step_number": 2,
                    "target_description": "email field",
                    "selected_by": "css",
                    "selected_locator": "input[formcontrolname='email']",
                    "confidence": 0.9,
                    "reason": "matched formcontrolname",
                    "fallback_locators": [
                        {"by": "css", "target": ""},
                        {"by": "xpath", "target": "//input[@formcontrolname='email']"},
                    ],
                }
            ]
        },
    )

    step = plan.steps[1]
    assert step.target == "input[formcontrolname='email']"
    assert [item.model_dump() for item in step.locator_candidates] == [
        {"by": "xpath", "target": "//input[@formcontrolname='email']"}
    ]
