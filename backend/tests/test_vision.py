from backend.services.vision.service import VisionService


service = VisionService()


result = service.analyze(
    "C:/Users/jash2/AI-Robotics_PrintSensei/backend/tests/test_images/mousetest.jpg"
)


print(result.model_dump())