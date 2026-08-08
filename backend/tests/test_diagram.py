from backend.core.enums import TaskType
from backend.core.request import Request

from backend.engines.diagram.engine import DiagramEngine


request = Request(
    task=TaskType.DIAGRAM,
    instruction="Create a labeled diagram of a DC Motor."
)

engine = DiagramEngine()

response = engine.run(request)

print(response.model_dump())