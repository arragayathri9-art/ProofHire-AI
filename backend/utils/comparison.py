from typing import List

def compare_skills(candidate_skills: List[str], job_required_skills: List[str], job_preferred_skills: List[str]):
    candidate_skills_lower = [s.lower() for s in candidate_skills]
    
    skills_present = []
    potential_skill_gaps = []
    
    # Check required skills
    for skill in job_required_skills:
        if skill.lower() in candidate_skills_lower:
            skills_present.append(skill)
        else:
            potential_skill_gaps.append(skill)
            
    # Check preferred skills
    for skill in job_preferred_skills:
        if skill.lower() in candidate_skills_lower:
            skills_present.append(skill)
        else:
            potential_skill_gaps.append(skill)
            
    # All candidate skills are unverified initially
    skills_requiring_verification = list(candidate_skills)
    
    return {
        "skills_present": skills_present,
        "potential_skill_gaps": potential_skill_gaps,
        "skills_requiring_verification": skills_requiring_verification
    }
