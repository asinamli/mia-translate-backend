import json
import logging

from app.core.logging import JsonFormatter


def test_json_formatter_outputs_structured_log():
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )

    record.job_id = "job_test"
    record.status = "completed"

    formatted_log = JsonFormatter().format(record)
    data = json.loads(formatted_log)

    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["message"] == "test message"
    assert data["job_id"] == "job_test"
    assert data["status"] == "completed"
    assert "timestamp" in data