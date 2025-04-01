# Lottery Number Generator - Powerball & Mega Millions

## 📊 Probability-Based Number Generators
Disclaimer: This code is for personal use and started as a self written code, I then used A.I. to help me incorporate the crazy idea of measuring probability based on the machines measurements.

#### These scripts generate lottery numbers using:
- **Historical hot numbers** (most frequently drawn)
- **Physics-based machine biases** (ball size, chamber dimensions, airflow)
- **Weighted probability distributions**

## 🎰 Key Features

### For Both Games:
- ✅ Hot number weighting (3x more likely)
- ✅ Machine physics probability modeling
- ✅ Duplicate draw checking
- ✅ CSV configurable hot numbers
- ✅ Command-line control

### Powerball (NZ):
- Main numbers: 1-40 (pick 6)
- Powerball: 1-10
- Hot mains: [23, 32, 36, 17, 40, 13, 5]
- Hot Powerballs: [1, 5, 6, 9]

### Mega Millions (USA):
- Main numbers: 1-70 (pick 5)
- Mega Ball: 1-25
- Hot mains: [17, 31, 10, 20, 39, 4, 23, 14, 48, 70, 3, 46, 29, 64, 53]
- Hot MegaBalls: [22, 9, 24, 11, 19, 3, 10, 17, 4]

## ⚙️ Usage
```bash
python nzlottogen.py -n 10  # Generate 10 Powerball sets
python megamillions.py -n 15  # Generate 15 Mega Millions sets