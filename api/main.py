import base64
import io
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from helpers.chibi_drawing import (
    PolaroidAnalysisResult,
    analyse_polaroid_image,
    generate,
)
from pydantic import BaseModel, Field

# --- Environment and S3 Configuration ---
load_dotenv()

# S3 Client
S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
s3_client = None

# Check for all required S3 env vars
if all([os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"), S3_BUCKET_NAME, AWS_REGION]):
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=AWS_REGION
    )
else:
    print("Warning: S3 environment variables not fully configured. File operations will fail.")

def get_s3_url(file_name: str) -> str:
    """Generates a public URL for a file in S3."""
    if not S3_BUCKET_NAME or not AWS_REGION or not s3_client:
        return ""
    return f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file_name}"

def get_s3_key_from_url(url: str) -> str:
    """Extracts the object key from a full S3 URL."""
    path = urlparse(url).path
    return path.lstrip('/')

# --- General Setup ---

# Define data file keys for S3
WATERMELONS_DATA_FILE = "data/watermelons.json"
# REMOVED: POLAROIDS_DATA_PREFIX = "data/polaroids/" # No longer needed
POLAROIDS_DATA_FILE = "data/polaroids.json" # This is the single source of truth


# --- Common Models ---

class ImageCreate(BaseModel):
    image_base64: str
    skip_ai: bool = False

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
    """Reads watermelon data from the JSON file in S3."""
    if not s3_client or not S3_BUCKET_NAME:
        print("S3 client not configured, cannot read data.")
        return []
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=WATERMELONS_DATA_FILE)
        content = response["Body"].read().decode("utf-8")
        if not content:
            return []
        return json.loads(content)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return []  # File doesn't exist yet, return empty list
        else:
            print(f"Error reading from S3: {e}")
            raise
    except json.JSONDecodeError:
        return []  # File is empty or corrupt

def write_watermelons_data(data: List[Dict]):
    """Writes watermelon data to the JSON file in S3."""
    if not s3_client or not S3_BUCKET_NAME:
        print("S3 client not configured, cannot write data.")
        return
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=WATERMELONS_DATA_FILE,
            Body=json.dumps(data, indent=4, default=str),
            ContentType="application/json"
        )
    except ClientError as e:
        print(f"Error writing to S3: {e}")
        raise

# --- Polaroid Feature Models & Helpers ---

class Sticker(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    src: str
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    scale: float = 1.0
    on_back: bool = False

class Polaroid(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    src: str
    createdAt: datetime = Field(default_factory=datetime.now)
    description: str = ""
    diary_entry: str = ""
    stickers: List[Sticker] = Field(default_factory=list)

class PolaroidUpdate(BaseModel):
    createdAt: datetime
    description: str
    diary_entry: str
    stickers: List[Sticker]

def read_polaroids_data() -> List[Dict]:
    """Reads polaroid data from the JSON file in S3."""
    if not s3_client or not S3_BUCKET_NAME:
        print("S3 client not configured, cannot read data.")
        return []
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=POLAROIDS_DATA_FILE)
        content = response["Body"].read().decode("utf-8")
        if not content:
            return []
        return json.loads(content)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return []  # File doesn't exist yet, return empty list
        else:
            print(f"Error reading from S3: {e}")
            raise
    except json.JSONDecodeError:
        return []  # File is empty or corrupt

def write_polaroids_data(data: List[Dict]):
    """Writes the entire polaroid list to the JSON file in S3."""
    if not s3_client or not S3_BUCKET_NAME:
        print("S3 client not configured, cannot write data.")
        return
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=POLAROIDS_DATA_FILE,
            Body=json.dumps(data, indent=4, default=str),
            ContentType="application/json"
        )
    except ClientError as e:
        print(f"Error writing polaroids to S3: {e}")
        raise

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

# --- Watermelon API Endpoints ---

@app.get("/watermelons", response_model=List[Watermelon])
async def get_watermelons():
    """Retrieve all saved watermelon records."""
    data = read_watermelons_data()
    return [Watermelon(**item) for item in data]

@app.post("/watermelons", response_model=Watermelon, status_code=201)
async def create_watermelon(payload: ImageCreate):
    """Create a new watermelon record by uploading an image to S3."""
    if not s3_client or not S3_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="S3 storage is not configured on the server.")
    
    try:
        header, encoded = payload.image_base64.split(",", 1)
        media_type = header.split(":")[1].split(";")[0]
        file_ext = media_type.split("/")[1]
        
        if file_ext not in ["jpeg", "jpg", "png", "gif"]:
             raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: jpeg, jpg, png, gif.")

        image_data = base64.b64decode(encoded)
        image_name = f"images/watermelons/{uuid.uuid4()}.{file_ext}"
        
        s3_client.upload_fileobj(
            io.BytesIO(image_data),
            S3_BUCKET_NAME,
            image_name,
            ExtraArgs={"ContentType": media_type, "ACL": "public-read"}
        )
        image_url = get_s3_url(image_name)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process and upload image: {e}")

    new_watermelon = Watermelon(src=image_url)

    watermelons_data = read_watermelons_data()
    watermelons_data.append(new_watermelon.model_dump(mode="json"))
    write_watermelons_data(watermelons_data)

    return new_watermelon

@app.put("/watermelons/{watermelon_id}", response_model=Watermelon)
async def update_watermelon(watermelon_id: str, payload: WatermelonUpdate):
    """Update a watermelon's ratings and creation date."""
    watermelons_data = read_watermelons_data()
    
    watermelon_to_update = None
    index_to_update = -1
    for i, item in enumerate(watermelons_data):
        if item.get("id") == watermelon_id:
            watermelon_to_update = item
            index_to_update = i
            break

    if not watermelon_to_update:
        raise HTTPException(status_code=404, detail="Watermelon not found")

    # Update the dictionary in place
    watermelon_to_update["rachy"] = payload.rachy.model_dump()
    watermelon_to_update["davey"] = payload.davey.model_dump()
    watermelon_to_update["createdAt"] = payload.createdAt

    # Write the modified list back
    write_watermelons_data(watermelons_data)
    
    return Watermelon(**watermelon_to_update)

@app.delete("/watermelons/{watermelon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watermelon(watermelon_id: str):
    """Delete a watermelon record and its associated image from S3."""
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

    if "src" in watermelon_to_delete and watermelon_to_delete["src"] and s3_client:
        image_key = get_s3_key_from_url(watermelon_to_delete["src"])
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=image_key)
        except ClientError as e:
            print(f"Error removing S3 object {image_key}: {e}")

    watermelons_data.pop(index_to_delete)
    write_watermelons_data(watermelons_data)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Polaroid API Endpoints ---

def generate_stickers_from_analysis(analysis_result: PolaroidAnalysisResult) -> List[Sticker]:
    """
    Generates chibi stickers based on the analysis result.
    """
    print(f"Starting sticker generation for {len(analysis_result.chibi_tasks)} tasks.")
    all_sticker_paths = []
    
    for i, task in enumerate(analysis_result.chibi_tasks):
        sticker_paths = generate(prompt=task.generation_prompt, task_num=i + 1)
        if sticker_paths:
            all_sticker_paths.extend(sticker_paths)
            
    if not all_sticker_paths:
        print("Sticker generation task finished: No stickers were generated.")
        return []

    new_stickers = [Sticker(src=path) for path in all_sticker_paths]
    print(f"Sticker generation task COMPLETE: Generated {len(new_stickers)} stickers.")
    return new_stickers


@app.get("/polaroids", response_model=List[Polaroid])
async def get_polaroids():
    """Retrieve all saved polaroid records."""
    data = read_polaroids_data()
    return [Polaroid(**item) for item in data]

@app.post("/polaroids", response_model=Polaroid, status_code=201)
async def create_polaroid(payload: ImageCreate):
    """
    Create a new polaroid by uploading to S3. Optionally analyzes the image for
    a title and generates chibi stickers if not skipped.
    """
    if not s3_client or not S3_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="S3 storage is not configured on the server.")
        
    try:
        header, encoded = payload.image_base64.split(",", 1)
        media_type = header.split(":")[1].split(";")[0]
        file_ext = media_type.split("/")[1]
        
        if file_ext not in ["jpeg", "jpg", "png", "gif", "webp"]:
             raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: jpeg, jpg, png, gif, webp.")

        image_data = base64.b64decode(encoded)
        image_name = f"images/polaroids/{uuid.uuid4()}.{file_ext}"
        
        s3_client.upload_fileobj(
            io.BytesIO(image_data),
            S3_BUCKET_NAME,
            image_name,
            ExtraArgs={"ContentType": media_type, "ACL": "public-read"}
        )
        image_url = get_s3_url(image_name)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process and upload image: {e}")

    initial_description = ""
    stickers = []

    if not payload.skip_ai:
        try:
            print(f"Analyzing polaroid image: {image_url}")
            analysis_result = await analyse_polaroid_image(image_bytes=image_data, file_ext=file_ext)
            if analysis_result:
                initial_description = analysis_result.short_title
                print(f"Analysis complete. Title: '{initial_description}'")
                if analysis_result.chibi_tasks:
                    print(f"Task to generate {len(analysis_result.chibi_tasks)} chibi stickers for new polaroid.")
                    stickers = generate_stickers_from_analysis(analysis_result)
            else:
                print("Image analysis did not return a result.")
        except Exception as e:
            print(f"An error occurred during polaroid analysis: {e}")
    else:
        print("Skipping AI analysis for new polaroid.")


    new_polaroid = Polaroid(
        src=image_url,
        description=initial_description,
        stickers=stickers
    )

    # Read the list, add the new polaroid, write the list back
    polaroids_data = read_polaroids_data()
    polaroids_data.append(new_polaroid.model_dump(mode="json"))
    write_polaroids_data(polaroids_data)

    return new_polaroid

@app.post("/polaroids/{polaroid_id}/stickers", response_model=Polaroid)
async def regenerate_stickers_for_polaroid(polaroid_id: str):
    """
    Deletes old stickers and generates a new set of stickers for a given polaroid.
    Also updates the polaroid's description based on the new analysis.
    """
    if not s3_client or not S3_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="S3 storage is not configured on the server.")

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

    image_url = polaroid_to_update.get("src")
    if not image_url:
        raise HTTPException(status_code=404, detail="Polaroid does not have a source image.")

    image_key = get_s3_key_from_url(image_url)
    file_ext = os.path.splitext(image_key)[1].lstrip('.')

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=image_key)
        image_bytes = response['Body'].read()
    except ClientError as e:
        print(f"Failed to download image from S3: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve polaroid image for analysis.")
    
    try:
        print(f"Re-analyzing polaroid image for sticker regeneration: {image_url}")
        analysis_result = await analyse_polaroid_image(image_bytes=image_bytes, file_ext=file_ext)
        if not analysis_result:
            raise HTTPException(status_code=500, detail="AI analysis failed to produce a result.")
        print(f"Re-analysis complete. New Title: '{analysis_result.short_title}'")
    except Exception as e:
        print(f"An error occurred during polaroid re-analysis: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during polaroid analysis: {e}")

    # Delete old sticker images from S3
    if "stickers" in polaroid_to_update and polaroid_to_update["stickers"]:
        print(f"Deleting {len(polaroid_to_update['stickers'])} old stickers for polaroid {polaroid_id}.")
        for sticker in polaroid_to_update["stickers"]:
            if "src" in sticker and sticker["src"]:
                sticker_key = get_s3_key_from_url(sticker["src"])
                try:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=sticker_key)
                except ClientError as e:
                    print(f"Error removing old S3 sticker object {sticker_key}: {e}")

    # Generate new stickers
    new_stickers = []
    if analysis_result.chibi_tasks:
        print(f"Generating {len(analysis_result.chibi_tasks)} new chibi stickers for polaroid {polaroid_id}.")
        new_stickers = generate_stickers_from_analysis(analysis_result)

    # Update the polaroid in the list
    polaroid_to_update["description"] = analysis_result.short_title
    polaroid_to_update["stickers"] = [s.model_dump(mode="json") for s in new_stickers]
    
    # Write the entire list back to S3
    write_polaroids_data(polaroids_data)
    
    # Return the updated polaroid
    return Polaroid(**polaroid_to_update)

@app.put("/polaroids/{polaroid_id}", response_model=Polaroid)
async def update_polaroid(polaroid_id: str, payload: PolaroidUpdate):
    """Update a polaroid's description, diary entry, creation date, and stickers."""
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

    # Create the updated model, making sure to preserve the original ID and src
    updated_model = Polaroid(
        id=polaroid_id,
        src=polaroid_to_update['src'], # Keep the original src
        description=payload.description,
        diary_entry=payload.diary_entry,
        createdAt=payload.createdAt,
        stickers=payload.stickers
    )
    
    # Replace the old dictionary with the new one in the list
    polaroids_data[index_to_update] = updated_model.model_dump(mode='json')
    
    # Write the entire list back
    write_polaroids_data(polaroids_data)
    
    return updated_model

@app.delete("/polaroids/{polaroid_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_polaroid(polaroid_id: str):
    """Delete a polaroid, its image, and any associated stickers from S3."""
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

    if not s3_client or not S3_BUCKET_NAME:
        print("Warning: S3 not configured. Cannot delete files from bucket.")
    else:
        # Delete the main polaroid image
        if "src" in polaroid_to_delete and polaroid_to_delete["src"]:
            image_key = get_s3_key_from_url(polaroid_to_delete["src"])
            try:
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=image_key)
            except ClientError as e:
                print(f"Error removing S3 object {image_key}: {e}")

        # Delete associated sticker images
        if "stickers" in polaroid_to_delete:
            for sticker in polaroid_to_delete["stickers"]:
                if "src" in sticker and sticker["src"]:
                    sticker_key = get_s3_key_from_url(sticker["src"])
                    try:
                        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=sticker_key)
                    except ClientError as e:
                        print(f"Error removing S3 sticker object {sticker_key}: {e}")
    
    # Remove the polaroid from the list
    polaroids_data.pop(index_to_delete)
    
    # Write the modified list back to S3
    write_polaroids_data(polaroids_data)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
