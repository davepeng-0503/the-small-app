# The Small App

A small app for me and my girlfriend.

This project is a shared digital scrapbook with two main features: rating watermelons and decorating polaroid-style photos with AI-generated stickers.

## Features

-   **Watermelon Rating**: Upload photos of watermelons and rate them on texture, juiciness, and sweetness.
-   **Polaroid Decorator**: Upload photos, get an AI-generated title, and have AI-generated 'chibi' stickers created based on the photo's content. You can then drag, drop, resize, and rotate these stickers onto your polaroids.
-   **Cloud Storage**: All images and data are stored securely in an AWS S3 bucket.

## Tech Stack

-   **Backend**: Python, FastAPI, Google Gemini, Boto3 (for AWS S3)
-   **Frontend**: SvelteKit, TypeScript, TailwindCSS, DaisyUI
-   **DevOps**: Bash (`run.sh`) and Batch (`run.bat`) scripts for easy, cross-platform setup.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

-   **Python 3.x**: Required for the backend server.
-   **Node.js with npm**: Required for the frontend client.
-   **Git**: For cloning the repository.

You will also need credentials for:

-   **AWS S3 Bucket**: You need an active S3 bucket for storing images and data files.
-   **Google API Key**: You need a Google Gemini API key for the AI features (image analysis and sticker generation). You can get one from [Google AI Studio](https://aistudio.google.com/app/apikey).

## Setup & Running the Application

This project includes automated setup scripts for both macOS/Linux and Windows to streamline the installation and launch process.

---

### For macOS & Linux

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/the-small-app.git
    cd the-small-app
    ```

2.  **Configure Environment Variables**
    The first time you run the setup script, it will automatically create an `api/.env` file from the `.env.example` template.
    Open `api/.env` with a text editor and fill in your details for:
    -   `AWS_S3_BUCKET_NAME`
    -   `AWS_REGION`
    -   `AWS_ACCESS_KEY_ID`
    -   `AWS_SECRET_ACCESS_KEY`
    -   `GOOGLE_API_KEY`

3.  **Run the Setup Script**
    First, make the script executable, then run it.

    ```bash
    chmod +x run.sh
    ./run.sh
    ```

    The script will:
    -   ✅ Check for Python and Node.js.
    -   ✅ Create and configure the `api/.env` file if it doesn't exist.
    -   ✅ Set up a Python virtual environment in `api/venv`.
    -   ✅ Install all required backend and frontend dependencies.
    -   ✅ Pre-download the machine learning model for image background removal.
    -   🚀 Start both the backend and frontend servers concurrently.

4.  **Access the App**
    -   **Frontend**: [http://localhost:5173](http://localhost:5173)
    -   **Backend API**: [http://localhost:8000](http://localhost:8000)

5.  **Stopping the App**
    Press `Ctrl+C` in the terminal where the script is running to shut down both servers gracefully.

---

### For Windows

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/the-small-app.git
    cd the-small-app
    ```

2.  **Configure Environment Variables**
    The first time you run the setup script, it will automatically create an `api/.env` file from the `.env.example` template.
    Open `api/.env` with a text editor (like Notepad) and fill in your details for:
    -   `AWS_S3_BUCKET_NAME`
    -   `AWS_REGION`
    -   `AWS_ACCESS_KEY_ID`
    -   `AWS_SECRET_ACCESS_KEY`
    -   `GOOGLE_API_KEY`

3.  **Run the Setup Script**
    Simply double-click the `run.bat` file or execute it from the Command Prompt.
    ```cmd
    run.bat
    ```
    The script will:
    -   ✅ Check for Python and Node.js.
    -   ✅ Create and configure the `api/.env` file if it doesn't exist.
    -   ✅ Set up a Python virtual environment in `api\\venv`.
    -   ✅ Install all required backend and frontend dependencies.
    -   ✅ Pre-download the machine learning model for image background removal.
    -   🚀 Start both the backend and frontend servers in **new, separate command prompt windows**.

4.  **Access the App**
    -   **Frontend**: [http://localhost:5173](http://localhost:5173)
    -   **Backend API**: [http://localhost:8000](http://localhost:8000)

5.  **Stopping the App**
    To stop the application, simply close the two new command prompt windows that were opened by the script (titled "FastAPI Backend" and "SvelteKit Frontend").
