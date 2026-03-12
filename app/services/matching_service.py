import re
import json
from typing import List, Dict, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ====================== Configuration ======================
TOP_K_TFIDF = 15       # Number of candidates from TF-IDF stage
TOP_K_FINAL = 5        # Final number of recommendations
ENABLE_LLM_RANKING = True  # Toggle LLM ranking

# ======================== Phase 1: Hard Filtering ========================
def apply_hard_filters(companies: List[Dict], user_preferences: Optional[Dict]) -> List[Dict]:
    """
    Stage 1: Eliminate companies that don't meet non-negotiable criteria.
    
    Mathematical definition:
    F_hard(s, c) = 1 if constraints satisfied else 0
    
    Args:
        companies: List of all company dicts
        user_preferences: Dict with 'location', 'ctc_range', 'work_environment'
    
    Returns:
        Filtered list of companies passing hard constraints
    """
    if not user_preferences:
        return companies
    
    filtered = []
    location_pref = user_preferences.get('location', '').lower()
    ctc_pref = user_preferences.get('ctc_range', '')
    work_env_pref = user_preferences.get('work_environment', '').lower()
    
    for company in companies:
        # ----- Location Filter -----
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
            # "Anywhere" passes all
        
        # ----- CTC Filter -----
        if ctc_pref and 'ctc' in company:
            if '-' in ctc_pref:
                try:
                    parts = ctc_pref.split('-')
                    min_ctc = int(parts[0].strip().split()[0])
                    max_ctc = int(parts[1].strip().split()[0])
                    company_ctc = company.get('ctc', 0)
                    if company_ctc < min_ctc or company_ctc > max_ctc:
                        continue
                except:
                    pass
        
        # ----- Work Environment Filter -----
        if work_env_pref and 'work_mode' in company:
            company_mode = company.get('work_mode', '').lower()
            if 'remote' in work_env_pref and 'remote' not in company_mode:
                continue
        
        filtered.append(company)
    
    return filtered


# ======================== Phase 2: TF-IDF + Cosine Similarity ========================
def build_company_text(company: Dict) -> str:
    """
    Build searchable text representation of a company.
    Combines role, skills, and description into single document.
    """
    parts = []
    
    # Add role (weighted by repetition)
    role = company.get('role', '')
    if role:
        parts.append(role)
        parts.append(role)  # Repeat for emphasis
    
    # Add skills
    skills = company.get('skills', [])
    if skills:
        parts.append(' '.join(skills))
    
    # Add description
    desc = company.get('description', '')
    if desc:
        parts.append(desc)
    
    # Add location
    location = company.get('location', '')
    if location:
        parts.append(location)
    
    return ' '.join(parts).lower()

# --------------- Function to TF-IDF + Cosine Similarity Ranking -----------------
def tfidf_cosine_ranking(
    user_profile: str,
    companies: List[Dict],
    top_k: int = TOP_K_TFIDF
) -> List[Tuple[float, Dict]]:
    """
    Stage 2: TF-IDF Vectorization + Cosine Similarity ranking.
    
    Mathematical Foundation:
    TF-IDF transforms text into vectors where:
        TF(t,d) = frequency of term t in document d
        IDF(t) = log(N / df(t)) where df(t) = docs containing t
        TF-IDF(t,d) = TF(t,d) × IDF(t)
    
    Cosine Similarity:
        sim(A,B) = (A · B) / (||A|| × ||B||)
    
    Args:
        user_profile: User's combined profile text
        companies: List of company dicts (post hard-filter)
        top_k: Number of top candidates to return
    
    Returns:
        List of (similarity_score, company) tuples, sorted descending
    """
    if not companies:
        return []
    
    # Build company documents
    company_texts = [build_company_text(c) for c in companies]
    
    # Create TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',
        ngram_range=(1, 2),  # Unigrams and bigrams
        max_features=5000,
        min_df=1
    )
    
    # Fit on all documents (companies + user profile)
    all_texts = company_texts + [user_profile.lower()]
    
    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
    except ValueError:
        # Fallback if vectorization fails (e.g., empty texts)
        print("[TF-IDF] Vectorization failed, returning original order")
        return [(0.0, c) for c in companies[:top_k]]
    
    # User vector is the last one, company vectors are the rest
    # Convert to CSR format for proper slicing support
    tfidf_csr = tfidf_matrix.tocsr()  # type: ignore
    n_docs = tfidf_csr.shape[0]
    user_vector = tfidf_csr[n_docs - 1]
    company_vectors = tfidf_csr[:n_docs - 1]
    
    # Calculate cosine similarity
    similarities = cosine_similarity(user_vector, company_vectors).flatten()
    
    # Create scored list
    scored = [(float(similarities[i]), companies[i]) for i in range(len(companies))]
    
    # Sort by similarity descending
    scored.sort(key=lambda x: x[0], reverse=True)
    
    return scored[:top_k]

# ======================== Phase 3: LLM Re-ranking ========================
def llm_rerank_companies(
    user_profile: str,
    candidates: List[Tuple[float, Dict]],
    top_k: int = TOP_K_FINAL
) -> List[Dict]:
    """
    Stage 3: Use LLM to semantically re-rank top candidates.
    
    This provides nuanced ranking considering:
    - Career trajectory alignment
    - Cultural fit indicators
    - Growth potential
    - Hidden relevance patterns
    
    Args:
        user_profile: User's profile text
        candidates: List of (tfidf_score, company) from Stage 2
        top_k: Final number of recommendations
    
    Returns:
        Top-k companies with combined scores
    """
    if not ENABLE_LLM_RANKING or not candidates:
        # Skip LLM ranking, use TF-IDF scores directly
        result = []
        for score, company in candidates[:top_k]:
            company_with_score = company.copy()
            company_with_score['_match_score'] = round(score * 100, 2)
            company_with_score['_ranking_method'] = 'tfidf_only'
            result.append(company_with_score)
        return result
    
    # Prepare prompt for LLM ranking
    candidates_summary = []
    for i, (score, company) in enumerate(candidates):
        candidates_summary.append({
            'index': i,
            'name': company.get('name'),
            'role': company.get('role'),
            'location': company.get('location'),
            'skills': company.get('skills', [])[:5],  # Top 5 skills
            'tfidf_score': round(score * 100, 2)
        })
    
    prompt = f"""You are a career matching expert. Re-rank these {len(candidates)} companies for the student.

STUDENT PROFILE:
{user_profile[:1500]}

CANDIDATE COMPANIES (pre-filtered by TF-IDF similarity):
{json.dumps(candidates_summary, indent=2)}

TASK: 
Analyze semantic fit beyond keyword matching. Consider:
1. Career trajectory alignment
2. Skill growth opportunities  
3. Role-profile match quality

Return a JSON object with:
{{
    "rankings": [
        {{"index": 0, "final_score": 85, "reason": "Strong Python match..."}},
        ...
    ]
}}

Return ONLY the top {top_k} best matches. Order by final_score descending.
Return ONLY valid JSON."""

    # Try to get LLM ranking
    try:
        from app.services.ai_service import call_gemini, call_groq, call_ollama, clean_json_response
        
        llm_response = None
        for name, func in [("Gemini", call_gemini), ("Groq", call_groq), ("Ollama", call_ollama)]:
            try:
                print(f"[LLM Ranking] Attempting {name}...")
                raw = func(prompt)
                llm_response = clean_json_response(raw)
                print(f"[LLM Ranking] Success with {name}")
                break
            except Exception as e:
                print(f"[LLM Ranking] {name} failed: {e}")
                continue
        
        if llm_response and 'rankings' in llm_response:
            # Map LLM rankings back to companies
            result = []
            for rank_item in llm_response['rankings'][:top_k]:
                idx = rank_item.get('index', 0)
                if 0 <= idx < len(candidates):
                    _, company = candidates[idx]
                    company_with_score = company.copy()
                    company_with_score['_match_score'] = rank_item.get('final_score', 0)
                    company_with_score['_llm_reason'] = rank_item.get('reason', '')
                    company_with_score['_ranking_method'] = 'tfidf_llm_hybrid'
                    result.append(company_with_score)
            
            if result:
                return result
    
    except Exception as e:
        print(f"[LLM Ranking] Failed to import/run: {e}")
    
    # Fallback: Use TF-IDF scores
    print("[LLM Ranking] Falling back to TF-IDF scores")
    result = []
    for score, company in candidates[:top_k]:
        company_with_score = company.copy()
        company_with_score['_match_score'] = round(score * 100, 2)
        company_with_score['_ranking_method'] = 'tfidf_fallback'
        result.append(company_with_score)
    return result


# ======================== Main Ranking Function ========================
def rank_companies(
    user_profile_text: str,
    companies: List[Dict],
    user_preferences: Optional[Dict] = None,
    use_llm_ranking: bool = True
) -> List[Dict]:
    """
    Ranks companies using three-stage hybrid algorithm.
    
    Pipeline:
        94 Companies
             │
             ▼ Stage 1: Hard Filters (FREE, instant)
        ~70-90 candidates
             │
             ▼ Stage 2: TF-IDF + Cosine Similarity (FREE, ~10ms)
        Top 15 candidates
             │
             ▼ Stage 3: LLM Re-ranking (API cost, ~2s)
        Top 5 final recommendations
    
    Mathematical Model:
        Stage 2: sim(user, company) = cos(TF-IDF(user), TF-IDF(company))
        Stage 3: LLM semantic re-ranking of top-k
    
    Args:
        user_profile_text: Combined text (quiz answers + resume)
        companies: List of company dicts
        user_preferences: Dict with 'location', 'ctc_range', 'work_environment'
        use_llm_ranking: Whether to use LLM for final ranking
    
    Returns:
        Top 5 companies with match scores attached
    """
    global ENABLE_LLM_RANKING
    ENABLE_LLM_RANKING = use_llm_ranking
    
    print(f"[Matching] Starting hybrid ranking for {len(companies)} companies...")
    
    # ==================== STAGE 1: HARD FILTERING ====================
    filtered_companies = apply_hard_filters(companies, user_preferences)
    print(f"[Matching] Stage 1 (Hard Filters): {len(filtered_companies)}/{len(companies)} remain")
    
    if not filtered_companies:
        print("[Matching] No companies passed filters, returning empty")
        return []
    
    # ==================== STAGE 2: TF-IDF + COSINE ====================
    tfidf_candidates = tfidf_cosine_ranking(
        user_profile_text, 
        filtered_companies, 
        top_k=TOP_K_TFIDF
    )
    
    print(f"[Matching] Stage 2 (TF-IDF Cosine): Top {len(tfidf_candidates)} candidates")
    if tfidf_candidates:
        print("[Matching] TF-IDF scores:")
        for score, c in tfidf_candidates[:5]:
            print(f"  - {c['name']}: {score*100:.1f}%")
    
    # ==================== STAGE 3: LLM RE-RANKING ====================
    if use_llm_ranking:
        print(f"[Matching] Stage 3 (LLM Ranking): Re-ranking top {TOP_K_TFIDF} → {TOP_K_FINAL}")
        final_results = llm_rerank_companies(
            user_profile_text,
            tfidf_candidates,
            top_k=TOP_K_FINAL
        )
    else:
        print(f"[Matching] Stage 3 (Skipped): Using TF-IDF scores directly")
        final_results = []
        for score, company in tfidf_candidates[:TOP_K_FINAL]:
            company_with_score = company.copy()
            company_with_score['_match_score'] = round(score * 100, 2)
            company_with_score['_ranking_method'] = 'tfidf_only'
            final_results.append(company_with_score)
    
    # Log final results
    print(f"[Matching] Final {len(final_results)} recommendations:")
    for c in final_results:
        method = c.get('_ranking_method', 'unknown')
        reason = c.get('_llm_reason', '')[:50] + '...' if c.get('_llm_reason') else ''
        print(f"  - {c['name']}: {c.get('_match_score', 0)}/100 ({method}) {reason}")
    
    return final_results


# ======================== Backward Compatibility Aliases ========================
# These functions maintain compatibility with ai_service.py imports

def hard_filter_companies(companies: List[Dict], user_preferences: Optional[Dict]) -> List[Dict]:
    """Alias for apply_hard_filters - maintains backward compatibility."""
    return apply_hard_filters(companies, user_preferences)


def quick_score_companies(user_profile_text: str, companies: List[Dict], top_k: int = 20) -> List[Dict]:
    """
    Quick scoring using TF-IDF cosine similarity.
    Returns top_k companies with 'score' field attached.
    Maintains backward compatibility with old API.
    """
    if not companies:
        return []
    
    scored = tfidf_cosine_ranking(user_profile_text, companies, top_k=top_k)
    
    # Convert (score, company) tuples to companies with score field
    result = []
    for score, company in scored:
        company_with_score = company.copy()
        company_with_score['score'] = round(score * 100, 2)
        result.append(company_with_score)
    
    return result
