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
