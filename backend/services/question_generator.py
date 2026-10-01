import os
import json
import random
from typing import List, Dict, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
from schemas.schemas import GeneratedQuestionSchema, SelectedSkillPlan
from utils.retry import with_gemini_retry

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

FALLBACK_QUESTION_BANK = {
    "python": [
        {
            "question_type": "mcq",
            "difficulty": "Intermediate",
            "question_text": "What is the primary difference between a Python generator function (using yield) and a standard function returning a list?",
            "options": [
                "A) Generators consume more memory because they pre-compute all items in advance.",
                "B) Generators evaluate lazily on-demand, yielding values one at a time and maintaining minimal memory footprint.",
                "C) Generators can only return integers and strings, while standard functions support any type.",
                "D) Standard functions run asynchronously by default, whereas generators are synchronous."
            ],
            "correct_answer": "B",
            "evaluation_criteria": {
                "expected_answer": "B",
                "explanation": "Generators evaluate lazily on-demand using yield, producing items only when requested and keeping memory consumption low."
            },
            "max_score": 5
        },
        {
            "question_type": "coding",
            "difficulty": "Intermediate",
            "question_text": "What will the following Python code output?\n\n```python\ndef process_items(val, items=[]):\n    items.append(val)\n    return items\n\nprint(process_items(1))\nprint(process_items(2))\n```\nProvide the exact output or explain what happens.",
            "options": [],
            "correct_answer": "[1]\n[1, 2]",
            "evaluation_criteria": {
                "expected_output": "[1]\n[1, 2]",
                "keywords": ["[1]", "[1, 2]", "mutable default", "persists"],
                "explanation": "Default arguments in Python are evaluated once when the function is defined. The list persists across subsequent calls."
            },
            "max_score": 5
        },
        {
            "question_type": "scenario",
            "difficulty": "Advanced",
            "question_text": "A Python web application experiences high memory consumption and latency spikes when processing batch uploads of 500,000 JSON records. How would you architect a streaming or chunked ingestion pipeline in Python to stabilize memory and throughput?",
            "options": [],
            "correct_answer": "Use ijson or chunked stream processing, process records in batched generator chunks (e.g. 1000 items), utilize asynchronous background queues (Celery/RQ) with database bulk inserts, avoid loading entire payload into RAM.",
            "evaluation_criteria": {
                "rubric": {
                    "correctness": "Mentions streaming parsers (ijson, chunking) and avoiding loading full payload into memory (max 2 pts)",
                    "relevance": "Directly addresses memory and latency bottlenecks (max 1 pt)",
                    "reasoning": "Clear pipeline architecture rationale (generators, queues, bulk operations) (max 1 pt)",
                    "completeness": "Addresses both ingestion and database persistence (max 1 pt)"
                }
            },
            "max_score": 5
        },
        {
            "question_type": "short_answer",
            "difficulty": "Intermediate",
            "question_text": "Explain how Python's GIL (Global Interpreter Lock) impacts multi-threaded CPU-bound programs versus I/O-bound programs, and what alternative concurrency model you would use for CPU-heavy tasks.",
            "options": [],
            "correct_answer": "The GIL allows only one native thread to execute Python bytecode at a time. It does not bottleneck I/O-bound programs because threads release the GIL during I/O operations. For CPU-bound tasks, multiprocessing or process pools (e.g. concurrent.futures.ProcessPoolExecutor) should be used instead to utilize multiple CPU cores.",
            "evaluation_criteria": {
                "rubric": {
                    "correctness": "Correctly contrasts CPU-bound vs I/O-bound under the GIL (max 2 pts)",
                    "relevance": "Explains why I/O releases the lock and CPU-bound contends (max 1 pt)",
                    "reasoning": "Identifies multiprocessing/ProcessPoolExecutor as the proper solution for CPU tasks (max 1 pt)",
                    "completeness": "Provides concise, clear technical distinction (max 1 pt)"
                }
            },
            "max_score": 5
        }
    ],
    "sql": [
        {
            "question_type": "mcq",
            "difficulty": "Intermediate",
            "question_text": "In relational databases, what is the key difference between a WHERE clause and a HAVING clause?",
            "options": [
                "A) WHERE filters aggregated rows after GROUP BY; HAVING filters individual rows before grouping.",
                "B) WHERE filters rows before aggregation occurs; HAVING filters aggregated groups after GROUP BY.",
                "C) WHERE can only be used with primary keys; HAVING can be used with any column.",
                "D) WHERE is supported in SQLite, whereas HAVING is only supported in PostgreSQL."
            ],
            "correct_answer": "B",
            "evaluation_criteria": {
                "expected_answer": "B",
                "explanation": "WHERE filters rows before grouping/aggregation; HAVING filters the result set after the GROUP BY aggregation has been applied."
            },
            "max_score": 5
        },
        {
            "question_type": "coding",
            "difficulty": "Intermediate",
            "question_text": "Write a SQL query to find the department name and the average salary of employees in each department, only including departments where the average salary is greater than $75,000.\nAssume table `employees` has columns `department_id`, `salary`, and table `departments` has `id`, `name`.",
            "options": [],
            "correct_answer": "SELECT d.name, AVG(e.salary) FROM departments d JOIN employees e ON d.id = e.department_id GROUP BY d.id, d.name HAVING AVG(e.salary) > 75000;",
            "evaluation_criteria": {
                "expected_output": "SELECT with JOIN, GROUP BY, and HAVING AVG(salary) > 75000",
                "keywords": ["JOIN", "GROUP BY", "HAVING", "AVG"],
                "rubric": {
                    "correctness": "Accurate JOIN, GROUP BY, and HAVING clause (max 2 pts)",
                    "relevance": "Correct filtering on aggregated salary > 75000 (max 1 pt)",
                    "reasoning": "Uses HAVING instead of WHERE for the aggregate condition (max 1 pt)",
                    "completeness": "Includes selected columns and proper table aliases (max 1 pt)"
                }
            },
            "max_score": 5
        },
        {
            "question_type": "scenario",
            "difficulty": "Advanced",
            "question_text": "A query joining two large tables (`orders` with 10M rows and `users` with 2M rows) on `user_id` has suddenly slowed from 200ms to 14 seconds. What diagnostic steps and index strategies would you apply to investigate and resolve this?",
            "options": [],
            "correct_answer": "Run EXPLAIN ANALYZE to inspect query plan (look for sequential table scans vs index scans, hash join vs nested loop). Verify whether an index exists on orders(user_id) and users(id). Check for table statistics staleness (ANALYZE / VACUUM). Consider composite indexing or partitioning if orders has huge volume.",
            "evaluation_criteria": {
                "rubric": {
                    "correctness": "Mentions EXPLAIN / EXPLAIN ANALYZE and verifying indexing on the foreign key column orders(user_id) (max 2 pts)",
                    "relevance": "Addresses the specific 10M row join performance bottleneck (max 1 pt)",
                    "reasoning": "Explains query plan interpretation (sequential scan vs index scan) (max 1 pt)",
                    "completeness": "Suggests index creation, statistics update, or vacuuming (max 1 pt)"
                }
            },
            "max_score": 5
        }
    ],
    "machine learning": [
        {
            "question_type": "mcq",
            "difficulty": "Intermediate",
            "question_text": "When training a model with a severely imbalanced dataset (99% negative class, 1% positive class), which evaluation metric is LEAST informative for true model efficacy?",
            "options": [
                "A) Precision-Recall AUC (PR-AUC)",
                "B) Raw Accuracy",
                "C) F1-Score",
                "D) Balanced Accuracy"
            ],
            "correct_answer": "B",
            "evaluation_criteria": {
                "expected_answer": "B",
                "explanation": "A naive model predicting the negative class 100% of the time achieves 99% raw accuracy while detecting zero true positives, rendering accuracy misleading on imbalanced data."
            },
            "max_score": 5
        },
        {
            "question_type": "short_answer",
            "difficulty": "Intermediate",
            "question_text": "Explain the concept of Data Drift versus Concept Drift in a production machine learning system, and give a concrete example of each.",
            "options": [],
            "correct_answer": "Data drift (covariate shift) occurs when the input feature distribution P(X) changes over time while the relationship to the target P(Y|X) remains constant (e.g. users become younger on an app). Concept drift occurs when the statistical relationship between features and target P(Y|X) changes (e.g. consumer purchasing patterns suddenly shift during a pandemic).",
            "evaluation_criteria": {
                "rubric": {
                    "correctness": "Clearly differentiates between feature distribution shift P(X) and relationship shift P(Y|X) (max 2 pts)",
                    "relevance": "Provides concrete, valid real-world examples for both (max 1 pt)",
                    "reasoning": "Explains the underlying statistical or practical cause (max 1 pt)",
                    "completeness": "Answers both Data Drift and Concept Drift thoroughly (max 1 pt)"
                }
            },
            "max_score": 5
        },
        {
            "question_type": "coding",
            "difficulty": "Intermediate",
            "question_text": "Complete the following Python snippet to prevent data leakage during feature scaling in a scikit-learn machine learning workflow:\n\n```python\nfrom sklearn.preprocessing import StandardScaler\n\n# X_train, X_test already split\nscaler = StandardScaler()\n# TODO: Fit and transform train, and transform test properly\n```\nWrite the correct two lines of code.",
            "options": [],
            "correct_answer": "X_train_scaled = scaler.fit_transform(X_train)\nX_test_scaled = scaler.transform(X_test)",
            "evaluation_criteria": {
                "expected_output": "scaler.fit_transform(X_train)\nscaler.transform(X_test)",
                "keywords": ["fit_transform", "transform"],
                "explanation": "The scaler must be fit ONLY on training data to prevent test set distribution leakage."
            },
            "max_score": 5
        }
    ],
    "fastapi": [
        {
            "question_type": "mcq",
            "difficulty": "Intermediate",
            "question_text": "In FastAPI, what is the primary benefit of declaring route handlers with async def when performing asynchronous database operations?",
            "options": [
                "A) It automatically compiles the Python code to C++ for faster execution.",
                "B) It allows the event loop to switch context and handle other incoming requests concurrently while waiting for I/O.",
                "C) It encrypts all payloads transmitted over the wire using TLS by default.",
                "D) It bypasses Pydantic schema validation for higher throughput."
            ],
            "correct_answer": "B",
            "evaluation_criteria": {
                "expected_answer": "B",
                "explanation": "async def allows the async event loop to handle concurrent requests cooperatively during non-blocking I/O operations."
            },
            "max_score": 5
        },
        {
            "question_type": "coding",
            "difficulty": "Basic",
            "question_text": "In FastAPI, write a minimal endpoint GET `/health` that returns a JSON response `{\"status\": \"healthy\"}` using FastAPI decorator syntax.",
            "options": [],
            "correct_answer": "@app.get('/health')\ndef health_check():\n    return {'status': 'healthy'}",
            "evaluation_criteria": {
                "expected_output": "@app.get('/health')",
                "keywords": ["@app.get('/health')", "return {'status': 'healthy'}", 'return {"status": "healthy"}'],
                "explanation": "Standard FastAPI GET endpoint definition."
            },
            "max_score": 5
        }
    ]
}

def get_fallback_questions_for_skill(skill: str, count: int, difficulty: str) -> List[Dict[str, Any]]:
    skill_lower = skill.lower()
    matched_key = None
    for key in FALLBACK_QUESTION_BANK:
        if key in skill_lower or skill_lower in key:
            matched_key = key
            break
            
    if matched_key:
        bank = FALLBACK_QUESTION_BANK[matched_key]
        questions = []
        for q in bank[:count]:
            item = dict(q)
            item["skill"] = skill
            questions.append(item)
        return questions

    # Generic technical fallback if skill is unique
    return [
        {
            "skill": skill,
            "question_type": "mcq",
            "difficulty": difficulty,
            "question_text": f"In enterprise architecture, what is a fundamental best practice when designing systems utilizing {skill}?",
            "options": [
                f"A) Decouple configuration from business logic and maintain modular component boundaries.",
                f"B) Hardcode environment credentials directly in {skill} modules for faster access.",
                f"C) Disable error logging and monitoring to minimize disk overhead.",
                f"D) Execute all write operations in a single global synchronous lock."
            ],
            "correct_answer": "A",
            "evaluation_criteria": {"expected_answer": "A", "explanation": "Decoupling configuration and maintaining modular architecture is an industry best practice."},
            "max_score": 5
        },
        {
            "skill": skill,
            "question_type": "scenario",
            "difficulty": difficulty,
            "question_text": f"You are tasked with deploying a mission-critical component built with {skill}. During peak traffic, you observe latency degradation. Describe your systematic diagnostic approach and how you would mitigate the bottleneck.",
            "options": [],
            "correct_answer": f"Profile application performance to isolate CPU vs I/O vs network bottlenecks. Check resource saturation (memory/CPU). Review connection pools, caching opportunities, and concurrency limits specific to {skill}.",
            "evaluation_criteria": {
                "rubric": {
                    "correctness": f"Systematic profiling and bottleneck diagnosis relevant to {skill} (max 2 pts)",
                    "relevance": "Directly targets latency and concurrency resolution (max 1 pt)",
                    "reasoning": "Logical troubleshooting workflow (max 1 pt)",
                    "completeness": "Covers both diagnostics and practical mitigation (max 1 pt)"
                }
            },
            "max_score": 5
        }
    ][:count]

@with_gemini_retry("Question Generation Agent")
def generate_questions_for_skill_with_gemini(
    skill: str,
    target_job: str,
    evidence_level_before: str,
    difficulty: str,
    question_count: int,
    candidate_claims_for_skill: List[str],
    question_types_needed: List[str],
    model_name: str = "gemini-3.5-flash"
) -> List[Dict[str, Any]]:
    """
    Generates personalized evaluation questions for a specific skill using Gemini.
    """
    types_str = ", ".join(question_types_needed)
    claims_context = "\n".join([f"- {c}" for c in candidate_claims_for_skill]) if candidate_claims_for_skill else "General professional claim in resume"

    prompt = f"""
    You are the expert Question Generation Agent for "ProofHire AI".
    Generate exactly {question_count} personalized technical assessment questions for the skill: "{skill}".

    CONTEXT:
    Target Job: {target_job}
    Skill: {skill}
    Candidate's Evidence Level Before Assessment: {evidence_level_before}
    Target Difficulty: {difficulty} (Basic, Intermediate, or Advanced)
    Candidate's Relevant Resume Claims:
    {claims_context}

    QUESTION REQUIREMENTS:
    1. Generate exactly {question_count} questions.
    2. The question types should be selected from: [{types_str}].
       - If 'mcq': Must provide exactly 4 options labeled 'A) ...', 'B) ...', 'C) ...', 'D) ...'. 'correct_answer' MUST be the single correct letter ('A', 'B', 'C', or 'D').
       - If 'coding': Must ask candidate to write or predict output of code. Must provide 'correct_answer' with clean reference output or solution, and in 'evaluation_criteria' provide 'expected_output' and deterministic evaluation criteria.
       - If 'scenario': Real-world practical problem-solving. 'evaluation_criteria' must include a rubric breakdown (correctness max 2 pts, relevance max 1 pt, reasoning max 1 pt, completeness max 1 pt).
       - If 'short_answer': Concise technical question. 'evaluation_criteria' must include rubric breakdown.
    3. 'max_score' MUST be 5 for every question.
    4. Questions must test genuine technical understanding, not trivial trivia.
    5. NEVER include protected personal characteristics or bias.

    Return JSON array of questions matching this structure:
    [
      {{
        "skill": "{skill}",
        "question_type": "mcq|scenario|short_answer|coding",
        "difficulty": "{difficulty}",
        "question_text": "...",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "correct_answer": "...",
        "evaluation_criteria": {{ "expected_answer": "...", "rubric": {{ ... }} }},
        "max_score": 5
      }}
    ]
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
        if isinstance(data, list):
            raw_qs = data
        elif isinstance(data, dict):
            raw_qs = data.get("questions") or [data]
        else:
            raw_qs = []
        if raw_qs:
            return raw_qs[:question_count]
    except Exception as e:
        print(f"Gemini Question Generation note for {skill}: {e}")

    # Fallback questions for this skill
    return get_fallback_questions_for_skill(skill, question_count, difficulty)


def generate_full_assessment_questions(
    selected_skills: List[Dict[str, Any]],
    target_job: str,
    claims_by_skill: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
    """
    Coordinates question generation across all selected skills to achieve:
    - 8 to 12 total questions (typically 9-10)
    - Balanced distribution: ~4 MCQ, ~2 Scenario, ~2 Short-Answer, ~2 Coding
    """
    all_questions = []
    
    # Target distribution across the entire assessment:
    # 4 MCQ, 2 scenario, 2 short-answer, 2 coding
    type_pool = ["mcq", "mcq", "mcq", "mcq", "scenario", "scenario", "short_answer", "short_answer", "coding", "coding"]
    random.seed(42) # Deterministic shuffle for consistency
    random.shuffle(type_pool)
    
    pool_idx = 0
    order_counter = 1

    for plan in selected_skills:
        skill = plan.get("skill") or "Technical Skill"
        count = plan.get("question_count", 3)
        diff = plan.get("recommended_difficulty", "Intermediate")
        ev_level = plan.get("evidence_level_before", "Needs Verification")
        claims = claims_by_skill.get(skill.lower(), [])

        # Assign types from pool for this skill
        types_for_skill = []
        for _ in range(count):
            if pool_idx < len(type_pool):
                types_for_skill.append(type_pool[pool_idx])
                pool_idx += 1
            else:
                types_for_skill.append("mcq")

        # Call Question Generation Agent with fallback protection
        try:
            skill_questions = generate_questions_for_skill_with_gemini(
                skill=skill,
                target_job=target_job,
                evidence_level_before=ev_level,
                difficulty=diff,
                question_count=count,
                candidate_claims_for_skill=claims,
                question_types_needed=types_for_skill
            )
        except Exception as err:
            print(f"Notice: Gemini question generation encountered error for {skill} ({err}). Using fallback bank.")
            skill_questions = get_fallback_questions_for_skill(skill, count, diff)

        for q in skill_questions:
            q_dict = dict(q) if isinstance(q, dict) else q.dict()
            q_dict["skill"] = skill
            q_dict["order_num"] = order_counter
            if "max_score" not in q_dict or not q_dict["max_score"]:
                q_dict["max_score"] = 5
            all_questions.append(q_dict)
            order_counter += 1

    return all_questions
