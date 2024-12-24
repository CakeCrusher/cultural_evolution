# Implementation of the Paper: "Cultural Evolution of Cooperation among LLM Agents"

## Objective
This project implements the methodology outlined in the paper *Cultural Evolution of Cooperation among LLM Agents* by Vallinder and Hughes (2024). The paper explores whether a society of large language model (LLM) agents can develop cooperative norms through cultural evolution, using the classic *Donor Game*. The goal is to evaluate multi-agent interaction dynamics and the emergence of cooperation under iterative deployment.

Read the paper here: [*Cultural Evolution of Cooperation among LLM Agents*](https://arxiv.org/pdf/2412.10270)

This implementation consists of:
1. **A Numeric Simulation**: A simplified representation of the Donor Game.
2. **An Agentic Simulation**: A sophisticated model leveraging OpenAI's client SDK with structured outputs.

## Purpose
The numeric simulation validates the stability and cooperative potential of simplified Donor Game setups. The agentic simulation extends this by exploring emergent behaviors in LLM-based agents under culturally evolutionary conditions. The agentic approach also includes mechanisms for strategy generation, decision-making, and multi-generational evolution.

## Quickstart

### Prerequisites
- Python 3.10+
- Required Python libraries (install via `requirements.txt`):
  ```bash
  pip install -r requirements.txt
  ```
- OpenAI API credentials (add `.env` file with your API key, based on `.env.example`).

### Run the Numeric Simulation
1. Open the [**`donors_game-numeric.ipynb`**](./donors_game-numeric.ipynb) notebook.
2. Execute the cells to simulate the numeric Donor Game and visualize total reputation and wallet outcomes over iterations.

### Run the Agentic Simulation
1. Open the [**`donors_game-agentic.ipynb`**](./donors_game-agentic.ipynb) notebook.
2. Execute the cells to simulate multi-generation cooperative evolution among LLM agents using OpenAI's SDK.
3. Modify hyperparameters (e.g., number of players, trace depth, donation multiplier) as needed to explore various scenarios.

### File Legend
- **[`.env`](./.env)**: Contains API credentials for OpenAI.
- **[`.env.example`](./.env.example)**: Example file to set up your environment variables.
- **[`donors_game-numeric.ipynb`](./donors_game-numeric.ipynb)**: Simulates the Donor Game using a numeric approach.
- **[`donors_game-agentic.ipynb`](./donors_game-agentic.ipynb)**: Implements the Donor Game for LLM agents with strategy evolution using OpenAI's SDK.
- **[`README.md`](./README.md)**: This readme document.
- **[`requirements.txt`](./requirements.txt)**: Lists required dependencies for the project.
- **[`Vallinder and Hughes - 2024 - Cultural Evolution of Cooperation among LLM Agents.pdf`](./NOTES-Vallinder%20and%20Hughes%20-%202024%20-%20Cultural%20Evolution%20of%20Cooperation%20among%20LLM%20Agents.pdf)**: Notes on the original paper.

## Development Status
The project is in active development. The next steps include:
1. [ ] Implementing telemetry for the agentic script to improve analysis of results and facilitate troubleshooting.

## Further Research
- Explore hereditary single-parent taxonomies in evolutionary game theory for additional insights into strategy development.

Stay tuned for updates and enhancements!