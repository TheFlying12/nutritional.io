from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

openai_key = os.getenv("OPENAI_KEY")


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

        #from openai import OpenAI
        #client = OpenAI()
        client = OpenAI(api_key=openai_key)

        completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
        {"role": "developer", "content": "You are a dietician that should be polite and helpful."},
        {
            "role": "user",
            "content": prompt
        }
    ]
)

        # Return the generated meal plan
        return {"meal_plan": completion.choices[0].message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FollowUpRequest(BaseModel):
    conversation: str

@app.post("/follow-up")
async def follow_up(request: FollowUpRequest):
    try:
        client = OpenAI(api_key=openai_key)

        completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
        {"role": "developer", "content": "You are a dietician that should be polite and helpful."},
        {
            "role": "user",
            "content": request.conversation
        }
    ]
)
        # Return the generated meal plan
        return {"follow_up": completion.choices[0].message}

    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))