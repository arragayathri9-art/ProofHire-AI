# ProofHire AI — Evidence-Based Candidate Verification Platform

ProofHire AI is an end-to-end recruitment verification system that replaces speculative resume claims with empirical evidence. It analyzes resumes against job descriptions, cross-references claims with live GitHub repositories and credential records, administers targeted skill assessments, generates verified skill profiles, produces interview intelligence probes, and compiles comprehensive final verification reports.

---

## 🚀 Key Features

1. **Resume Intelligence**: Automated semantic parsing of candidate resumes, extracting skills, claims, and project histories.
2. **Job Requirement Alignment**: Deep analysis of job requirements and qualification mapping.
3. **Evidence Verification Center**: Empirical verification of claims via uploaded documents, project URLs, and direct GitHub repository inspections.
4. **GitHub Repository Intelligence**: Automated repo inspection analyzing language distributions, commit activity, dependencies, and code structure.
5. **Credential & Certificate Intelligence**: Document extraction and verification for professional certifications.
6. **Adaptive Skill Assessment**: Dynamic assessments aligned directly with candidate claims and target role requirements.
7. **Verified Skill Profile & Proof Graph**: Weighted scoring combining resume claims, code evidence, assessment results, and verified credentials.
8. **Interview Intelligence**: Contextual interview question generation, interviewer notes tracking, and interactive follow-up generation.
9. **Final ProofHire Report**: Actionable, verifiable report aggregating the full verification pipeline for hiring teams.

---

## 🛠 Tech Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy, Uvicorn, Google Gemini API, PyMuPDF (fitz), SQLite
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Lucide React, Axios

---

## ⚙️ Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_token_here (optional, for higher rate limits)
```

Start the FastAPI backend:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

For production build:
```bash
npm run build
```

---

## 🔒 Security & Privacy

- All sensitive environment variables (`.env`, API keys, personal access tokens) are excluded via `.gitignore`.
- Deterministic scoring without automated hiring/rejection bias.
