#!/usr/bin/env python3
"""Seed a user's EmployerFlow profile from candidate_profile-style CV data."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models import User, UserProfile

PROFILE = {
    "headline": "AI & Data Engineer | MSc Data Science (Greenwich) | Azure DP-203 | Production RAG & Data Platforms",
    "location": "Hyderabad, India",
    "visa_status": "EU Blue Card Eligible",
    "linkedin": "linkedin.com/in/souramarti",
    "github": "github.com/SVamseekar",
    "phone": "+91-9121661281",
    "certification": "Microsoft Certified: Azure Data Engineer Associate (DP-203, March 2025)",
    "summary": (
        "Data and AI Engineer with an M.Sc. in Data Science (University of Greenwich, Merit) and "
        "Microsoft Certified Azure Data Engineer Associate (DP-203). Experienced in end-to-end data "
        "pipelines on Azure and Databricks, production RAG/LLM agent systems (Gemini, FAISS, Google ADK), "
        "and event-driven microservices. EU Blue Card eligible, open to relocation across Germany, "
        "Netherlands, Ireland, and wider EU."
    ),
    "stack_highlight": (
        "Python, Java 17/21, Spring Boot 3, Databricks, dbt, Azure Data Factory, GCP Cloud Run, "
        "FastAPI, Gemini 2.5 Flash, Google ADK, FAISS, PostgreSQL, Docker, Kubernetes"
    ),
    "skills": [
        "Python", "Java 17/21", "Spring Boot 3", "PySpark", "dbt", "Azure Data Factory",
        "Azure Databricks", "Azure Synapse Analytics", "GCP Cloud Run", "FastAPI",
        "Gemini 2.5 Flash", "Google ADK", "RAG", "FAISS", "BM25", "LangChain",
        "PostgreSQL", "MongoDB", "Redis", "DuckDB", "RabbitMQ", "Docker", "Kubernetes",
        "Power BI", "Tableau", "React 19", "TypeScript", "Flutter", "PaddleOCR",
        "scikit-learn", "TensorFlow", "LightGBM", "ETL/ELT", "Apache Spark",
    ],
    "role_targets": [
        "AI Engineer",
        "Data Platform Engineer",
        "Data Engineer",
        "ML Engineer",
        "Backend Engineer (AI/Data focus)",
    ],
    "relocation_targets": [
        "Germany", "Netherlands", "Ireland", "Austria",
        "Sweden", "Denmark", "Finland", "Belgium", "Switzerland",
    ],
    "languages": {
        "English": "fluent",
        "Telugu": "native",
        "Hindi": "fluent",
        "German": "beginner",
        "Dutch": "beginner",
        "Japanese": "beginner",
    },
    "projects": [
        {
            "name": "WorkforceGuard AI",
            "one_liner": "EU Pay Transparency compliance analytics platform — 26-model dbt pipeline, ML workforce models, EU27 labour market data",
            "themes": [
                "eu compliance", "workforce analytics", "hr analytics", "people analytics",
                "public sector", "govtech", "data platform", "dbt", "fastapi",
                "ai governance", "labour market", "pay gap", "eu policy", "eurostat",
            ],
        },
        {
            "name": "Masova",
            "one_liner": "Event-driven microservices + 8 Google ADK agents with 12-country EU VAT engine — Java/Spring Boot & React Native",
            "themes": [
                "fintech", "event-driven", "microservices", "spring boot", "distributed systems",
                "backend", "java", "rabbitmq", "compliance", "eu vat", "saas", "gemini", "gdpr",
            ],
        },
        {
            "name": "Aequitas",
            "one_liner": "Public transport equity intelligence — 1.75M GTFS trips, geospatial analytics, FAISS RAG policy dashboard",
            "themes": [
                "transport analytics", "smart cities", "public sector analytics", "geospatial",
                "govtech", "mobility", "urban", "infrastructure", "rag", "gtfs",
            ],
        },
        {
            "name": "Bharat Alpha",
            "one_liner": "Production RAG & algorithmic trading for 52 Nifty 50 companies — Gemini 2.5 Flash, FAISS, Spring Boot, GCP",
            "themes": [
                "fintech", "rag", "llm", "ai infrastructure", "data platform",
                "algorithmic trading", "spring boot", "gcp", "supabase",
            ],
        },
        {
            "name": "EU AI Assurance OS",
            "one_liner": "EU AI Act governance control plane — Spring Boot 3, pgvector RAG, Next.js compliance dashboard",
            "themes": [
                "eu ai act", "compliance", "ai governance", "rag", "spring boot",
                "next.js", "pgvector", "audit", "regulatory",
            ],
        },
        {
            "name": "BillSathi",
            "one_liner": "Multi-engine OCR + ML bill classification — PaddleOCR, LightGBM, Gemini, Flutter",
            "themes": ["ocr", "document ai", "classification", "mobile", "fastapi"],
        },
        {
            "name": "Innosolv Trading Platform",
            "one_liner": "Algorithmic trading platform — Java 17, Spring Boot 3, MongoDB, high-frequency NSE derivatives",
            "themes": ["fintech", "java", "spring boot", "mongodb", "event-driven", "backend"],
        },
    ],
}


def main():
    email = sys.argv[1] if len(sys.argv) > 1 else "martisoura@gmail.com"
    db = SessionLocal()
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        print(f"User not found: {email}")
        sys.exit(1)

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        print("Profile row missing")
        sys.exit(1)

    user.full_name = "Marti Soura Vamseekar"

    profile.headline = PROFILE["headline"]
    profile.location = PROFILE["location"]
    profile.visa_status = PROFILE["visa_status"]
    profile.linkedin = PROFILE["linkedin"]
    profile.github = PROFILE["github"]
    profile.phone = PROFILE["phone"]
    profile.certification = PROFILE["certification"]
    profile.summary = PROFILE["summary"]
    profile.stack_highlight = PROFILE["stack_highlight"]
    profile.skills_json = json.dumps(PROFILE["skills"])
    profile.projects_json = json.dumps(PROFILE["projects"])
    profile.languages_json = json.dumps(PROFILE["languages"])
    profile.role_targets_json = json.dumps(PROFILE["role_targets"])
    profile.relocation_targets_json = json.dumps(PROFILE["relocation_targets"])

    db.commit()
    print(f"Profile seeded for {email}")
    print(f"  skills: {len(PROFILE['skills'])}")
    print(f"  projects: {len(PROFILE['projects'])}")
    db.close()


if __name__ == "__main__":
    main()