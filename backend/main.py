from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

openai_key = os.getenv("OPENAI_KEY")

print(openai_key)

openai.api_key = openai_key

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class NutritionRequest(BaseModel):
    name: str
    age: int
    height: float
    weight: float
    goal: str
    planType: str
    currentDiet: str = None

@app.post("/generate-meal-plan")
async def generate_meal_plan(data: NutritionRequest):
    #print("hello world")
    try:
        # Create the prompt for OpenAI
        prompt = f"""
        Generate a personalized meal plan based on the following details:
        Name: {data.name}
        Age: {data.age}
        Height: {data.height} cm
        Weight: {data.weight} kg
        Goal: {data.goal}
        {f"Current Diet: {data.currentDiet}" if data.planType == "tweaks" and data.currentDiet else ""}
        Provide a detailed plan.
        """

        # Call OpenAI API
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500
        )

        # Return the generated meal plan
        return {"meal_plan": response.choices[0].text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
