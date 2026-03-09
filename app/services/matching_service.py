import re

#======================== Function to hard-filter companies (Phase 1) ========================
def hard_filter_companies(companies, user_preferences=None):
    """
    Phase 1: Remove companies that don't match objective criteria (location, CTC, work mode).
    Returns all survivors — no scoring here.
    """
    if not user_preferences:
        return companies

    filtered = []
    location_pref = user_preferences.get('location', '').lower()
    ctc_pref = user_preferences.get('ctc_range', '')
    work_env_pref = user_preferences.get('work_environment', '').lower()

    for company in companies:
        # ----- Filter by location -----
        if location_pref:
            company_location = company.get('location', '').lower()
            if 'remote' in location_pref:
                if 'remote' not in company_location:
                    continue
            elif 'indore' in location_pref:
                if 'indore' not in company_location and 'remote' not in company_location:
                    continue
            elif 'bhopal' in location_pref:
                if 'bhopal' not in company_location and 'remote' not in company_location:
                    continue
            elif 'central india' in location_pref or 'anywhere' in location_pref:
                pass

        # ----- Filter by CTC -----
        if ctc_pref and 'ctc' in company:
            if '-' in ctc_pref:
                try:
                    min_ctc, max_ctc = ctc_pref.split('-')
                    min_ctc = int(min_ctc.strip().split()[0])
                    max_ctc = int(max_ctc.strip().split()[0])
                    company_ctc = company.get('ctc', 0)
                    if company_ctc < min_ctc or company_ctc > max_ctc:
                        continue
                except Exception:
                    pass

        # ----- Filter by work environment -----
        if work_env_pref and 'work_mode' in company:
            company_mode = company.get('work_mode', '').lower()
            if 'remote' in work_env_pref and 'remote' not in company_mode:
                continue

        filtered.append(company)

    print(f"Hard filter: {len(companies)} → {len(filtered)} companies")
    return filtered


#======================== Function to quick-score for pre-ranking (Phase 2) ========================
def quick_score_companies(user_profile_text, companies):
    """
    Phase 2: Fast regex scoring to pre-rank filtered companies.
    Returns top 20 with scores attached (for LLM to do final intelligent ranking).
    """
    profile_lower = user_profile_text.lower()
    scored = []

    for company in companies:
        score = 0
        company_skills = [s.lower() for s in company.get('skills', [])]
        company_role = company.get('role', '').lower()

        # Role Match (+10 points)
        if company_role:
            pattern = rf'\b{re.escape(company_role)}\b'
            if re.search(pattern, profile_lower, re.IGNORECASE):
                score += 10

        # Skill Match (+1 point each)
        for skill in company_skills:
            pattern = rf'\b{re.escape(skill)}\b'
            if re.search(pattern, profile_lower, re.IGNORECASE):
                score += 1

        company_copy = dict(company)
        company_copy['score'] = score
        scored.append(company_copy)

    scored.sort(key=lambda x: x['score'], reverse=True)

    top_20 = scored[:20]
    print(f"Quick score: top 20 scores = {[c['score'] for c in top_20[:5]]}...")
    return top_20
