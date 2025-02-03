from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import SessionLocal, engine
from backend import models
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Load environment variables
load_dotenv()
openai_key = os.getenv("OPENAI_KEY")

# Initialize FastAPI app
app = FastAPI(title="Nutrition.io API")

# Create database tables
models.Base.metadata.create_all(bind=engine)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")  # Change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Configure CORS
ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
]

if os.getenv("ENVIRONMENT") == "development":
    ALLOWED_ORIGINS.extend([
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (adjust later for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow OPTIONS
    allow_headers=["*"],  # Allow all headers
)

# Force HTTPS
# app.add_middleware(HTTPSRedirectMiddleware)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    birthday: str  # Format: YYYY-MM-DD
    age: int = Field(..., gt=0, lt=150)
    height: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)
    goal: str

class NutritionRequest(BaseModel):
    username: str
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

class TweakRequest(BaseModel):
    username: str
    currentDiet: str

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
    Username: {data.username}
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

# Move this function up, before any endpoints
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Then all your endpoints that use get_current_user should come after this function
@app.post("/generate-meal-plan")
async def generate_meal_plan(
    data: NutritionRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        client = get_openai_client()
        print("Received request data:", data)
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
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

        meal_plan = completion.choices[0].message.content
        
        # Save the meal plan to the user's record
        current_user.current_meal_plan = meal_plan
        db.commit()

        result = {
            "mealPlan": meal_plan,
            "status": "success"
        }
        print("Generated response:", result)
        return result

    except Exception as e:
        print(f"Detailed error in generate_meal_plan: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate meal plan: {str(e)}"
        )

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
            model="gpt-4o-mini",  # Changed to correct model name
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


# OPTIONS handler
@app.options("/register")
async def register_options():
    return {}  # Empty response is fine - CORS middleware handles the headers

# New user registration endpoint
@app.post("/register")
async def register_user(data: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = models.User.get_password_hash(data.password)
    db_user = models.User(
        username=data.username,
        email=data.email,
        hashed_password=hashed_password,
        first_name=data.first_name,
        last_name=data.last_name,
        birthday=datetime.strptime(data.birthday, "%Y-%m-%d").date(),
        age=data.age,
        height=data.height,
        weight=data.weight,
        goal=data.goal,
        current_meal_plan=""
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User registered successfully"}

# Token generation endpoint
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.username == form_data.username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.verify_password(form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        print(f"Login error: {str(e)}")  # Add debug print
        raise

# Update meal plan endpoint
@app.post("/update-meal-plan")
async def update_meal_plan(
    meal_plan: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.current_meal_plan = meal_plan
    db.commit()
    return {"message": "Meal plan updated successfully"}

@app.get("/user/me")
async def get_current_user_data(current_user: models.User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "age": current_user.age,
        "height": current_user.height,
        "weight": current_user.weight,
        "goal": current_user.goal
    }

@app.get("/debug/user/{username}")
async def debug_user(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        return {
            "exists": True,
            "has_password": bool(user.hashed_password),
            "email": user.email
        }
    return {"exists": False}

@app.get("/user/meal-plan")
async def get_user_meal_plan(current_user: models.User = Depends(get_current_user)):
    return {
        "meal_plan": current_user.current_meal_plan
    }

@app.post("/tweak-meal-plan")
async def tweak_meal_plan(
    request: TweakRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        client = get_openai_client()
        
        prompt = f"""
        Current user's meal plan needs adjustments. Details:
        Username: {request.username}
        Requested Changes: {request.currentDiet}
        
        Current Meal Plan:
        {current_user.current_meal_plan}
        
        Please provide an updated meal plan incorporating the requested changes while maintaining nutritional balance.
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional dietitian. Modify the existing meal plan based on user feedback while ensuring it remains nutritionally sound."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        new_meal_plan = completion.choices[0].message.content
        
        # Update the user's meal plan in the database
        current_user.current_meal_plan = new_meal_plan
        db.commit()

        return {
            "mealPlan": new_meal_plan,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update meal plan: {str(e)}"
        )