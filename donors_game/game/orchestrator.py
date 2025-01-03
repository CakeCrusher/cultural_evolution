from typing import List, Tuple, Optional
from models.config import GameState
from game.player import Player
from utils.misc import sanitize_filename
from utils.telemetry import tracer
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues
from opentelemetry import context as context_api
import json
import os
from concurrent.futures import ThreadPoolExecutor
import random


class Orchestrator:
    def __init__(self, game_state: GameState):
        with tracer.start_as_current_span("init_orchestrator") as span:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.CHAIN.value,
            )
            span.set_attribute(
                SpanAttributes.INPUT_VALUE, game_state.model_json_schema()
            )
            self.game_state = game_state
            self.players = [
                Player(game_state=game_state, i=i) for i in range(game_state.players)
            ]

            dir_path = (
                f"g{game_state.generations}_r{game_state.rounds}_p{game_state.players}/"
            )
            if not game_state.save_path:
                game_state.save_path = f"g{game_state.generations}_r{game_state.rounds}_p{game_state.players}.json"
            self.save_path = f"../data/{sanitize_filename(game_state.model_name)}/" + dir_path + game_state.save_path

            self.history = {}

    def find_player(self, name: str) -> Player:
        for player in self.players:
            if player.name == name:
                return player
        raise ValueError(f"Player {name} not found")

    def create_donor_recipient_pairs(self) -> List[Tuple[Player, Player]]:
        """
        Builds a random pairing so that no player is matched with themselves.
        Not strictly uniform over all derangements, but typically good enough.
        """
        n = len(self.players)
        available = list(range(n))
        result = [None] * n

        for i in range(n):
            # Exclude i from the candidates
            candidates = [x for x in available if x != i]

            # If there is no candidate (happens if i is the only one left in available),
            # we need to 'repair' by swapping with a previously assigned position.
            if not candidates:
                # Swap with any earlier position that isn't i
                # Because it implies we must have assigned some position j = i earlier
                # and it's causing a corner case now.
                for j in range(i):
                    if result[j] != j:
                        old_assignee = result[j]
                        result[j] = i
                        result[i] = old_assignee
                        break

            else:
                choice = random.choice(candidates)
                result[i] = choice
                available.remove(choice)

        # Now result[i] = index of the player who receives from i.
        # Convert that into (donor, recipient) pairs:
        return [(self.players[i], self.players[result[i]]) for i in range(n)]

    def play_round(self):
        with tracer.start_as_current_span("play_round") as span:
            span.set_attribute(
                SpanAttributes.INPUT_VALUE, self.game_state.model_dump_json()
            )
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.CHAIN.value,
            )
            pairs = self.create_donor_recipient_pairs()
            span.set_attribute(
                SpanAttributes.OUTPUT_VALUE,
                json.dumps(
                    [f"{donor.name} -> {recipient.name}" for donor, recipient in pairs]
                ),
            )
            # TODO: can be parallelized but need to keep wallets static untill the end

            current_context = context_api.get_current()

            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        donor.setup_donation,
                        recipient,
                        self.game_state,
                        self.players,
                        current_context,
                    )
                    for donor, recipient in pairs
                ]
                # Wait for all donations to complete
                results = [future.result() for future in futures]

            for result in results:
                donor = self.find_player(result.donor_name)
                recipient = self.find_player(result.recipient_name)
                donor.execute_donation(recipient, self.game_state, result)

            self.game_state.round += 1

    def evolve(self):
        with tracer.start_as_current_span("evolve") as span:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.AGENT.value,
            )
            span.set_attribute(
                SpanAttributes.INPUT_VALUE, self.game_state.model_dump_json()
            )
            self.game_state.round = 1
            self.game_state.generation += 1
            print(f"\n\nEvolving to generation {self.game_state.generation}")
            # sort players by wallet
            self.players = sorted(self.players, key=lambda x: x.wallet, reverse=True)
            # get top half
            top_half = self.players[
                : int(len(self.players) * self.game_state.cutoff_threshold)
            ]
            # clone players
            top_players_strings = "\n".join(
                [
                    f"player {player.name} with wallet {player.wallet} and strategy: {player.strategy}"
                    for player in top_half
                ]
            )
            print(f"\n\nTop half:\n{top_players_strings}")
            self.players = [
                Player(game_state=self.game_state, i=i, parents=top_half)
                for i in range(self.game_state.players)
            ]

    def save_state(self):
        self.history[f"g{self.game_state.generation}"] = [
            player.model_dump() for player in self.players
        ]
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        data = self.game_state.model_dump()
        data["history"] = self.history
        with open(self.save_path, "w") as f:
            json.dump(data, f)

    def run(self) -> List[Player]:
        for generation_count in range(self.game_state.generations):
            with tracer.start_as_current_span(f"generation_{generation_count}") as span:
                span.set_attribute(
                    SpanAttributes.INPUT_VALUE, self.game_state.model_dump_json()
                )
                span.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.CHAIN.value,
                )
                print(f"\n\nGeneration {self.game_state.generation}")
                for round_count in range(self.game_state.rounds):
                    with tracer.start_as_current_span(f"round_{round_count}") as span:
                        span.set_attribute(
                            SpanAttributes.INPUT_VALUE,
                            self.game_state.model_dump_json(),
                        )
                        span.set_attribute(
                            SpanAttributes.OPENINFERENCE_SPAN_KIND,
                            OpenInferenceSpanKindValues.CHAIN.value,
                        )
                        print(
                            f"\n\n\tGeneration {self.game_state.generation} Round {self.game_state.round}"
                        )
                        self.play_round()
                        self.save_state()
                if self.game_state.generation < self.game_state.generations:
                    self.evolve()

        return self.players
