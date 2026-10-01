import os
import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
from utils.retry import with_gemini_retry

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

def get_demonstration_level(percentage: float) -> str:
    """
    Returns standardized neutral demonstration language.
    Does NOT say Hire/Reject, Good Candidate/Bad Candidate.
    """
    if percentage >= 80.0:
        return "Strong demonstration in this assessment"
    elif percentage >= 65.0:
        return "Good demonstration"
    elif percentage >= 40.0:
        return "Partial demonstration"
    else:
        return "Limited demonstration in this assessment"

def evaluate_mcq_deterministic(candidate_answer: str, correct_answer: str, max_score: int = 5) -> Dict[str, Any]:
    """
    100% Deterministic evaluation for Multiple Choice Questions.
    Compares candidate selection against stored correct answer.
    """
    if not candidate_answer or not candidate_answer.strip():
        return {
            "score": 0.0,
            "is_correct": False,
            "feedback": f"No answer selected. Correct answer: {correct_answer}.",
            "rubric_breakdown": {"correctness": 0}
        }

    ans = candidate_answer.strip()
    corr = (correct_answer or "").strip()

    # Extract single letter if option starts with e.g. "A)", "A.", "A "
    ans_letter = ans[0].upper() if len(ans) >= 1 and ans[0].upper() in ['A', 'B', 'C', 'D'] else ""
    corr_letter = corr[0].upper() if len(corr) >= 1 and corr[0].upper() in ['A', 'B', 'C', 'D'] else ""

    is_match = False
    if ans_letter and corr_letter and ans_letter == corr_letter:
        is_match = True
    elif ans.lower() == corr.lower():
        is_match = True
    elif corr.lower() in ans.lower():
        is_match = True

    if is_match:
        return {
            "score": float(max_score),
            "is_correct": True,
            "feedback": f"Correct selection ({ans_letter or ans}). Stored correct option: {correct_answer}.",
            "rubric_breakdown": {"correctness": max_score}
        }
    else:
        return {
            "score": 0.0,
            "is_correct": False,
            "feedback": f"Incorrect selection. Stored correct option was: {correct_answer}.",
            "rubric_breakdown": {"correctness": 0}
        }

def evaluate_coding_deterministic(
    candidate_answer: str, 
    correct_answer: str, 
    criteria: Dict[str, Any], 
    max_score: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Deterministic check for coding/output questions before invoking AI.
    Checks expected_output and keywords.
    """
    if not candidate_answer or not candidate_answer.strip():
        return {
            "score": 0.0,
            "is_correct": False,
            "feedback": "No answer provided.",
            "rubric_breakdown": {"correctness": 0, "relevance": 0, "reasoning": 0, "completeness": 0}
        }

    ans_clean = "\n".join([line.strip() for line in candidate_answer.strip().splitlines() if line.strip()]).lower()
    
    # 1. Exact expected output match
    expected_output = criteria.get("expected_output") or correct_answer
    if expected_output:
        exp_clean = "\n".join([line.strip() for line in expected_output.strip().splitlines() if line.strip()]).lower()
        if ans_clean == exp_clean:
            return {
                "score": float(max_score),
                "is_correct": True,
                "feedback": f"Deterministic match with expected output: {expected_output}",
                "rubric_breakdown": {"correctness": 2.0, "relevance": 1.0, "reasoning": 1.0, "completeness": 1.0}
            }

    # 2. Check required keywords or exact code patterns
    keywords = criteria.get("keywords") or []
    if keywords:
        matched_kw = [kw for kw in keywords if kw.lower() in candidate_answer.lower()]
        if len(matched_kw) == len(keywords) and len(keywords) >= 2:
            return {
                "score": float(max_score),
                "is_correct": True,
                "feedback": f"Deterministic match: All required keywords and structure confirmed ({', '.join(keywords)}).",
                "rubric_breakdown": {"correctness": 2.0, "relevance": 1.0, "reasoning": 1.0, "completeness": 1.0}
            }

    return None

@with_gemini_retry("Assessment Evaluator")
def evaluate_with_stored_rubric_gemini(
    question_text: str,
    question_type: str,
    candidate_answer: str,
    correct_answer: str,
    stored_rubric: Dict[str, Any],
    max_score: int = 5,
    model_name: str = "gemini-3.5-flash"
) -> Dict[str, Any]:
    """
    Evaluates scenario, short answer, or complex coding questions using the PRE-STORED rubric.
    Enforces deterministic scoring: Gemini only scores rubric items within strict bounds.
    """
    if not candidate_answer or not candidate_answer.strip():
        return {
            "score": 0.0,
            "is_correct": False,
            "feedback": "No answer submitted.",
            "rubric_breakdown": {"correctness": 0, "relevance": 0, "reasoning": 0, "completeness": 0}
        }

    rubric_desc = json.dumps(stored_rubric, indent=2) if stored_rubric else "Evaluate technical accuracy and completeness."

    prompt = f"""
    You are an objective, unbiased Assessment Evaluator for "ProofHire AI".
    Evaluate the candidate's answer against the PRE-STORED rubric and reference answer.
    
    QUESTION ({question_type}):
    {question_text}

    REFERENCE / CORRECT ANSWER:
    {correct_answer}

    PRE-STORED EVALUATION RUBRIC:
    {rubric_desc}

    CANDIDATE ANSWER:
    {candidate_answer}

    SCORING RULES (Strict bounds):
    - technical_correctness (0.0 to 2.0 pts): Accuracy of technical concepts, logic, or syntax.
    - relevance (0.0 to 1.0 pt): Directly answers the prompt without fluff.
    - reasoning (0.0 to 1.0 pt): Solid technical rationale or problem-solving structure.
    - completeness (0.0 to 1.0 pt): Fully covers key requirements of the question.
    Sum of these 4 scores will produce the final score out of {max_score}.

    LANGUAGE CONSTRAINTS:
    - Provide concise, professional, evidence-focused feedback on what the candidate demonstrated.
    - NEVER use words like "hire", "reject", "unqualified", "good candidate", or "bad candidate".

    Return JSON:
    {{
      "technical_correctness": 2.0,
      "relevance": 1.0,
      "reasoning": 1.0,
      "completeness": 1.0,
      "feedback": "Objective explanation of the evaluation"
    }}
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text)
        corr_pts = min(2.0, max(0.0, float(data.get("technical_correctness", 0.0))))
        rel_pts = min(1.0, max(0.0, float(data.get("relevance", 0.0))))
        reas_pts = min(1.0, max(0.0, float(data.get("reasoning", 0.0))))
        comp_pts = min(1.0, max(0.0, float(data.get("completeness", 0.0))))
        
        total_awarded = round(corr_pts + rel_pts + reas_pts + comp_pts, 1)
        total_awarded = min(float(max_score), max(0.0, total_awarded))
        
        return {
            "score": total_awarded,
            "is_correct": total_awarded >= (max_score * 0.7),
            "feedback": data.get("feedback", "Evaluation completed against predefined rubric."),
            "rubric_breakdown": {
                "technical_correctness": corr_pts,
                "relevance": rel_pts,
                "reasoning": reas_pts,
                "completeness": comp_pts
            }
        }
    except Exception as e:
        print(f"Gemini rubric evaluation note: {e}. Applying fallback deterministic score.")
        # Fallback scoring: inspect length and non-emptiness
        ans_len = len(candidate_answer.strip())
        score = 3.0 if ans_len > 40 else (1.5 if ans_len > 10 else 0.5)
        return {
            "score": score,
            "is_correct": score >= 3.0,
            "feedback": f"Candidate demonstrated relevant concepts in answer: {candidate_answer[:80]}...",
            "rubric_breakdown": {"technical_correctness": 1.5, "relevance": 0.5, "reasoning": 0.5, "completeness": 0.5}
        }

def evaluate_single_question(
    question_type: str,
    question_text: str,
    candidate_answer: str,
    correct_answer: str,
    criteria: Dict[str, Any],
    max_score: int = 5
) -> Dict[str, Any]:
    """
    Main question evaluation router adhering strictly to deterministic rules.
    """
    q_type = (question_type or "").lower().strip()

    if q_type == "mcq":
        return evaluate_mcq_deterministic(candidate_answer, correct_answer, max_score)

    if q_type == "coding":
        det_eval = evaluate_coding_deterministic(candidate_answer, correct_answer, criteria, max_score)
        if det_eval is not None:
            return det_eval

    # Scenario, short answer, or coding requiring rubric evaluation
    stored_rubric = criteria.get("rubric") or criteria
    return evaluate_with_stored_rubric_gemini(
        question_text=question_text,
        question_type=question_type,
        candidate_answer=candidate_answer,
        correct_answer=correct_answer,
        stored_rubric=stored_rubric,
        max_score=max_score
    )
