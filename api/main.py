import os
import json
import uuid
import base64
from datetime import datetime
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- General Setup ---

# Define storage paths
STORAGE_DIR = "storage"
IMAGES_DIR = os.path.join(STORAGE_DIR, "images")
WATERMELONS_DATA_FILE = os.path.join(STORAGE_DIR, "watermelons.json")
POLAROIDS_DATA_FILE = os.path.join(STORAGE_DIR, "polaroids.json")

# Ensure storage directories and data files exist on startup
os.makedirs(IMAGES_DIR, exist_ok=True)
if not os.path.exists(WATERMELONS_DATA_FILE):
    with open(WATERMELONS_DATA_FILE, "w") as f:
        json.dump([], f)
if not os.path.exists(POLAROIDS_DATA_FILE):
    with open(POLAROIDS_DATA_FILE, "w") as f:
        json.dump([], f)

# --- Common Models ---

class ImageCreate(BaseModel):
    image_base64: str

# --- Watermelon Feature Models & Helpers ---

class Ratings(BaseModel):
    texture: int = 50
    juiciness: int = 50
    sweetness: int = 50

class Watermelon(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    src: str
    createdAt: datetime = Field(default_factory=datetime.now)
    rachy: Ratings = Field(default_factory=Ratings)
    davey: Ratings = Field(default_factory=Ratings)

class WatermelonUpdate(BaseModel):
    rachy: Ratings
    davey: Ratings
    createdAt: datetime

def read_watermelons_data() -> List[Dict]:
    """Reads watermelon data from the JSON file."""
    if not os.path.exists(WATERMELONS_DATA_FILE) or os.path.getsize(WATERMELONS_DATA_FILE) == 0:
        return []
    with open(WATERMELONS_DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def write_watermelons_data(data: List[Dict]):
    """Writes watermelon data to the JSON file."""
    with open(WATERMELONS_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

# --- Polaroid Feature Models & Helpers ---

class Polaroid(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    src: str
    createdAt: datetime = Field(default_factory=datetime.now)
    description: str = ""

class PolaroidUpdate(BaseModel):
    createdAt: datetime
    description: str

def read_polaroids_data() -> List[Dict]:
    """Reads polaroid data from the JSON file."""
    if not os.path.exists(POLAROIDS_DATA_FILE) or os.path.getsize(POLAROIDS_DATA_FILE) == 0:
        return []
    with open(POLAROIDS_DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def write_polaroids_data(data: List[Dict]):
    """Writes polaroid data to the JSON file."""
    with open(POLAROIDS_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)


# --- FastAPI App Initialization ---

app = FastAPI()

# CORS Middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory to serve images
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


# --- Watermelon API Endpoints ---

@app.get("/watermelons", response_model=List[Watermelon])
async def get_watermelons():
    """Retrieve all saved watermelon records."""
    data = read_watermelons_data()
    return [Watermelon(**item) for item in data]

@app.post("/watermelons", response_model=Watermelon, status_code=201)
async def create_watermelon(payload: ImageCreate):
    """Create a new watermelon record from an uploaded image."""
    try:
        # The base64 string from a data URL includes a header, e.g., "data:image/jpeg;base64,"
        header, encoded = payload.image_base64.split(",", 1)
        file_ext = header.split("/")[1].split(";")[0]
        
        if file_ext not in ["jpeg", "jpg", "png", "gif"]:
             raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: jpeg, jpg, png, gif.")

        image_data = base64.b64decode(encoded)
        image_name = f"{uuid.uuid4()}.{file_ext}"
        image_path = os.path.join(IMAGES_DIR, image_name)
        
        with open(image_path, "wb") as f:
            f.write(image_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {e}")

    # Create a new watermelon with default ratings
    new_watermelon = Watermelon(src=f"/images/{image_name}")

    # Save to our JSON "database"
    watermelons_data = read_watermelons_data()
    watermelons_data.append(new_watermelon.model_dump(mode="json"))
    write_watermelons_data(watermelons_data)

    return new_watermelon

@app.put("/watermelons/{watermelon_id}", response_model=Watermelon)
async def update_watermelon(watermelon_id: str, payload: WatermelonUpdate):
    """Update a watermelon's ratings and creation date."""
    watermelons_data = read_watermelons_data()
    
    watermelon_to_update = None
    for item in watermelons_data:
        if item.get("id") == watermelon_id:
            watermelon_to_update = item
            break

    if not watermelon_to_update:
        raise HTTPException(status_code=404, detail="Watermelon not found")

    # Update ratings in the dictionary
    watermelon_to_update["rachy"] = payload.rachy.model_dump()
    watermelon_to_update["davey"] = payload.davey.model_dump()
    watermelon_to_update["createdAt"] = payload.createdAt

    write_watermelons_data(watermelons_data)
    
    # Return the updated data, validated through the Pydantic model
    return Watermelon(**watermelon_to_update)

# --- Polaroid API Endpoints ---

@app.get("/polaroids", response_model=List[Polaroid])
async def get_polaroids():
    """Retrieve all saved polaroid records."""
    data = read_polaroids_data()
    return [Polaroid(**item) for item in data]

@app.post("/polaroids", response_model=Polaroid, status_code=201)
async def create_polaroid(payload: ImageCreate):
    """Create a new polaroid record from an uploaded image."""
    try:
        header, encoded = payload.image_base64.split(",", 1)
        file_ext = header.split("/")[1].split(";")[0]
        
        if file_ext not in ["jpeg", "jpg", "png", "gif"]:
             raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: jpeg, jpg, png, gif.")

        image_data = base64.b64decode(encoded)
        image_name = f"{uuid.uuid4()}.{file_ext}"
        image_path = os.path.join(IMAGES_DIR, image_name)
        
        with open(image_path, "wb") as f:
            f.write(image_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {e}")

    new_polaroid = Polaroid(src=f"/images/{image_name}")

    polaroids_data = read_polaroids_data()
    polaroids_data.append(new_polaroid.model_dump(mode="json"))
    write_polaroids_data(polaroids_data)

    return new_polaroid

@app.put("/polaroids/{polaroid_id}", response_model=Polaroid)
async def update_polaroid(polaroid_id: str, payload: PolaroidUpdate):
    """Update a polaroid's description and creation date."""
    polaroids_data = read_polaroids_data()
    
    polaroid_to_update = None
    for item in polaroids_data:
        if item.get("id") == polaroid_id:
            polaroid_to_update = item
            break

    if not polaroid_to_update:
        raise HTTPException(status_code=404, detail="Polaroid not found")

    polaroid_to_update["description"] = payload.description
    polaroid_to_update["createdAt"] = payload.createdAt

    write_polaroids_data(polaroids_data)
    
    return Polaroid(**polaroid_to_update)
