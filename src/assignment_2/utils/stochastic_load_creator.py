"""Simple script for creating json files for stochastic load profiles."""

import json

import numpy as np

# Parameters
N_PROFILES = 300 # Number of load profiles
N_IN_SAMPLE = 100 # Number of in-sample profiles
N_TIMESTEPS = 60 # One bidding hour with minute resolution
LOAD_MIN = 220 # Minimum consumption
LOAD_MAX = 600 # Maximum consumption
MAX_STEP = 35 # Maximum step size

rng = np.random.default_rng(seed=42)


def generate_profile() -> list:
    """Generate one feasible 60-minute load profile.

    Parameters:
        None

    Returns:
        list: A list of 60 integers representing the load profile.
    """
    profile = []

    # Random starting load
    current = rng.integers(LOAD_MIN, LOAD_MAX + 1)
    profile.append(int(current))

    for _ in range(1, N_TIMESTEPS):

        lower = max(LOAD_MIN, current - MAX_STEP)
        upper = min(LOAD_MAX, current + MAX_STEP)

        current = rng.integers(lower, upper + 1)
        profile.append(int(current))

    return profile


# Generate 300 scenarios
all_profiles = {}

for i in range(1, N_PROFILES + 1):
    all_profiles[str(i)] = generate_profile()


# Split scenarios
in_sample = {
    str(i): all_profiles[str(i)]
    for i in range(1, 101)
}

out_of_sample = {
    str(i - 100): all_profiles[str(i)]
    for i in range(101, 301)
}


# Save files
with open("src/assignment_2/data/in_sample_load.json", "w") as f:
    json.dump(in_sample, f, indent=4)

with open("src/assignment_2/data/out_of_sample_load.json", "w") as f:
    json.dump(out_of_sample, f, indent=4)