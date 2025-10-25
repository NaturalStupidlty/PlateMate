PlateMate is an intelligent backend service designed to analyze the nutritional value of foods and dishes based on images. It uses modern AI models to recognize food and external databases to obtain information from barcodes.

 Key features
Photo-based meal analysis: Upload a photo of your meal, and the service will use Google Gemini API to identify its components and calculate the total calories, protein, fat, and carbohydrates.

Barcode scanning: Send a photo of a product's barcode, and the service will find it in the Open Food Facts database, providing nutritional information for the entire package.

Technology stack
Backend: FastAPI, Uvicorn

AI/ML: Google Gemini API (gemini-2.5-flash)

Barcode recognition: pyzbar, OpenCV

HTTP requests: httpx

Data validation: Pydantic



⚙️ Setup and launch
Follow these steps to launch the project locally.

1. Clone the repository
git clone [https://github.com/NaturalStupidlty/PlateMate.git](https://github.com/NaturalStupidlty/PlateMate.git)
cd pm

2. Create and activate a virtual environment
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

44. Configure environment variables

Create a .env file in the project's root folder.

.env

# Required for accessing the AI image analysis model
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"

# Required for the Telegram bot to operate
TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"


5. Run the server

Important: Run the server and the bot in two separate terminals.

Open the first terminal.

Ensure you are in the project folder (PlateMate).

Execute the command:

uvicorn app.main:app --reload --port 8001


The server will be available at http://127.0.0.1:8001. Do not close this terminal.

6. Run the Telegram bot

Open the second terminal.

Ensure you are in the project folder (PlateMate).

Execute the command:

python app/bot/main.py


The bot will start running. Do not close this terminal.

📚 API Documentation

Interactive documentation (Swagger UI) is automatically generated and available at (when the server is running):
http://127.0.0.1:8001/docs.

Endpoint examples
Food analysis by photo
URL: /api/v1/nutrition/analyze-photo

Method: POST

Body: multipart/form-data

image: Image file


Analysis by barcode
URL: /api/v1/nutrition/analyze-barcode

Method: POST

Body: multipart/form-data

image: Image file with barcode

Translated with DeepL.com (free version)