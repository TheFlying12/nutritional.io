from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String)
    age = Column(Integer)
    height = Column(Float)
    weight = Column(Float)
    goal = Column(String)
    current_meal_plan = Column(Text)
    
    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.hashed_password)