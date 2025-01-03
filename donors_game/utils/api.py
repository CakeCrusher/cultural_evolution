import json
import openai
import os
from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes
from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

if OPENAI_BASE_URL:
    client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
else:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)


def structured_generation_wrapper(*args, **kwargs) -> dict:
    # sleep(.1)
    span = trace.get_current_span()
    args_to_log = {
        **kwargs,
        "response_format": kwargs["response_format"].model_json_schema(),
    }
    span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps(args_to_log))
    res = client.beta.chat.completions.parse(**kwargs)
    span.set_attribute(SpanAttributes.OUTPUT_VALUE, res.model_dump_json())
    so = res.choices[0].message.parsed
    if not so:
        raise ValueError("No response from LLM")
    return so
