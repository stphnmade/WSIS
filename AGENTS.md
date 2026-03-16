# WSIS Agent Instructions

Goal: Build WSIS using modular Python services.

Agents should follow this order:

1. Data ingestion
2. Data normalization
3. Livability scoring engine
4. Reddit sentiment pipeline
5. FastAPI backend
6. Streamlit frontend
7. AWS deployment

Rules:
- Keep modules small
- Separate data pipelines from UI
- Use environment variables
