PlateMate is an intelligent backend service designed to analyze the nutritional value of foods and dishes based on images. It uses modern AI models to recognize food and external databases to obtain information from barcodes.

 Key features
Photo-based meal analysis: Upload a photo of your meal, and the service will use Google Gemini API to identify its components and calculate the total calories, protein, fat, and carbohydrates.

Barcode scanning: Send a photo of a product's barcode, and the service will find it in the Open Food Facts database, providing nutritional information for the entire package.

Technology stack
Backend: FastAPI, Uvicorn

AI/ML: Google Gemini API (gemini-2.5-flash)
!!! APIKEY in core.config !!!

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


5. Start the server
uvicorn app.main:app --reload --port 8001

The server will be available at http://127.0.0.1:8001.

API documentation
Interactive documentation (Swagger UI) is automatically generated and available at:
http://127.0.0.1:8001/docs

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