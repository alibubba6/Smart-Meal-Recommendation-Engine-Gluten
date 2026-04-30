import streamlit as st
import pandas as pd
import os
import re
import ast
from pathlib import Path
import streamlit as st
import requests
from googleapiclient.discovery import build
from google import genai
from google.genai import types


# --- API CONFIGURATION ---
# Access keys from your .streamlit/secrets.toml
USDA_API_KEY = st.secrets["USDA_API_KEY"]
GOOGLE_SEARCH_API_KEY = st.secrets["GOOGLE_SEARCH_API_KEY"]
GOOGLE_CSE_ID = st.secrets.get("GOOGLE_CSE_ID", "")
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

@st.cache_resource
def get_gemini_client():
    # Use the key from your st.secrets
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Initialize the new client
client = get_gemini_client()

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
            red_flags = [
    # Core Grains
    "wheat", "barley", "rye", "triticale", "spelt", "kamut", "farro", "durum", "bulgur",
    
    # Derivatives & Processing Terms
    "malt", "malted", "maltodextrin", "brewer's yeast", "autolyzed yeast", "yeast extract", 
    "hydrolyzed wheat protein", "vital wheat gluten", "seitan", "wheat starch", 
    
    # Flour & Meal Types
    "semolina", "couscous", "graham flour", "einkorn", "emmer", "farina", "atta", 
    "matzo", "matzah", "panko",
    
    # Specific High-Risk Additives
    "modified food starch", "modified wheat starch", "cereal protein", "binder", 
    "filler", "malt vinegar", "soy sauce", "teriyaki", "roux"
]
            for flag in red_flags:
                if flag in description or flag in ingredients_list:
                    return True, f"Detected {flag} in USDA data."
                    
        return False, "No obvious gluten detected via USDA."
    except Exception as e:
        return None, f"USDA API Error: {e}"

def check_gluten_via_google(ingredient_name):
    """
    Uses Google Custom Search API to get raw data about an ingredient's gluten status.
    This data is then passed to Gemini for analysis.
    """
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CSE_ID:
        return ["API Configuration missing (Keys or CSE ID)."]

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": f"is {ingredient_name} gluten free celiac safe",
        "num": 3
    }
    
    try:
        response = requests.get(url, params=params)
        res = response.json()
        
        # Check for the 403 Permission Denied error or other API issues
        if "error" in res:
            return [f"Google API Error: {res['error']['message']}"]
            
        # Extract snippets from search results
        if "items" in res:
            return [item['snippet'] for item in res['items']]
            
        return ["No specific search results found."]
    except Exception as e:
        return [f"Search failed: {str(e)}"]
    
   
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
    "flour": "Use gluten-free flour blend.",
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
    # 1. Local CSV Check (Part 0)
    matches = lookup_matches(ingredient_text, lookup_df)
    
    csv_score = 0
    why_flagged = "No gluten detected."
    rec_action = "allow"
    
    if matches:
        best_match = max(matches, key=lambda x: x.get("risk_score", 0))
        csv_score = int(best_match.get("risk_score", 0))
        why_flagged = best_match.get("why_flagged", "Known source.")
        rec_action = best_match.get("rec_action", "allow")

    # 2. USDA API Check (Part 1)
    # Convert the (True/False, msg) return into a numeric score
    usda_found, usda_msg = check_usda_gluten(ingredient_text)
    usda_score = 3 if usda_found else 0 # If USDA finds a red flag, it's High Risk (3)

    # 3. Determine Final Risk
    final_risk_score = max(csv_score, usda_score)
    if usda_score > csv_score:
        why_flagged = usda_msg

    # 4. Substitution & AI Logic (Parts 2 & 3)
    sub = "None needed."
    if final_risk_score >= 1:
        # Step A: Check hardcoded dictionary first (Fastest)
        sub = next((SUBSTITUTIONS[k] for k in SUBSTITUTIONS if k in ingredient_text.lower()), None)
        
        # Step B: If no hardcoded sub OR if we need deeper analysis (Researching unknowns)
        if not sub:
            try:
                snippets = check_gluten_via_google(ingredient_text)
                context = "\n".join(snippets)
            
            # Updated call for Gemini 3 Flash
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=f"Analyze gluten risk for '{ingredient_text}'. Context: {context}. Provide safety verdict and 1-sentence sub."
                )
            
            # Use .text to get the string response
                sub = response.text
            
            # Logic to update risk score based on AI findings
                if any(word in sub.lower() for word in ["risk", "unsafe", "contain"]):
                    final_risk_score = max(final_risk_score, 2)
                    why_flagged = "Flagged by Gemini 3 Web Analysis"
                
            except Exception as e:
                sub = f"Substitution error: {str(e)}"
        
    return {
        "ingredient": ingredient_text, 
        "risk_score": final_risk_score,
        "rec_action": "reject" if final_risk_score >= 2 else rec_action,
        "why_flagged": why_flagged,
        "substitution": sub
    }

# --- STREAMLIT UI ---
st.set_page_config(page_title="SMRE Gluten Audit", layout="wide")
st.title("Smart Meal Recommendation Engine (SMRE) Gluten Pipeline")

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

        risk_icons = {3: "🔴", 2: "🟠", 1: "🟡", 0: "🟢"}
        
        for r in results:
            score = r['risk_score']
            icon = risk_icons.get(score, "⚪")
            
            # Use the icon in the expander title for instant visibility
            with st.expander(f"{icon} {r['ingredient']} (Risk: {score})"):
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