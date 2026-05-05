# 46755_Assignment_2
This repo contains code and data for group 32 for assignment 2

## Repo structure
In the "assignment_2" folder, four folders are found:
- "data" contains json files for all data inputs
- "step_1" is step 1 of the assignment
- "step_2" is step 2 of the assignment
- "utils" contains utility scripts for data processing

## Intro
Each step has its own runnable entry point.

`assignment_2/step_1/main.py` covers the day-ahead and balancing market participation of a 500 MW price-taking wind farm and runs all four tasks of step 1:
- Builds 1,600 combined scenarios from wind, day-ahead price, and system imbalance data and shuffles them with a fixed seed.
- Solves the stochastic offering problem on the in-sample subset under both the one-price and two-price balancing schemes (Tasks 1.1 and 1.2), and plots the hourly bids and per-scenario profit distributions.
- Performs an 8-fold cross-validation with 200 in-sample / 1,400 out-of-sample scenarios per fold and reports the averaged in-sample vs. out-of-sample expected profits for both schemes (Task 1.3).
- Solves the risk-averse offering problem with CVaR (α = 0.90) sweeping β from 0 to 1, and plots the expected-profit-vs-CVaR efficient frontier and the resulting bid quantities (Task 1.4).

`assignment_2/step_2/main.py` covers the FCR-D Up reserve bid of a stochastic flexible load (0–600 kW) under Energinet's P90 requirement and runs all three tasks of step 2:
- Loads the 100 in-sample and 200 out-of-sample minute-resolution load profiles.
- Solves the in-sample reserve-bid problem with both ALSO-X and the CVaR reformulation at ε = 0.10 (Task 2.1).
- Verifies the P90 requirement on the out-of-sample profiles for both methods, reporting the empirical reliability and expected reserve shortfall (Task 2.2).
- Sweeps the P-threshold from 80 % to 100 % using ALSO-X and plots the in-sample bid and out-of-sample expected shortfall against the threshold (Task 2.3).

## Development
1. Have git installed on your machine.
2. Have python installed on your machine. At least the version specified in pyproject.toml
3. Have the python extension installed in your VSCode
4. CTRL + Shift + P -> Python: Create Environment -> Venv -> Select python version
5. Download dependencies by running "pip install -e." in the powershell terminal. Environment should activate automatically when powershell terminal is launched.

### Ruff
    For proper development, please have Ruff installed.
    After installement; go to File -> Preferences -> Settings.
        Turn on "Format on save".

### Notes and links
1. Wind data is taken from [renewables.ninja](https://www.renewables.ninja/). A random data set was generated based on a location around Kgs. Lyngby, DK. A randomly picked set of 20 days of the year 2019 were taken for the data set. The data was converted to MW from kW, and then a list was created to ease the copy-paste process into the json file. 

2. DA prices data is taken from [Entsoe](https://transparency.entsoe.eu/market/energyPrices?appState=%7B%22sa%22%3A%5B%22BZN%7C10YDK-2--------M%22%5D%2C%22st%22%3A%22BZN%22%2C%22mm%22%3Atrue%2C%22ma%22%3Afalse%2C%22sp%22%3A%22HALF%22%2C%22dt%22%3A%22TABLE%22%2C%22df%22%3A%222025-01-01%22%2C%22tz%22%3A%22CET%22%7D). The first days of every month is taken from January 2023 to August 2024 and converted to a json file.
