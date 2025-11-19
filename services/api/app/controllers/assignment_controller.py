from services.api.app.agents.add_work_agent import AddWorkAgent
from services.api.app.agents.assignment_agent import AssignmentAgent
from services.api.app.agents.availability_checker_agent import AvailabilityCheckerAgent
from services.api.app.agents.resource_finder_agent import ResourceFinderAgent
from services.api.app.agents.work_analyzer_agent import WorkAnalyzerAgent
from services.api.app.db.repositories import WorkRequestsRepo


class AssignmentController:
    def __init__(self):
        self.add_agent = AddWorkAgent()
        self.analyzer = WorkAnalyzerAgent()
        self.finder = ResourceFinderAgent()
        self.checker = AvailabilityCheckerAgent()
        self.assigner = AssignmentAgent()

    def add_work(self, payload: dict) -> dict:
        return self.add_agent.run(payload)

    def _run_pipeline_until_scoring(self, work_id: str):
        analysis = self.analyzer.run({"work_id": work_id})
        found = self.finder.run(analysis)
        scored = self.checker.run(found)
        return analysis, found, scored

    def assign(self, work_id: str, llm_provider: str = "template") -> dict:
        analysis, found, scored = self._run_pipeline_until_scoring(work_id)
        assignment_input = {
            **scored,
            "work_type": analysis["work_type"],
            "priority": analysis["priority"],
            "scheduled_timestamp": analysis["scheduled_timestamp"],
        }
        assignment = self.assigner.run(assignment_input, llm_provider=llm_provider)
        return assignment

    def fetch_status(self, work_id: str):
        return WorkRequestsRepo.get_work_by_id(work_id)

    def run_pipeline_verbose(self, work_id: str, llm_provider: str = "template"):
        analysis, found, scored = self._run_pipeline_until_scoring(work_id)
        assignment_input = {
            **scored,
            "work_type": analysis["work_type"],
            "priority": analysis["priority"],
            "scheduled_timestamp": analysis["scheduled_timestamp"],
        }
        assignment = self.assigner.run(assignment_input, llm_provider=llm_provider)
        return {
            "analysis": analysis,
            "candidates": found,
            "scored": scored,
            "assignment": assignment,
        }

