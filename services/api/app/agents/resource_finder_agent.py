# services/api/app/agents/resource_finder_agent.py
from services.api.app.agents.base_agent import BaseAgent
from services.api.app.db.repositories import ResourcesRepo

# embeddings FAISS optional
try:
    from services.api.app.services.embeddings import query_faiss_by_text

    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False


class ResourceFinderAgent(BaseAgent):
    def run(self, input_data: dict) -> dict:
        required = input_data.get("required_specialty")
        alternate = input_data.get("alternate_specialty")
        candidates = ResourcesRepo.get_by_specialty([required, alternate])
        # If very few candidates, expand via semantic FAISS (if available)
        if FAISS_AVAILABLE and len(candidates) < 3:
            try:
                q = f"{input_data.get('work_type','')} {input_data.get('description','')}"
                sem = query_faiss_by_text(q, top_k=5)
                ids = [r["id"] for r in sem]
                sem_cands = ResourcesRepo.get_by_ids(ids)
                # merge
                idset = {c["resource_id"] for c in candidates}
                for s in sem_cands:
                    if s["resource_id"] not in idset:
                        candidates.append(s)
            except Exception:
                pass
        return {
            "work_id": input_data["work_id"],
            "candidates": candidates,
            "priority": input_data.get("priority", 1),
            "work_type": input_data.get("work_type"),
            "description": input_data.get("description"),
            "scheduled_timestamp": input_data.get("scheduled_timestamp"),
            "required_specialty": required,
            "alternate_specialty": alternate,
        }
