# Lottery Number Generators

These tools generate lottery numbers by combining **historical frequency analysis** with **weighted probability systems** to improve your odds *(while remembering that all lotteries remain games of pure chance)*.

---
How to use:
* Simply run either nzlottogen.py or megamillionsgen.py

## NZ Lotto Powerball Generator

### Key Rules
- **Main Numbers:** 6 numbers from 1–40  
- **Powerball:** 1 number from 1–10  

### 🔥 Hot Numbers (Based on Historical Data)
| Type           | Most Frequent Numbers               |
|----------------|-------------------------------------|
| Main Numbers   | 23, 32, 36, 17, 40, 13, 5          |
| Powerball      | 1, 5, 6, 9                          |

### 📊 Probability Model
**Weighted Selection:**
- Base weight for all numbers: `1.0`  
- Hot numbers get `3x` weight (`3.0`)  
- Probabilities normalize to 100%:  
  ```python
  weights /= np.sum(weights)  # Ensures ∑(probabilities) = 1

## USA Mega Millions Generator

### Key Rules
- **Main Numbers:** 5 numbers from 1–70  
- **Mega Ball:** 1 number from 1–25  
- **Draw Days:** Tuesday and Friday  

### 🔥 Hot Numbers (Based on Historical Data)
| Type           | Most Frequent Numbers (Last 5 Years) |
|----------------|--------------------------------------|
| Main Numbers   | 17, 31, 10, 20, 39, 4, 23, 14, 48   |
| Mega Ball      | 22, 9, 24, 11, 19                   |
| Least Drawn    | 65, 66, 67, 68, 69, 70 (Main)       |
|                | 1, 2, 3, 25 (Mega Ball)             |

### 📊 Probability Model
**Weighted Selection System:**
- Base weight for all numbers: `1.0`  
- Hot numbers get `3.5x` weight (`3.5`)  
- Cold numbers get `0.7x` weight (`0.7`)  
- Probabilities normalize to 100%:  
  ```python
  weights = np.where(is_hot, 3.5, np.where(is_cold, 0.7, 1.0))
  weights /= np.sum(weights)  # Normalization