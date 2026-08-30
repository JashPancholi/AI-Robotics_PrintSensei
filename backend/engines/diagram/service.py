from .analyzer import DiagramAnalyzer
from .optimizer import DiagramOptimizer
from .prompt_builder import DiagramPromptBuilder
from backend.core.response import Response
from backend.services.image.service import ImageGenerationService


class DiagramService:


    def __init__(self):

        self.analyzer = DiagramAnalyzer()

        self.optimizer = DiagramOptimizer()

        self.prompt_builder = DiagramPromptBuilder()

        self.image_service = ImageGenerationService()



    def generate(self, request):

        # Step 1: Understand user request
        specification = (
            self.analyzer.analyze(request)
        )


        # Step 2: Optimize for printer
        optimized = (
            self.optimizer.optimize(
                specification,
                request.detail_level
            )
        )


        # Step 3: Create final image prompt
        prompt = (
            self.prompt_builder.build(
                optimized
            )
        )


        # Step 4: Generate image
        image_path = (
            self.image_service.generate(
                prompt,
                request.task.value
            )
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