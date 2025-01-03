from pydantic import BaseModel


class DynamicGameState(BaseModel):
    generation: int = 0
    round: int = 0


class GameConfig(BaseModel):
    donation_multiplier: float = 2
    trace_depth: int = 3
    base_wallet: int = 10
    generations: int = 10
    rounds: int = 12
    players: int = 12
    cutoff_threshold: float = 0.5
    save_path: str = "game_state.json"
    model_name: str = "gpt-4o-mini"


class GameState(GameConfig, DynamicGameState):
    pass


class Decision(BaseModel):
    # agents data
    recipient_name: str
    donor_name: str
    # game state data
    dynamic_game_state: DynamicGameState
    # donation data
    donation_percent: float
    donation_amount: float
    # donor wallet data
    donor_wallet_before: float
    donor_wallet_after: float

    class Config:
        arbitrary_types_allowed = True
