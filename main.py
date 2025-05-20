# main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os # Keep this for os.makedirs

# --- Database Configuration ---
# The database file will be created directly in the /app/ directory inside the container
DATABASE_URL = "sqlite:///./sql_app.db"

# Create a SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} # Needed for SQLite to allow multiple threads
)

# Declare a base class for declarative models
Base = declarative_base()

# Create a SessionLocal class to get database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Database Models (SQLAlchemy) ---

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    price = Column(Float)
    tax = Column(Float, nullable=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

# --- Function to create database tables ---
def create_db_tables():
    """Creates all database tables if they don't exist."""
    print("Attempting to create database tables...")
    # Ensure the directory exists before creating the database file (for consistency, though redundant for '.')
    db_file_path = DATABASE_URL.replace("sqlite:///./", "")
    db_dir = os.path.dirname(db_file_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")

# --- Dependency to get a database session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models (for FastAPI request/response validation) ---

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

class ItemCreate(ItemBase):
    pass

class ItemRead(ItemBase):
    id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# --- FastAPI Application Instance ---
app = FastAPI(
    title="Dummy FastAPI App with SQLite & SQLAlchemy",
    description="A simple FastAPI application demonstrating CI/CD with Jenkins, now with persistent data using SQLite and SQLAlchemy.",
    version="1.0.0"
)

# --- Root Endpoint ---

@app.get("/")
async def read_root():
    """
    Returns a welcome message from the API.
    """
    return {"message": "Welcome to the Dummy FastAPI App! Now with SQLite & SQLAlchemy. Ready for Jenkins integration."}

# --- Item Endpoints ---

@app.get("/items/", response_model=List[ItemRead], summary="Get all items")
async def get_all_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all available items from the database.
    """
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@app.post("/items/", response_model=ItemRead, status_code=201, summary="Create a new item")
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """
    Create a new item in the database.
    """
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/{item_id}", response_model=ItemRead, summary="Get an item by ID")
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single item by its unique ID from the database.
    """
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/items/{item_id}", response_model=ItemRead, summary="Update an existing item")
async def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    """
    Update an existing item's details by its ID in the database.
    """
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}", status_code=204, summary="Delete an item")
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete an item from the database by its ID.
    """
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}

# --- User Endpoints ---

@app.get("/users/", response_model=List[UserRead], summary="Get all users")
async def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all registered users from the database.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.post("/users/", response_model=UserRead, status_code=201, summary="Create a new user")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user in the database.
    """
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserRead, summary="Get a user by ID")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single user by their unique ID from the database.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.put("/users/{user_id}", response_model=UserRead, summary="Update an existing user")
async def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    """
    Update an existing user's details by their ID in the database.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}", status_code=204, summary="Delete a user")
async def delete_user(item_id: int, db: Session = Depends(get_db)):
    """
    Delete an item from the database by its ID.
    """
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}

# --- Health Check Endpoint (Useful for CI/CD) ---

@app.get("/health", summary="Health check endpoint")
async def health_check(db: Session = Depends(get_db)):
    """
    Returns a simple status to indicate the API is running and can connect to the database.
    """
    try:
        # Try to execute a simple query to check database connectivity
        db.execute(Item.__table__.select().limit(1))
        return {"status": "healthy", "message": "API is up and running, database connected!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# --- Simple Test Endpoint (Example for unit testing) ---

@app.get("/add/{num1}/{num2}", summary="Add two numbers")
async def add_numbers(num1: int, num2: int):
    """
    Returns the sum of two numbers.
    """
    return {"result": num1 + num2}