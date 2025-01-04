from typing import List
from pydantic import BaseModel, Field
import dspy


class StrategyBuilder(BaseModel):
    """Build the strategy"""

    thoughts: List[str] = Field(
        ...,
        description="Briefly describe your thought process for the strategy to take for this round. KEEP THOUGHTS SHORT AND NO MORE THAN 4 THOUGHTS.",
    )
    strategy: str = Field(
        ...,
        description="The strategy to be used, must begin with 'My strategy will be'. KEEP THOUGHTS SHORT AND NO MORE THAN 4 THOUGHTS.",
    )


class DonationBuilder(BaseModel):
    """Build the donation"""

    thoughts: List[str] = Field(
        ...,
        description="Briefly describe your thought process for the donation to make for this round.",
    )
    donation: float = Field(
        ...,
        description="The percentage amount of resources to donate. MUST BE A FLOAT BETWEEN 0 AND 1.",
    )


class NewStrategy(dspy.Signature):
    strat_gen_instruction: str = dspy.InputField()
    improved_strategy: str = dspy.OutputField(desc="New strategy that is better than the top strategies")

