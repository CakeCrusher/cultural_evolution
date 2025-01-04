import os
from phoenix.otel import register
from openinference.semconv.resource import ResourceAttributes
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


OTEL_EXPORTER_OTLP_HEADERS = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
PHOENIX_CLIENT_HEADERS = os.getenv("PHOENIX_CLIENT_HEADERS")
PHOENIX_COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if (
    not OTEL_EXPORTER_OTLP_HEADERS
    or not PHOENIX_CLIENT_HEADERS
    or not PHOENIX_COLLECTOR_ENDPOINT
    or not OPENAI_API_KEY
):
    raise ValueError("Missing required environment variables")

endpoint = PHOENIX_COLLECTOR_ENDPOINT + "/v1/traces"

project_name = "dspy_donors_game"

tracer_provider = register(project_name=project_name, endpoint=endpoint)


resource = Resource(attributes={ResourceAttributes.PROJECT_NAME: project_name})

tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider=tracer_provider)
tracer = trace.get_tracer(__name__)
span_exporter = OTLPSpanExporter(endpoint=endpoint)
simple_span_processor = SimpleSpanProcessor(span_exporter=span_exporter)
trace.get_tracer_provider().add_span_processor(simple_span_processor)
# tracer_provider.add_span_processor(simple_span_processor)
# trace.set_tracer_provider(tracer_provider)
# tracer = trace.get_tracer(__name__)
