# 46755_Assignment_2
This repo contains code and data for group 32 for assignment 2

## Repo structure
In the "src" folder, three folders are found:
- "data" contains json files for all data inputs
- "step_1" is step 1 of the assignment
- "step_2" is step 2 of the assignment

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
1. Wind data is taken from [renewables.ninja](https://www.renewables.ninja/). A random data set was generated based on a location around Kgs. Lyngby, DK. The first 20 days of the year were taken for the data set. The data was converted to MW from kW, and then a list was created to ease the copy-paste process into the json file. 