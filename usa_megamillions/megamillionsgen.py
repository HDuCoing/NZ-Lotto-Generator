import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import random

# Load hot numbers
data = pd.read_csv("mmhotnumbers.csv")
hot_numbers = data["Number"].tolist()

# Fetch Mega Millions results
url = 'https://www.megamillions.com/Winning-Numbers/Previous-Drawings.aspx'
response = requests.get(url)

if response.status_code != 200:
    print("Error fetching Mega Millions results. Check the URL or try again later.")
    exit()

soup = BeautifulSoup(response.content, 'html.parser')

previous_results = []
previous_megaballs = []

# Extract winning numbers from table rows
table = soup.find("table", {"class": "table"})  # Adjust class if needed
if table:
    rows = table.find_all("tr")[1:]  # Skip header row

    for row in rows:
        columns = row.find_all("td")
        if len(columns) >= 2:  # Ensure valid row
            main_numbers = [int(num.text.strip()) for num in columns[1].find_all("span", {"class": "balls"})]
            mega_ball = int(columns[2].find("span", {"class": "megaball"}).text.strip())

            if main_numbers:
                previous_results.append(main_numbers)
                previous_megaballs.append(mega_ball)

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

    # Adjust range for Mega Millions (1-70)
    weights = [0.014] * 70
    for num in selected_numbers:
        if 1 <= num <= 70:
            weights[num - 1] = 0.020  # Increase probability for selected numbers

    # Normalize weights to sum to 1
    weights = np.array(weights)
    weights /= weights.sum()

    # Generate unique Mega Millions numbers
    main_numbers = np.random.choice(range(1, 71), size=5, replace=False, p=weights)
    mega_ball = random.choice(range(1, 26))  # Mega Ball (1-25)

    return main_numbers.tolist(), mega_ball

# Generate 30 sets of numbers and check for previous draws
for _ in range(30):
    lotto, mega_ball = generate_numbers()
    if any(set(result) == set(lotto) for result in previous_results):
        print("PREVIOUSLY DRAWN:", lotto, "Mega Ball:", mega_ball)
    else:
        print("New Numbers:", lotto, "Mega Ball:", mega_ball)