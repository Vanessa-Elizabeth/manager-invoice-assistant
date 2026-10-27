import io
import re
from datetime import datetime
import pandas as pd
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Manager Invoice Assistant",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Visual styling ---
st.markdown("""
<style>
:root { --ink:#172B4D; --muted:#62748A; --green:#16836B; --line:#E3EAF1; }
.block-container { padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1440px; }
[data-testid="stSidebar"] { background: #F5F8FB; border-right: 1px solid #E3EAF1; }
.hero { background: linear-gradient(115deg,#102A43 0%,#145B52 100%); padding: 1.45rem 1.6rem;
        border-radius: 18px; color: white; margin-bottom: 1.2rem; }
.hero h1 { color: white; font-size: 2rem; margin: 0 0 .35rem 0; }
.hero p { color: #E4F5F1; margin: 0; font-size: 1rem; }
.metric { border: 1px solid #E3EAF1; border-radius: 14px; padding: 1rem 1.1rem; background: white; }
.metric-label { color:#62748A; font-size:.86rem; margin-bottom:.3rem; }
.metric-value { color:#172B4D; font-size:1.65rem; font-weight:750; }
.metric-note { color:#16836B; font-size:.78rem; margin-top:.2rem; }
.section-title { color:#172B4D; font-size:1.15rem; font-weight:700; margin: .3rem 0 .65rem 0; }
.small-note { color:#62748A; font-size:.86rem; }
div[data-testid="stFileUploader"] { border:1.5px dashed #9CB8C8; border-radius:14px; padding:1rem; background:#F8FBFD; }
.stButton button[kind="primary"] { background:#16836B; border-color:#16836B; border-radius:10px; }
.stButton button { border-radius:10px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🧾 Manager Assistant")
    st.caption("Invoice preparation workspace")
    st.divider()
    page = st.radio("WORKSPACE", ["Overview", "Process invoice", "Export centre"], index=0)
    st.divider()
    st.markdown("**Workflow**")
    st.markdown("① Upload document  \n② Extract details  \n③ Review uncertain fields  \n④ Export draft")
    st.info("This prototype does not post transactions directly into Manager Desktop.")
    st.caption("Demo mode • Use fictional or redacted documents only")

st.markdown("""
<div class="hero">
  <h1>Invoice Assistant</h1>
  <p>Turn invoice documents into organised, reviewable accounting drafts.</p>
</div>
""", unsafe_allow_html=True)

if "drafts" not in st.session_state:
    st.session_state.drafts = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

def extract_text(file):
    raw = file.getvalue()
    name = file.name.lower()
    parts, errors = [], []
    if name.endswith(".pdf"):
        try:
            import fitz
            doc = fitz.open(stream=raw, filetype="pdf")
            for i, page in enumerate(doc):
                txt = page.get_text("text").strip()
                if txt:
                    parts.append(f"--- Page {i+1} ---\\n{txt}")
                else:
                    try:
                        import pytesseract
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        parts.append(f"--- Page {i+1} OCR ---\\n{pytesseract.image_to_string(img)}")
                    except Exception:
                        errors.append("This appears to be a scanned PDF. Tesseract OCR may be needed.")
            doc.close()
        except Exception:
            errors.append("Could not read this PDF. Check the installed PDF packages.")
    else:
        try:
            img = Image.open(io.BytesIO(raw))
            import pytesseract
            parts.append(pytesseract.image_to_string(img))
        except Exception:
            errors.append("Image text extraction needs Tesseract OCR installed.")
    return "\\n".join(parts).strip(), errors

def guess_fields(text, filename):
    supplier = ""
    reference = ""
    date = ""
    patterns = [
        r"(?im)^(?:supplier|vendor|from|billed by)\s*[:\-]\s*(.+)$",
        r"(?im)^(?:invoice\s*to|supplier name)\s*[:\-]\s*(.+)$",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            supplier = m.group(1).strip()[:100]
            break
    m = re.search(r"(?i)(?:invoice\s*(?:no|number|#)|reference)\s*[:#\-]?\s*([A-Z0-9\-\/]+)", text)
    if m:
        reference = m.group(1).strip()
    m = re.search(r"\b(\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4})\b", text)
    if m:
        date = m.group(1)
    return supplier, reference, date

if page == "Overview":
    a, b, c = st.columns(3)
    for col, label, value, note in [
        (a, "Documents in this session", str(len(st.session_state.drafts)), "Drafts prepared here"),
        (b, "Awaiting review", str(sum(1 for d in st.session_state.drafts if d.get("status") == "Review needed")), "Human check required"),
        (c, "Ready to export", str(sum(1 for d in st.session_state.drafts if d.get("status") == "Ready to export")), "Not yet posted to Manager"),
    ]:
        with col:
            st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown('<div class="section-title">Start processing an invoice</div>', unsafe_allow_html=True)
        st.markdown("Upload an invoice or receipt. The assistant will attempt to read the document and prepare details for review.")
        if st.button("＋  Process a new invoice", type="primary", use_container_width=True):
            st.session_state.go_process = True
            st.rerun()
        st.markdown('<p class="small-note">Supported files: PDF, JPG, PNG, WEBP and TIFF.</p>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-title">How it works</div>', unsafe_allow_html=True)
        st.markdown("**1. Upload**  \nChoose an invoice file.")
        st.markdown("**2. Extract**  \nText extraction attempts to read the document.")
        st.markdown("**3. Review**  \nCorrect fields and confirm totals.")
        st.markdown("**4. Export**  \nDownload a draft spreadsheet for the next Manager workflow.")
    st.divider()
    st.markdown('<div class="section-title">Recent drafts</div>', unsafe_allow_html=True)
    if st.session_state.drafts:
        df = pd.DataFrame([{k: d.get(k, "") for k in ["supplier", "reference", "date", "currency", "total", "status"]} for d in st.session_state.drafts])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No invoices processed in this session yet. Your first draft will appear here.")
    if st.session_state.get("go_process"):
        st.session_state.go_process = False
        st.session_state.page_override = "Process invoice"

elif page == "Process invoice" or st.session_state.get("page_override") == "Process invoice":
    st.session_state.page_override = None
    st.markdown('<div class="section-title">1. Upload invoice</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Choose a document", type=["png","jpg","jpeg","webp","tif","tiff","pdf"], help="Use a fictional or redacted file while testing.")
    text = ""
    errors = []
    if uploaded:
        with st.spinner("Reading document…"):
            text, errors = extract_text(uploaded)
        st.success(f"Document loaded: {uploaded.name}")
        if errors:
            for err in errors:
                st.warning(err)
        if text:
            st.markdown('<div class="section-title">2. Review extracted details</div>', unsafe_allow_html=True)
            st.caption("The prototype extracts text using OCR/PDF text reading. It does not yet use an AI model to understand every invoice field.")
            guess_supplier, guess_reference, guess_date = guess_fields(text, uploaded.name)
            with st.form("invoice_review"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    supplier = st.text_input("Supplier", value=guess_supplier)
                    reference = st.text_input("Invoice / reference number", value=guess_reference)
                with col2:
                    invoice_date = st.text_input("Invoice date", value=guess_date, placeholder="e.g. 25/10/2026")
                    currency = st.selectbox("Currency", ["UGX", "USD", "EUR", "GBP", "KES", "Other"])
                with col3:
                    description = st.text_input("Invoice description", placeholder="Short description")
                    account = st.text_input("Suggested Manager expense account", placeholder="Confirm from your chart of accounts")
                st.markdown("**Invoice line items**")
                st.caption("Add or correct the line details below. Values are drafts until checked by a person.")
                lines = st.data_editor(
                    pd.DataFrame([{"Description": "", "Quantity": 1.0, "Unit price": 0.0, "Tax": 0.0}]),
                    num_rows="dynamic", use_container_width=True, key="line_editor"
                )
                total = float((pd.to_numeric(lines["Quantity"], errors="coerce").fillna(0) * pd.to_numeric(lines["Unit price"], errors="coerce").fillna(0) + pd.to_numeric(lines["Tax"], errors="coerce").fillna(0)).sum())
                st.metric("Calculated draft total", f"{currency} {total:,.2f}")
                submitted = st.form_submit_button("Save draft for review", type="primary", use_container_width=True)
            with st.expander("View extracted text"):
                st.text_area("Text read from the document", value=text, height=220)
            if submitted:
                status = "Review needed" if not supplier or not invoice_date or not reference else "Ready to export"
                draft = {"supplier": supplier, "reference": reference, "date": invoice_date, "currency": currency, "description": description, "account": account, "total": total, "status": status, "lines": lines.copy()}
                st.session_state.drafts.append(draft)
                st.session_state.last_result = draft
                st.success("Draft saved in this session. Nothing has been posted to Manager.")
                st.rerun()
        else:
            st.info("No readable text was found. You can still use the document as a reference while OCR is configured.")
    else:
        st.markdown("Upload a file to begin. After extraction, the review form will appear here.")
        st.markdown("""
        <div style="border:1px solid #E3EAF1;border-radius:14px;padding:1.2rem;background:#F8FBFD">
        <b>What the finished AI version is intended to do</b>
        <ul>
          <li>Find supplier, invoice date and invoice number automatically.</li>
          <li>Identify item descriptions, quantities, unit prices and totals.</li>
          <li>Flag unreadable or conflicting fields for human review.</li>
          <li>Prepare a structured draft for Manager batch entry.</li>
        </ul>
        <span style="color:#62748A">These AI capabilities are planned, not active in this prototype yet.</span>
        </div>
        """, unsafe_allow_html=True)

elif page == "Export centre":
    st.markdown('<div class="section-title">Export centre</div>', unsafe_allow_html=True)
    st.write("Download the drafts captured in this app session for review. Exports are not confirmed Manager Batch Create imports.")
    if not st.session_state.drafts:
        st.info("No saved drafts yet. Process an invoice first.")
    else:
        rows = [{k: d.get(k, "") for k in ["supplier", "reference", "date", "currency", "description", "account", "total", "status"]} for d in st.session_state.drafts]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download draft CSV", df.to_csv(index=False).encode("utf-8-sig"), "manager_invoice_drafts.csv", "text/csv", type="primary")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Drafts")
        st.download_button("Download draft Excel", output.getvalue(), "manager_invoice_drafts.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()
st.caption("Prototype only • No direct posting to Manager Desktop • Human review is required before accounting use.")
