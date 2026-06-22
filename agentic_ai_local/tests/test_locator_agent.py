from app.agents import locator_agent


def test_locator_fallback_matches_email_field_by_formcontrolname():
    result = locator_agent._fallback(
        {
            "steps": [
                {
                    "step_number": 2,
                    "action": "type",
                    "target_description": "email field",
                }
            ]
        },
        {
            "inputs": [
                {
                    "tag": "input",
                    "id": "mat-input-0",
                    "form_control_name": "email",
                    "css_selector": "#mat-input-0",
                    "xpath": "//*[@id='mat-input-0']",
                }
            ],
            "buttons": [],
        },
    )

    assert result.missing_targets == []
    assert result.locators[0].selected_by == "id"
    assert result.locators[0].selected_locator == "mat-input-0"


def test_locator_fallback_uses_control_inventory_for_prompt_mapping():
    result = locator_agent._fallback(
        {
            "steps": [
                {
                    "step_number": 3,
                    "action": "click",
                    "target_description": "sign in button",
                }
            ]
        },
        {
            "controls": [
                {
                    "tag": "button",
                    "role": "button",
                    "accessible_name": "Sign in",
                    "text": "Sign in",
                    "css_selector": "button[data-testid='signin']",
                    "xpath": "//button[normalize-space()='Sign in']",
                    "keywords": ["sign", "in"],
                }
            ]
        },
    )

    assert result.missing_targets == []
    assert result.locators[0].selected_by == "css"
    assert result.locators[0].selected_locator == "button[data-testid='signin']"
    assert "control inventory" in result.locators[0].reason


def test_locator_fallback_preserves_ordered_candidate_selectors():
    result = locator_agent._fallback(
        {
            "steps": [
                {
                    "step_number": 1,
                    "action": "type",
                    "target_description": "username field",
                }
            ]
        },
        {
            "controls": [
                {
                    "tag": "input",
                    "role": "textbox",
                    "name": "username",
                    "css_selector": "input[name='username']",
                    "xpath": "//input[@name='username']",
                    "candidate_selectors": [
                        {"by": "css", "target": "input[placeholder='Username']"},
                        {"by": "xpath", "target": "//input[@placeholder='Username']"},
                    ],
                    "keywords": ["username"],
                }
            ]
        },
    )

    locator = result.locators[0]
    assert locator.selected_by == "name"
    assert locator.selected_locator == "username"
    assert [item.model_dump() for item in locator.fallback_locators] == [
        {"by": "css", "target": "input[name='username']"},
        {"by": "xpath", "target": "//input[@name='username']"},
        {"by": "css", "target": "input[placeholder='Username']"},
        {"by": "xpath", "target": "//input[@placeholder='Username']"},
    ]
