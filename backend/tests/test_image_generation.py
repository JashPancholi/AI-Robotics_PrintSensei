from backend.core.enums import TaskType
from backend.core.request import Request
from backend.engines.diagram.service import DiagramService

# Define a test request including an optional reference image path or base64 data
request = Request(
    task=TaskType.DIAGRAM,
    instruction="Make me a detailed labeled diagram of the IEM in the reference image including its internals as well",
    detail_level="medium",
    image="backend/tests/test_images/iem.jpg"
)

# Initialize service and process the multi-modal diagram request
service = DiagramService()
result = service.generate(request)

print(result)
