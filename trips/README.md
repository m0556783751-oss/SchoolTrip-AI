# SchoolTrip AI 🎒

מערכת AI אינטראקטיבית לתכנון טיולים עבור בתי ספר.

## טכנולוגיות
- **Python** + **LangChain** + **LangGraph** + **OpenAI GPT**
- **LangSmith** – מעקב, מערכי נתונים והערכות
- **Streamlit** – ממשק משתמש
- **JSON** – מאגר יעדים מקומי

## התקנה

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

ערוך את `.env` עם המפתחות שלך:
```
OPENAI_API_KEY=sk-...
LANGCHAIN_API_KEY=lsv2_...
```

## הרצה

```bash
streamlit run app.py
```

## טסטים

```bash
pytest tests/ -v
```

## הערכה (LangSmith)

```bash
python -m evaluation.evaluators
```

## מבנה הגרף

```
START → collect_details → validate_details
  ↳ (חסר מידע?) → ask_clarification ⟲ loop
  ↳ (הכל תקין) → find_destinations → evaluate_options
    ↳ (אין יעדים) → finalize_trip → END
    ↳ (יש יעדים) → generate_itinerary → teacher_review
      ↳ (אושר) → finalize_trip → END
      ↳ (שינויים) → revise_plan ⟲ loop
```
