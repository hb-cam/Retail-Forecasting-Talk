# Payments Forecasting with Retail Data

[View the Live Presentation](https://hb-cam.github.io/Retail-Forecasting-Talk/decks/build/retail-forecast.html)

**AMLC Community Talk — March 2026**

Scaling insights with an interpretable, drift-resistant solution of a dynamic system.

This repo contains the slide deck, Jupyter notebooks, and Python source code for a talk on structural econometric forecasting applied to retail and payments data.

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

## License

MIT
