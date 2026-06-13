# Doc Processing

A small resume parsing application that extracts structured candidate information from uploaded resumes.

The app uses:
- `FastAPI` for the HTTP API server
- `Azure Document Intelligence` to extract text from PDF, DOCX, and image resumes
- `Azure OpenAI` to parse resume text into structured fields

## Features

- Upload a resume file and receive JSON output
- Supports PDF, DOCX, JPG, JPEG, PNG, TIFF, and TIF formats
- Returns key fields:
  - `name`
  - `email`
  - `phone`
  - `location`
  - `top_skill`

## Requirements

- Python 3.11+ (or compatible Python 3.x)
- The packages listed in `requirements.txt`

## Installation

1. Clone the repository or open the workspace.
2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and provide the required Azure configuration values.

## Environment Variables

The app expects the following values from environment variables:

- `AZURE_OPENAI_ENDPOINT` — Azure OpenAI endpoint URL
- `AZURE_OPENAI_KEY` — Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT` — Azure OpenAI deployment name
- `AZURE_DOC_INTEL_ENDPOINT` — Azure Document Intelligence endpoint URL
- `AZURE_DOC_INTEL_KEY` — Azure Document Intelligence API key

Example `.env`:

```env
AZURE_OPENAI_ENDPOINT=https://<your-openai-endpoint>.azure.com/
AZURE_OPENAI_KEY=<your-openai-key>
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_DOC_INTEL_ENDPOINT=https://<your-doc-intel-endpoint>.cognitiveservices.azure.com/
AZURE_DOC_INTEL_KEY=<your-doc-intel-key>
```

## Running the API Server

Start the server from the root directory:

```bash
uvicorn src.api_server:app --reload
OR
py -m uvicorn src.api_server:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

### POST /parse-resume

Upload a resume file and receive structured JSON.

Request:
- Content-Type: `multipart/form-data`
- Form field: `file`
- Supported file extensions: `.pdf`, `.docx`, `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`

Response:

```json
{
  "name": "...",
  "email": "...",
  "phone": "...",
  "location": "...",
  "top_skill": "..."
}
```

### GET /health

Returns a simple health check response.

Response:

```json
{
  "status": "ok"
}
```

## How It Works

1. `src.api_server` receives the uploaded file and temporarily stores it.
2. `src.resume_parser.extract_text_from_resume` sends the file to Azure Document Intelligence and extracts readable text.
3. `src.resume_parser.parse_fields_with_openai` sends the text to Azure OpenAI for structured field extraction.
4. If the OpenAI call fails, the app falls back to a basic regex extractor.

## Notes

- The OpenAI parser uses a strict system prompt and expects JSON-only output.
- Raw extracted text is removed from API responses for security.
- This repository is intended as a lightweight resume parsing service and can be extended for additional fields or richer parsing logic.

## License

This project does not include a license file. Add one if you plan to share or publish it.
