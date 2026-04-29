import streamlit as st
import pandas as pd
import gdown
import os
import re
import ast
from pathlib import Path
import streamlit as st
import requests
from googleapiclient.discovery import build

# --- API CONFIGURATION ---
# Access keys from your .streamlit/secrets.toml
USDA_API_KEY = st.secrets["USDA_API_KEY"]
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
# Note: Google Search API also needs a Search Engine ID (CX)
GOOGLE_CSE_ID = st.secrets.get("GOOGLE_CSE_ID", "") 

def check_gluten_via_google(ingredient_name):
    """Searches the web to see if a specific ingredient contains gluten."""
    api_key = st.secrets["GOOGLE_API_KEY"]
    cse_id = st.secrets["GOOGLE_CSE_ID"]
    
    service = build("customsearch", "v1", developerKey=api_key)
    query = f"is {ingredient_name} gluten free celiac safe"
    
    # Execute search
    res = service.cse().list(q=query, cx=cse_id, num=3).execute()
    
    # Return the snippets from the top 3 results
    return [item['snippet'] for item in res.get('items', [])]

def check_usda_gluten(ingredient_name):
    """
    Queries USDA FoodData Central to check for gluten-containing keywords 
    in the ingredient description or ingredients list.
    """
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}"
    payload = {"query": ingredient_name, "pageSize": 1}
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        if data.get("foods"):
            food_item = data["foods"][0]
            description = food_item.get("description", "").lower()
            ingredients_list = food_item.get("ingredients", "").lower()
            
            # Search for gluten red flags
            red_flags = ["wheat", "barley", "rye", "malt", "brewer's yeast"]
            for flag in red_flags:
                if flag in description or flag in ingredients_list:
                    return True, f"Detected {flag} in USDA data."
                    
        return False, "No obvious gluten detected via USDA."
    except Exception as e:
        return None, f"USDA API Error: {e}"

def get_google_substitution(ingredient_name):
    """
    Uses Google Custom Search API to find gluten-free alternatives.
    """
    search_query = f"gluten free substitute for {ingredient_name}"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": search_query,
        "num": 1
    }
    
    try:
        response = requests.get(url, params=params)
        results = response.json()
        if "items" in results:
            # Return the snippet from the first search result
            return results["items"][0]["snippet"]
        return "No substitution found via Google."
    except Exception as e:
        return f"Google API Error: {e}"

# --- UPDATED EVALUATION LOGIC ---
def evaluate_ingredient(ingredient_text):
    # 1. Keep your existing local lookup logic as a first pass
    matches = lookup_matches(ingredient_text)
    
    # 2. Call USDA API for a deeper check
    usda_found, usda_msg = check_usda_gluten(ingredient_text)
    
    # Determine risk
    risk_score = 0
    if matches:
        risk_score = max(int(m.get("risk_score", 0)) for m in matches)
    if usda_found:
        risk_score = max(risk_score, 2) # Elevate risk if USDA confirms wheat/barley/rye
        
    # 3. If high risk, use Google to find a modern substitution
    sub = "None needed."
    if risk_score >= 1:
        # Check hardcoded SUBSTITUTIONS first, then fallback to Google
        sub = next((SUBSTITUTIONS[k] for k in SUBSTITUTIONS if k in ingredient_text.lower()), None)
        if not sub:
            sub = get_google_substitution(ingredient_text)
            
    return {
        "ingredient": ingredient_text, 
        "risk_score": risk_score,
        "substitution": sub,
        "usda_note": usda_msg
    }
   
@st.cache_data
def load_data():
    """Loads datasets directly from the repository and prepares lookup structures."""
    recipes_path = "recipes.csv"
    lookup_path = "gluten_lookup_table_scored.csv"
    
    # 1. Check if files exist
    if not os.path.exists(recipes_path) or not os.path.exists(lookup_path):
        st.error("Data files not found. Please ensure recipes.csv and gluten_lookup_table_scored.csv are in the repository.")
        return pd.DataFrame(), pd.DataFrame()
    
    # 2. Load the data
    recipes_df = pd.read_csv(recipes_path)
    lookup_df = pd.read_csv(lookup_path)

    # 3. Prep lookup structures (This must happen BEFORE the return)
    lookup_df["alias_norm"] = lookup_df["alias"].astype(str).str.lower().str.strip()
    
    # Sort by length descending to match longer phrases first (e.g., "whole wheat flour" before "wheat")
    lookup_df = lookup_df.sort_values(
        by="alias_norm", 
        key=lambda s: s.str.len(), 
        ascending=False
    ).reset_index(drop=True)
    
    return recipes_df, lookup_df

# --- INITIALIZE APP ---
# This part stays OUTSIDE the function so it runs when the app starts
recipes_df, lookup_df = load_data()
SUBSTITUTIONS = {
    "soy sauce": "Use certified gluten-free tamari.",
    "teriyaki sauce": "Use a certified gluten-free teriyaki sauce or coconut aminos.",
    "malt vinegar": "Use apple cider vinegar or rice vinegar if appropriate.",
    "malt": "Replace with a certified gluten-free flavoring or omit if possible.",
    "malt extract": "Use a certified gluten-free flavoring or omit if possible.",
    "malt syrup": "Use molasses, honey, or a certified gluten-free syrup if appropriate.",
    "brewer's yeast": "Use certified gluten-free nutritional yeast if appropriate.",
    "modified food starch": "Use cornstarch, arrowroot, or tapioca starch if the recipe allows.",
    "bouillon": "Use a certified gluten-free broth or stock.",
    "miso": "Use a certified gluten-free miso or chickpea miso.",
    "wheat flour": "Use a certified 1:1 gluten-free flour blend.",
    "all-purpose flour": "Use a certified 1:1 gluten-free flour blend.",
    "bread flour": "Use a gluten-free bread flour blend if baking.",
    "graham flour": "Use a gluten-free flour blend and adjust sweetness if needed.",
    "semolina": "Use certified gluten-free pasta or rice-based pasta.",
    "durum": "Use certified gluten-free pasta or rice-based pasta.",
    "spelt": "Use a certified gluten-free flour blend or gluten-free grain alternative.",
    "farro": "Use rice, quinoa, or certified gluten-free sorghum.",
    "kamut": "Use quinoa, brown rice, or a certified gluten-free grain.",
    "couscous": "Use quinoa or gluten-free couscous alternative.",
    "panko": "Use gluten-free panko or crushed gluten-free crackers.",
    "breadcrumbs": "Use gluten-free breadcrumbs.",
    "flour tortilla": "Use a certified gluten-free tortilla or corn tortilla.",
    "seitan": "Use tofu, tempeh, mushrooms, or chicken depending on recipe context.",
    "roux": "Use butter and gluten-free flour, or a cornstarch slurry depending on the recipe."
}

def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_ingredient(ingredient: str) -> str:
    text = normalize_text(ingredient)
    # Remove measurements and units
    text = re.sub(r"^\d+[\/\d\.]*\s*", "", text)
    text = re.sub(r"\b(cup|cups|tbsp|tablespoon|tsp|teaspoon|oz|lb|gram|g|kg|ml|l|pinch|clove|slice|slices)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def parse_maybe_list(value):
    if isinstance(value, list): return value
    try:
        parsed = ast.literal_eval(str(value))
        if isinstance(parsed, list): return parsed
    except:
        pass
    return [x.strip() for x in str(value).split(",") if x.strip()]

def lookup_matches(ingredient_text: str, lookup_df):
    norm = clean_ingredient(ingredient_text)
    matches = []
    
    for _, row in lookup_df.iterrows():
        # Keep the str() here—it ensures numerical alias names don't crash the script
        if str(row["alias_norm"]) in norm:
            matches.append(row.to_dict())
    return matches

def evaluate_ingredient(ingredient_text, lookup_df):
    matches = lookup_matches(ingredient_text, lookup_df)
    
    # Default: Score 0 (Safe)
    risk_score = 0
    rec_action = "allow"
    why_flagged = "No gluten detected."
    sub = "None needed."

    if matches:
        # Get highest risk match from CSV
        best_match = max(matches, key=lambda x: x.get("risk_score", 0))
        risk_score = int(best_match.get("risk_score", 0))
        rec_action = best_match.get("rec_action", "allow")
        why_flagged = best_match.get("why_flagged", "Known safe.")

        # SUBSTITUTION LOGIC based on 0-3 scale
        if risk_score >= 1:
            # 1. Try local dictionary first
            sub = next((SUBSTITUTIONS[k] for k in SUBSTITUTIONS if k in ingredient_text.lower()), None)
            
            # 2. If Risk 2 or 3 and no local sub, use Google API
            if not sub and risk_score >= 2:
                sub = get_google_substitution(ingredient_text)
            
            # 3. Fallback text if still no sub found
            if not sub:
                sub = "Check label for gluten-free certification."

    return {
        "ingredient": ingredient_text, 
        "risk_score": risk_score,
        "rec_action": rec_action,
        "why_flagged": why_flagged,
        "substitution": sub
    }

# --- STREAMLIT UI ---
st.set_page_config(page_title="SMRE Gluten Audit", layout="wide")
st.title("🛡️ Smart Meal Recommendation Engine (SMRE) Gluten Pipeline")

# --- One-sentence description below the title ---
st.markdown("An automated auditing system designed to identify gluten-containing ingredients and suggest safe, high-quality alternatives for celiac-safe meal planning.")

recipes_df, lookup_df = load_data()

st.sidebar.header("Controls")
if st.sidebar.button("Random Recipe"):
    # --- Professional Disclaimer below the button ---
    st.sidebar.caption("⚠️ **Disclaimer:** This engine utilizes AI and automated data retrieval. While designed for accuracy, results should be verified for clinical safety; always consult product labels for strict dietary requirements.")
    
    recipe = recipes_df.sample(1).iloc[0]
    
    st.header(f"Recipe: {recipe.get('title', 'Untitled')}")
    
    # ... rest of your existing display logic ...
    ingredients = parse_maybe_list(recipe.get("ingredients", []))
    results = [evaluate_ingredient(ing, lookup_df) for ing in ingredients]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Ingredients Audit")
        for r in results:
            score = r['risk_score']
        # Display the specific score in the header
            with st.expander(f"{r['ingredient']} (Risk Score: {score})"):
                st.write(f"**Action:** {r['rec_action'].title()}")
                st.write(f"**Details:** {r['why_flagged']}")
            
                if score == 3:
                    st.error(f"🚨 **High Risk:** {r['substitution']}")
                elif score == 2:
                    st.error(f"⚠️ **Risk:** {r['substitution']}")
                elif score == 1:
                    st.warning(f"🔍 **Possible Risk:** {r['substitution']}")
                else:
                    st.success("✅ **No Gluten:** Likely Safe")
                    
    with col2:
        st.subheader("📖 Directions")
        directions = parse_maybe_list(recipe.get("directions", []))
        for i, step in enumerate(directions, 1):
            st.write(f"**{i}.** {step}")