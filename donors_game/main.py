import dotenv
from game.orchestrator import Orchestrator
from models.config import GameState
from openinference.semconv.trace import SpanAttributes
from utils.telemetry import tracer
from opentelemetry import trace
from openinference.semconv.trace import OpenInferenceSpanKindValues

dotenv.load_dotenv()

game_state = GameState(
    generations=10,
    rounds=12,
    players=12,
    save_path="game_state.json",
    model_name="llama3.1:8b-instruct-q2_K",
)

with tracer.start_as_current_span(f"donors_game-{game_state.model_name}-g{game_state.generations}_r{game_state.rounds}_p{game_state.players}") as span:
    try:
        span.set_attribute(SpanAttributes.INPUT_VALUE, game_state.model_dump_json())
        span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, OpenInferenceSpanKindValues.CHAIN.value)
        orchestrator = Orchestrator(game_state)
        final_players = orchestrator.run()
    except Exception as e:
        span.set_status(trace.Status(trace.StatusCode.ERROR))
        span.record_exception(e)

