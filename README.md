# PlateMate

PlateMate is an intelligent backend service designed to analyze the nutritional value of food products and meals. It operates as a microservice API that processes requests from a Telegram bot.

## Core Features

Meal Analysis (AI-Powered): Upload a meal photo, and the service uses the Google Gemini API to identify components, calculate total macronutrients (P/F/C) and calories, and generate a Hot Vector (feature vector) of the meal's components.

Barcode Scanning: Finds products in the Open Food Facts database, providing nutritional information for the entire package.

User Recommendation System: Based on the last 5 Hot Vectors from user's meal history, the service generates personalized food recommendations using a custom Cross-Attention Triplet Model (PyTorch).

Telegram Bot Interface: The primary interface for users to interact with the service.

## 🛠️ Tech Stack

This project uses modern technologies for high performance and scalability:

Runtime Environment: ```Python 3.11```

Backend Framework: FastAPI, Uvicorn (High-performance ASGI server)

AI / VLM: Google Gemini API (gemini-2.5)

Machine Learning: PyTorch, Pandas, Numpy (Custom Vector Similarity Search)

Barcode/Image Processing: pyzbar, OpenCV, Pillow

Messaging Interface: python-telegram-bot

Networking: httpx (Asynchronous HTTP client)

Data Validation: Pydantic

Configuration: python-dotenv, pydantic-settings

## 📂 Project Structure

This project uses a standard multi-layer architecture for clarity and scalability:
```
/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── nutrition.py    # Endpoints for Photo/Barcode analysis.
│   │   │   ├── recommendations.py # Endpoints for ML recommendations.
│   │   │   ├── images.py       # Endpoint for serving image files by ID.
│   │   │   └── users.py        # User profile endpoints (placeholder).
│   │   └── router.py         # Registers all v1 endpoints.
│   ├── bot/
│   │   └── main.py           # Telegram Bot logic (ConversationHandler, API calls).
│   ├── core/
│   │   └── config.py         # Handles environment variables (`.env`).
│   ├── db/
│   │   └── schemas.py        # Pydantic models (NutritionInfo, RecommendationQuery).
│   ├── ml_stuff/             # ML Model Assets (excluded from GitHub via .gitignore).
│   │   ├── crossatt_triplet.pth
│   │   └── results_food_features.pkl 
│   │   └── dish_images.pkl
│   ├── services/
│   │   ├── barcode_service.py# Open Food Facts integration.
│   │   ├── recommendation_service.py # Core ML logic: model loading, similarity search.
│   │   └── vision_service.py # Gemini API setup and Hot Vector generation.
│   └── main.py               # FastAPI application entry point and startup logic.
├── .env                      # Stores secret API keys (IGNORED by Git).
├── .gitignore                # Ensures large files and secrets are not committed.
└── requirements.txt          # Lists all Python project dependencies.
```

## ⚙️ Setup and Launch

Follow these steps to run the project locally.

1. Clone the repository
```
git clone [https://github.com/NaturalStupidlty/PlateMate.git](https://github.com/NaturalStupidlty/PlateMate.git)
cd PlateMate
```

2. Prepare ML Assets

The ```ml_stuff/``` folder contains large data files ```(.pkl, .pth)``` which are not committed to GitHub. You must ensure these files are locally present in the PlateMate/ml_stuff/ directory before running the server.

3. Create and activate a virtual environment

#### For Windows
```
python -m venv venv
venv\Scripts\activate
```
#### For macOS/Linux
```
python3.11 -m venv venv # Suggesting python3.11 here
source venv/bin/activate
```

4. Install dependencies
```
pip install -r requirements.txt
```

5. Configure environment variables

Create a ```.env``` file in the project's root folder.

```
# Required for accessing the AI image analysis model
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"

# Required for the Telegram bot to operate
TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
```

6. Launch the Application

Important: Run the server and the bot in two separate terminals.

Terminal 1: FastAPI Server (API)

Open the first terminal.

Execute the command (using port 8001 to avoid conflicts):
```
uvicorn app.main:app --port 8001
```

The server will be available at http://127.0.0.1:8001. Do not close this terminal.

Terminal 2: Telegram Bot (Interface)

Open the second terminal.

Execute the command:
```
python app/bot/main.py
```
