from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()
openai_key = os.getenv("OPENAI_KEY")

# Initialize FastAPI app
app = FastAPI(title="Nutrition.io API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class NutritionRequest(BaseModel):
    name: str
    age: int = Field(..., gt=0, lt=150)
    height: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)
    goal: str
    planType: str
    currentDiet: Optional[str] = None

class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str

class FollowUpRequest(BaseModel):
    conversation: List[Message]

# OpenAI client configuration
def get_openai_client():
    try:
        return OpenAI()
    except Exception as e:
        print(f"Error initializing OpenAI client: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize AI service"
        )

# Helper function to create meal plan prompt
def create_meal_plan_prompt(data: NutritionRequest) -> str:
    return f"""
    Generate a personalized meal plan based on the following details:
    Name: {data.name}
    Age: {data.age}
    Height: {data.height} in
    Weight: {data.weight} lbs
    Goal: {data.goal}
    {f"Current Diet: {data.currentDiet}" if data.planType == "tweaks" and data.currentDiet else ""}
    
    Please provide a detailed meal plan that includes:
    1. Daily caloric requirements
    2. Macro nutrient breakdown
    3. Meal timing recommendations
    4. Specific meal suggestions for each day
    5. Portion sizes and alternatives
    """

@app.post("/generate-meal-plan")
async def generate_meal_plan(data: NutritionRequest):
    try:
        client = get_openai_client()
        
        completion = client.chat.completions.create(
            model="gpt-4",  # Changed to correct model name
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional dietitian. Provide evidence-based nutrition advice and detailed meal plans that are practical and sustainable."
                },
                {
                    "role": "user",
                    "content": create_meal_plan_prompt(data)
                }
            ]
        )

        return {
            "mealPlan": completion.choices[0].message.content,
            "status": "success"
        }

    except Exception as e:
        print(f"Detailed error: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/follow-up")
async def follow_up(request: FollowUpRequest):
    try:
        client = get_openai_client()
        
        # Ensure system message is first
        messages = [
            {
                "role": "system",
                "content": "You are a professional dietitian providing follow-up support. Reference previous discussions and meal plans when appropriate."
            }
        ]
        
        # Add conversation history
        messages.extend([
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation
        ])
        
        completion = client.chat.completions.create(
            model="gpt-4",  # Changed to correct model name
            messages=messages,
        )
        
        return {
            "response": completion.choices[0].message.content,
            "status": "success"
        }
    
    except Exception as e:
        print(f"Error in follow-up: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process follow-up request"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}