import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import random

# Hot numbers based on Mega Millions historical analysis (2010-2023)
# Most frequent main numbers (1-70)
hot_main_numbers = [17, 31, 10, 20, 39, 4, 23, 14, 48, 70, 3, 46, 29, 64, 53]
# Most frequent Mega Balls (1-25)
hot_megaballs = [22, 9, 24, 11, 19, 3, 10, 17, 4]

# Load hot numbers from CSV (if available)
try:
    data = pd.read_csv("mmhotnumbers.csv")
    hot_numbers = data["Number"].tolist()
except FileNotFoundError:
    hot_numbers = hot_main_numbers  # Fallback to our analysis

# Fetch Mega Millions results
url = 'https://www.megamillions.com/Winning-Numbers/Previous-Drawings.aspx'
headers = {'User-Agent': 'Mozilla/5.0'}  # Some sites require user-agent
try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Error fetching Mega Millions results: {e}")
    exit()

soup = BeautifulSoup(response.content, 'html.parser')
previous_results = []
previous_megaballs = []

# Extract winning numbers (adjust selectors as needed)
drawings = soup.find_all("div", class_="drawing")
for drawing in drawings:
    try:
        # Main numbers (5 white balls)
        main_numbers = [int(num.text) for num in drawing.find_all("li", class_="ball")[:5]]
        # Mega Ball (gold ball)
        mega_ball = int(drawing.find("li", class_="megaball").text)

        previous_results.append(main_numbers)
        previous_megaballs.append(mega_ball)
    except (AttributeError, ValueError):
        continue


def generate_numbers():
    # Weighted selection for main numbers (1-70)
    main_weights = np.ones(70) * 1.0  # Base weight

    # Boost hot numbers (3x more likely)
    for num in hot_main_numbers:
        if 1 <= num <= 70:
            main_weights[num - 1] = 3.0

    # Normalize weights
    main_weights /= main_weights.sum()

    # Ensure we get 5 unique numbers with at least 2 hot numbers
    while True:
        main_numbers = np.random.choice(
            range(1, 71),
            size=5,
            replace=False,
            p=main_weights
        )
        # Check for at least 2 hot numbers
        if len(set(main_numbers) & set(hot_main_numbers)) >= 2:
            break

    # Weighted selection for Mega Ball (1-25)
    megaball_weights = np.ones(25) * 1.0
    for num in hot_megaballs:
        if 1 <= num <= 25:
            megaball_weights[num - 1] = 3.0
    megaball_weights /= megaball_weights.sum()

    mega_ball = np.random.choice(
        range(1, 26),
        p=megaball_weights
    )

    return sorted(main_numbers.tolist()), mega_ball


# Generate 30 sets of numbers
print("\n=== Mega Millions Number Generator ===")
print("Prioritizing historically frequent numbers:\n")
print(f"Hot Main Numbers: {sorted(hot_main_numbers)}")
print(f"Hot Mega Balls: {sorted(hot_megaballs)}\n")

for i in range(1, 31):
    lotto, mega_ball = generate_numbers()
    # Check if this combination has been drawn before
    is_previous = any(
        set(result) == set(lotto) and mb == mega_ball
        for result, mb in zip(previous_results, previous_megaballs)
    )

    if is_previous:
        print(f"{i:2d}. PREVIOUSLY DRAWN: {lotto} + Mega Ball: {mega_ball}")
    else:
        print(f"{i:2d}. New Numbers: {lotto} + Mega Ball: {mega_ball}")