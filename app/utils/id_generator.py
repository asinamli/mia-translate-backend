from uuid import uuid4


def generate_request_id() -> str:
    return f"req_{uuid4().hex}"


def generate_job_id() -> str:
    return f"job_{uuid4().hex}"