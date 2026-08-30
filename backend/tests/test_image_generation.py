from backend.core.enums import TaskType
from backend.core.request import Request

from backend.engines.diagram.service import DiagramService


request = Request(
    task=TaskType.DIAGRAM,
    instruction="Make me a PEAS (Performance, Environment, Actuators, Sensors) diagram for a self-driving car.",
    detail_level="medium"
)


service = DiagramService()

result = service.generate(request)


print(result)