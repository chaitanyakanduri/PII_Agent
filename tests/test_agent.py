import unittest
from unittest.mock import patch, MagicMock
from agent import PIIRedactionAgent
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class TestPIIRedactionAgent(unittest.TestCase):

    @patch("tools.ocr_di.ocr_file_to_text")
    @patch("tools.redact.process_bytes")
    @patch("tools.logger.get_logger")
    def test_run_success(self, mock_get_logger, mock_process_bytes, mock_ocr_file_to_text):
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_ocr_file_to_text.return_value = ("Extracted text", {})
        mock_process_bytes.return_value = {"status": "success"}

        agent = PIIRedactionAgent()
        file_bytes = b"test data"
        content_type = "application/pdf"

        # Act
        result = agent.run(file_bytes, content_type)

        # Assert
        mock_process_bytes.assert_called_once_with(file_bytes, content_type)
        self.assertEqual(result, {"status": "success"})
        mock_logger.debug.assert_called_with("Agent run invoked")

    @patch("tools.redact.process_bytes")
    @patch("tools.logger.get_logger")
    def test_run_exception(self, mock_get_logger, mock_process_bytes):
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_process_bytes.side_effect = Exception("Processing error")

        agent = PIIRedactionAgent()
        file_bytes = b"test data"
        content_type = "application/pdf"

        # Act & Assert
        with self.assertRaises(Exception) as context:
            agent.run(file_bytes, content_type)
        self.assertEqual(str(context.exception), "Processing error")
        mock_logger.error.assert_called_with("Error during processing: Processing error")

    @patch("tools.redact.process_bytes")
    def test_text_redaction_ssn(self, mock_process_bytes):
        # Arrange
        mock_process_bytes.return_value = {
            "redacted_text": "John's SSN is [SSN_REDACTED] and email [EMAIL_REDACTED]",
            "entities": [
                {"entity": "US_SSN", "start": 12, "end": 23},
                {"entity": "EMAIL_ADDRESS", "start": 37, "end": 55},
            ],
        }

        agent = PIIRedactionAgent()
        text = "John's SSN is 123-45-6789 and email john.doe@example.com"

        # Act
        res = agent.run(text.encode("utf-8"), "text/plain")

        # Assert
        assert "[SSN_REDACTED]" in res["redacted_text"]
        assert "[EMAIL_REDACTED]" in res["redacted_text"]
        ents = {e["entity"] for e in res["entities"]}
        assert "US_SSN" in ents and "EMAIL_ADDRESS" in ents

    def test_text_redaction_phone_dob(self):
        agent = PIIRedactionAgent()
        text = "Call me at (555) 123-4567. DOB: 12/31/1990."
        res = agent.run(text.encode("utf-8"), "text/plain")
        assert "[PHONE_REDACTED]" in res["redacted_text"]
        assert "[DOB_REDACTED]" in res["redacted_text"]

if __name__ == "__main__":
    unittest.main()
