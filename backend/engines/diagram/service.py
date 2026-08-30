from .analyzer import DiagramAnalyzer
from .optimizer import DiagramOptimizer
from .prompt_builder import DiagramPromptBuilder
from backend.core.response import Response
from backend.services.vision.service import VisionService
from backend.services.image.service import ImageGenerationService


class DiagramService:

    def __init__(self):
        self.vision_service = VisionService()
        self.analyzer = DiagramAnalyzer()
        self.optimizer = DiagramOptimizer()
        self.prompt_builder = DiagramPromptBuilder()
        self.image_service = ImageGenerationService()

    def generate(self, request, progress_callback=None):
        report = progress_callback or (lambda progress, stage: None)

        # Step 1: Optional visual perception
        vision_data = None
        if getattr(request, "image", None):
            report(10, "Analyzing reference image")
            vision_data = self.vision_service.analyze(request.image)

        # Step 2: Understand user request (grounded with vision context)
        report(15, "Planning diagram")
        specification = self.analyzer.analyze(
            request=request,
            vision_context=vision_data
        )
        report(35, "Diagram plan ready")

        # Step 3: Optimize for printer
        optimized = self.optimizer.optimize(
            specification,
            request.detail_level
        )
        report(45, "Optimized for 384px printer")

        # Step 4: Create final image prompt
        prompt = self.prompt_builder.build(
            optimized
        )
        report(55, "Image prompt ready")

        # Step 5: Generate image
        report(60, "Generating diagram image")
        image_path = self.image_service.generate(
            prompt,
            request.task.value
        )
        report(90, "Diagram image generated")

        return Response(
            success=True,
            message="Diagram generated successfully",
            payload={
                "specification": optimized,
                "prompt": prompt,
                "image": str(image_path)
            }
        )
