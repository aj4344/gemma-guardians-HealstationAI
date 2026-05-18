#!/usr/bin/env python3
"""
Test script to run 5 symptom queries against local Gamma model.
"""

import sys
import json
import os

# Set environment variables BEFORE importing api
os.environ["OFFLINE_MODE"] = "true"
os.environ["ENABLE_LOCAL_TRIAGE"] = "true"
os.environ["LOCAL_TTS_ENABLED"] = "false"

import api

queries = [
    ("case_1", "I have a mild sore throat and runny nose since yesterday."),
    ("case_2", "I was playing football in hot sun and now I have headache and feel dehydrated."),
    ("case_3", "I have pain on the left side of my chest for 20 minutes with sweating."),
    ("case_4", "I have fever for 3 days with cough and shortness of breath while walking."),
    ("case_5", "My blood sugar was very high today and I am vomiting, very thirsty, and breathing fast."),
]

results = []

for case_id, query in queries:
    try:
        result = api._run_local_gemma_triage(query, 'en')
        
        if result is None:
            results.append({
                "case": case_id,
                "query": query,
                "ok": False,
                "urgency": None,
                "specialist": None,
                "confidence": None,
                "diagnosis": None,
                "reasons": [],
                "actions": [],
                "error": "No response from local Gemma"
            })
        else:
            results.append({
                "case": case_id,
                "query": query,
                "ok": True,
                "urgency": result.get("urgency"),
                "specialist": result.get("specialist"),
                "confidence": result.get("confidence"),
                "diagnosis": result.get("doctor_response"),
                "reasons": result.get("reasons", []),
                "actions": result.get("actions", [])
            })
    except Exception as e:
        results.append({
            "case": case_id,
            "query": query,
            "ok": False,
            "urgency": None,
            "specialist": None,
            "confidence": None,
            "diagnosis": None,
            "reasons": [],
            "actions": [],
            "error": str(e)
        })

# Print JSON output
print(json.dumps(results, indent=2))
