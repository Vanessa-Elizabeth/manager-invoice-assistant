# Manager Invoice Assistant — UI Prototype

## What this version includes
- A dashboard-style opening screen with session counters and recent drafts.
- Sidebar navigation: Overview, Process invoice, and Export centre.
- PDF/image upload.
- Basic text extraction using PDF text reading or Tesseract OCR.
- A review form and draft CSV/Excel exports.

## Important limitations
This is a UI and workflow prototype, not a completed AI agent. It does not yet use an AI model to reliably interpret invoices, recommend expense accounts, detect duplicates, or map rows to the exact Manager Batch Create format. It does not post anything into Manager Desktop. Every field and total must be checked by a person.

## Privacy
Use fictional or redacted documents while testing. This app is not yet configured with user accounts, shared secure hosting, access controls, or a central database.

## Run on Windows
1. Install Python 3.11 or newer.
2. Install Tesseract OCR if you want image OCR; add it to PATH.
3. Extract the ZIP.
4. Double-click `start_windows.bat`.

Or run:
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
