import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests

# Hot numbers based on analysis
hot_main_numbers = [23, 32, 36, 17, 40, 13, 5]  # Most frequent main numbers
hot_powerballs = [1, 5, 6, 9]  # Most frequent Powerball numbers

# Load hot numbers from CSV (if you still want to use this)
try:
    data = pd.read_csv("hotnumbers.csv")
    hot_numbers = data["Number"].tolist()
except FileNotFoundError:
    hot_numbers = hot_main_numbers  # Fallback to our analysis

# Fetch Lotto results from historical numbers website
url = 'http://www.lottoshop.co.nz/my-lotto-results-nz'
response = requests.get(url)

if response.status_code != 200:
    print("Error fetching lotto results. Check the URL or try again later.")
    exit()

soup = BeautifulSoup(response.content, 'html.parser')

previous_results = []
previous_powerballs = []

# Extract lotto numbers (assuming format remains consistent)
for span in soup.find_all('span'):
    text = span.get_text(strip=True)

    if 'Lotto:' in text:
        lotto_text = text.replace('Lotto:', '').replace(u'\xa0', ' ').strip()
        lotto_numbers = [int(num) for num in lotto_text.split(',') if num.isdigit()]
        if lotto_numbers:
            previous_results.append(lotto_numbers)

    elif 'Bonus:' in text:
        bonus_text = text.replace('Bonus:', '').strip()
        if bonus_text.isdigit():
            bonus_number = int(bonus_text)

    elif 'Powerball:' in text:
        powerball_text = text.replace('Powerball:', '').strip()
        if powerball_text.isdigit():
            previous_powerballs.append(int(powerball_text))


# Generate numbers with preference for hot numbers
def generate_numbers():
    # Create weighted probabilities
    all_numbers = list(range(1, 41))
    weights = np.ones(40) * 1.0  # Base weight

    # Increase weight for hot numbers
    for num in hot_main_numbers:
        weights[num - 1] = 3.0  # 3x more probability

    # Normalize weights
    weights /= weights.sum()

    # Generate unique lotto numbers
    while True:
        new_lotto_numbers = np.random.choice(
            all_numbers,
            size=6,
            replace=False,
            p=weights
        )
        # Ensure we have at least 2 hot numbers in the selection
        if len(set(new_lotto_numbers) & set(hot_main_numbers)) >= 2:
            break

    # Powerball with preference for hot powerballs
    powerball_weights = [3.0 if n in hot_powerballs else 1.0 for n in range(1, 11)]
    powerball_weights = np.array(powerball_weights)
    powerball_weights /= powerball_weights.sum()

    random_powerball_num = np.random.choice(
        range(1, 11),
        p=powerball_weights
    )

    return sorted(new_lotto_numbers.tolist()), random_powerball_num


# Generate 30 sets of numbers and check for previous draws
for _ in range(30):
    lotto, powerball = generate_numbers()
    if any(set(result) == set(lotto) for result in previous_results):
        print("PREVIOUSLY DRAWN:", lotto, "Powerball:", powerball)
    else:
        print("New Numbers:", lotto, "Powerball:", powerball)