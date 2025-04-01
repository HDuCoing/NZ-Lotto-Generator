import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
from typing import Tuple, List, Optional
import time
import logging
import argparse
from pathlib import Path
from scipy.stats import uniform

logger = logging.getLogger(__name__)

# Constants
HOT_MAIN_NUMBERS = [23, 32, 36, 17, 40, 13, 5]  # Most frequent main numbers
HOT_POWERBALLS = [1, 5, 6, 9]  # Most frequent Powerballs
MAIN_NUMBERS_RANGE = range(1, 41)
POWERBALL_RANGE = range(1, 11)
HOT_NUMBER_WEIGHT = 3.0  # Weight multiplier for hot numbers
BASE_WEIGHT = 1.0
MIN_HOT_NUMBERS = 2  # Minimum hot numbers per set
MAX_GENERATION_ATTEMPTS = 1000
REQUEST_TIMEOUT = 10  # seconds
DEFAULT_NUM_SETS = 10
RESULTS_URL = 'http://www.lottoshop.co.nz/my-lotto-results-nz'
HOT_NUMBERS_FILE = "hotnumbers.csv"

# Machine physics constants
BALL_DIAMETER = 38.10e-3  # meters (38.1mm)
BALL_MASS = 3.2e-3  # kg (3.2g)
CHAMBER_DIAMETER = 0.5  # meters (50cm)
AIR_PRESSURE = 17236.89  # Pascals (2.5 psi)


class PowerballGenerator:
    def __init__(self):
        self.hot_main_numbers = HOT_MAIN_NUMBERS
        self.hot_powerballs = HOT_POWERBALLS
        self.previous_results = []
        self.previous_powerballs = []
        self._load_hot_numbers()
        self._fetch_historical_results()
        self.machine_main_probs, self.machine_powerball_probs = self._calculate_machine_biases()

    def _calculate_machine_biases(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate probability biases from physical machine parameters."""
        # 1. Base geometric probability
        ball_volume = (4 / 3) * np.pi * (BALL_DIAMETER / 2) ** 3
        chamber_volume = np.pi * (CHAMBER_DIAMETER / 2) ** 2 * BALL_DIAMETER * 3
        geometric_prob = 1 / (chamber_volume / ball_volume)

        # 2. Airflow effects
        cross_section = np.pi * (BALL_DIAMETER / 2) ** 2
        force = AIR_PRESSURE * cross_section
        acceleration = force / BALL_MASS
        max_velocity = acceleration * 35  # 35s mixing time
        velocity_dist = uniform(loc=0, scale=max_velocity)

        # 3. Introduce small biases
        np.random.seed(42)  # Reproducibility

        # Main balls: ±1% mass variations, ±2% positional
        mass_variations = np.random.normal(BALL_MASS, BALL_MASS * 0.01, 40)
        positional_bias = np.random.permutation(np.linspace(0.98, 1.02, 40))
        main_probs = geometric_prob * velocity_dist.pdf(0.5 * max_velocity) * positional_bias
        main_probs *= (1 + (force / mass_variations - acceleration) / acceleration)
        main_probs /= main_probs.sum()

        # Powerballs: ±1% bias
        powerball_probs = geometric_prob * velocity_dist.pdf(0.5 * max_velocity) * np.random.uniform(0.99, 1.01, 10)
        powerball_probs /= powerball_probs.sum()

        return main_probs, powerball_probs

    def _load_hot_numbers(self) -> None:
        """Load hot numbers from CSV file if available."""
        try:
            if Path(HOT_NUMBERS_FILE).exists():
                data = pd.read_csv(HOT_NUMBERS_FILE)
                if "Number" in data.columns:
                    self.hot_main_numbers = data["Number"].tolist()
                    logger.info(f"Loaded hot numbers from {HOT_NUMBERS_FILE}")
        except Exception as e:
            logger.warning(f"Error loading hot numbers: {e}. Using defaults.")

    def _fetch_historical_results(self) -> None:
        """Fetch historical results to avoid duplicates."""
        try:
            response = requests.get(RESULTS_URL, timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.content, 'html.parser')

            for span in soup.find_all('span'):
                text = span.get_text(strip=True)
                if 'Lotto:' in text:
                    lotto_numbers = [int(num) for num in
                                     text.replace('Lotto:', '').replace(u'\xa0', ' ').strip().split(',') if
                                     num.strip().isdigit()]
                    if len(lotto_numbers) == 6:
                        self.previous_results.append(lotto_numbers)
                elif 'Powerball:' in text:
                    powerball = text.replace('Powerball:', '').strip()
                    if powerball.isdigit():
                        self.previous_powerballs.append(int(powerball))

            logger.info(f"Loaded {len(self.previous_results)} historical results")
        except Exception as e:
            logger.error(f"Error fetching results: {e}")

    def _generate_weighted_main_numbers(self) -> List[int]:
        """Generate main numbers with hot + machine biases."""
        weights = np.array([
            (HOT_NUMBER_WEIGHT if num in self.hot_main_numbers else BASE_WEIGHT) * self.machine_main_probs[num - 1]
            for num in MAIN_NUMBERS_RANGE
        ])
        weights /= weights.sum()

        return np.random.choice(list(MAIN_NUMBERS_RANGE), size=6, replace=False, p=weights).tolist()

    def _generate_weighted_powerball(self) -> int:
        """Generate powerball with hot + machine biases."""
        weights = np.array([
            (HOT_NUMBER_WEIGHT if num in self.hot_powerballs else BASE_WEIGHT) * self.machine_powerball_probs[num - 1]
            for num in POWERBALL_RANGE
        ])
        weights /= weights.sum()
        return int(np.random.choice(list(POWERBALL_RANGE), p=weights))

    def generate_numbers(self) -> Tuple[List[int], int]:
        """Generate a validated set of numbers."""
        for _ in range(MAX_GENERATION_ATTEMPTS):
            main_numbers = sorted(self._generate_weighted_main_numbers())
            if len(set(main_numbers) & set(self.hot_main_numbers)) >= MIN_HOT_NUMBERS:
                powerball = self._generate_weighted_powerball()
                return main_numbers, powerball

        # Fallback if hot number requirement can't be met
        return sorted(np.random.choice(list(MAIN_NUMBERS_RANGE), size=6, replace=False)), np.random.choice(
            list(POWERBALL_RANGE))

    def is_previous_draw(self, numbers: List[int]) -> bool:
        """Check for duplicate draws."""
        return any(set(result) == set(numbers) for result in self.previous_results)

    def generate_multiple_sets(self, num_sets: int) -> List[Tuple[List[int], int, bool]]:
        """Generate multiple sets with validation."""
        results = []
        for _ in range(num_sets):
            numbers, powerball = self.generate_numbers()
            results.append((numbers, powerball, self.is_previous_draw(numbers)))
        return results


def display_results(results: List[Tuple[List[int], int, bool]], num_sets: int) -> None:
    """Pretty-print results."""
    print("\n" + "=" * 50)
    print(f"POWERBALL NUMBER GENERATOR - {num_sets} SETS (HOT + MACHINE-BIASED)")
    print("=" * 50 + "\n")

    for i, (numbers, powerball, is_previous) in enumerate(results, 1):
        status = "PREVIOUSLY DRAWN" if is_previous else "New Numbers"
        print(f"Set {i:2d}: {status} - {[str(i) for i in numbers]} Powerball: {powerball}")

    print("\n" + "=" * 50)
    print("Note: Combines historical hot numbers with machine physics biases")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate Powerball numbers with physics-based biases")
    parser.add_argument("-n", "--num-sets", type=int, default=DEFAULT_NUM_SETS, help="Number of sets to generate")
    args = parser.parse_args()

    generator = PowerballGenerator()
    results = generator.generate_multiple_sets(args.num_sets)
    display_results(results, args.num_sets)


if __name__ == "__main__":
    main()
