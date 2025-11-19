# services/api/app/agents/base_agent.py
class BaseAgent:
    def run(self, input_data: dict) -> dict:
        raise NotImplementedError
