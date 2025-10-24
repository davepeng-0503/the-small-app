@ECHO OFF
:: A script to set up and run the full application (backend and frontend) on Windows.
:: It handles Python and Node.js dependencies and runs both servers in separate windows.
::
:: V6: Added 'call' before 'pip install' and 'npm install'.
::     Without 'call', the script would transfer execution to npm/pip
::     and never return to this script, causing it to stop prematurely.

ECHO --- The Small App Setup ---

:: --- Step 1: Environment File Check ---
ECHO.
ECHO [1/5] Checking for environment file...
IF NOT EXIST "api\.env" (
    ECHO No .env file found in the 'api' directory.
    IF EXIST ".env.example" (
        ECHO Copying '.env.example' to 'api\.env'...
        copy ".env.example" "api\.env" > nul
        ECHO ================= IMPORTANT ACTION REQUIRED =================
        ECHO A new file has been created at 'api\.env'.
        ECHO Please open this file and fill in your API keys and S3 bucket details.
        ECHO After saving your changes, please run this script again.
        ECHO ===========================================================
    ) ELSE (
        ECHO ERROR: '.env.example' not found. Cannot create .env file automatically.
    )
    goto end
)
ECHO ✅ .env file found.

:: --- Step 2: System Dependency Check ---
ECHO.
ECHO [2/5] Checking for required tools (python, npm)...
where python >nul 2>nul
if %errorlevel% neq 0 (
    ECHO ERROR: python is not installed or not in PATH. Please install Python 3 and try again.
    goto end
)
where npm >nul 2>nul
if %errorlevel% neq 0 (
    ECHO ERROR: npm is not installed or not in PATH. Please install Node.js and npm and try again.
    goto end
)
ECHO ✅ System dependencies found.

:: --- Step 3: Backend Setup ---
ECHO.
ECHO [3/5] Setting up Backend (API)...
:: Move into the API directory
cd /d "%~dp0api"

IF NOT EXIST "venv" (
    ECHO Creating Python virtual environment in 'api\venv'...
    python -m venv venv
    if %errorlevel% neq 0 (
        ECHO ERROR: Failed to create Python virtual environment.
        :: Return to script root on failure
        cd /d "%~dp0"
        goto end
    )
)

ECHO Activating virtual environment and installing Python dependencies...
call venv\Scripts\activate.bat
call pip install -r requirements.txt
if %errorlevel% neq 0 (
    ECHO ERROR: Failed to install Python dependencies.
    call venv\Scripts\deactivate.bat
    :: Return to script root on failure
    cd /d "%~dp0"
    goto end
)

ECHO Pre-downloading background removal model (this might take a moment)...
python -c "from rembg import new_session; new_session()"
if %errorlevel% neq 0 (
    ECHO Warning: Could not pre-download the ML model. The app may download it on first use, causing a delay.
)

call venv\Scripts\deactivate.bat
:: Return to script root after success
cd /d "%~dp0"
ECHO ✅ Backend setup complete.

:: --- Step 4: Frontend Setup ---
ECHO.
ECHO [4/5] Setting up Frontend (Client)...
:: Move into the Client directory
cd /d "%~dp0client"

ECHO Installing npm dependencies from package.json...
call npm install
if %errorlevel% neq 0 (
    ECHO ERROR: Failed to install npm dependencies.
    :: Return to script root on failure
    cd /d "%~dp0"
    goto end
)

:: Return to script root after success
cd /d "%~dp0"
ECHO ✅ Frontend setup complete.

:: --- Step 5: Run Application ---
ECHO.
ECHO [5/5] Starting Application...

ECHO Starting FastAPI server in a new window...
:: Change directory to the API folder first.
:: The 'start' command will make the new window inherit this directory as its starting path.
cd /d "%~dp0api"
start "FastAPI Backend" cmd /k "call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 9999"

ECHO Starting SvelteKit dev server in a new window...
:: Change directory to the client folder first.
cd /d "%~dp0client"
start "SvelteKit Frontend" cmd /k "call npm run dev -- --port 9998"

:: Return to the script's root directory
cd /d "%~dp0"

ECHO Waiting for servers to initialize...
timeout /t 5 /nobreak > nul

ECHO.
ECHO 🚀 Application is running in separate windows!
ECHO ------------------------------------------
ECHO Backend API available at: http://localhost:9999
ECHO Frontend available at:   http://localhost:9998 (or another port if 9998 is busy)
ECHO ------------------------------------------
ECHO.
ECHO To stop the application, simply close the two new command prompt windows that were opened.
ECHO This main script window can be closed now.
ECHO.

:end
pause

