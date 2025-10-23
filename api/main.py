import base64
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from helpers.chibi_drawing import (PolaroidAnalysisResult,
                                     analyse_polaroid_image, generate)
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

class Sticker(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    src: str
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    scale: float = 1.0

class Polaroid(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    src: str
    createdAt: datetime = Field(default_factory=datetime.now)
    description: str = ""
    stickers: List[Sticker] = Field(default_factory=list)

class PolaroidUpdate(BaseModel):
    createdAt: datetime
    description: str
    stickers: List[Sticker]

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

@app.delete("/watermelons/{watermelon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watermelon(watermelon_id: str):
    """Delete a watermelon record and its associated image."""
    watermelons_data = read_watermelons_data()

    watermelon_to_delete = None
    index_to_delete = -1
    for i, item in enumerate(watermelons_data):
        if item.get("id") == watermelon_id:
            watermelon_to_delete = item
            index_to_delete = i
            break

    if not watermelon_to_delete:
        raise HTTPException(status_code=404, detail="Watermelon not found")

    # Delete the associated image file
    if "src" in watermelon_to_delete and watermelon_to_delete["src"]:
        image_path = os.path.join(IMAGES_DIR, os.path.basename(watermelon_to_delete["src"]))
        if os.path.exists(image_path):
            os.remove(image_path)

    # Remove the watermelon from the list
    watermelons_data.pop(index_to_delete)

    write_watermelons_data(watermelons_data)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Polaroid API Endpoints ---

def generate_and_update_stickers(polaroid_id: str, analysis_result: PolaroidAnalysisResult):
    """
    Background task to generate chibi stickers and update the polaroid data file.
    """
    print(f"Starting background sticker generation for polaroid_id: {polaroid_id}")
    all_sticker_paths = []
    
    # Generate images for each task
    for i, task in enumerate(analysis_result.chibi_tasks):
        # generate() returns a list of paths, so we extend our main list
        sticker_paths = generate(prompt=task.generation_prompt, task_num=i + 1)
        if sticker_paths:
            all_sticker_paths.extend(sticker_paths)
            
    if not all_sticker_paths:
        print(f"Background task: No stickers were generated for polaroid {polaroid_id}.")
        return

    new_stickers = [Sticker(src=path) for path in all_sticker_paths]

    # This part is a critical section. In a real app, use a lock or a proper DB.
    polaroids_data = read_polaroids_data()
    
    polaroid_to_update = None
    index_to_update = -1
    for i, item in enumerate(polaroids_data):
        if item.get("id") == polaroid_id:
            polaroid_to_update = item
            index_to_update = i
            break

    if not polaroid_to_update:
        print(f"Background task ERROR: Could not find polaroid with id {polaroid_id} to update.")
        return

    # Update the stickers list for the found polaroid
    polaroid_to_update["stickers"] = [s.model_dump(mode='json') for s in new_stickers]
    polaroids_data[index_to_update] = polaroid_to_update

    write_polaroids_data(polaroids_data)
    print(f"Background task COMPLETE: Updated polaroid {polaroid_id} with {len(new_stickers)} stickers.")


@app.get("/polaroids", response_model=List[Polaroid])
async def get_polaroids():
    """Retrieve all saved polaroid records."""
    data = read_polaroids_data()
    # Pydantic will gracefully handle old data without stickers, defaulting to []
    return [Polaroid(**item) for item in data]

@app.post("/polaroids", response_model=Polaroid, status_code=201)
async def create_polaroid(payload: ImageCreate, background_tasks: BackgroundTasks):
    """
    Create a new polaroid from an image.
    This analyzes the image to get a title, creates the polaroid record immediately,
    and then queues a background task to generate the chibi stickers.
    """
    try:
        header, encoded = payload.image_base64.split(",", 1)
        file_ext = header.split("/")[1].split(";")[0]
        
        if file_ext not in ["jpeg", "jpg", "png", "gif", "webp"]:
             raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: jpeg, jpg, png, gif, webp.")

        image_data = base64.b64decode(encoded)
        image_name = f"{uuid.uuid4()}.{file_ext}"
        image_path = os.path.join(IMAGES_DIR, image_name)
        
        with open(image_path, "wb") as f:
            f.write(image_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {e}")

    # Analyze the image to get a title and chibi generation tasks
    analysis_result = None
    initial_description = ""
    try:
        print(f"Analyzing polaroid image: {image_path}")
        analysis_result = await analyse_polaroid_image(image_path)
        if analysis_result:
            initial_description = analysis_result.short_title
            print(f"Analysis complete. Title: '{initial_description}'")
        else:
            print("Image analysis did not return a result.")
    except Exception as e:
        # Log the error but don't block polaroid creation
        print(f"An error occurred during polaroid analysis: {e}")

    # Create the polaroid record immediately
    new_polaroid = Polaroid(
        src=f"/images/{image_name}",
        description=initial_description,
        stickers=[] # Stickers will be added by the background task
    )

    polaroids_data = read_polaroids_data()
    polaroids_data.append(new_polaroid.model_dump(mode="json"))
    write_polaroids_data(polaroids_data)

    # If analysis was successful, queue the background task for sticker generation
    if analysis_result and analysis_result.chibi_tasks:
        background_tasks.add_task(
            generate_and_update_stickers, 
            polaroid_id=new_polaroid.id, 
            analysis_result=analysis_result
        )
        print(f"Queued background task to generate {len(analysis_result.chibi_tasks)} chibi stickers for polaroid {new_polaroid.id}.")
    else:
        print(f"No chibi tasks found for polaroid {new_polaroid.id}. Skipping background task.")

    return new_polaroid

@app.put("/polaroids/{polaroid_id}", response_model=Polaroid)
async def update_polaroid(polaroid_id: str, payload: PolaroidUpdate):
    """Update a polaroid's description, creation date, and stickers."""
    polaroids_data = read_polaroids_data()
    
    polaroid_to_update = None
    index_to_update = -1
    for i, item in enumerate(polaroids_data):
        if item.get("id") == polaroid_id:
            polaroid_to_update = item
            index_to_update = i
            break

    if not polaroid_to_update:
        raise HTTPException(status_code=404, detail="Polaroid not found")

    # Create a new Polaroid object from the payload to ensure all fields are validated
    updated_data = Polaroid(
        id=polaroid_id,
        src=polaroid_to_update['src'], # src should not be changed on update
        description=payload.description,
        createdAt=payload.createdAt,
        stickers=payload.stickers
    )

    polaroids_data[index_to_update] = updated_data.model_dump(mode='json')
    write_polaroids_data(polaroids_data)
    
    return updated_data

@app.delete("/polaroids/{polaroid_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_polaroid(polaroid_id: str):
    """Delete a polaroid, its image, and any associated stickers."""
    polaroids_data = read_polaroids_data()

    polaroid_to_delete = None
    index_to_delete = -1
    for i, item in enumerate(polaroids_data):
        if item.get("id") == polaroid_id:
            polaroid_to_delete = item
            index_to_delete = i
            break

    if not polaroid_to_delete:
        raise HTTPException(status_code=404, detail="Polaroid not found")

    # Delete the main polaroid image
    if "src" in polaroid_to_delete and polaroid_to_delete["src"]:
        image_path = os.path.join(IMAGES_DIR, os.path.basename(polaroid_to_delete["src"]))
        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete associated sticker images
    if "stickers" in polaroid_to_delete:
        for sticker in polaroid_to_delete["stickers"]:
            if "src" in sticker and sticker["src"]:
                sticker_path = os.path.join(IMAGES_DIR, os.path.basename(sticker["src"]))
                if os.path.exists(sticker_path):
                    try:
                        os.remove(sticker_path)
                    except OSError as e:
                        # Log error if sticker can't be removed, but don't fail the whole operation
                        print(f"Error removing sticker file {sticker_path}: {e}")

    # Remove the polaroid from the list
    polaroids_data.pop(index_to_delete)

    write_polaroids_data(polaroids_data)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
