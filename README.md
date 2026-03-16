# Payments Forecasting with Retail Data

[View the Live Presentation](https://hb-cam.github.io/Retail-Forecasting-Talk/decks/build/retail-forecast.html)

**AMLC Community Talk — March 2026**

Scaling insights with an interpretable, drift-resistant solution of a dynamic system.

This repo contains the slide deck, Jupyter notebooks, and Python source code for a talk on structural econometric forecasting applied to retail and payments data.

### Run the Notebooks

#### Run in Colab
These notebooks are configured to run in **Google Colab** with zero local setup.

| Analysis Module | Focus | Link |
| :--- | :--- | :--- |
| **Retail Cyclicality** | STL decomposition, cross-correlation, and crisis comparison. | [![Cyclicality Analysis](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hb-cam/Retail-Forecasting-Talk/blob/main/notebooks/Retail_Cyclicality.ipynb) |
| **Forecasting Model** | Structural regression modeling and macroeconomic indexing. | [![Forecasting Model](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hb-cam/Retail-Forecasting-Talk/blob/main/notebooks/Retail_Forecast.ipynb) |

> [!TIP]
> **Using FRED in Colab:** When the notebook opens, you will be prompted to enter your [FRED API Key](https://fred.stlouisfed.org/docs/api/api_key.html) to fetch live data. The notebooks include pre-computed outputs if you prefer to just browse.

#### Run locally
```bash
uv run jupyter lab
```

Open `notebooks/Retail_Cyclicality.ipynb` or `notebooks/Retail_Forecast.ipynb`. Both notebooks ship with outputs so you can read them without running, but a FRED API key is required to re-execute cells.

### Run Tests

```bash
uv run pytest -v                   # All tests (requires FRED_API_KEY in .env)
uv run pytest -v -k "not Live"    # Unit tests only (no network)
```

## 💬 Q&A and Discussion
If you're attending the AMLC talk and have questions about the structural econometric approach or the `statsmodels` implementation, please [open an issue](https://github.com/hb-cam/Retail-Forecasting-Talk/issues) or reach out during the networking session!

## What's Inside

| Path | Description |
|------|-------------|
| `decks/build/retail-forecast.html` | Pre-built slide deck — open in a browser and present |
| `decks/retail-forecast.md` | Slide deck source (Marp format) |
| `notebooks/Retail_Cyclicality.ipynb` | Cyclicality analysis: STL decomposition, cross-correlation, crisis comparison |
| `notebooks/Retail_Forecast.ipynb` | Forecasting model: regression with macroeconomic indices |
| `src/data_loader.py` | FRED API data loader (`FredMacroRetailLoader`) |
| `src/regression_dclass/` | Versioned regression module (v0 → v1 → v2 progression) |
| `tests/` | 26 tests covering the data loader (unit + live FRED API) |

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js (optional, for deck dev server)
- A free [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html)

### Setup

```bash
git clone https://github.com/hb-cam/Retail-Forecasting-Talk.git
cd Retail-Forecasting-Talk

# Install Python dependencies
uv sync

# Configure your FRED API key
cp .env.example .env
# Edit .env and add your key
```

### View the Presentation

The easiest way — just open the pre-built HTML:

```bash
open decks/build/retail-forecast.html    # macOS
xdg-open decks/build/retail-forecast.html  # Linux
```

Press **F11** for fullscreen. All diagrams and assets are self-contained.

To run the dev server (requires Node.js):

```bash
npm install
npm run deck:serve
# Opens at http://localhost:3000
```

## Talk Overview

1. **The Problem** — sampling bias and simultaneity in operational data
2. **The Structural Solution** — decomposing revenue through macro → industry → operational → financial layers
3. **Building It Right** — functional form, indexation, and regression rigor
4. **Modeling Dynamics** — stationarity, co-integration, and AR models
5. **Using the Forecast** — uncertainty, scenarios, and stakeholder communication
6. **Maintaining the Model** — tracking drift and maintaining accuracy

## Tech Stack

- **Python:** pandas, numpy, matplotlib, statsmodels, requests
- **Data:** FRED API (Federal Reserve Economic Data)
- **Slides:** Marp CLI with vendored Mermaid.js for offline diagrams
- **Package management:** uv


## 🤝 Contributing

We welcome contributions from the community! Whether you are fixing a bug in the regression module or adding a new analysis notebook, please follow these steps to ensure a smooth workflow.

### 1. Prerequisites
This project uses **[uv](https://docs.astral.sh/uv/)** for Python package and project management. If you don't have it yet, install it via:
```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

```

### 2. Development Workflow

1. **Fork & Clone**: Fork the repository and clone it to your local machine.
2. **Environment Setup**: Run `uv sync` to create a virtual environment and install all dependencies (including dev dependencies like `pytest`).
```bash
uv sync

```

3. **Create a Branch**:
```bash
git checkout -b feature/your-feature-name

```

4. **Data Access**: Ensure your `.env` file contains your `FRED_API_KEY`.
5. **Coding Standards**: We use `v0 -> v1 -> v2` versioning in the `src/regression_dclass` to show model evolution. If updating the model, please maintain this progression.

### 3. Testing

Before submitting a Pull Request, please ensure all tests pass. We use `pytest` for both unit and live API integration tests.

```bash
# Run all tests (requires API key)
uv run pytest

# Run only unit tests (no network required)
uv run pytest -k "not Live"

```

### 4. Submitting Changes

* Open a Pull Request with a clear description of the changes.
* Ensure your notebooks have been "cleared" of large binary outputs unless they are essential for the demonstration.
* If you are an attendee of the **AMLC Meetup**, feel free to open an issue for questions or suggestions!

---

**License** This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

```
