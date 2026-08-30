from backend.core.enums import TaskType
from backend.core.request import Request
from backend.engines.diagram.service import DiagramService

# Define a test request including an optional reference image path or base64 data
request = Request(
    task=TaskType.DIAGRAM,
    instruction="Make me a detailed diagram of the computer mouse",
    detail_level="medium",
    image="C:/Users/jash2/AI-Robotics_PrintSensei/backend/tests/test_images/mousetest.jpg"
)

# Initialize service and process the multi-modal diagram request
service = DiagramService()
result = service.generate(request)

print(result)

'''

Make sure `DiagramService.generate()` is configured to inspect `request.image` and route it to `VisionService.analyze()` before calling `DiagramAnalyzer.analyze()`[cite: 1].

'''

# Inside backend/engines/diagram/service.py
vision_data = None
if getattr(request, "image", None):
    vision_data = self.vision_service.analyze(request.image)

diagram_spec = self.analyzer.analyze(
    request=request,
    vision_context=vision_data
)