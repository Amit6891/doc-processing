import json
import re
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from openai import OpenAI

from src.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_DOC_INTEL_ENDPOINT,
    AZURE_DOC_INTEL_KEY,
)


def extract_text_from_resume(file_path: str) -> str:
    client = DocumentIntelligenceClient(
        endpoint=AZURE_DOC_INTEL_ENDPOINT,
        credential=AzureKeyCredential(AZURE_DOC_INTEL_KEY),
    )

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # Use pre-layout - Handles PDFs, images, word docs
    poller = client.begin_analyze_document(
        model_id="prebuilt-layout", body=AnalyzeDocumentRequest(bytes_source=file_bytes)
    )
    result = poller.result()

    # concatenate all paragraphs into reading order
    paragraphs = [p.content for p in result.paragraphs or []]
    full_text = "\n".join(paragraphs)

    if not full_text.strip():
        # fallback: join raw lines from every page
        lines = []
        for page in result.pages or []:
            for line in page.lines or []:
                lines.append(line.content)
        full_text = "\n".join(lines)

    return full_text


SYSTEM_PROMPT = """
You are an expert resume parser. Extract the following fields from the resume text.
Return ONLY a valid JSON object — no markdown, no explanation.
 
Fields to extract:
  - name        : Full name of the candidate
  - email       : Primary email address
  - phone       : Primary phone number (with country code if present)
  - location    : Country and/or State/Province (e.g. "India", "California, USA")
  - top_skill   : The candidate's single most prominent technical skill or role
                  (e.g. ".NET Developer", "Full-Stack Engineer", "Lead Architect",
                  "Data Scientist", "DevOps Engineer", "Java Developer")
 
Rules:
  - If a field is not found, return null for that field.
  - For top_skill, infer from job titles, skills sections, certifications, or years
    of experience — pick the ONE that best defines the candidate's identity.
  - Output must be parseable JSON, nothing else.
 
Example output:
{
  "name":      "Amit Chauhan",
  "email":     "amit.chauhan@test.com",
  "phone":     "+91-9999999999",
  "location":  "Chandigarh, India",
  "top_skill": "Azure AI Architect"
}
""".strip()


def parse_fields_with_openai(resume_text: str) -> dict:
    """
    Sends extracted resume text to Azure OpenAI (via AI Foundry) and returns
    a dict with name, email, phone, location, top_skill.
    """
    client = OpenAI(api_key=AZURE_OPENAI_KEY, base_url=AZURE_OPENAI_ENDPOINT)

    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Resume Text:\n\n{resume_text}"},
        ],
    )

    raw_json = response.choices[0].message.content
    return json.loads(raw_json)


def regex_fallback(text: str) -> dict:
    """
    Simple regex extraction — used as a safety net or for offline testing.
    Not as accurate as the LLM approach.
    """
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    phone_match = re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text)

    return {
        "name": None,  # hard to do reliably with regex alone
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "location": None,
        "top_skill": None,
    }


def parse_resume(file_path: str, fallback_on_error: bool = True) -> dict:
    """
    Full pipeline:
      1. Extract text with Azure Document Intelligence
      2. Parse fields with Azure OpenAI (AI Foundry)
      3. Optionally fall back to regex on API errors

    Returns a dict:
    {
        "name":       str | None,
        "email":      str | None,
        "phone":      str | None,
        "location":   str | None,
        "top_skill":  str | None,
        "_raw_text":  str          # the extracted resume text (useful for debugging)
    }
    """
    print(f"[1] Extracting text from: {file_path}")
    raw_text = extract_text_from_resume(file_path)

    print("Parsing fields with Azure OpenAI")
    try:
        fields = parse_fields_with_openai(raw_text)
    except Exception as ex:
        if fallback_on_error:
            print(f"⚠ OpenAI call failed ({ex}), using regex fallback")
            fields = regex_fallback(raw_text)
        else:
            raise
    fields["_raw_text"] = raw_text
    return fields
