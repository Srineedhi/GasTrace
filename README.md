# AEROSENSE AI — Gas Leak Source Localization

**TECHNOVA 2026 · Problem Statement PS-15**

An interactive, simulation-driven platform for exploring gas-leak source localization from sparse sensor measurements. AEROSENSE AI combines plume simulation, probabilistic inference, sensor-data visualization, and an interactive digital-twin dashboard to investigate how limited observations can support source localization.

## Overview

Gas leaks in industrial environments can be difficult to localize when sensor coverage is limited. AEROSENSE AI provides a simulation environment for studying this problem, visualizing inferred source locations, and evaluating localization behavior under controlled scenarios.

The project is designed as a research and demonstration prototype. Its outputs should not be interpreted as certified industrial measurements or safety guarantees.

## Key Features

- **Gas-plume simulation:** Explore simulated gas dispersion and sensor observations.
- **Sparse-sensor analysis:** Investigate localization when measurements are available from a limited sensor network.
- **Probabilistic inference:** Estimate plausible leak-source locations from simulated observations.
- **Interactive digital twin:** Explore the scenario through a dashboard with visual panels and controls.
- **Live simulation workflows:** Examine changing observations and localization behavior.
- **Performance benchmarking:** Evaluate the method under controlled simulation scenarios.
- **Visualization and diagnostics:** Inspect plots, alerts, and inference outputs.
- **Automated tests:** Use the included test suite to check core behavior and application functionality.

## System Architecture

```text
Simulated Gas-Leak Scenario
            |
            v
   Plume / Sensor Physics
            |
            v
 Sparse Sensor Observations
            |
            v
 Probabilistic Inference
            |
            v
 Source-Location Estimate
            |
            v
 Dashboard, Plots and Diagnostics
            |
            v
 Controlled Benchmark Evaluation
```

## Technology Stack

- **Language:** Python
- **Application framework:** Streamlit
- **Numerical computing:** NumPy
- **Data processing:** Pandas
- **Visualization:** Matplotlib
- **Testing:** pytest
- **Deployment target:** Streamlit Community Cloud

## Project Structure

```text
gas-leak-digital-twin/
├── app.py
├── twin/
│   ├── alerts.py
│   ├── config.py
│   ├── inference.py
│   ├── interactive.py
│   ├── live.py
│   ├── mission.py
│   ├── panels.py
│   ├── physics.py
│   ├── plots.py
│   ├── styles.py
│   └── ui.py
├── tests/
│   ├── test_app.py
│   └── test_core.py
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or a compatible version supported by the project's dependencies
- pip
- Git

### Installation

Clone the repository:

```bash
git clone https://github.com/SrineedhiRB/Aerosense_AI.git
cd Aerosense_AI
```

If the project files are inside the `gas-leak-digital-twin` subfolder, enter it:

```bash
cd gas-leak-digital-twin
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the application dependencies:

```bash
pip install -r requirements.txt
```

### Run the application

```bash
streamlit run app.py
```

Streamlit will display a local URL in the terminal. Open that URL in your browser.

### Run tests

Install development dependencies if needed:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
python -m pytest -q
```

## Deployment

The application can be deployed through Streamlit Community Cloud by connecting this GitHub repository, selecting the `main` branch, and specifying `app.py` as the entry point.

**Live demo:** Add the deployed application URL here after deployment.

## Evaluation and Limitations

- Benchmark results depend on the simulation assumptions and the scenarios being evaluated.
- Results generated from a simplified plume model do not establish real-world localization accuracy.
- Probabilistic estimates and coverage diagnostics should not be treated as proof of calibration.
- Active-sensing or sensor-placement recommendations are exploratory heuristics, not proven optimal plans.
- The application is an educational and engineering prototype, not a certified gas-detection, worker-protection, or emergency-response system.

Real-world deployment would require appropriate physical sensors, validated dispersion models, field testing, uncertainty analysis, and independent safety assessment.

## Future Work

- Evaluate performance under different sensor densities and noise levels.
- Test robustness against wind variation and model mismatch.
- Add repeatable benchmark scenarios and quantitative evaluation metrics.
- Improve uncertainty visualization and localization diagnostics.
- Investigate integration with real sensor telemetry after appropriate validation.
- Automate tests and deployment checks through continuous integration.

## Contributing

Contributions can focus on simulation realism, inference methods, test coverage, visualization, reproducibility, and documentation.

1. Fork the repository.
2. Create a feature branch.
3. Make a focused change.
4. Run the test suite.
5. Submit a pull request describing the change and its validation.

## License

See the [LICENSE](LICENSE) file for the terms governing use, modification, and distribution.


