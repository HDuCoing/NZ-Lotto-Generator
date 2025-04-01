import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import random

# Load hot numbers
data = pd.read_csv("hotnumbers.csv")
hot_numbers = data["Number"].tolist()

# Fetch Lotto results from your preferred website
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


# Fibonacci function
def fib(n):
    a, b = 0, 1
    fib_nums = []
    for _ in range(n):
        fib_nums.append(a)
        a, b = b, a + b
    return fib_nums


def generate_numbers():
    fib_nums = fib(10)
    selected_numbers = list(set(fib_nums + hot_numbers))  # Merge Fibonacci and hot numbers

    # Ensure weights align with 1-40 range
    weights = [0.020] * 40
    for num in selected_numbers:
        if 1 <= num <= 40:
            weights[num - 1] = 0.030  # Increase probability for selected numbers

    # Normalize weights to sum to 1
    weights = np.array(weights)
    weights /= weights.sum()

    # Generate unique lotto numbers
    new_lotto_numbers = np.random.choice(range(1, 41), size=6, replace=False, p=weights)
    random_powerball_num = random.choice(range(1, 11))

    return new_lotto_numbers.tolist(), random_powerball_num


# Generate 30 sets of numbers and check for previous draws
for _ in range(30):
    lotto, powerball = generate_numbers()
    if any(set(result) == set(lotto) for result in previous_results):
        print("PREVIOUSLY DRAWN:", lotto, "Powerball:", powerball)
    else:
        print("New Numbers:", lotto, "Powerball:", powerball)
