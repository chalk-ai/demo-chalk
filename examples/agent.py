"""Entrypoint executed inside the sandbox container.

Self-contained -- does not import src/ modules, which pull in Chalk feature
registration. Takes a user ID, queries Chalk fraud features, and makes a
fraud risk decision using an LLM agent loop.
"""

import json
import os
import sys

from chalk.client import ChalkClient
from openai import OpenAI

SYSTEM_PROMPT = (
    "You are a fraud analyst for a financial services company. "
    "You evaluate user accounts to decide whether they are fraudulent, suspicious, or clean. "
    "You have access to real-time signals from the Chalk feature store -- "
    "use the tools to look up user profile data, transaction patterns, and credit report information. "
    "Start by querying the user's basic profile and risk score, then look at their "
    "transaction aggregates (count, average amount, night ratio, return ratio), "
    "and finally check their credit report. "
    "Red flags include: denylisted emails, high risk scores, high ACH return ratios, "
    "high night transaction ratios, low credit scores, and high percent past due. "
    "When you request features, request them in small groups and keep calling the tool to gather more evidence. "
    "Reply with FRAUD, SUSPICIOUS, or CLEAN on the first line, "
    "then one sentence of reasoning."
)

FEATURE_NAMES = [
    "user.name",
    "user.email",
    "user.created_at",
    "user.denylisted",
    "user.email_age_days",
    "user.is_fraud",
    "user.name_email_match_score",
    "user.risk_score",
    "user.txn_count",
    "user.avg_txn_amount",
    "user.night_txn_ratio",
    "user.ach_return_ratio",
    "user.email_domain",
    "user.risk_category",
    "user.account_age_days",
    "user.credit_report.score",
    "user.credit_report.num_tradelines",
    "user.credit_report.total_balance",
    "user.credit_report.percent_past_due",
]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_chalk_features",
            "description": (
                "Fetch fraud detection features for a user by their id. "
                "Select which features to retrieve from the available list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer"},
                    "features": {
                        "type": "array",
                        "items": {"type": "string", "enum": FEATURE_NAMES},
                        "minItems": 1,
                    },
                },
                "required": ["user_id", "features"],
            },
        },
    },
]


def run_agent(
    openai_client, messages: list, handlers: dict, model: str = "gpt-5.5"
) -> str:
    steps = []
    while True:
        response = openai_client.chat.completions.create(
            model=model,
            tools=TOOLS,
            messages=messages,
        )

        msg = response.choices[0].message
        if not msg.tool_calls:
            decision = msg.content or ""
            trace = "\n".join(steps)
            return f"{trace}\n\n{decision}".lstrip() if steps else decision

        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        for tc in msg.tool_calls:
            inp = json.loads(tc.function.arguments)
            handler = handlers.get(tc.function.name)
            if handler is None:
                raise RuntimeError(f"unknown tool: {tc.function.name}")
            result = handler(inp)
            args = ", ".join(f"{k}={v!r}" for k, v in inp.items())
            steps.append(f"  {tc.function.name}({args}) -> {result}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})


user_id = int(sys.argv[1])

chalk_client = ChalkClient()
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=10)


def get_chalk_features(inp: dict) -> str:
    ctx = chalk_client.query(
        input={"user.id": inp["user_id"]},
        output=inp["features"],
    )
    return "\n".join(f"{a.field}: {a.value}" for a in ctx.data)


messages: list = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {
        "role": "user",
        "content": (
            f"Evaluate user ID {user_id} for fraud risk. "
            "Query their profile, transaction patterns, and credit data to make a determination."
        ),
    },
]

print(
    run_agent(
        openai_client,
        messages,
        handlers={"get_chalk_features": get_chalk_features},
    )
)
