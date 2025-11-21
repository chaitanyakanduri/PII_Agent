@patch("tools.redact.process_bytes")
def test_text_redaction_phone_dob(self, mock_process_bytes):
    # Arrange
    mock_process_bytes.return_value = {
        "redacted_text": "Call me at [PHONE_REDACTED]. DOB: [DOB_REDACTED].",
        "entities": [
            {"entity": "PHONE_NUMBER", "start": 12, "end": 25},
            {"entity": "DATE_TIME", "start": 31, "end": 41},
        ],
    }

    agent = PIIRedactionAgent()
    text = "Call me at (555) 123-4567. DOB: 12/31/1990."

    # Act
    res = agent.run(text.encode("utf-8"), "text/plain")

    # Assert
    assert "[PHONE_REDACTED]" in res["redacted_text"]
    assert "[DOB_REDACTED]" in res["redacted_text"]