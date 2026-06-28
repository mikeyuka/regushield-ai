import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime
from app.config import settings

def extract_text_from_pdf(file_path: str) -> str:
    # Try using pypdf if installed
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        if text.strip():
            return text
    except ImportError:
        pass

    # Fallback/lightweight text extraction loop for PDF files when pypdf is not installed:
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        matches = re.findall(b'\\(([^)]+)\\)', content)
        extracted_lines = []
        for m in matches:
            try:
                text_str = m.decode("utf-8", errors="ignore").strip()
                if len(text_str) > 2 and any(c.isalnum() for c in text_str):
                    extracted_lines.append(text_str)
            except Exception:
                pass
        if extracted_lines:
            return "\n".join(extracted_lines)
    except Exception:
        pass

    # Ultimate fallback: read file as text with replacement error handling
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def extract_text(file_path: str) -> str:
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def extract_expiration_date(text: str) -> str | None:
    # Search for "expiration date", "expiry date", "valid until", "expiry", "expires"
    patterns = [
        r"(?:expiry|expiration|valid\s+until|expires)\s*(?:date)?\s*(?::|is)?\s*(\d{4}-\d{2}-\d{2})",
        r"(?:expiry|expiration|valid\s+until|expires)\s*(?:date)?\s*(?::|is)?\s*(\d{2}/\d{2}/\d{4})",
        r"(?:expiry|expiration|valid\s+until|expires)\s*(?:date)?\s*(?::|is)?\s*([A-Za-z]+\s+\d{1,2},\s*\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass
                    
    # Also find any YYYY-MM-DD format date in the text
    all_dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if all_dates:
        return all_dates[0]
    return None

def parse_with_rules_engine(text: str) -> dict:
    # 1. document_id
    document_id = "UNKNOWN"
    id_patterns = [
        r"Certificate\s+No\.?:\s*([A-Za-z0-9-]+)",
        r"Report\s+No\.?:\s*([A-Za-z0-9-]+)",
        r"Document\s+ID:\s*([A-Za-z0-9-]+)",
        r"No\.?:\s*([A-Za-z0-9-]+)"
    ]
    for pat in id_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            document_id = match.group(1).strip()
            break

    # 2. testing_laboratory & is_accredited
    testing_laboratory = "UNKNOWN"
    is_accredited = False
    
    if re.search(r"SGS", text, re.IGNORECASE):
        testing_laboratory = "SGS United Kingdom Ltd"
        is_accredited = True
    elif re.search(r"Intertek", text, re.IGNORECASE):
        testing_laboratory = "Intertek Testing Services"
        is_accredited = True
    elif re.search(r"TÜV|TUV", text, re.IGNORECASE):
        testing_laboratory = "TÜV Rheinland"
        is_accredited = True
    elif re.search(r"Bureau Veritas|BV\s", text, re.IGNORECASE):
        testing_laboratory = "Bureau Veritas"
        is_accredited = True

    # 3. standards_cited
    standards_cited = []
    # Match EN standards
    en_matches = re.findall(r"\bEN\s*\d+(?:-\d+)?(?:\s*:\s*\d+(?:\+\w+:\d+|\+\w+\d+)?)?\b", text, re.IGNORECASE)
    for m in en_matches:
        std_m = re.sub(r"\s+", " ", m).upper().strip()
        if std_m not in standards_cited:
            standards_cited.append(std_m)
            
    for std_name in ["REACH", "MSDS", "ROHS", "ASTM F963"]:
        if re.search(r"\b" + re.escape(std_name) + r"\b", text, re.IGNORECASE):
            if std_name not in standards_cited:
                standards_cited.append(std_name)

    # 4. expiration_date
    expiration_date = extract_expiration_date(text)

    # 5. declaration_of_conformity_status
    declaration_of_conformity_status = "VALID"
    if re.search(r"\b(?:fail|invalid|rejected|non-compliant|does\s+not\s+comply)\b", text, re.IGNORECASE):
        declaration_of_conformity_status = "INVALID"
    elif expiration_date:
        try:
            exp_dt = datetime.strptime(expiration_date, "%Y-%m-%d")
            if exp_dt < datetime.now():
                declaration_of_conformity_status = "EXPIRED"
        except Exception:
            pass

    # 6. hazards_identified
    hazards_identified = []
    hazardous_keywords = ["phthalates", "lead", "cadmium", "heavy metals", "choking", "flammable", "toxic"]
    for hz in hazardous_keywords:
        if re.search(r"\b" + re.escape(hz) + r"\b", text, re.IGNORECASE):
            hazards_identified.append(hz)

    # 7. matches_product_sku
    matches_product_sku = True

    return {
        "document_id": document_id,
        "testing_laboratory": testing_laboratory,
        "is_accredited": is_accredited,
        "standards_cited": standards_cited,
        "declaration_of_conformity_status": declaration_of_conformity_status,
        "expiration_date": expiration_date,
        "hazards_identified": hazards_identified,
        "matches_product_sku": matches_product_sku
    }

def call_anthropic_api(api_key: str, text: str, doc_type: str) -> dict:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    system_prompt = (
        "You are an expert document compliance analyzer. Your job is to parse safety certificates, "
        "test reports, MSDS documents, and declarations of conformity. Output a valid, structured compliance JSON schema "
        "based strictly on the text provided. Do not include any conversational filler, markdown formatting (other than raw JSON), "
        "or explanations outside the JSON object.\n\n"
        "The JSON object must strictly follow this schema:\n"
        "{\n"
        "  \"document_id\": \"extracted certificate number or 'UNKNOWN'\",\n"
        "  \"testing_laboratory\": \"extracted laboratory name, e.g. SGS United Kingdom Ltd, or 'UNKNOWN'\",\n"
        "  \"is_accredited\": boolean (true if testing lab is standard/recognized (e.g. SGS, Intertek, TÜV, BV), false otherwise),\n"
        "  \"standards_cited\": array of strings (e.g. ['EN 71-1:2014+A1:2018', 'EN 71-3']),\n"
        "  \"declaration_of_conformity_status\": \"VALID\", \"INVALID\", or \"EXPIRED\",\n"
        "  \"expiration_date\": \"YYYY-MM-DD\" or null,\n"
        "  \"hazards_identified\": array of strings (e.g. ['phthalates'] or []),\n"
        "  \"matches_product_sku\": boolean (default true)\n"
        "}"
    )
    
    prompt = f"Document Type: {doc_type}\n\nDocument Text:\n{text}"
    
    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4000,
        "temperature": 0,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=30) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        content_text = res_data["content"][0]["text"].strip()
        json_match = re.search(r"\{.*\}", content_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return json.loads(content_text)

def parse_compliance_document(file_path: str, doc_type: str) -> dict:
    # 1. Extract text from the file
    text = extract_text(file_path)
    
    # 2. Check if ANTHROPIC_API_KEY is present
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if api_key and api_key.strip():
        try:
            return call_anthropic_api(api_key, text, doc_type)
        except Exception:
            # Fallback to rules engine if API call fails
            pass
            
    # 3. Fallback to rule engine
    return parse_with_rules_engine(text)
