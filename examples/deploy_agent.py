#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = ["chalkcompute>=2.12.1"]
# ///
#
# Runs the fraud investigation agent in a sandbox against a user ID.
#
# Usage:
#   uv run deploy_agent.py 42

import sys
import uuid
from pathlib import Path

from chalkcompute import Image, NetworkPolicy, Sandbox, Secret

_dir = Path(__file__).resolve().parent

image = (
    Image.debian_slim("3.12")
    .pip_install([
        "chalkpy>=2.130.5",
        "openai",
    ])
    .add_local_file(str(_dir / "agent.py"), "/app/agent.py")
    .workdir("/app")
)

user_id = sys.argv[1] if len(sys.argv) > 1 else "1"

sandbox = Sandbox(
    image=image,
    name=f"fraud-agent-{uuid.uuid4().hex[:8]}",
    secrets=[
        Secret.from_chalk_env("OPENAI_API_KEY"),
    ],
    chalk_identity=True,
    network_policy=NetworkPolicy(
        allowed_hosts=["api.openai.com", "*.chalk.ai"],
    ),
    cpu="1",
    memory="2Gi",
).run()

try:
    result = sandbox.exec(
        "python", "agent.py", user_id,
        timeout_secs=120,
    )
    print(result.stdout_text)
    if result.stderr_text:
        print(result.stderr_text, file=sys.stderr)
finally:
    sandbox.terminate()
