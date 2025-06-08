

---

# ChronicCareIQ

**Personalized, research-driven wellness planning for chronic conditions.**

## Overview

Many people with chronic conditions struggle to find reliable, personalized guidance. Generic wellness apps don’t account for individual health profiles, emerging research, or lifestyle constraints. **ChronicCareIQ** is an AI-powered coach that combines clinical studies, vetted nutrition data, adaptive planning, and real-time customization—so users get truly trustworthy, actionable advice.

## Features

- **14-Day Personalized Wellness Plan:**  
  Generates a two-week plan tailored to any chronic condition and user preferences.
- **Meals & Nutrition:**  
  Meals are built from up-to-date USDA nutrient data and clinical trial insights. If no suitable recipes are found, the system suggests nutritionist-approved meal ideas.
- **Daily Activities:**  
  Each day includes a primary activity (e.g., yoga, strength training) and a complementary practice (e.g., meditation, breathwork) with rationale.
- **Research-Backed:**  
  Integrates the latest findings from PubMed and ClinicalTrials.gov.
- **Real-Time Edits:**  
  Users can edit any item via chat (e.g., “Skip salmon dinner”, “Replace breakfast on day 3 with oatmeal”). Busy days are automatically adjusted for easier meals and lighter activities.
- **Instant Updates:**  
  All edits apply instantly, and the plan re-renders in real time.

## How It Works

1. **User Survey:**  
   Users fill out a survey with their condition, dietary and exercise preferences, and busy days.
2. **Plan Generation:**  
   The backend orchestrates multiple AI “agents” to generate a personalized plan:
   - **NutritionAgent:** Suggests foods and recipes using USDA FoodData Central and LLM fallback.
   - **RecipeAgent:** Finds recipes via Spoonacular API.
   - **WellnessAgent:** Suggests daily activities and complementary practices.
   - **ResearchAgent:** Summarizes recent clinical trials.
   - **ChatAdjustmentAgent:** Applies user edits to the plan via LLM.
3. **Frontend:**  
   HTML/CSS/JS interface for survey, plan grid, and chat.

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** FastAPI (Python)
- **AI/LLM:** Microsoft Phi-4 via Azure, LangChain-style orchestration
- **APIs:**  
  - USDA FoodData Central (nutrition)
  - Spoonacular (recipes)
  - PubMed/ClinicalTrials.gov (research)

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/chroniccareiq.git
   cd chroniccareiq
   ```

2. **Install dependencies:**
   ```sh
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up API keys:**
   - Replace `DEMO_KEY` in agents.py with your USDA API key.
   - Replace the Spoonacular API key in agents.py.
   - Set your GitHub PAT for Azure LLM access.

4. **Run the backend:**
   ```sh
   uvicorn main:app --reload
   ```

5. **Open the frontend:**  
   Open `index.html` in your browser.
   OR serve locally with:
    ```sh
    python -m http.server 8080
    ```

## Customization

- **Add new conditions:**  
  Update the survey and agent logic to support more chronic conditions.
- **Change plan duration:**  
  Adjust the `days` parameter in the plan generation logic.

