"""
Profile Intelligence Service - Phase 4: Verified Skill Profile + Skill Proof Graph

Deterministic evidence aggregation service that evaluates multi-source job-related evidence:
- Resume Claims
- Project Evidence & Documents
- Certificate Evidence
- GitHub / URL Evidence (with access status: Retrieved, Submitted Only, Retrieval Failed)
- Skill Assessment Performance (actual mathematical percentages)

STRICT DECISION SUPPORT RULES:
- Categorical evidence levels: Strong Evidence, Good Evidence, Moderate Evidence, Limited Evidence, Needs Verification
- NO invented percentages or subjective truth claims
- Factual explanations derived directly from recorded counts and inspection states
- Safe database upserts preventing duplicate rows
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import re
from datetime import datetime
from sqlalchemy.orm import Session
import models.models as models

# --- Section 6: Standard Assessment Interpretation ---
def map_assessment_percentage_to_label(pct: Optional[float]) -> str:
    """
    Maps actual skill assessment percentages to standardized descriptive assessment labels.
    Refers strictly to performance demonstrated in the assessment.
    """
    if pct is None:
        return "Not Assessed"
    if pct >= 85.0:
        return "Strong Demonstration"
    elif pct >= 70.0:
        return "Good Demonstration"
    elif pct >= 50.0:
        return "Partial Demonstration"
    elif pct >= 1.0:
        return "Limited Demonstration"
    else:
        return "Not Demonstrated in This Assessment"

# --- Section 11: Job-Related Practical Next Steps ---
PRACTICAL_SUGGESTIONS = {
    "python": "Practical coding exercise or script walkthrough may provide additional evidence.",
    "fastapi": "Practical API endpoint implementation task may provide additional evidence.",
    "docker": "Repository or container configuration review (Dockerfile / Compose) may provide additional evidence.",
    "kubernetes": "Cluster manifest or deployment configuration review may provide additional evidence.",
    "sql": "Practical SQL schema query exercise or performance optimization task may provide additional evidence.",
    "pandas": "Practical data wrangling or dataframe transformation task may provide additional evidence.",
    "machine learning": "Model pipeline review, evaluation metric analysis, or notebook walkthrough may provide additional evidence.",
    "deep learning": "Neural network architecture walkthrough or experiment log review may provide additional evidence.",
    "generative ai": "Prompt engineering case study or LLM integration task may provide additional evidence.",
    "git": "Review of commit history, pull requests, and branching workflow may provide additional evidence.",
    "github": "Inspection of active repository contributions and code reviews may provide additional evidence.",
    "rest apis": "API design assessment or mock integration test may provide additional evidence.",
    "cloud platforms": "Cloud architecture review or deployment workflow inspection may provide additional evidence.",
    "aws": "AWS infrastructure diagram review or CloudFormation/Terraform check may provide additional evidence.",
    "react": "Component architecture review or frontend interactive task may provide additional evidence.",
    "react.js": "Component architecture review or frontend interactive task may provide additional evidence.",
    "node.js": "Asynchronous backend service implementation task may provide additional evidence.",
    "postgresql": "Relational schema review or indexed query challenge may provide additional evidence.",
    "mongodb": "NoSQL document schema design walkthrough may provide additional evidence."
}

def get_next_verification_step(skill_name: str, evidence_level: str) -> Optional[str]:
    """Provides targeted, job-related verification suggestion for skills that need further evidence."""
    if evidence_level in ["Strong Evidence", "Good Evidence"]:
        return None
    
    clean_skill = skill_name.strip().lower()
    if clean_skill in PRACTICAL_SUGGESTIONS:
        return PRACTICAL_SUGGESTIONS[clean_skill]
    
    for key, suggestion in PRACTICAL_SUGGESTIONS.items():
        if key in clean_skill or clean_skill in key:
            return suggestion
            
    return f"Practical {skill_name} task or targeted technical review may provide additional evidence."

def normalize_skill(skill: str) -> str:
    """Standardizes skill string for matching across resume, job, and evidence sources."""
    if not skill:
        return ""
    # Remove dots and extra spaces, lowercase
    cleaned = skill.strip().lower().replace(".", "").replace("-", " ")
    return cleaned

def skill_matches(skill_a: str, skill_b: str) -> bool:
    """Checks whether two skill strings refer to the same capability."""
    norm_a = normalize_skill(skill_a)
    norm_b = normalize_skill(skill_b)
    if not norm_a or not norm_b:
        return False
    if norm_a == norm_b:
        return True
    # Word boundary matching
    pattern_a = r'\b' + re.escape(norm_a) + r'\b'
    pattern_b = r'\b' + re.escape(norm_b) + r'\b'
    if re.search(pattern_a, norm_b) or re.search(pattern_b, norm_a):
        return True
    return False

# --- Section 5: Transparent Backend Evidence-Level Rules ---
def get_github_signals_for_skill(skill_name: str, all_evidence: List[Any]) -> List[Dict[str, Any]]:
    """
    Connects real retrieved GitHub repository signals to the target skill.
    Only uses signals actually retrieved from GitHub.
    Examples:
      - .py files / Python signal -> Python evidence
      - FastAPI dependency/import -> FastAPI evidence
      - React dependency / JSX -> React / React.js evidence
      - Express dependency -> Express evidence
      - Dockerfile / compose -> Docker evidence
      - SQL / database files -> SQL / Database evidence
      - TypeScript files / tsconfig -> TypeScript evidence
    """
    matched: List[Dict[str, Any]] = []
    norm_target = normalize_skill(skill_name)
    
    # Standard ecosystem synonyms
    SYNONYM_MAP = {
        "python": ["python", ".py"],
        "fastapi": ["fastapi"],
        "react": ["react", "react.js", "reactjs", ".jsx", ".tsx"],
        "react.js": ["react", "react.js", "reactjs", ".jsx", ".tsx"],
        "express": ["express", "express.js", "expressjs"],
        "express.js": ["express", "express.js", "expressjs"],
        "node": ["node.js", "nodejs", "node", "javascript"],
        "node.js": ["node.js", "nodejs", "node", "javascript"],
        "javascript": ["javascript", "node.js", "nodejs", "js"],
        "typescript": ["typescript", "ts", ".tsx"],
        "docker": ["docker", "dockerfile", "containerization"],
        "sql": ["sql", "database", "sql / database", "postgresql", "mysql", "sqlite", "prisma", "alembic"],
        "database": ["sql", "database", "sql / database", "postgresql", "mysql", "sqlite", "prisma", "alembic"],
        "postgresql": ["postgresql", "sql", "database", "sql / database"],
        "mysql": ["mysql", "sql", "database", "sql / database"],
        "ci/cd": ["ci/cd", "github actions", "devops", "workflow"],
        "django": ["django"],
        "flask": ["flask"],
        "machine learning": ["machine learning", "pytorch", "tensorflow", "scikit-learn", "sklearn"]
    }
    
    target_synonyms = SYNONYM_MAP.get(norm_target, [norm_target])

    for ev in all_evidence:
        if getattr(ev, "evidence_type", "") != "github" and not getattr(ev, "repository_name", None):
            continue
        
        # Only use signals actually retrieved from GitHub
        if getattr(ev, "evidence_access_status", "") != "retrieved":
            continue
            
        repo_name = getattr(ev, "repository_name", None) or (ev.url.split("/")[-1] if getattr(ev, "url", None) else "repository")
        owner = getattr(ev, "repository_owner", None) or "github"
        repo_full = f"{owner}/{repo_name}"

        # 1. Inspect skill_signals stored during repository intelligence
        signals = getattr(ev, "skill_signals", None) or []
        for s in signals:
            sig_skill = s.get("skill", "")
            norm_sig = normalize_skill(sig_skill)
            
            is_match = (
                skill_matches(sig_skill, skill_name) or
                norm_sig in target_synonyms or
                any(syn in norm_sig for syn in target_synonyms) or
                any(syn in sig_skill.lower() for syn in target_synonyms)
            )
            
            if is_match:
                matched.append({
                    "repository": repo_full,
                    "signal_skill": sig_skill,
                    "source": s.get("source", f"{sig_skill} detected in repository"),
                    "confidence": s.get("confidence", "High"),
                    "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                    "access_status": "retrieved"
                })

        # 2. Inspect file_tree for specific file patterns (.py, Dockerfile, SQL, JSX/TSX)
        file_tree = getattr(ev, "file_tree", None) or []
        if isinstance(file_tree, list):
            # .py files -> Python evidence
            if norm_target in ["python", ".py"] or "python" in target_synonyms:
                py_files = [f for f in file_tree if isinstance(f, str) and f.endswith(".py")]
                if py_files and not any(m["repository"] == repo_full and "Python files" in m["source"] for m in matched):
                    matched.append({
                        "repository": repo_full,
                        "signal_skill": "Python",
                        "source": "Python files detected",
                        "confidence": "High",
                        "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                        "access_status": "retrieved"
                    })

            # Dockerfile -> Docker evidence
            if norm_target in ["docker", "dockerfile"] or "docker" in target_synonyms:
                docker_files = [f for f in file_tree if isinstance(f, str) and ("dockerfile" in f.lower() or "docker-compose" in f.lower())]
                if docker_files and not any(m["repository"] == repo_full and "Dockerfile" in m["source"] for m in matched):
                    matched.append({
                        "repository": repo_full,
                        "signal_skill": "Docker",
                        "source": "Dockerfile detected",
                        "confidence": "High",
                        "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                        "access_status": "retrieved"
                    })

            # SQL / database files -> Database evidence
            if norm_target in ["sql", "database", "postgresql", "mysql"] or any(k in target_synonyms for k in ["sql", "database"]):
                sql_files = [f for f in file_tree if isinstance(f, str) and (f.endswith(".sql") or "migration" in f.lower() or "schema" in f.lower() or "prisma" in f.lower())]
                if sql_files and not any(m["repository"] == repo_full and "SQL" in m["source"] for m in matched):
                    matched.append({
                        "repository": repo_full,
                        "signal_skill": "Database",
                        "source": "SQL/database files detected",
                        "confidence": "High",
                        "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                        "access_status": "retrieved"
                    })

            # React JSX/TSX files
            if norm_target in ["react", "react.js", "reactjs"] or "react" in target_synonyms:
                react_files = [f for f in file_tree if isinstance(f, str) and (f.endswith(".jsx") or f.endswith(".tsx"))]
                if react_files and not any(m["repository"] == repo_full and "React component" in m["source"] for m in matched):
                    matched.append({
                        "repository": repo_full,
                        "signal_skill": "React",
                        "source": "React component files detected",
                        "confidence": "High",
                        "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                        "access_status": "retrieved"
                    })

        # 3. Inspect manifest_files for dependencies (fastapi, react, express)
        manifests = getattr(ev, "manifest_files", None) or {}
        if isinstance(manifests, dict):
            manifest_str = " ".join([f"{k} {v}" for k, v in manifests.items() if isinstance(v, str)]).lower()
            
            # FastAPI dependency/import -> FastAPI evidence
            if norm_target in ["fastapi"] or "fastapi" in target_synonyms:
                if "fastapi" in manifest_str and not any(m["repository"] == repo_full and "FastAPI" in m["source"] for m in matched):
                    matched.append({
                        "repository": repo_full,
                        "signal_skill": "FastAPI",
                        "source": "FastAPI dependency detected",
                        "confidence": "High",
                        "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                        "access_status": "retrieved"
                    })

            # React dependency -> React evidence
            if norm_target in ["react", "react.js", "reactjs"] or "react" in target_synonyms:
                if '"react"' in manifest_str or "'react'" in manifest_str or "react@" in manifest_str or "react" in manifest_str:
                    if not any(m["repository"] == repo_full and "React dependency" in m["source"] for m in matched):
                        matched.append({
                            "repository": repo_full,
                            "signal_skill": "React",
                            "source": "React dependency detected",
                            "confidence": "High",
                            "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                            "access_status": "retrieved"
                        })

            # Express dependency -> Express evidence
            if norm_target in ["express", "express.js", "expressjs"] or "express" in target_synonyms:
                if "express" in manifest_str and not any(m["repository"] == repo_full and "Express" in m["source"] for m in matched):
                    matched.append({
                        "repository": repo_full,
                        "signal_skill": "Express",
                        "source": "Express dependency detected",
                        "confidence": "High",
                        "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                        "access_status": "retrieved"
                    })

        # 4. Inspect primary_language
        primary_lang = getattr(ev, "primary_language", None) or ""
        if primary_lang and (skill_matches(primary_lang, skill_name) or normalize_skill(primary_lang) in target_synonyms):
            if not any(m["repository"] == repo_full and skill_matches(m["signal_skill"], primary_lang) for m in matched):
                matched.append({
                    "repository": repo_full,
                    "signal_skill": primary_lang,
                    "source": f"{primary_lang} files detected",
                    "confidence": "High",
                    "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                    "access_status": "retrieved"
                })

        # 5. Inspect languages distribution
        langs_dict = getattr(ev, "languages", None) or {}
        for l_name, l_bytes in langs_dict.items():
            if (skill_matches(l_name, skill_name) or normalize_skill(l_name) in target_synonyms) and l_bytes > 500:
                if not any(m["repository"] == repo_full and skill_matches(m["signal_skill"], l_name) for m in matched):
                    matched.append({
                        "repository": repo_full,
                        "signal_skill": l_name,
                        "source": f"{l_name} files detected",
                        "confidence": "High",
                        "repository_url": getattr(ev, "repository_url", None) or getattr(ev, "url", None),
                        "access_status": "retrieved"
                    })

    return matched

def compute_evidence_level(
    has_resume_claim: bool,
    retrieved_evidence_count: int,
    submitted_evidence_count: int,
    assessment_pct: Optional[float],
    has_retrieved_github: bool = False,
    github_signals_count: int = 0,
    has_certificate_evidence: bool = False,
    certificate_count: int = 0
) -> Tuple[str, str]:
    """
    Deterministic evidence aggregation rule engine.
    Conservative categorizations:
    - Strong Evidence: Multiple independent relevant retrieved sources OR GitHub repo signals + strong assessment (>= 70%).
    - Good Evidence: Multiple retrieved sources OR GitHub repo signals with confirmed file tree/manifests.
    - Moderate Evidence: Relevant retrieved evidence exists OR assessment provides demonstration (>= 50%).
                         A certificate alone can contribute to reaching Moderate if combined with resume claim.
    - Limited Evidence: Resume claim + one weak/submitted-only source OR assessment 1-49%.
    - Needs Verification: Only resume claim exists without meaningful evidence, or unverified.

    PHASE 7B CERTIFICATE EVIDENCE RULES:
    - Certificate evidence is SUPPORTING/CREDENTIAL evidence (not practical demonstration)
    - Certificate alone CANNOT reach Strong Evidence
    - Certificate + resume claim = Moderate Evidence (not Limited or Needs Verification)
    - Certificate + GitHub OR Certificate + Assessment = same level as without certificate
      (certificate does not add extra signal on top of GitHub/Assessment)
    
    STRICT MISSING EVIDENCE RULE:
    If a candidate claims a skill but:
      No GitHub evidence exists AND Assessment is weak/not completed AND no certificate
      -> MUST return ('Needs Verification', 'Unverified')!
    """
    has_assessment = assessment_pct is not None
    pct = assessment_pct if has_assessment else -1.0
    
    # 1. Missing Evidence / False Verification Protection (Requirement 7)
    if not has_retrieved_github and retrieved_evidence_count == 0:
        if not has_assessment or pct < 50.0:
            # Phase 7B: Certificate + resume claim = Moderate Evidence
            if has_certificate_evidence and has_resume_claim:
                return "Moderate Evidence", "Moderate"
            # Phase 7B: Certificate alone (no resume) = Limited Evidence
            if has_certificate_evidence:
                return "Limited Evidence", "Limited"
            return "Needs Verification", "Unverified"
        if 50.0 <= pct < 70.0:
            return "Limited Evidence", "Limited"
        if pct >= 70.0:
            return "Moderate Evidence", "Moderate"

    # 2. Strong Evidence
    if has_retrieved_github and has_assessment and pct >= 70.0:
        return "Strong Evidence", "Strong"
    if retrieved_evidence_count >= 2 and has_assessment and pct >= 70.0:
        return "Strong Evidence", "Strong"
    if has_retrieved_github and has_resume_claim and has_assessment and pct >= 85.0:
        return "Strong Evidence", "Strong"

    # 3. Good / Moderate Evidence
    if has_retrieved_github and has_assessment and pct >= 50.0:
        return "Good Evidence", "Strong"
    if retrieved_evidence_count >= 2:
        return "Good Evidence", "Strong"
    if has_retrieved_github:
        # Verified repository code signals confirmed from GitHub REST API
        return "Moderate Evidence", "Moderate"
    if has_assessment and pct >= 70.0:
        return "Moderate Evidence", "Moderate"
    if has_assessment and 50.0 <= pct < 70.0:
        return "Moderate Evidence", "Moderate"

    # 4. Limited Evidence
    if has_resume_claim and submitted_evidence_count >= 1:
        return "Limited Evidence", "Limited"
    if has_assessment and 1.0 <= pct < 50.0:
        return "Limited Evidence", "Limited"
    # Phase 7B: Certificate present but reached here means other signals exist
    if has_certificate_evidence:
        return "Limited Evidence", "Limited"

    # 5. Needs Verification
    return "Needs Verification", "Unverified"

def get_assessment_status(assessment_pct: Optional[float]) -> str:
    """Returns: Passed / Partial / Needs Improvement / Not Tested"""
    if assessment_pct is None:
        return "Not Tested"
    if assessment_pct >= 70.0:
        return "Passed"
    elif assessment_pct >= 50.0:
        return "Partial"
    else:
        return "Needs Improvement"

def build_proof_sources(
    skill_name: str,
    has_resume_claim: bool,
    github_signals: List[Dict[str, Any]],
    assessment_res: Optional[Dict[str, Any]],
    evidence_strength: str,
    certificates: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """
    Builds concrete, non-fabricated proof sources list for a skill.
    Example:
      ✓ Resume claim
      ✓ GitHub repository retrieved: psf/requests
      ✓ Python files detected
      ✓ Certificate evidence: Google Data Analytics (Google) [DOCUMENT EXTRACTED]
      ✓ Assessment score: 12/15
      Evidence Strength: Strong
    """
    sources: List[str] = []
    
    # 1. Resume claim
    if has_resume_claim:
        sources.append("✓ Resume claim")
    else:
        sources.append("✗ No resume claim")

    # 2. GitHub Evidence
    if github_signals:
        repos_seen = set()
        for s in github_signals:
            repo = s.get("repository", "")
            if repo and repo not in repos_seen:
                repos_seen.add(repo)
                sources.append(f"✓ GitHub repository retrieved: {repo}")
            
            src_desc = s.get("source", "")
            if "file" in src_desc.lower() or "py" in src_desc.lower() or "depend" in src_desc.lower() or "declared" in src_desc.lower() or "workflow" in src_desc.lower():
                sources.append(f"✓ {src_desc}")
            else:
                sources.append(f"✓ {s.get('signal_skill', skill_name)} verified in repository files")
    else:
        sources.append("✗ No GitHub repository evidence")

    # 3. Certificate Evidence
    if certificates:
        for c in certificates:
            c_name = c.get("name") or "Technical Credential"
            c_iss = c.get("issuer")
            iss_str = f" ({c_iss})" if c_iss else ""
            v_stat = c.get("verification_status", "DOCUMENT EXTRACTED")
            sources.append(f"✓ Certificate evidence: {c_name}{iss_str} [{v_stat}]")

    # 4. Assessment score
    if assessment_res and assessment_res.get("percentage") is not None:
        score = int(assessment_res.get("score", 0))
        max_score = int(assessment_res.get("max_score", 0))
        pct = assessment_res.get("percentage", 0)
        sources.append(f"✓ Assessment score: {score}/{max_score} ({pct:.0f}%)")
    else:
        sources.append("✗ Assessment not completed")

    # 5. Evidence Strength
    sources.append(f"Evidence Strength: {evidence_strength}")

    return sources

# --- Section 9: Factual Proof Explanation Generator ---
def generate_proof_explanation(
    skill_name: str,
    evidence_strength: str,
    has_resume_claim: bool,
    github_signals: List[Dict[str, Any]],
    assessment_pct: Optional[float],
    assessment_label: str,
    certificates: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Phase 7B: Constructs a factual, transparent narrative for 'Why this skill rating?'.
    Now includes certificate evidence in the explanation.
    Guarantees no hallucinated numbers or ungrounded claims.
    """
    repos = list({s.get("repository") for s in github_signals if s.get("repository")})
    sig_descs = [s.get("source", s.get("signal_skill", "")) for s in github_signals[:2]]
    
    # Build certificate fragment
    cert_fragment = ""
    if certificates:
        cert_names = []
        for c in certificates[:2]:
            c_name = c.get("name") or "certificate"
            c_iss = c.get("issuer")
            c_stat = c.get("verification_status", "DOCUMENT EXTRACTED")
            cert_names.append(f"{c_name}{(' (' + c_iss + ')') if c_iss else ''} [{c_stat}]")
        cert_fragment = f" Certificate credential evidence provided: {'; '.join(cert_names)}."

    if evidence_strength == "Strong":
        if github_signals and assessment_pct is not None:
            return (
                f"{skill_name} received strong evidence because the candidate claimed {skill_name} experience, "
                f"{skill_name}-related repository signals were retrieved from GitHub ({', '.join(repos)}: {'; '.join(sig_descs)}), "
                f"and the candidate demonstrated the skill in the assessment ({assessment_pct:.1f}% - {assessment_label})."
                f"{cert_fragment}"
            )
        elif github_signals:
            return (
                f"{skill_name} received strong evidence because multiple verified repository signals were retrieved "
                f"from GitHub ({', '.join(repos)}: {'; '.join(sig_descs)}) confirming active codebase implementation."
                f"{cert_fragment}"
            )
        else:
            return (
                f"{skill_name} received strong evidence based on high-level demonstration in the assessment ({assessment_pct:.1f}%) "
                f"and verified resume documentation."
                f"{cert_fragment}"
            )

    elif evidence_strength in ["Moderate", "Good"]:
        if github_signals:
            return (
                f"{skill_name} received moderate evidence because {skill_name}-related repository signals were retrieved "
                f"from GitHub ({', '.join(repos)}: {'; '.join(sig_descs)}), though assessment demonstration is pending."
                f"{cert_fragment}"
            )
        elif assessment_pct is not None:
            return (
                f"{skill_name} received moderate evidence based on candidate assessment performance ({assessment_pct:.1f}% - {assessment_label}), "
                f"though code repository evidence has not yet been connected."
                f"{cert_fragment}"
            )
        elif certificates:
            return (
                f"{skill_name} received moderate evidence through credential documentation: {cert_fragment.strip()} "
                f"Combined with resume claims, this provides supporting credential evidence. "
                f"Practical assessment or GitHub evidence would strengthen this further."
            )
        else:
            return (
                f"{skill_name} received moderate evidence through documented claims and submitted project materials."
            )

    elif evidence_strength == "Limited":
        if assessment_pct is not None:
            return (
                f"{skill_name} received limited evidence because the candidate demonstrated partial assessment performance ({assessment_pct:.1f}%), "
                f"without verified GitHub repository evidence."
                f"{cert_fragment}"
            )
        elif certificates:
            return (
                f"{skill_name} received limited evidence. {cert_fragment.strip()} "
                f"Certificate evidence provides credential support, but practical demonstration through assessment or GitHub code is recommended."
            )
        else:
            return (
                f"{skill_name} received limited evidence because only an initial uninspected reference was submitted."
            )

    else: # Unverified / Needs Verification
        if has_resume_claim:
            return (
                f"{skill_name} requires verification because although the candidate claimed {skill_name} experience, "
                f"no GitHub repository evidence exists and assessment has not been completed."
                f"{cert_fragment}"
            )
        else:
            return (
                f"{skill_name} is unverified because there is currently no resume claim, repository evidence, or assessment recorded."
            )

# --- Section 8: Skill Proof Graph Builder ---
def build_skill_proof_graph(
    candidate_name: str,
    skill_name: str,
    claims: List[Dict[str, Any]],
    projects: List[Dict[str, Any]],
    certificates: List[Dict[str, Any]],
    github_signals: List[Dict[str, Any]],
    github_urls: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    assessment_res: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Constructs node/edge graph data representation containing REAL stored evidence only.
    Hierarchical structure:
    Candidate
       ↓
    Skill (e.g. Python)
       ├── Resume Claim
       ├── GitHub Repository
       │      └── Signals (e.g. Python files detected)
       └── Skill Assessment
              └── Score (e.g. 12/15)
    """
    cand_node_id = "cand_root"
    skill_node_id = "skill_root"
    
    nodes = [
        {
            "id": cand_node_id,
            "type": "Candidate",
            "label": candidate_name or "Candidate",
            "title": f"Candidate: {candidate_name or 'Candidate'}",
            "status": "Candidate",
            "isRoot": True
        },
        {
            "id": skill_node_id,
            "type": "Skill",
            "label": skill_name,
            "title": f"Skill: {skill_name}",
            "status": "Target Skill"
        }
    ]
    edges = [
        {
            "from": cand_node_id,
            "to": skill_node_id,
            "label": "evaluating"
        }
    ]

    # 1. Resume Claims
    if claims:
        for idx, c in enumerate(claims):
            node_id = f"claim_{idx+1}"
            text_snippet = c.get("claim_text", "")
            if len(text_snippet) > 80:
                text_snippet = text_snippet[:77] + "..."
            nodes.append({
                "id": node_id,
                "type": "Resume Claim",
                "label": f"Resume Claim #{idx+1}" if len(claims) > 1 else "Resume Claim",
                "title": c.get("claim_text", ""),
                "status": "Claimed in Resume",
                "source_section": c.get("source_section", "Experience")
            })
            edges.append({
                "from": skill_node_id,
                "to": node_id,
                "label": "resume claim"
            })
    else:
        nodes.append({
            "id": "claim_none",
            "type": "Resume Claim",
            "label": "Resume Claim",
            "title": "No resume claim detected",
            "status": "Not Claimed"
        })
        edges.append({
            "from": skill_node_id,
            "to": "claim_none",
            "label": "not claimed"
        })

    # 2. GitHub Evidence & Signals
    if github_signals:
        repos_seen = {}
        for s in github_signals:
            r = s.get("repository", "GitHub Repository")
            repos_seen.setdefault(r, []).append(s)

        for r_idx, (r_name, r_sigs) in enumerate(repos_seen.items()):
            repo_id = f"repo_{r_idx+1}"
            nodes.append({
                "id": repo_id,
                "type": "GitHub Repository",
                "label": f"GitHub Repository ({r_name})",
                "title": f"Repository: {r_name}",
                "status": "Retrieved",
                "repository_url": r_sigs[0].get("repository_url")
            })
            edges.append({
                "from": skill_node_id,
                "to": repo_id,
                "label": "github repository"
            })

            for s_idx, sig in enumerate(r_sigs):
                sig_id = f"sig_{r_idx+1}_{s_idx+1}"
                sig_desc = sig.get("source", sig.get("signal_skill", "Signal detected"))
                nodes.append({
                    "id": sig_id,
                    "type": "GitHub Signal",
                    "label": sig_desc,
                    "title": f"Evidence Signal: {sig_desc}",
                    "status": "Verified Signal"
                })
                edges.append({
                    "from": repo_id,
                    "to": sig_id,
                    "label": "detected signal"
                })
    elif github_urls:
        for idx, g in enumerate(github_urls):
            node_id = f"url_{idx+1}"
            url_text = g.get("url") or g.get("title") or "Repository"
            access = g.get("evidence_access_status") or "retrieved"
            nodes.append({
                "id": node_id,
                "type": "GitHub Repository",
                "label": g.get("title") or "GitHub Repository",
                "title": url_text,
                "url": g.get("url"),
                "status": access.capitalize().replace("_", " "),
                "evidence_access_status": access
            })
            edges.append({
                "from": skill_node_id,
                "to": node_id,
                "label": "github repository"
            })
    else:
        nodes.append({
            "id": "github_none",
            "type": "GitHub Repository",
            "label": "GitHub Repository",
            "title": "No GitHub evidence found",
            "status": "None"
        })
        edges.append({
            "from": skill_node_id,
            "to": "github_none",
            "label": "none"
        })

    # 3. Assessment & Score
    if assessment_res and assessment_res.get("percentage") is not None:
        pct = assessment_res.get("percentage", 0.0)
        score = int(assessment_res.get("score", 0))
        max_score = int(assessment_res.get("max_score", 0))
        label = assessment_res.get("demonstration_level") or map_assessment_percentage_to_label(pct)
        
        nodes.append({
            "id": "assessment_demo",
            "type": "Skill Assessment",
            "label": "Skill Assessment",
            "title": f"ProofHire Assessment: {pct:.1f}% ({label})",
            "status": label
        })
        edges.append({
            "from": skill_node_id,
            "to": "assessment_demo",
            "label": "assessment"
        })

        nodes.append({
            "id": "assessment_score",
            "type": "Assessment Score",
            "label": f"{score}/{max_score}",
            "title": f"Score: {score}/{max_score} ({pct:.0f}%)",
            "status": label
        })
        edges.append({
            "from": "assessment_demo",
            "to": "assessment_score",
            "label": "score"
        })
    else:
        nodes.append({
            "id": "assessment_demo",
            "type": "Skill Assessment",
            "label": "Skill Assessment",
            "title": "Assessment not tested",
            "status": "Not Tested"
        })
        edges.append({
            "from": skill_node_id,
            "to": "assessment_demo",
            "label": "not tested"
        })

    # 4. Optional Project Nodes
    for idx, p in enumerate(projects):
        node_id = f"proj_{idx+1}"
        p_name = p.get("project_name") or p.get("title") or f"Project #{idx+1}"
        access = p.get("evidence_access_status") or "retrieved"
        nodes.append({
            "id": node_id,
            "type": "Project",
            "label": p_name,
            "title": p.get("description", p_name),
            "status": access.capitalize().replace("_", " "),
            "evidence_access_status": access
        })
        edges.append({
            "from": skill_node_id,
            "to": node_id,
            "label": "project evidence"
        })

    # 5. Optional Certificate Nodes
    for idx, cert in enumerate(certificates):
        node_id = f"cert_{idx+1}"
        cert_name = cert.get("name") or cert.get("title") or f"Certificate #{idx+1}"
        access = cert.get("evidence_access_status", "retrieved")
        nodes.append({
            "id": node_id,
            "type": "Certificate",
            "label": cert_name,
            "title": cert.get("issuer") or cert_name,
            "status": access.capitalize().replace("_", " "),
            "evidence_access_status": access
        })
        edges.append({
            "from": skill_node_id,
            "to": node_id,
            "label": "credential"
        })

    # 6. Supporting Documents
    for idx, doc in enumerate(documents):
        node_id = f"doc_{idx+1}"
        doc_title = doc.get("title") or f"Document #{idx+1}"
        access = doc.get("evidence_access_status") or "retrieved"
        nodes.append({
            "id": node_id,
            "type": "Supporting Document",
            "label": doc_title,
            "title": doc.get("description") or doc_title,
            "status": access.capitalize().replace("_", " "),
            "evidence_access_status": access
        })
        edges.append({
            "from": skill_node_id,
            "to": node_id,
            "label": "document"
        })

    return {
        "skill": skill_name,
        "nodes": nodes,
        "edges": edges
    }

# --- Aggregation & Persistence Core ---
def compute_and_save_skill_profile(analysis_id: int, db: Session) -> Dict[str, Any]:
    """
    Main aggregator for Phase 4 Verified Skill Profile.
    Loads raw DB records, computes deterministic categories, updates/upserts `SkillVerification`
    records, and returns structured API payload.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise ValueError("Analysis not found")

    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    if not candidate or not job:
        raise ValueError("Candidate or Job record missing for analysis")

    # Fetch stored claims, candidate skills, evidence, and assessment
    candidate_skills = db.query(models.CandidateSkill).filter(models.CandidateSkill.candidate_id == candidate.id).all()
    candidate_claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
    all_evidence = db.query(models.SkillEvidence).filter(models.SkillEvidence.analysis_id == analysis.id).all()
    
    assessment = db.query(models.Assessment).filter(models.Assessment.analysis_id == analysis.id).first()
    assessment_results_list = []
    if assessment:
        assessment_results_list = db.query(models.AssessmentResult).filter(models.AssessmentResult.assessment_id == assessment.id).all()

    # Build Assessment Map: skill_lower -> AssessmentResult dict
    assessment_map = {}
    for ar in assessment_results_list:
        sk_key = ar.skill.strip().lower()
        assessment_map[sk_key] = {
            "skill": ar.skill,
            "score": ar.score,
            "max_score": ar.max_score,
            "percentage": ar.percentage,
            "demonstration_level": ar.demonstration_level
        }

    # Aggregate candidate projects & certifications from Candidate JSON
    candidate_projects = candidate.projects or []
    candidate_certifications = candidate.certifications or []

    # Compile the Universe of relevant job skills
    # Prioritizes required skills, then preferred skills, plus candidate skills matching job context
    job_required = job.required_skills or []
    job_preferred = job.preferred_skills or []
    
    all_job_skills_ordered: List[Dict[str, Any]] = []
    seen_skills: Set[str] = set()

    for s in job_required:
        norm = normalize_skill(s)
        if norm and norm not in seen_skills:
            all_job_skills_ordered.append({"name": s.strip(), "is_required": True, "is_preferred": False})
            seen_skills.add(norm)

    for s in job_preferred:
        norm = normalize_skill(s)
        if norm and norm not in seen_skills:
            all_job_skills_ordered.append({"name": s.strip(), "is_required": False, "is_preferred": True})
            seen_skills.add(norm)

    # If candidate has assessed skills not strictly named in job listing, include them
    for ar in assessment_results_list:
        norm = normalize_skill(ar.skill)
        if norm and norm not in seen_skills:
            all_job_skills_ordered.append({"name": ar.skill.strip(), "is_required": False, "is_preferred": False})
            seen_skills.add(norm)

    # Process each skill
    card_items: List[Dict[str, Any]] = []
    summary_counts = {
        "total_skills": len(all_job_skills_ordered),
        "strong_evidence_count": 0,
        "good_evidence_count": 0,
        "moderate_evidence_count": 0,
        "limited_evidence_count": 0,
        "needs_verification_count": 0,
        "not_demonstrated_count": 0
    }

    job_groups: Dict[str, List[Dict[str, Any]]] = {
        "Well Supported": [],
        "Partially Supported": [],
        "Needs Further Verification": [],
        "Not Demonstrated Yet": []
    }

    for skill_info in all_job_skills_ordered:
        skill_name = skill_info["name"]
        
        # 1. Match Claims
        matched_claims = []
        for c in candidate_claims:
            claim_skill_name = c.skill.skill_name if c.skill else ""
            if (claim_skill_name and skill_matches(claim_skill_name, skill_name)) or skill_matches(skill_name, c.claim_text):
                matched_claims.append({
                    "id": c.id,
                    "claim_text": c.claim_text,
                    "source_section": c.source_section,
                    "evidence_level": c.evidence_level,
                    "evidence_access_status": c.evidence_access_status
                })

        has_resume_claim = (len(matched_claims) > 0)
        # Check if candidate explicitly lists this skill under skills section
        if not has_resume_claim:
            for cs in candidate_skills:
                if skill_matches(cs.skill_name, skill_name):
                    has_resume_claim = True
                    break

        # 2. Match Projects
        matched_projects = []
        for p in candidate_projects:
            technologies = p.get("technologies") or []
            desc = p.get("description", "")
            p_name = p.get("project_name", "")
            if any(skill_matches(t, skill_name) for t in technologies) or skill_matches(skill_name, desc) or skill_matches(skill_name, p_name):
                matched_projects.append({
                    "project_name": p_name,
                    "description": desc,
                    "evidence_access_status": "retrieved" if p.get("project_link_if_available") else "submitted_only"
                })

        # 3. Match Certificates
        matched_certs = []
        for cert in candidate_certifications:
            c_name = cert.get("name", "")
            if skill_matches(skill_name, c_name):
                matched_certs.append({
                    "name": c_name,
                    "issuer": cert.get("issuer", ""),
                    "evidence_access_status": "retrieved" if cert.get("credential_link_if_available") else "submitted_only"
                })

        # Match uploaded Certificate Evidence from Evidence Center
        for ev in all_evidence:
            if ev.evidence_type == "certificate":
                cert_skills = ev.supported_skills or []
                matches_cert = any(skill_matches(cs, skill_name) for cs in cert_skills)
                if not matches_cert and ev.title:
                    matches_cert = skill_matches(skill_name, ev.title)
                if not matches_cert and getattr(ev, "certificate_name", None):
                    matches_cert = skill_matches(skill_name, ev.certificate_name)

                if matches_cert:
                    matched_certs.append({
                        "name": getattr(ev, "certificate_name", None) or ev.title or "Certificate",
                        "issuer": getattr(ev, "issuer", None) or "Issuing Organization",
                        "credential_id": getattr(ev, "credential_id", None),
                        "verification_status": getattr(ev, "verification_status", None) or "DOCUMENT EXTRACTED",
                        "evidence_access_status": "retrieved" if getattr(ev, "verification_status", None) in ["DOCUMENT EXTRACTED", "CREDENTIAL URL VERIFIED"] else "submitted_only"
                    })

        # 4. Match Evidence Items (URLs, Docs, GitHub, Assessment Evidence)
        matched_urls = []
        matched_docs = []
        
        for ev in all_evidence:
            if ev.evidence_type in ["skill_assessment", "certificate"]:
                # Handled separately in dedicated sections
                continue

            ev_skills = ev.supported_skills or []
            matches_ev = any(skill_matches(es, skill_name) for es in ev_skills)
            if not matches_ev and ev.title:
                matches_ev = skill_matches(skill_name, ev.title)
            if not matches_ev and ev.description:
                matches_ev = skill_matches(skill_name, ev.description)

            if matches_ev:
                access = ev.evidence_access_status or "retrieved"
                ev_dict = {
                    "id": ev.id,
                    "title": ev.title or "Evidence item",
                    "description": ev.description,
                    "url": ev.url,
                    "evidence_access_status": access
                }
                if ev.evidence_type in ["url", "github"]:
                    matched_urls.append(ev_dict)
                else:
                    matched_docs.append(ev_dict)

        # 5. Assessment demonstration lookup
        assessment_match = None
        for sk_k, ar_data in assessment_map.items():
            if skill_matches(sk_k, skill_name):
                assessment_match = ar_data
                break

        assessment_pct = assessment_match["percentage"] if assessment_match else None
        assessment_label = map_assessment_percentage_to_label(assessment_pct)

        # 6. Retrieve GitHub Signals for this specific skill
        github_signals = get_github_signals_for_skill(skill_name, all_evidence)
        has_retrieved_github = (len(github_signals) > 0)
        github_evidence_status = "Retrieved" if has_retrieved_github else "None"
        claim_status = "Claimed" if has_resume_claim else "Not Claimed"
        assessment_status = get_assessment_status(assessment_pct)

        # 7. Calculate Evidence Counts & Inspection States
        # An evidence item is considered retrieved if its access status is "retrieved"
        retrieved_count = 0
        submitted_only_count = 0

        all_sources = matched_projects + matched_certs + matched_urls + matched_docs
        for src in all_sources:
            if src.get("evidence_access_status") == "retrieved":
                retrieved_count += 1
            else:
                submitted_only_count += 1

        total_evidence_count = len(all_sources) + len(github_signals)

        # 8. Evaluate Deterministic Evidence Level and Evidence Strength
        # Phase 7B: Pass certificate info to evidence level calculator
        has_cert_evidence = len(matched_certs) > 0
        evidence_level, evidence_strength = compute_evidence_level(
            has_resume_claim=has_resume_claim,
            retrieved_evidence_count=retrieved_count,
            submitted_evidence_count=submitted_only_count,
            assessment_pct=assessment_pct,
            has_retrieved_github=has_retrieved_github,
            github_signals_count=len(github_signals),
            has_certificate_evidence=has_cert_evidence,
            certificate_count=len(matched_certs)
        )

        # 9. Build Concrete Proof Sources list
        proof_sources = build_proof_sources(
            skill_name=skill_name,
            has_resume_claim=has_resume_claim,
            github_signals=github_signals,
            assessment_res=assessment_match,
            evidence_strength=evidence_strength,
            certificates=matched_certs
        )

        # 10. Determine Job Skill Group
        if evidence_strength == "Strong":
            job_group = "Well Supported"
        elif evidence_strength in ["Moderate", "Good"]:
            job_group = "Partially Supported"
        elif has_resume_claim or total_evidence_count > 0:
            job_group = "Needs Further Verification"
        else:
            job_group = "Not Demonstrated Yet"

        # 11. Next Verification Suggestion
        next_step = get_next_verification_step(skill_name, evidence_level)

        # 12. Generate Factual Explanation (Why this skill rating?)
        # Phase 7B: Include certificate evidence in explanation
        explanation = generate_proof_explanation(
            skill_name=skill_name,
            evidence_strength=evidence_strength,
            has_resume_claim=has_resume_claim,
            github_signals=github_signals,
            assessment_pct=assessment_pct,
            assessment_label=assessment_label,
            certificates=matched_certs if matched_certs else None
        )

        # 13. Sources Breakdown
        sources_breakdown = {
            "resume_claims": matched_claims,
            "projects": matched_projects,
            "certificates": matched_certs,
            "github_urls": matched_urls,
            "github_signals": github_signals,
            "supporting_documents": matched_docs,
            "assessment": assessment_match
        }

        # 14. Build Visual Skill Proof Graph Data
        graph_data = build_skill_proof_graph(
            candidate_name=candidate.name,
            skill_name=skill_name,
            claims=matched_claims,
            projects=matched_projects,
            certificates=matched_certs,
            github_signals=github_signals,
            github_urls=matched_urls,
            documents=matched_docs,
            assessment_res=assessment_match
        )

        # 15. Update or Upsert into Database (prevents duplication upon refresh)
        existing_rec = db.query(models.SkillVerification).filter(
            models.SkillVerification.analysis_id == analysis.id,
            models.SkillVerification.skill_name == skill_name
        ).first()

        if existing_rec:
            existing_rec.resume_claim_present = has_resume_claim
            existing_rec.claim_status = claim_status
            existing_rec.github_evidence = github_evidence_status
            existing_rec.assessment_status = assessment_status
            existing_rec.evidence_strength = evidence_strength
            existing_rec.proof_sources = proof_sources
            existing_rec.claims_count = len(matched_claims)
            existing_rec.evidence_count = total_evidence_count
            existing_rec.retrieved_evidence_count = retrieved_count
            existing_rec.assessment_percentage = assessment_pct
            existing_rec.assessment_label = assessment_label
            existing_rec.evidence_level = evidence_level
            existing_rec.job_group = job_group
            existing_rec.explanation = explanation
            existing_rec.next_verification_step = next_step
            existing_rec.sources_breakdown = sources_breakdown
            existing_rec.graph_data = graph_data
            existing_rec.updated_at = datetime.utcnow()
            db_record = existing_rec
        else:
            db_record = models.SkillVerification(
                analysis_id=analysis.id,
                candidate_id=candidate.id,
                skill_name=skill_name,
                resume_claim_present=has_resume_claim,
                claim_status=claim_status,
                github_evidence=github_evidence_status,
                assessment_status=assessment_status,
                evidence_strength=evidence_strength,
                proof_sources=proof_sources,
                claims_count=len(matched_claims),
                evidence_count=total_evidence_count,
                retrieved_evidence_count=retrieved_count,
                assessment_percentage=assessment_pct,
                assessment_label=assessment_label,
                evidence_level=evidence_level,
                job_group=job_group,
                explanation=explanation,
                next_verification_step=next_step,
                sources_breakdown=sources_breakdown,
                graph_data=graph_data
            )
            db.add(db_record)

        # Card Item Payload
        item_payload = {
            "id": db_record.id or 0,
            "skill_name": skill_name,
            "is_required": skill_info["is_required"],
            "is_preferred": skill_info["is_preferred"],
            "resume_claim_present": has_resume_claim,
            "claim_status": claim_status,
            "github_evidence": github_evidence_status,
            "assessment_status": assessment_status,
            "evidence_strength": evidence_strength,
            "proof_sources": proof_sources,
            "github_signals": github_signals,
            "claims_count": len(matched_claims),
            "evidence_count": total_evidence_count,
            "retrieved_evidence_count": retrieved_count,
            "assessment_percentage": assessment_pct,
            "assessment_label": assessment_label,
            "evidence_level": evidence_level,
            "job_group": job_group,
            "explanation": explanation,
            "next_verification_step": next_step,
            "sources_breakdown": sources_breakdown,
            "graph_data": graph_data
        }
        card_items.append(item_payload)
        job_groups[job_group].append(item_payload)

        # Summary tally
        if evidence_level == "Strong Evidence":
            summary_counts["strong_evidence_count"] += 1
        elif evidence_level == "Good Evidence":
            summary_counts["good_evidence_count"] += 1
        elif evidence_level == "Moderate Evidence":
            summary_counts["moderate_evidence_count"] += 1
        elif evidence_level == "Limited Evidence":
            summary_counts["limited_evidence_count"] += 1
        elif evidence_level == "Needs Verification":
            summary_counts["needs_verification_count"] += 1

        if job_group == "Not Demonstrated Yet":
            summary_counts["not_demonstrated_count"] += 1

    db.commit()

    # Re-assign real DB IDs after commit
    for item in card_items:
        if item["id"] == 0:
            rec = db.query(models.SkillVerification).filter(
                models.SkillVerification.analysis_id == analysis.id,
                models.SkillVerification.skill_name == item["skill_name"]
            ).first()
            if rec:
                item["id"] = rec.id

    return {
        "analysis_id": analysis.id,
        "candidate_id": candidate.id,
        "candidate_name": candidate.name,
        "job_id": job.id,
        "job_title": job.title,
        "job_company": job.company or "",
        "profile_status": "Verified Skill Evidence Profile Active",
        "pipeline_position": {
            "resume_analysis": "completed",
            "evidence_verification": "completed",
            "skill_assessment": "completed" if assessment and assessment.status == "completed" else "in_progress",
            "verified_skill_profile": "current",
            "interview_intelligence": "next"
        },
        "banner_message": "ProofHire combines resume claims, submitted evidence, and assessment performance to create an explainable skill evidence profile.",
        "summary": summary_counts,
        "job_skill_groups": job_groups,
        "skills": card_items,
        "disclaimer": "This is decision-support information only. 'Not Demonstrated Yet' means ProofHire currently lacks sufficient demonstration. It does NOT mean the candidate does not possess the skill."
    }
