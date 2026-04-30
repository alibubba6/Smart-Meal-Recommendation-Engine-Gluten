# Smart Meal Recommendation Engine (SMRE): Gluten Pipeline

An AI-powered hybrid meal recommendation engine designed to provide safe, personalized, and gluten-aware recipes. This system combines **deterministic rule-based auditing** with **dynamic API verification** and **generative AI analysis** to ensure celiac-safe meal planning.

## Live Application
Access the deployed engine here:
**[Smart Meal Recommendation Engine (SMRE) - Gluten Pipeline](https://smart-meal-recommendation-engine-gluten.streamlit.app/)**

## Overview
The SMRE Gluten Pipeline solves the challenge of identifying "hidden" gluten in complex recipes. By cross-referencing local datasets with the **USDA FoodData Central API**, **Google Custom Search API**, and the **Gemini 3 Flash** model, the engine provides a multi-layered risk assessment for every ingredient.

## Tech Stack
* **Frontend:** Streamlit.
* **Language:** Python 3.x.
* **Data Science:** Pandas, NumPy, Regex, AST.
* **APIs:**
    * **USDA FoodData Central:** For granular ingredient component analysis and red-flag detection.
    * **Google Custom Search (JSON API):** For real-time web verification snippets.
    * **Google Gemini 3 Flash:** For advanced reasoning, safety verdicts, and intelligent substitution discovery.
* **Deployment:** Streamlit Cloud / GitHub.

## System Architecture
The engine utilizes a four-stage evaluation process for ingredient safety:

1. **Deterministic Lookup:** Scans `gluten_lookup_table_scored.csv` for known gluten aliases using optimized string matching.
2. **USDA API Deep Dive:** If the local check is inconclusive, the system queries the USDA database to inspect descriptions and ingredient lists for specific red-flag keywords like "maltodextrin," "brewer's yeast," or "triticale".
3. **Web-Informed Research:** If a risk is suspected, the system fetches real-time data from the Google Search API to identify modern manufacturing risks.
4. **Generative AI Analysis:** The **Gemini 3 Flash** model analyzes the gathered context to provide a final safety verdict and a human-like substitution recommendation.

## Features
* **Enhanced Risk Scoring:** Categorizes ingredients into a 4-tier scale: Likely Safe (0), Possible Risk (1), Risk (2), and High Risk (3).
* **Intelligent Substitution:** Uses a hybrid of hardcoded mappings and AI-generated suggestions (e.g., swapping soy sauce for certified gluten-free tamari).
* **Smart Parsing:** Employs Regex and Abstract Syntax Trees (AST) to normalize recipe data by removing measurements (e.g., "cups," "tbsp") and preparation notes.
* **Visual Audit Trail:** Provides a UI with status icons (🟢 to 🔴) and expandable details for every audited ingredient.

## Repository Structure
* `SMRE10.py`: The core Streamlit application and multi-stage logic.
* `requirements.txt`: Includes `google-genai`, `google-api-python-client`, `requests`, and `pandas`.
* `gluten_lookup_table_scored.csv`: Local database of gluten aliases and associated risk scores.
* `recipes.csv`: Database of diverse meal options.

## Setup & Installation
1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/alibubba6/Smart-Meal-Recommendation-Engine-Gluten.git](https://github.com/alibubba6/Smart-Meal-Recommendation-Engine-Gluten.git)

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
