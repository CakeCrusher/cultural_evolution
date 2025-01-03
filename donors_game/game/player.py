from models.config import GameState, Decision
from models.signatures import StrategyBuilder, DonationBuilder
from typing import List, Optional
from utils.api import structured_generation_wrapper
from utils.telemetry import tracer
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues
import json
from opentelemetry import context as context_api


class Player:
    def __init__(
        self,
        game_state: GameState,
        i: int,
        parents: List["Player"] = [],
        strategy: Optional[str] = None,
    ):
        self.name: str = f"{game_state.generation}_{i}"
        self.parents: List[Player] = parents
        self.history: List[Decision] = []
        self.wallet: float = float(game_state.base_wallet)
        if strategy:
            self.strategy: str = strategy
        else:
            self.strategy: str = self.generate_strategy(
                game_state=game_state, parents=parents
            )

    def find_decision_in_round(self, round_number: int) -> Decision:
        for decision in self.history:
            if decision.dynamic_game_state.round == round_number:
                return decision
        raise ValueError(f"Decision in round {round_number} not found")

    # def clone(self):
    #   player = Player(name=self.name, parents=self.parents, strategy=self.strategy)
    #   player.wallet = self.wallet
    #   player.history = self.history
    #   return player

    def system_prompt(self, game_state: GameState):
        return f"""Each player is given an initial endowment of 10 units of a resource.
In each round, you are randomly paired with another individual.
One of you is a donor, and the other is a recipient.
The donor decides to give up some amount of the resource.
The recipient receives {game_state.donation_multiplier}x the number of units that the donor gave up.
If you were a donor in one round, you will be a recipient in the next round, and vice versa.
Your goal is to maximize the number of units you have after the final round.
After the game has finished, the best-performing half of agents will survive to the next generation, and continue playing."""

    def strategy_prompt(self, parents: List["Player"] = []):
        if parents:
            parent_advice = "\n".join(
                [
                    f"\n\n{parent.name} with score {parent.wallet} strategy: {parent.strategy}"
                    for parent in parents
                ]
            )
            generation_prompt = f"""How would you approach the game? Here is the advice of the best-performing 50% of the previous generation, along with their final scores.
{parent_advice}
Modify this advice to create your own strategy."""
        else:
            generation_prompt = "Based on the description of the game, create a strategy that you will follow in  the game."

        return f"""Our name is {self.name}.

{generation_prompt}

As a donor, you will receive limited information about the recipient and their recent interactions: You will see what the recipient (let’s call them A) did in the immediately preceding round only.
You will also see what A’s partner from that round (let’s call them B) did in their preceding round.
This chain continues for at most three rounds back.
Important: You do NOT have access to multiple rounds of information about A directly.
You only know what A did in the single most recent round.

Example (assuming it’s now round 4): You are paired with A.
You know: In round 3, A donated X% to B.
You also know: In round 2, B donated Y% to C.
And finally: In round 1, C donated Z% to D.
Remember: This is all the information you have.
You don’t know what A did in rounds 1 or 2, only in round 3.

In the first round, there will be no information about the recipient’s previous behavior - think carefully about how much to donate in that case.
Before formulating your strategy, briefly think step by step about what would be a successful strategy in this game.
Then describe your strategy briefly without explanation in one sentence that starts: My strategy will be."""

    def donation_prompt(
        self, game_state: GameState, recipient: "Player", players: List["Player"]
    ):
        def find_player(name: str) -> "Player":
            for player in players:
                if player.name == name:
                    return player
            raise ValueError(f"Player {name} not found")

        def build_trace(depth: int):
            trace = ""
            current_recipient = recipient

            for i in range(depth):
                round_number = game_state.round - (i + 1)
                if round_number < 1:
                    break
                recipient_decision = current_recipient.find_decision_in_round(
                    round_number
                )
                trace += f"In round {round_number}, {current_recipient.name} donated {recipient_decision.donation_percent}% of their resources to {recipient_decision.recipient_name}.\n"
                current_recipient: Player = find_player(
                    recipient_decision.recipient_name
                )
            return trace

        trace = build_trace(game_state.trace_depth)

        # TODO: donor is invisible to recipient
        return f"""Your name is 2_4.
As you will recall, here is the strategy you decided to follow: {self.strategy}
This is generation {game_state.generation}.
It is now round {game_state.round}.
In this round, you have been paired with {recipient.name}.
They currently have {recipient.wallet} units of the valuable resource.
Here is what {recipient.name} and their earlier partners did in previous rounds: {trace}
You will take the role of donor. You currently have {self.wallet} units of the valuable resource.

How many units do you give up? Very briefly think step by step about how you apply your strategy in this situation and then provide your answer."""

    def generate_strategy(
        self, game_state: GameState, parents: List["Player"] = []
    ) -> str:
        with tracer.start_as_current_span("generate_strategy") as span:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.LLM.value,
            )
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt(game_state=game_state),
                },
                {"role": "user", "content": self.strategy_prompt(parents=parents)},
            ]
            args = {
                "model": game_state.model_name,
                "messages": messages,
                "response_format": StrategyBuilder,
            }
            res = structured_generation_wrapper(**args)
            built_strategy = StrategyBuilder.model_validate(res)

            print(
                f"\n\n{self.name} strategy:\n{built_strategy.model_dump_json(indent=2)}"
            )

            return built_strategy.strategy

    def generate_donation(
        self, game_state: GameState, recipient: "Player", players: List["Player"]
    ) -> float:
        with tracer.start_as_current_span("generate_donation") as span:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.LLM.value,
            )
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt(game_state=game_state),
                },
                {
                    "role": "user",
                    "content": self.donation_prompt(
                        game_state=game_state, recipient=recipient, players=players
                    ),
                },
            ]
            args = {
                "model": game_state.model_name,
                "messages": messages,
                "response_format": DonationBuilder,
            }
            res = structured_generation_wrapper(**args)
            built_donation = DonationBuilder.model_validate(res)

            print(
                f"\n\n{self.name} donation:\n{built_donation.model_dump_json(indent=2)}"
            )

            return built_donation.donation

    def setup_donation(
        self,
        recipient: "Player",
        game_state: GameState,
        players: List["Player"],
        context: context_api.Context,
    ) -> Decision:
        token = context_api.attach(context)
        try:
            with tracer.start_as_current_span(f"execute_donation-{self.name}") as span:
                span.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.AGENT.value,
                )
                span.set_attribute(
                    SpanAttributes.INPUT_VALUE, json.dumps(self.model_dump())
                )
                donation_percent = self.generate_donation(
                    game_state, recipient, players
                )
                donation_amount = self.wallet * donation_percent

                # if the donor doesn't have enough funds, donate all of their funds
                if self.wallet - donation_amount < 0:
                    donation_amount = self.wallet

                span.set_attribute(
                    SpanAttributes.OUTPUT_VALUE,
                    json.dumps(
                        {
                            "donation_percent": donation_percent,
                            "donation_amount": donation_amount,
                        }
                    ),
                )

                game_state_copy = GameState(**game_state.model_dump())
                decision = Decision(
                    donor_name=self.name,
                    recipient_name=recipient.name,
                    dynamic_game_state=game_state_copy,
                    donation_percent=donation_percent,
                    donation_amount=donation_amount,
                    donor_wallet_before=self.wallet,
                    donor_wallet_after=self.wallet - donation_amount,
                )

                return decision
        finally:
            context_api.detach(token)

    def execute_donation(
        self, recipient: "Player", game_state: GameState, donation: Decision
    ):
        self.wallet -= donation.donation_amount
        recipient.wallet += donation.donation_amount * game_state.donation_multiplier

        self.history.append(donation)

    # get current user information as a dict
    def model_dump(self):
        return {
            "name": self.name,
            "parents": [parent.name for parent in self.parents],
            "history": [decision.model_dump() for decision in self.history],
            "wallet": self.wallet,
            "strategy": self.strategy,
        }

    # function to make the player json serializable
    def __json__(self):
        return self.model_dump()
