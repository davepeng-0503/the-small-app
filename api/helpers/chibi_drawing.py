import io
import os
import uuid
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from google.genai import Client
from PIL import Image
from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.google import GoogleModel
from rembg import remove

# --- Storage Configuration ---
STORAGE_DIR = "storage"
IMAGES_DIR = os.path.join(STORAGE_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# --- Gemini Configuration ---

MODEL_NAME = "gemini-2.5-pro" # Using a powerful model for the complex task
FLASH_MODEL_NAME = "gemini-2.5-flash" # Using a fast model for the simple task

def configure_gemini() -> None:
    """
    Loads environment variables from a .env file and validates that the
    GOOGLE_API_KEY is present.

    Raises:
        ValueError: If the GOOGLE_API_KEY is not set in the environment.
    """
    load_dotenv()
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")

# Configure Gemini API key on script load
try:
    configure_gemini()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please ensure you have a .env file with GOOGLE_API_KEY set.")
    # In a real application, you might exit or handle this more gracefully
    # For this script, we'll let it proceed, but agent/client calls will fail.


def get_gemini_model(model_name: str) -> GoogleModel:
    """
    Creates and returns a configured GoogleModel instance.
    
    Args:
        model_name: The name of the Google model to use.

    Returns:
        GoogleModel: Configured Gemini model for use with Pydantic AI agents.
    """
    return GoogleModel(model_name)

# --- Refined Pydantic Model ---

class ChibiGenerationTask(BaseModel):
    """
    Defines the instructions for generating a single chibi character 
    based on a person in the photo.
    """
    character_description: str = Field(..., 
        description="Brief description of the person in the photo this chibi is based on (e.g., 'person in blue shirt and glasses').")
    
    chibi_action: str = Field(..., 
        description="The fun, dynamic action the chibi is doing (e.g., 'peeking around the corner', 'running along the edge', 'waving excitedly').")

    generation_prompt: str = Field(..., 
        description="A complete, detailed prompt for a text-to-image model (like Imagen or DALL-E) to generate this specific chibi. Must include 'chibi style', clothing details, the action, 'transparent background', and cropping instructions.")


chibi_designer_agent = Agent(
    model=get_gemini_model(MODEL_NAME),
    output_type=List[ChibiGenerationTask],
    system_prompt=(
        "You are a master chibi artist and creative director. Your task is to analyze the "
        "input photo and design cute, fun chibi characters based on the people you see. "
        "For **each clearly visible person**, you must create one `ChibiGenerationTask`.\n\n"
        "If there is a group create one extra ChibiGenerationTask featuring all people\n\n"
        "Your instructions must be precise and very descriptive:\n"
        "1.  **Character:** Briefly describe the person make sure to say man and woman not boy and girl (e.g., 'person with blonde hair and red jacket').\n"
        "2.  **Clothing:** The chibi's clothes MUST be a simplified, chibi-style version of the clothes in the photo.\n"
        "3.  **Action:** Invent a **fun, dynamic, and clearly positive action** for the chibi, like 'waving excitedly from the side', 'running happily', 'jumping for joy', 'sitting and giggling', or 'giving a thumbs-up'.\n"
        "4.  **Prompt:** Write a final, incredibly detailed (around 350 words) **`generation_prompt`** for a text-to-image AI. This prompt is crucial. It must include:\n"
        "    - **Art Style:** The style should be 'cute, pastel-colored chibi drawing', avoiding overly saturated or sharp anime aesthetics. Think soft colors and gentle lines and cartoon / comic like.\n"
        "    - **Critically** Each ChibiGenerationTask should be descriptive enough so that each of the images share the same style\n"
        "    - The character's full description (clothes, hair, etc.).\n"
        "    - Their specific action (e.g., 'waving from the side', 'running happily').\n"
        "    - **Crucially:** You MUST include 'transparent background' so the chibi can be layered.\n"
        "    - **The prompt *must* also include a thin white border\n"
))

# --- Helper Function: Image Generation ---

def generate(prompt: str, task_num: int) -> List[str]:
    """
    Generates image(s) for a single task prompt and saves them to the images storage directory.

    Args:
        prompt: The generation prompt for the image model.
        task_num: The sequential number of the task (for logging).

    Returns:
        A list of server-relative image paths (e.g., ['/images/<uuid4>.png']) for the saved images.
    """
    saved_files: List[str] = []
    client = Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    print(f"  -> Generating image(s) for task {task_num}...")
    
    try:
        result = client.models.generate_images(
            model="models/imagen-4.0-generate-001",
            prompt=f"""{prompt}""",
            config=dict(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="1:1",
                image_size="1K",
            ), # type: ignore
        )

        if not result.generated_images:
            print(f"  -> No images generated for task {task_num}.")
            print(result)
            return []

        # Loop through all generated images (even though we only request 1)
        for generated_image in result.generated_images:
            filename = f"{uuid.uuid4()}.png"
            save_path = os.path.join(IMAGES_DIR, filename)

            if generated_image.image is not None and generated_image.image.image_bytes is not None:
                # This is your variable holding the image bytes
                image_bytes = generated_image.image.image_bytes 

                # 1. Create a file-like object in memory from your bytes
                image_data = io.BytesIO(image_bytes)

                # 2. Open the image using Image.open(), which can read from a file-like object
                img = Image.open(image_data)
                img = remove(img)
                img.save(save_path)
                print(f"  -> Successfully saved to {save_path}")
                api_path = f"/images/{filename}"
                saved_files.append(api_path)
        
        return saved_files

    except Exception as e:
        print(f"  -> ERROR generating image for task {task_num}: {e}")
        return []

# --- Main Exported Function ---

async def generate_chibis_from_image(image_path: Path | str) -> List[str]:
    """
    Main exported function to generate chibi images from a source image file.

    Args:
        image_path: The file path (string or Path) to the source image.

    Returns:
        A list of server-relative image paths (e.g., ['/images/<uuid4>.png']) 
        for the successfully generated and saved images.

    Raises:
        FileNotFoundError: If the provided image_path does not exist.
        Exception: Can raise exceptions from the AI model if API calls fail.
    """
    # Ensure path is a Path object
    img_path = Path(image_path)

    # Ensure the image exists before reading
    if not img_path.exists():
        print(f"Error: Image path does not exist: {img_path}")
        raise FileNotFoundError(f"Image path does not exist: {img_path}")

    print(f"Loading image from: {img_path}")
    image_bytes = img_path.read_bytes()
    
    # Infer media type from extension
    media_type = "image/jpeg" # Default
    suffix = img_path.suffix.lower()
    if suffix == ".png":
        media_type = "image/png"
    elif suffix == ".webp":
        media_type = "image/webp"
        
    image_content = BinaryContent(image_bytes, media_type=media_type)

    all_generated_files: List[str] = []

    # Run the chibi designer agent
    try:
        print("Running chibi designer agent... (This may take a moment)")
        chibi_res = await chibi_designer_agent.run([image_content])
        print("\n--- Chibi Generation Tasks ---")
        
        if not chibi_res.output:
            print("No chibis were designed. Check the image or prompt.")
            return []
            
        print(f"Agent designed {len(chibi_res.output)} task(s).")
        for i, task in enumerate(chibi_res.output):
            print(f"\nTask {i+1}:")
            print(f"  Character: {task.character_description}")
            print(f"  Action:    {task.chibi_action}")
            
            # Generate function now returns a list of server-relative paths
            task_filenames = generate(task.generation_prompt, i + 1)
            all_generated_files.extend(task_filenames)
            
        print("-" * 20)
        print(f"Successfully generated {len(all_generated_files)} image(s).")
        return all_generated_files

    except Exception as e:
        print(f"An error occurred running the chibi_designer_agent: {e}")
        # Re-raise the exception to signal failure to the caller
        raise e
