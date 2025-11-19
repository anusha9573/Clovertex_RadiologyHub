# services/api/app/agents/assignment_agent.py
from services.api.app.agents.base_agent import BaseAgent
from services.api.app.db.repositories import (
    ResourceCalendarRepo,
    ResourcesRepo,
    WorkRequestsRepo,
)
from services.api.app.services.llm_client import LLMClient


class AssignmentAgent(BaseAgent):
    def run(self, input_data: dict, llm_provider: str = "template") -> dict:
        scored = input_data.get("scored_candidates", [])
        work_id = input_data.get("work_id")
        if not scored:
            return {
                "work_id": work_id,
                "assigned_to": None,
                "explanation": "No candidate available",
            }

        top = scored[0]
        resource_id = top["resource_id"]
        calendar_id = top.get("calendar_id")

        WorkRequestsRepo.assign_work(work_id, resource_id)
        if calendar_id:
            ResourceCalendarRepo.increment_workload(calendar_id, delta=1)
        ResourcesRepo.increment_cases_handled(resource_id, delta=1)

        llm_input = {
            "work_type": input_data.get("work_type"),
            "priority": input_data.get("priority"),
            "selected_resource": top.get("name"),
            "skill_level": top.get("skill_level"),
            "cases_handled": top.get("total_cases_handled"),
            "availability": top.get("availability_window"),
            "workload": top.get("current_workload"),
        }
        explanation = LLMClient.generate_explanation(llm_input, provider=llm_provider)

        return {
            "work_id": work_id,
            "work_type": input_data.get("work_type"),
            "priority": input_data.get("priority"),
            "scheduled_timestamp": input_data.get("scheduled_timestamp"),
            "assigned_to": resource_id,
            "explanation": explanation,
            "selected": top,
            "scored_candidates": scored,
        }
