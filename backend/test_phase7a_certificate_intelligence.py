import sys
import io
import os
import requests
import fitz  # pymupdf

# Set stdout encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

def create_sample_certificate_pdf(output_path="test_certificate.pdf"):
    """Creates a sample PDF certificate for testing."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    
    content = """
    CERTIFICATE OF COMPLETION
    
    This is to certify that
    
    ARRA GAYATRI
    
    has successfully completed the
    
    Google Data Analytics Professional Certificate
    
    Issued by: Google
    Issue Date: October 15, 2023
    Expiry Date: Does not expire
    Credential ID: GCC-98421-ANLYTCS
    Credential URL: https://coursera.org/verify/GCC-98421-ANLYTCS
    
    Skills Covered:
    Data Analysis, SQL, Data Visualization, Spreadsheets, Python, Tableau, Data Cleaning
    
    Verified by Google Career Certificates Program
    """
    
    rect = fitz.Rect(50, 50, 560, 740)
    page.insert_textbox(rect, content, fontsize=12, fontname="helv", align=fitz.TEXT_ALIGN_CENTER)
    doc.save(output_path)
    doc.close()
    return output_path

def run_tests():
    pdf_path = create_sample_certificate_pdf("test_certificate.pdf")
    
    results = {
        "upload": False,
        "extraction": False,
        "fields": False,
        "skills": False,
        "storage": False,
        "verification": False,
        "evidence_center": False
    }

    try:
        # 1. Test Certificate Upload & Extraction endpoint
        with open(pdf_path, "rb") as f:
            files = {"file": ("test_certificate.pdf", f, "application/pdf")}
            data = {
                "analysis_id": "4",
                "certificate_name": "Google Data Analytics Professional Certificate",
                "issuer": "Google",
                "credential_id": "GCC-98421-ANLYTCS",
                "credential_url": "https://coursera.org/verify/GCC-98421-ANLYTCS"
            }
            res = requests.post("http://127.0.0.1:8000/api/evidence/certificate", data=data, files=files, timeout=40)
        
        if res.status_code == 200:
            results["upload"] = True
            body = res.json()
            evidence = body.get("evidence") or {}

            # 2. Document Extraction Test
            doc_status = body.get("document_extraction_status") or evidence.get("document_extraction_status")
            if doc_status == "EXTRACTED":
                results["extraction"] = True

            # 3. Field Extraction Test
            cert_name = body.get("certificate_name") or evidence.get("certificate_name")
            issuer = body.get("issuer") or evidence.get("issuer")
            cand_name = body.get("candidate_name") or evidence.get("certificate_candidate_name")
            cred_id = body.get("credential_id") or evidence.get("credential_id")
            
            if cert_name and issuer and (cand_name or cred_id):
                results["fields"] = True

            # 4. Skill Mapping Test
            skills_detected = body.get("skills") or evidence.get("supported_skills") or []
            if any("data" in s.lower() or "sql" in s.lower() or "python" in s.lower() for s in skills_detected):
                results["skills"] = True

            # 5. Database Storage Test
            evidence_id = body.get("evidence_id") or evidence.get("id")
            if evidence_id:
                results["storage"] = True

            # 6. Verification Status Test
            verif_status = body.get("verification_status") or evidence.get("verification_status")
            # Must be one of the honest allowed statuses and must NOT falsely claim institutional issuance
            allowed_statuses = [
                "DOCUMENT EXTRACTED", 
                "CREDENTIAL URL VERIFIED", 
                "SUBMITTED ONLY", 
                "VERIFICATION UNAVAILABLE", 
                "VERIFICATION FAILED"
            ]
            if verif_status in allowed_statuses:
                results["verification"] = True

        # 7. Evidence Center Integration Test (GET /api/analyses/4)
        ana_res = requests.get("http://127.0.0.1:8000/api/analyses/4", timeout=15)
        if ana_res.status_code == 200:
            ana_data = ana_res.json()
            all_evidence = ana_data.get("evidence", [])
            has_cert_ev = any(e.get("evidence_type") == "certificate" for e in all_evidence)
            if has_cert_ev:
                results["evidence_center"] = True

    finally:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass

    print("\n==================================================")
    print("PHASE 7A — CERTIFICATE INTELLIGENCE")
    print(f"Certificate Upload: {'PASS' if results['upload'] else 'FAIL'}")
    print(f"Document Extraction: {'PASS' if results['extraction'] else 'FAIL'}")
    print(f"Field Extraction: {'PASS' if results['fields'] else 'FAIL'}")
    print(f"Skill Mapping: {'PASS' if results['skills'] else 'FAIL'}")
    print(f"Database Storage: {'PASS' if results['storage'] else 'FAIL'}")
    print(f"Verification Status: {'PASS' if results['verification'] else 'FAIL'}")
    print(f"Evidence Center Integration: {'PASS' if results['evidence_center'] else 'FAIL'}")
    print("==================================================\n")

if __name__ == "__main__":
    run_tests()
