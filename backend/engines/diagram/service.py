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

    def generate(self, request):
        # Step 1: Optional visual perception (non-fatal: fall back to
        # text-only if the free vision model misbehaves).
        vision_data = None
        if getattr(request, "image", None):
            try:
                vision_data = self.vision_service.analyze(request.image)
            except Exception as exc:  # noqa: BLE001 - vision is best-effort
                print(f"[DiagramService] Vision analysis failed, continuing without it: {exc}")

        # Step 2: Understand user request (grounded with vision context)
        specification = self.analyzer.analyze(
            request=request,
            vision_context=vision_data
        )

        # Step 3: Optimize for printer
        optimized = self.optimizer.optimize(
            specification,
            request.detail_level
        )

        # Step 4: Create final image prompt
        prompt = self.prompt_builder.build(
            optimized
        )

        # Step 5: Generate image
        image_path = self.image_service.generate(
            prompt,
            request.task.value
        )

        return Response(
            success=True,
            message="Diagram generated successfully",
            payload={
                "specification": optimized,
                "prompt": prompt,
                "image": str(image_path)
            }
        )