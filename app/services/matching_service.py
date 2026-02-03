import re

#======================== Function to rank companies ========================
def rank_companies(user_profile_text, companies, user_preferences=None):
    """
    Ranks companies based on user profile with strict matching and filtering.
    
    Args:
        user_profile_text: Combined text (answers + resume)
        companies: List of company dicts
        user_preferences: Dict with 'location', 'ctc_range', 'work_environment'
    
    Returns:
        Top 5 companies
    """
    print(f"Ranking {len(companies)} companies...")
    
    # Normalize user profile
    profile_lower = user_profile_text.lower()
    
    # ------------------------ PHASE 1: HARD FILTERING ------------------------
    filtered_companies = []
    
    if user_preferences: # Based on user preferences
        location_pref = user_preferences.get('location', '').lower()
        ctc_pref = user_preferences.get('ctc_range', '')
        work_env_pref = user_preferences.get('work_environment', '').lower()
        
        for company in companies:

            # ----- Filter by location ----- 
            if location_pref:
                company_location = company.get('location', '').lower()
                
                # If user wants "Remote"
                if 'remote' in location_pref:
                    if 'remote' not in company_location:
                        continue  # Skip non-remote if user wants remote
                # If user wants specific city
                elif 'indore' in location_pref:
                    if 'indore' not in company_location and 'remote' not in company_location:
                        continue
                elif 'bhopal' in location_pref:
                    if 'bhopal' not in company_location and 'remote' not in company_location:
                        continue
                # "Anywhere in Central India" - allow Indore, Bhopal, Remote
                elif 'central india' in location_pref or 'anywhere' in location_pref:
                    pass  # Include all
            
            # ----- Filter by CTC ----- 
            if ctc_pref and 'ctc' in company:
                # Parse user CTC range (e.g., "3-5 LPA", "8-12 LPA")
                if '-' in ctc_pref:
                    try:
                        min_ctc, max_ctc = ctc_pref.split('-')
                        min_ctc = int(min_ctc.strip().split()[0])  # Extract number
                        max_ctc = int(max_ctc.strip().split()[0])
                        
                        company_ctc = company.get('ctc', 0)
                        if company_ctc < min_ctc or company_ctc > max_ctc:
                            continue  # Skip if outside range
                    except:
                        pass  # Ignore parsing errors
            
            # ----- Filter by work environment ----- 
            if work_env_pref and 'work_mode' in company:
                company_mode = company.get('work_mode', '').lower()
                if 'remote' in work_env_pref and 'remote' not in company_mode:
                    continue
            
            # Append company to filtered list
            filtered_companies.append(company)

    else:
        # No preferences, use all companies
        filtered_companies = companies
    
    print(f"After filtering: {len(filtered_companies)} companies remain")
    
    # ------------------------ PHASE 2: SCORING ------------------------
    scored_companies = []
    
    for company in filtered_companies:
        score = 0
        
        # Normalize company data
        company_skills = [s.lower() for s in company.get('skills', [])]
        company_role = company.get('role', '').lower()
        
        # 1. Role Match (HIGH PRIORITY: +10 points)
        # Use regex word boundary to avoid partial matches
        if company_role:
            pattern = rf'\b{re.escape(company_role)}\b'
            if re.search(pattern, profile_lower, re.IGNORECASE):
                score += 10
        
        # 2. Skill Match (LOW PRIORITY: +1 point each)
        for skill in company_skills:
            # Use word boundary to prevent "Java" matching "JavaScript"
            pattern = rf'\b{re.escape(skill)}\b'
            if re.search(pattern, profile_lower, re.IGNORECASE):
                score += 1
        
        # Append company with score
        scored_companies.append((score, company))
    
    # --------------------- --- PHASE 3: SORT & RETURN TOP 5 ------------------------
    scored_companies.sort(key=lambda x: x[0], reverse=True)
    
    # Debug: Print top scores and companies
    print(f"Top 5 scores: {[s[0] for s in scored_companies[:5]]}")
    print(f"Top 5 companies names: {[s[1]['name'] for s in scored_companies[:5]]}")
    
    return [c[1] for c in scored_companies[:5]]
