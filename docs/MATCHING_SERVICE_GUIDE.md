# Matching Service Guide

This file explains what happens inside app/services/matching_service.py in simple technical English.

## What this service does

The matching service finds the best companies for one student profile.

It runs in 3 stages:

1. Hard filters (remove obvious mismatches)
2. TF-IDF + cosine similarity (score text relevance)
3. LLM reranking (semantic final ranking)

Output is a final list of top companies (default: 5).

## Main inputs

The main function is rank_companies(...).

It takes:

- user_profile_text: Combined student text (quiz answers + resume text)
- companies: List of company objects from companies.json
- user_preferences: Preferences like location, CTC range, work mode
- use_llm_ranking: True/False switch for stage 3

## Main output

It returns a list of company objects with extra fields:

- _match_score: Final score shown to user
- _ranking_method: Which path produced the result
- _llm_reason: Reason from LLM (only when LLM reranking succeeds)

## Configuration constants

At top of file:

- TOP_K_TFIDF = 15
- TOP_K_FINAL = 5
- ENABLE_LLM_RANKING = True

Meaning:

- Stage 2 keeps top 15 candidates
- Stage 3 returns final top 5

## Stage 1: Hard filters

Function: apply_hard_filters(...)

Purpose:

- Remove companies that do not satisfy non-negotiable preferences.

Current checks:

- Location:
  - If student asks remote, company must contain remote
  - If student asks indore/bhopal, company can be that city or remote
- CTC range:
  - Parses min-max from preference and keeps only in-range companies
- Work mode:
  - If student asks remote work environment, company must be remote

Why this stage exists:

- It removes bad options early and reduces later compute and LLM cost.

## Stage 2: TF-IDF + cosine similarity

Functions:

- build_company_text(...)
- tfidf_cosine_ranking(...)

How it works:

1. Build one text document per company:
   - role (added twice for extra weight)
   - skills list
   - description
   - location
2. Add student profile as one more document.
3. Vectorize all docs with TfidfVectorizer.
4. Compute cosine similarity between student vector and each company vector.
5. Sort descending and keep top TOP_K_TFIDF.

Vectorizer settings used now:

- stop_words = english
- ngram_range = (1, 2)
- max_features = 5000

Fallback:

- If TF-IDF vectorization fails (for example empty text), it returns original order with score 0.

### Worked example (student vs companies)

Student profile text:

- "Python Django FastAPI backend SQL REST API"

Company A text:

- "Python Django backend APIs PostgreSQL"

Company B text:

- "React frontend JavaScript UI CSS"

Company C text:

- "Python machine learning data science pandas"

What TF-IDF does here:

1. Build a vocabulary from all texts (python, django, react, backend, etc.).
2. Give each term a weight per document.
3. Terms common across many docs get lower importance; selective terms get higher importance.

What cosine similarity does here:

1. Compare student vector with each company vector.
2. Higher cosine score means closer direction, so better text match.

Example output scores (illustrative):

| Company | Cosine Score | Interpretation |

|---|---:|---|
| A | 0.78 | Strong overlap (python, django, backend) |
| C | 0.41 | Partial overlap (python present, role focus differs) |
| B | 0.09 | Low overlap (frontend stack, mostly different terms) |

So Stage 2 ranking becomes:

1. A
2. C
3. B

Then Stage 3 (LLM reranking) can adjust this order if semantic fit suggests a better final ranking.

## Stage 3: LLM reranking

Function: llm_rerank_companies(...)

Purpose:

- Improve ranking quality using semantic reasoning beyond keyword overlap.

How it works:

1. Create a prompt with:
   - student profile (truncated)
   - compact summary of TF-IDF candidates
2. Ask model to return JSON rankings with:
   - index
   - final_score
   - reason
3. Try providers in order:
   - Gemini
   - Groq
   - Ollama
4. Map ranked indexes back to original company objects.

Fallback paths:

- If provider import/call/JSON parsing fails, fallback to TF-IDF scores.
- If use_llm_ranking is False, skip this stage and use TF-IDF only.

## End-to-end flow example

Example with 94 companies:

1. Stage 1 filters to about 70-90
2. Stage 2 picks top 15 by cosine score
3. Stage 3 picks final top 5 with better semantic ordering

In plain words:

- Stage 1 removes companies the student would reject anyway.
- Stage 2 finds keyword and phrase relevance quickly.
- Stage 3 adds judgment (career trajectory, growth fit, practical role alignment).

## Why this design is good

- Fast: hard filter and TF-IDF are cheap
- Cost-aware: LLM sees only a shortlist
- Robust: multiple fallbacks if LLM fails
- Explainable: score and method fields show what happened

## Known limitations (current code)

- Location logic is string-based and rule-based, not geospatial.
- CTC parsing assumes a specific min-max text format.
- LLM prompt uses truncated student profile to control token cost.
- TOP_K values are fixed constants, not dynamic by dataset size.

## Safe tuning knobs

If you want better scale/quality, tune these first:

1. TOP_K_TFIDF: try 20 or 30 when dataset grows
2. TOP_K_FINAL: keep 5 for UI simplicity
3. build_company_text weighting: role repetition and field importance
4. Vectorizer max_features/ngram_range
5. Optional dynamic K formula based on number of companies

## Quick debug checklist

If results look bad:

1. Print filtered company count after stage 1
2. Print top 10 TF-IDF scores and inspect company text quality
3. Check if LLM reranking is actually enabled
4. Check provider fallback logs (Gemini/Groq/Ollama)
5. Verify company data quality in companies.json

## Where to read next

- app/services/matching_service.py: Ranking logic
- app/services/ai_service.py: Provider calls and final analysis prompt
- app/models.py: User preference extraction from quiz answers
