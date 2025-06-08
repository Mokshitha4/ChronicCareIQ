from typing import List, Dict
import os, json, requests
from pydantic import BaseModel
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
import re

# === LLM Client Setup ===
GITHUB_TOKEN = "*****"  # Replace with your actual GitHub PAT
if not GITHUB_TOKEN:
    raise RuntimeError("Set GITHUB_TOKEN env var to your GitHub PAT")
CLIENT = ChatCompletionsClient(
    endpoint="https://models.github.ai/inference",
    credential=AzureKeyCredential(GITHUB_TOKEN),
    api_version="2024-05-01-preview"
)
MODEL = "microsoft/Phi-4"

# 1. SurveyAgent: parse user survey into profile JSON
def survey_agent(answers: Dict) -> Dict:
    busy = [int(d) for d in answers.get('busyDays','').split(',') if d.strip().isdigit()]
    return {
        'condition': answers['condition'],
        'dietaryPrefs': answers.get('dietaryPrefs',''),
        'exercisePrefs': answers.get('exercisePrefs',''),
        'busyDays': busy
    }

# 2. NutritionAgent: USDA FoodData Central
class NutritionAgent:
    def run(self, condition: str, research: List[Dict]) -> List[Dict]:
        api_key = os.getenv('USDA_API_KEY')
        resp = requests.get(
            'https://api.nal.usda.gov/fdc/v1/foods/search',
            params={'api_key': api_key, 'query': condition, 'pageSize': 5},
            timeout=10
        )
        foods = []
        try:
            foods = resp.json().get('foods', [])
        except ValueError:
            foods = []
        if not foods:
            # Fallback: use LLM to suggest disease-specific foods based on research
            msg_list = [
                SystemMessage(content="You are a nutrition expert with deep knowledge of clinical research and " + json.dumps(research)),
                UserMessage(content=(
                    f'''You are a clinical nutritionist specializing in chronic disease management. Based on the latest research and nutritional guidelines, list 3 foods that are especially beneficial for someone with '{condition}'. For each, briefly explain why it helps manage this condition and also mention the recipes. Output format as a dictionary: {{"food_name": "benefit - recipe suggestion"}}.\n\nExample: 'Spinach - Rich in iron, helps with anemia - Spinach Salad with Lemon Dressing'\n\n Return only the dictionary of foods in the specified format and do not any other character or wirds other than the format.'''
                )),
            ]
            llm_resp = CLIENT.complete(model=MODEL, messages=msg_list, max_tokens=200)
            llm_content = llm_resp.choices[0].message.content.strip()
            print(llm_content)
            # Extract the first JSON object (dictionary) from the string
            try:
                match = re.search(r"\{[\s\S]*\}", llm_content)
                if not match:
                    raise ValueError("No JSON object found in LLM output")
                json_str = match.group(0)
                suggestions = json.loads(json_str)
                print(f"LLM suggestions: {suggestions}")  # Debugging output
                foods = []
                for name, value in suggestions.items():
                    parts = value.split(' - ')
                    suggestion = parts[0].strip() if len(parts) > 0 else ''
                    recipe = parts[1].strip() if len(parts) > 1 else ''
                    foods.append({'name': name.strip(), 'suggestion': suggestion, 'recipe': recipe})
                return foods
            except Exception as e:
                print(f"Failed to parse LLM nutrition response: {e}")
                return []

# 3. RecipeAgent: Spoonacular
class RecipeAgent:
    def run(self, ingredients: List[str], dietary: str) -> List[Dict]:
        api_key ="*****"# Replace with your actual Spoonacular API key
        resp = requests.get(
            'https://api.spoonacular.com/recipes/complexSearch',
            params={
                'apiKey': api_key,
                'includeIngredients': ','.join(ingredients),
                'diet': dietary,
                'number': 2
            }
        ).json().get('results', [])
        recipes=[]
        for r in resp:
            instr = requests.get(
                f"https://api.spoonacular.com/recipes/{r['id']}/analyzedInstructions",
                params={'apiKey': api_key}
            ).json()
            steps=[s['step'] for section in instr for s in section.get('steps',[])]
            recipes.append({'title': r['title'], 'steps': steps})
        return recipes

# 4. WellnessAgent: LLM-driven recommendations via Azure endpoint
# ...existing code...

class WellnessAgent:
    def run(self, activity: str, days: int = 14) -> List[Dict]:
        messages=[
            SystemMessage(content="You are a wellness coach for people with chronic conditions."),
            UserMessage(content=(
                f"For the main activity '{activity}', generate a list of {days} daily complementary wellness practices "
                "such as meditation, breathwork, or stretching. For each day, suggest a different practice and provide a one-sentence rationale. "
                "Respond as a numbered list in the format: 'Day X: Complement: [practice], Tip: [rationale]'."
            ))
        ]
        resp = CLIENT.complete(model=MODEL, messages=messages, temperature=0.7, max_tokens=days*60)
        text = resp.choices[0].message.content.strip()
        print(f"Wellness response: {text}")  # Debugging output

        # Parse the LLM response into a list of dicts
        results = []
        for line in text.split('\n'):
            if not line.strip():
                continue
            # Example expected: Day 1: Complement: Meditation, Tip: Helps calm the mind.
            parts = line.split('Complement:', 1)
            if len(parts) != 2:
                continue
            day_part, rest = parts
            comp, tip = rest.split('Tip:', 1) if 'Tip:' in rest else (rest, '')
            results.append({'complement': comp.strip(), 'tip': tip.strip()})
        # Ensure we have exactly 'days' results
        while len(results) < days:
            results.append({'complement': '', 'tip': ''})
        return results[:days]



# 5. ResearchAgent: ClinicalTrials.gov search + LLM summary
class ResearchAgent:
    def run(self, condition: str) -> List[Dict]:
        # Resilient GET with retries for ClinicalTrials.gov
        def safe_get(url, **kwargs):
            for _ in range(3):
                try:
                    return requests.get(url, timeout=10, **kwargs)
                except requests.exceptions.RequestException:
                    continue
            # On failure, return a dummy response-like object
            return None

        resp = safe_get(
            'https://clinicaltrials.gov/api/query/study_fields',
            params={ 'expr': condition, 'fields': 'BriefTitle,StartDate', 'min_rnk': 1, 'max_rnk': 3, 'fmt': 'json' }
        )
        if not resp or resp.status_code != 200 or not resp.text:
            return []  # gracefully return empty list on error or empty body
        try:
            resp_data = resp.json()
        except ValueError:
            return []
        studies = resp_data.get('StudyFieldsResponse',{}).get('StudyFields',[])
        summaries=[]
        for s in studies:
            title_list = s.get('BriefTitle', [])
            date_list = s.get('StartDate', [])
            if not title_list or not date_list:
                continue
            title = title_list[0]
            date = date_list[0]
            msg = UserMessage(content=f"Summarize the key findings of the clinical trial titled '{title}' started on {date}.")
            resp_llm = CLIENT.complete(model=MODEL, messages=[msg], max_tokens=100)
            summary_text = resp_llm.choices[0].message.content.strip() if resp_llm.choices else ''
            summaries.append({'title': title, 'year': date, 'summary': summary_text})
        return summaries

# 6. PlanGenerationAgent: sequential orchestration without LangChain agents. PlanGenerationAgent: sequential orchestration without LangChain agents

class PlanGenerationAgent:
    def __init__(self):
        self.research = ResearchAgent()
        self.nutrition = NutritionAgent()
        self.recipe = RecipeAgent()
        self.wellness = WellnessAgent()

    def run(self, profile: Dict) -> List[Dict]:
        cond = profile['condition']
        diet = profile['dietaryPrefs']
        exercise = profile['exercisePrefs']
        busy = set(profile['busyDays'])

        # Get all wellness recommendations at once
        wellness_list = self.wellness.run(exercise, days=14)
        meals = []
        plan = []
        for day in range(1, 15):
            if day in busy:
                plan.append({'day': day, 'meals': [], 'suggestions': [], 'ingredients':[],'wellness': {'activity': 'Rest', 'complement': '', 'tip': ''}, 'research': []})
                continue

            research = self.research.run(cond)
            foods = self.nutrition.run(cond, research)
            print(foods)
            ingredients = [f['name'] for f in foods]
            recipes = self.recipe.run(ingredients, diet)
            wellness = wellness_list[day-1]  # Use precomputed wellness for this day

            # If no recipes from API, use nutrition recipes
            if recipes:
                meals = [r['title'] for r in recipes]
            elif foods:
                meals = [f['recipe'] for f in foods]

            suggestions = [f['suggestion'] for f in foods]
            if not suggestions:
                suggestions = ['None available']

            plan.append({
                'day': day,
                'meals': meals,
                'wellness': {'activity': exercise, **wellness},
                'ingredients': ingredients,
                'nutrition': foods,
                'suggestions': suggestions,
                'research': research
            })
        print(plan)
        return plan


# 7. ChatAdjustmentAgent: apply edits via Azure client remains unchanged. ChatAdjustmentAgent: apply edits via Azure client remains unchanged. ChatAdjustmentAgent: apply edits via LLM
class ChatAdjustmentAgent:
    def run(self, plan: List[Dict], edit: str) -> List[Dict]:
        msg=UserMessage(content=f"You are a health planning assistant. Given this 14-day wellness plan: {plan}, and the user's request: '{edit}', update the plan accordingly. Return only the revised plan as valid JSON.")
        resp=CLIENT.complete(model=MODEL,messages=[msg],max_tokens=200)
        return json.loads(resp.choices[0].message.content.strip())

# 8. SynthesisAgent: summarize plan for UI
class SynthesisAgent:
    def run(self, plan: List[Dict]) -> str:
        lines=[]
        for d in plan:
            meals=', '.join(d['meals']); activity=d['wellness']['activity']; comp=d['wellness']['complement']
            research='; '.join([r['summary'] for r in d['research']])
            lines.append(f"Day {d['day']}: Meals: {meals}. Activity: {activity} + {comp}. Research: {research}")
        return '\n'.join(lines)