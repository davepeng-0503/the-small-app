#!/bin/bash

# A script to set up and run the full application (backend and frontend).
# It handles Python and Node.js dependencies and runs both servers concurrently.

# --- Style Definitions ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- The Small App Setup & Run Script ---${NC}"

# --- Global Variables ---
api_pid=""
client_pid=""

# --- Cleanup function on exit ---
cleanup() {
    echo -e "\n\n${YELLOW}Shutting down services...${NC}"
    
    # Kill processes using stored PIDs if they exist
    if [ -n "$api_pid" ]; then
        kill $api_pid 2>/dev/null
    fi
    if [ -n "$client_pid" ]; then
        kill $client_pid 2>/dev/null
    fi
    
    # Use pkill as a fallback to ensure servers are stopped
    pkill -f "uvicorn main:app"
    pkill -f "vite"

    echo -e "${GREEN}Cleanup complete. Goodbye!${NC}"
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM to run the cleanup function
trap cleanup SIGINT SIGTERM

# --- Step 1: Environment File Check ---
echo -e "\n${YELLOW}[1/5] Checking for environment file...${NC}"
if [ ! -f "api/.env" ]; then
    echo "No .env file found in the 'api' directory."
    if [ -f ".env.example" ]; then
        echo "Copying '.env.example' to 'api/.env'..."
        cp ".env.example" "api/.env"
        echo -e "${RED}================= IMPORTANT ACTION REQUIRED =================${NC}"
        echo -e "A new file has been created at ${YELLOW}'api/.env'${NC}."
        echo "Please open this file and fill in your API keys and S3 bucket details."
        echo "After saving your changes, please run this script again."
        echo -e "${RED}===========================================================${NC}"
    else
        echo -e "${RED}ERROR: '.env.example' not found. Cannot create .env file automatically.${NC}"
    fi
    exit 1
fi
echo "✅ .env file found."

# --- Step 2: System Dependency Check ---
echo -e "\n${YELLOW}[2/5] Checking for required tools (python3, npm)...${NC}"
# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check for Node/NPM
if ! command -v npm &> /dev/null; then
    echo -e "${RED}ERROR: npm is not installed. Please install Node.js and npm and try again.${NC}"
    exit 1
fi
echo "✅ System dependencies found."

# --- Step 3: Backend Setup ---
echo -e "\n${YELLOW}[3/5] Setting up Backend (API)...${NC}"
cd api

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment in 'api/venv'..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to create Python virtual environment.${NC}"
        cd ..
        exit 1
    fi
fi

echo "Activating virtual environment and installing Python dependencies from requirements.txt..."
source venv/bin/activate
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install Python dependencies.${NC}"
    deactivate
    cd ..
    exit 1
fi

echo "Pre-downloading background removal model (this might take a moment)..."
# This command triggers the download of the default model for 'rembg'
python -c "from rembg import new_session; new_session()"
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Could not pre-download the ML model. The app may download it on first use, causing a delay.${NC}"
fi

deactivate
cd ..
echo "✅ Backend setup complete."

# --- Step 4: Frontend Setup ---
echo -e "\n${YELLOW}[4/5] Setting up Frontend (Client)...${NC}"
cd client

echo "Installing npm dependencies from package.json..."
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install npm dependencies.${NC}"
    cd ..
    exit 1
fi

cd ..
echo "✅ Frontend setup complete."

# --- Step 5: Run Application ---
echo -e "\n${YELLOW}[5/5] Starting Application...${NC}"

# Start Backend
echo "Starting FastAPI server in the background..."
cd api
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 &
api_pid=$!
cd ..
sleep 5 # Give the backend a moment to start up

# Start Frontend
echo "Starting SvelteKit dev server in the background..."
cd client
npm run dev &
client_pid=$!
cd ..

echo -e "\n${GREEN}🚀 Application is running!${NC}"
echo -e "------------------------------------------"
echo -e "Backend API available at: ${YELLOW}http://localhost:8000${NC}"
echo -e "Frontend available at:   ${YELLOW}http://localhost:5173${NC} (or another port if 5173 is busy)"
echo -e "------------------------------------------"
echo -e "\nPress ${RED}Ctrl+C${NC} to stop all services."

# Wait for background processes to finish. The script will pause here until Ctrl+C is pressed.
wait $api_pid $client_pid
