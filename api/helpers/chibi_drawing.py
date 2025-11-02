import io
import os
import uuid
from typing import List, Optional

import boto3
from dotenv import load_dotenv
from google.genai import Client
from PIL import Image
from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.google import GoogleModel
from rembg import remove

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
    print("Warning: S3 environment variables not fully configured. File uploads will fail.")

def get_s3_url(file_name: str) -> str:
    """Generates a public URL for a file in S3."""
    if not S3_BUCKET_NAME or not AWS_REGION:
        return ""
    # Note: For this URL structure to work, the bucket must have public access enabled
    # and the object ACL must be "public-read".
    return f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file_name}"

# --- Gemini Configuration ---

MODEL_NAME = "gemini-2.5-pro" # Using a powerful model for the complex task
FLASH_MODEL_NAME = "gemini-2.5-flash" # Using a fast model for the simple task

def configure_gemini() -> None:
    """
    Validates that the GOOGLE_API_KEY is present in the environment.

    Raises:
        ValueError: If the GOOGLE_API_KEY is not set in the environment.
    """
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
    # For this script, we"ll let it proceed, but agent/client calls will fail.


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
        description="A complete, detailed prompt for a text-to-image model (like Imagen or DALL-E) to generate this specific chibi. Must include 'chibi style', clothing details, the action, and cropping instructions.")

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
        "- The chibi's clothes MUST be a exactly what the person is wearing.\n"
        "- Invent a **fun, dynamic, and positive action** for each chibi (e.g., 'waving excitedly', 'jumping for joy').\n"
        "- Write a final, detailed `generation_prompt` (around 450 words) for an image generation AI. This prompt is crucial and must include:\n"
        "    - Art Style: 'cute, pastel-colored chibi drawing', with soft colors and a cartoon/comic-like feel.\n"
        "    - Consistency: Ensure prompts are descriptive enough that all generated chibis share the same art style.\n"
        "    - Details: The character's full description (clothes, hair, etc.) and their action. Ensure hair and clothes have enough description to be generated with accuracy is imperative.\n"
        "    - **Crucially:** It MUST include 'completely white background' for layering.\n"
        "    - **Border:** It MUST also specify a 'thin white border' around the chibi."
    )
)

# --- Helper Function: Image Generation ---

def generate(prompt: str, task_num: int) -> List[str]:
    """
    Generates image(s) for a single task prompt and uploads them to S3.

    Args:
        prompt: The generation prompt for the image model.
        task_num: The sequential number of the task (for logging).

    Returns:
        A list of public S3 URLs for the generated images.
    """
    if not s3_client or not S3_BUCKET_NAME:
        print("  -> ERROR: S3 is not configured. Cannot generate and upload images.")
        return []

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

            if generated_image.image is not None and generated_image.image.image_bytes is not None:
                # This is your variable holding the image bytes
                image_bytes = generated_image.image.image_bytes 

                # 1. Create a file-like object in memory from your bytes
                image_data = io.BytesIO(image_bytes)

                # 2. Open the image using Image.open(), which can read from a file-like object
                # and remove the background.
                img = Image.open(image_data)
                img = remove(img)

                # 3. Save the processed image to an in-memory buffer
                output_buffer = io.BytesIO()
                img.save(output_buffer, format="PNG")
                output_buffer.seek(0) # Rewind the buffer to the beginning

                # 4. Upload the buffer's content to S3
                s3_client.upload_fileobj(
                    output_buffer,
                    S3_BUCKET_NAME,
                    filename,
                    ExtraArgs={"ContentType": "image/png", "ACL": "public-read"}
                )
                
                image_url = get_s3_url(filename)
                print(f"  -> Successfully uploaded to S3: {image_url}")
                saved_files.append(image_url)
        
        return saved_files

    except Exception as e:
        print(f"  -> ERROR generating image for task {task_num}: {e}")
        return []

# --- Main Exported Function ---

async def analyse_polaroid_image(image_bytes: bytes, file_ext: str) -> Optional[PolaroidAnalysisResult]:
    """
    Analyzes an image to generate a title and a plan for chibi stickers.
    This function does NOT generate the actual sticker images.

    Args:
        image_bytes: The byte content of the source image.
        file_ext: The file extension of the image (e.g., "jpeg", "png", "webp").

    Returns:
        A PolaroidAnalysisResult object containing the title and chibi tasks,
        or None if analysis fails.

    Raises:
        Exception: Can raise exceptions from the AI model if API calls fail.
    """
    # Infer media type from extension, default to jpeg
    media_type = f"image/{file_ext}" if file_ext else "image/jpeg"
        
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
