from services.api.app.agents.base_agent import BaseAgent
from services.api.app.db.repositories import SpecialtyMappingRepo, WorkRequestsRepo


FALLBACK_SPECIALTIES = {
    "MRI_Brain": ("Neurologist", "General_Radiologist"),
    "CT_Scan_Brain": ("Neurologist", "General_Radiologist"),
    "MRI_Cardiac": ("Cardiologist", "General_Radiologist"),
    "CT_Scan_Chest": ("General_Radiologist", None),
    "X_Ray_Bone": ("Musculoskeletal_Specialist", "General_Radiologist"),
    "X_Ray_Chest": ("General_Radiologist", None),
    "Ultrasound_Abdomen": ("General_Radiologist", None),
    "Mammography": ("Breast_Imaging_Specialist", "General_Radiologist"),
}


class WorkAnalyzerAgent(BaseAgent):
    def run(self, input_data: dict) -> dict:
        work_id = input_data.get("work_id")
        if not work_id:
            raise ValueError("work_id required")
        work = WorkRequestsRepo.get_work_by_id(work_id)
        if not work:
            raise ValueError(f"work_id {work_id} not found")

        mapping = SpecialtyMappingRepo.get_by_work_type(work["work_type"])
        if mapping:
            required = mapping.get("required_specialty")
            alternate = mapping.get("alternate_specialty")
        else:
            required = alternate = None

        if not required:
            fallback_required, fallback_alt = FALLBACK_SPECIALTIES.get(
                work["work_type"], ("General_Radiologist", "General_Radiologist")
            )
            required = fallback_required
            alternate = alternate or fallback_alt

        if not alternate:
            alternate = "General_Radiologist"

        return {
            "work_id": work_id,
            "work_type": work["work_type"],
            "description": work.get("description"),
            "priority": int(work.get("priority", 1)),
            "scheduled_timestamp": work.get("scheduled_timestamp"),
            "required_specialty": required,
            "alternate_specialty": alternate,
        }

