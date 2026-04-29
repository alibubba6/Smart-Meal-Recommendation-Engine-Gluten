# Smart Meal Recommendation Engine (SMRE): Gluten Pipeline

An AI-powered hybrid meal recommendation engine designed to provide safe, personalized, and gluten-aware recipes. This system combines **deterministic rule-based auditing** with **dynamic API verification** to ensure celiac-safe meal planning.

## Overview
The SMRE Gluten Pipeline solves the challenge of identifying "hidden" gluten in complex recipes. By cross-referencing local datasets with the **USDA FoodData Central API** and **Google Custom Search API**, the engine provides a multi-layered risk assessment for every ingredient.

## Tech Stack
* **Frontend:** Streamlit
* **Language:** Python 3.x
* **Data Science:** Pandas, NumPy, Regex
* **APIs:**
    * **USDA FoodData Central:** For granular ingredient component analysis.
    * **Google Custom Search (JSON API):** For real-time web verification and modern substitution discovery.
* **Deployment:** Streamlit Cloud / GitHub

## System Architecture
The engine utilizes a three-stage evaluation process for ingredient safety:

1.  **Deterministic Lookup:** Scans a local `lookup.csv` for known gluten aliases using optimized string matching.
2.  **USDA API Deep Dive:** If the local check is inconclusive, the system queries the USDA database to inspect the "description" and "ingredients list" for red-flag keywords (wheat, barley, rye, malt, etc.).
3.  **Dynamic Substitution Engine:** If an ingredient is flagged as high-risk, the engine searches the web via Google API to find contemporary, celiac-safe alternatives (e.g., swapping soy sauce for tamari).

## Features
* **Risk Scoring:** Categorizes ingredients into "Likely Safe" (0), "Possible Risk" (1), and "High Risk" (2).
* **Automated Substitution:** Provides immediate alternatives for high-risk items.
* **Smart Parsing:** Uses Regex and Abstract Syntax Trees (AST) to clean and normalize messy recipe data (removing units like "cups," "tbsp," or "finely chopped").
* **Cloud Data Integration:** Automatically downloads and caches large recipe datasets from Google Drive via `gdown`.

## Repository Structure
* `SMRE10.py`: The core Streamlit application and logic.
* `requirements.txt`: List of necessary Python libraries.
* `lookup.csv`: Local database of gluten-containing aliases and risk scores.
* `recipes.csv`: Database of diverse meal options.

## Setup & Installation
1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/yourusername/Smart-Meal-Recommendation-Engine-Gluten.git](https://github.com/yourusername/Smart-Meal-Recommendation-Engine-Gluten.git)
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Secrets:**
    Create a `.streamlit/secrets.toml` file with your API keys:
    ```toml
    USDA_API_KEY = "your_usda_key"
    GOOGLE_API_KEY = "your_google_key"
    GOOGLE_CSE_ID = "your_search_engine_id"
    ```
4.  **Run the App:**
    ```bash
    streamlit run SMRE10.py
    ```

---

### ⚠️ Disclaimer
*This engine utilizes AI and automated data retrieval. While designed for accuracy, results should be verified for clinical safety; always consult product labels for strict dietary requirements.*

---

**Development Status:** Active Capstone Project (Expected Graduation: May 2026)