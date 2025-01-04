from .api import client
from typing import Literal
from pydantic import BaseModel
import random
from typing import List, TypeVar, Tuple

T = TypeVar("T")


# function to sanitize a string to be used as a filename remove colons and other special characters
def sanitize_filename(filename: str) -> str:
    return filename.replace(":", "_").replace("-", "_").replace(" ", "_")


def strategy_metric(gold, pred, trace=None):
    class StrategyEval(BaseModel):
        """Evaluate the percieved effectiveness of the newly generated strategy"""

        feedback: Literal["more effective", "less effective", "neutral"]

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": f"""Evaluate the percieved effectiveness of the newly generated strategy.
            The strategy generation instruction is: {pred.strat_gen_instruction}
            """,
            },
            {"role": "user", "content": pred.improved_strategy},
        ],
        response_format=StrategyEval,
    )
    feedback = completion.choices[0].message.parsed
    if not feedback:
        raise ValueError("No feedback received")

    if feedback.feedback == "more effective":
        return 1
    elif feedback.feedback == "less effective":
        return 0
    else:
        return 0.4


def create_unique_subset_pairs(
    list1: List[T], list2: List[T], num_combinations: int = 5
) -> List[Tuple[List[T], List[T]]]:
    """
    Creates unique combinations of subsets from two lists.
    Each combination contains 1 to n items from each list.

    Args:
        list1: First list to sample from
        list2: Second list to sample from
        num_combinations: Number of unique combinations to generate

    Returns:
        List of tuples, each containing two lists (subset of list1, subset of list2)
    """
    results = []
    seen = set()

    max_attempts = num_combinations * 3  # Prevent infinite loops
    attempts = 0

    while len(results) < num_combinations and attempts < max_attempts:
        # Random sizes for subsets
        size1 = random.randint(1, len(list1))
        size2 = random.randint(1, len(list2))

        # Create random subsets
        subset1 = random.sample(list1, size1)
        subset2 = random.sample(list2, size2)

        # Create hashable representation of the combination
        combo_hash = (
            tuple(sorted(x.name for x in subset1)),
            tuple(sorted(x.name for x in subset2)),
        )

        # Only add if this combination is unique
        if combo_hash not in seen:
            seen.add(combo_hash)
            results.append((subset1, subset2))

        attempts += 1

    return results
