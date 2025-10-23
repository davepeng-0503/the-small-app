import io
import os
import uuid
from pathlib import Path
from typing import List, Optional

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

# --- Pydantic Models ---

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

class PolaroidAnalysisResult(BaseModel):
    """
    The result of analyzing a polaroid image, including a title and chibi tasks.
    """
    short_title: str = Field(..., description="A short, fun, descriptive title for the polaroid image (max 5 words).")
    chibi_tasks: List[ChibiGenerationTask] = Field(..., description="A list of chibi generation tasks based on people in the image.")


chibi_designer_agent = Agent(
    model=get_gemini_model(MODEL_NAME),
    output_type=PolaroidAnalysisResult,
    system_prompt=(
        "You are a master chibi artist and creative director. Your task is to analyze an "
        "input photo and generate two things:\n"
        "1. A `short_title` for the image: It must be fun, descriptive, and a maximum of 5 words.\n"
        "2. A list of `chibi_tasks` based on the people in the photo.\n\n"
        "For the `chibi_tasks`:\n"
        "- For **each clearly visible person**, create one `ChibiGenerationTask`.\n"
        "- If there is a group, create one extra `ChibiGenerationTask` featuring all people together.\n"
        "- The chibi's clothes MUST be a simplified, chibi-style version of what the person is wearing.\n"
        "- Invent a **fun, dynamic, and positive action** for each chibi (e.g., 'waving excitedly', 'jumping for joy').\n"
        "- Write a final, detailed `generation_prompt` (around 350 words) for an image AI. This prompt is crucial and must include:\n"
        "    - Art Style: 'cute, pastel-colored chibi drawing', with soft colors and a cartoon/comic-like feel.\n"
        "    - Consistency: Ensure prompts are descriptive enough that all generated chibis share the same art style.\n"
        "    - Details: The character's full description (clothes, hair, etc.) and their action.\n"
        "    - **Crucially:** It MUST include 'transparent background' for layering.\n"
        "    - **Border:** It MUST also specify a 'thin white border' around the chibi."
    )
)

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

async def analyse_polaroid_image(image_path: Path | str) -> Optional[PolaroidAnalysisResult]:
    """
    Analyzes an image to generate a title and a plan for chibi stickers.
    This function does NOT generate the actual sticker images.

    Args:
        image_path: The file path (string or Path) to the source image.

    Returns:
        A PolaroidAnalysisResult object containing the title and chibi tasks,
        or None if analysis fails.

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

    print(f"Loading image for analysis from: {img_path}")
    image_bytes = img_path.read_bytes()
    
    # Infer media type from extension
    media_type = "image/jpeg" # Default
    suffix = img_path.suffix.lower()
    if suffix == ".png":
        media_type = "image/png"
    elif suffix == ".webp":
        media_type = "image/webp"
        
    image_content = BinaryContent(image_bytes, media_type=media_type)

    try:
        print("Running polaroid analysis agent... (This may take a moment)")
        analysis_result_wrapper = await chibi_designer_agent.run([image_content])
        
        if not analysis_result_wrapper.output:
            print("Analysis returned no output from the agent.")
            return None
        
        analysis_result = analysis_result_wrapper.output
        print("\n--- Polaroid Analysis Complete ---")
        print(f"  - Title: {analysis_result.short_title}")
        print(f"  - Chibi Tasks Designed: {len(analysis_result.chibi_tasks)}")
        
        return analysis_result

    except Exception as e:
        print(f"An error occurred running the chibi_designer_agent: {e}")
        # Re-raise the exception to signal failure to the caller
        raise e
