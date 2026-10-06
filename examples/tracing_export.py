"""Run the offline analysis with spans exported to the console or an OTLP collector.

    pip install -e '.[tracing]' opentelemetry-sdk          # console
    python examples/tracing_export.py

    pip install opentelemetry-exporter-otlp-proto-http     # OTLP/HTTP collector
    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 python examples/tracing_export.py

Uses the offline provider: no network model calls, no API key.
"""

import json
import os
from pathlib import Path

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from northstar import DecisionOrchestrator, tracing
from northstar.contracts import ProgramScenario
from northstar.providers import OfflineProvider

provider = TracerProvider(resource=Resource.create({"service.name": "signalweave-ai"}))
if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    exporter = OTLPSpanExporter()  # endpoint read from OTEL_EXPORTER_OTLP_ENDPOINT
else:
    exporter = ConsoleSpanExporter()
provider.add_span_processor(BatchSpanProcessor(exporter))
tracing.configure(provider)

scenario_path = Path(__file__).with_name("synthetic_portfolio.json")
scenario = ProgramScenario.model_validate(json.loads(scenario_path.read_text()))
report = DecisionOrchestrator(provider=OfflineProvider()).run(scenario)
print(f"gate: {report.gate.status.value}")
provider.shutdown()  # flush
