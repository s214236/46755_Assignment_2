# 46755_Assignment_2
This repo contains code and data for group 32 for assignment 2

## Repo structure
In the "assignment_2" folder, three folders are found:
- "data" contains json files for all data inputs
- "step_1" is step 1 of the assignment
- "step_2" is step 2 of the assignment
- "utils" contains utility scripts for data processing

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
