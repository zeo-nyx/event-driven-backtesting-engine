# Tech Stack

## Language Choice: Python

Python is used due to:
- Strong data ecosystem for financial analysis
- Fast development speed for research workflows
- Readability for collaborative quant teams

## Architecture Pattern

Event-driven architecture was chosen because it mirrors production trading systems where data, signals, orders, and fills occur sequentially through asynchronous workflows.

## Library Choices

- **pandas**: tabular data loading and time-series manipulation
- **numpy**: numerical calculations for risk/return metrics
- **matplotlib**: optional plotting extension for equity curve visualization

## Project Structure Rationale

- `src/`: core engine modules with strict separation of concerns
- `data/`: historical CSV inputs
- `tests/`: unit tests for critical business logic
- markdown docs: product, architecture, and implementation communication for stakeholders

This structure keeps the codebase internship-friendly while remaining professional and extensible.
