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

# Constants for Mega Millions (USA)
HOT_MAIN_NUMBERS = [17, 31, 10, 20, 39, 4, 23, 14, 48, 70, 3, 46, 29, 64, 53]  # Most frequent main numbers
HOT_MEGABALLS = [22, 9, 24, 11, 19, 3, 10, 17, 4]  # Most frequent Mega Balls
MAIN_NUMBERS_RANGE = range(1, 71)  # Mega Millions main numbers are 1-70
MEGABALL_RANGE = range(1, 26)  # Mega Ball numbers are 1-25
HOT_NUMBER_WEIGHT = 3.0  # Weight multiplier for hot numbers
BASE_WEIGHT = 1.0
MIN_HOT_NUMBERS = 2  # Minimum hot numbers per set
MAX_GENERATION_ATTEMPTS = 1000
REQUEST_TIMEOUT = 10  # seconds
DEFAULT_NUM_SETS = 10
RESULTS_URL = 'https://www.megamillions.com/Winning-Numbers/Previous-Drawings.aspx'
HOT_NUMBERS_FILE = "mmhotnumbers.csv"

# Machine physics constants (adjusted for Mega Millions machine specs)
BALL_DIAMETER = 47.6e-3  # meters (47.6mm - Mega Millions uses larger balls)
BALL_MASS = 4.5e-3  # kg (4.5g - heavier than Powerball)
CHAMBER_DIAMETER = 0.6  # meters (60cm - slightly larger chamber)
AIR_PRESSURE = 17236.89  # Pascals (2.5 psi - same as Powerball)


class MegaMillionsGenerator:
    def __init__(self):
        self.hot_main_numbers = HOT_MAIN_NUMBERS
        self.hot_megaballs = HOT_MEGABALLS
        self.previous_results = []
        self.previous_megaballs = []
        self._load_hot_numbers()
        self._fetch_historical_results()
        self.machine_main_probs, self.machine_megaball_probs = self._calculate_machine_biases()

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
        mass_variations = np.random.normal(BALL_MASS, BALL_MASS * 0.01, 70)
        positional_bias = np.random.permutation(np.linspace(0.98, 1.02, 70))
        main_probs = geometric_prob * velocity_dist.pdf(0.5 * max_velocity) * positional_bias
        main_probs *= (1 + (force / mass_variations - acceleration) / acceleration)
        main_probs /= main_probs.sum()

        # Mega Balls: ±1% bias
        megaball_probs = geometric_prob * velocity_dist.pdf(0.5 * max_velocity) * np.random.uniform(0.99, 1.01, 25)
        megaball_probs /= megaball_probs.sum()

        return main_probs, megaball_probs

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
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(RESULTS_URL, headers=headers, timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract winning numbers from Mega Millions website
            drawings = soup.find_all("div", class_="drawing")
            for drawing in drawings:
                try:
                    # Main numbers (5 white balls)
                    main_numbers = [int(num.text) for num in drawing.find_all("li", class_="ball")[:5]]
                    # Mega Ball (gold ball)
                    megaball = int(drawing.find("li", class_="megaball").text)

                    self.previous_results.append(main_numbers)
                    self.previous_megaballs.append(megaball)
                except (AttributeError, ValueError):
                    continue

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

        return np.random.choice(list(MAIN_NUMBERS_RANGE), size=5, replace=False, p=weights).tolist()

    def _generate_weighted_megaball(self) -> int:
        """Generate megaball with hot + machine biases."""
        weights = np.array([
            (HOT_NUMBER_WEIGHT if num in self.hot_megaballs else BASE_WEIGHT) * self.machine_megaball_probs[num - 1]
            for num in MEGABALL_RANGE
        ])
        weights /= weights.sum()
        return int(np.random.choice(list(MEGABALL_RANGE), p=weights))

    def generate_numbers(self) -> Tuple[List[int], int]:
        """Generate a validated set of numbers."""
        for _ in range(MAX_GENERATION_ATTEMPTS):
            main_numbers = sorted(self._generate_weighted_main_numbers())
            if len(set(main_numbers) & set(self.hot_main_numbers)) >= MIN_HOT_NUMBERS:
                megaball = self._generate_weighted_megaball()
                return main_numbers, megaball

        # Fallback if hot number requirement can't be met
        return sorted(np.random.choice(list(MAIN_NUMBERS_RANGE), size=5, replace=False)), np.random.choice(
            list(MEGABALL_RANGE))

    def is_previous_draw(self, numbers: List[int], megaball: int) -> bool:
        """Check for duplicate draws."""
        return any(set(result) == set(numbers) and mb == megaball
               for result, mb in zip(self.previous_results, self.previous_megaballs))

    def generate_multiple_sets(self, num_sets: int) -> List[Tuple[List[int], int, bool]]:
        """Generate multiple sets with validation."""
        results = []
        for _ in range(num_sets):
            numbers, megaball = self.generate_numbers()
            results.append((numbers, megaball, self.is_previous_draw(numbers, megaball)))
        return results


def display_results(results: List[Tuple[List[int], int, bool]], num_sets: int) -> None:
    """Pretty-print results."""
    print("\n" + "=" * 50)
    print(f"MEGA MILLIONS NUMBER GENERATOR - {num_sets} SETS (HOT + MACHINE-BIASED)")
    print("=" * 50 + "\n")

    for i, (numbers, megaball, is_previous) in enumerate(results, 1):
        status = "PREVIOUSLY DRAWN" if is_previous else "New Numbers"
        print(f"Set {i:2d}: {status} - {[str(i) for i in numbers]} Mega Ball: {megaball}")

    print("\n" + "=" * 50)
    print("Note: Combines historical hot numbers with machine physics biases")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate Mega Millions numbers with physics-based biases")
    parser.add_argument("-n", "--num-sets", type=int, default=DEFAULT_NUM_SETS, help="Number of sets to generate")
    args = parser.parse_args()

    generator = MegaMillionsGenerator()
    results = generator.generate_multiple_sets(args.num_sets)
    display_results(results, args.num_sets)


if __name__ == "__main__":
    main()