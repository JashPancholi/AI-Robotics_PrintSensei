from backend.core.request import Request
from backend.core.response import Response

from .validator import DiagramValidator
from .analyzer import DiagramAnalyzer
from .prompt_builder import DiagramPromptBuilder



class DiagramEngine:


    def __init__(self):

        self.validator = DiagramValidator()

        self.analyzer = DiagramAnalyzer()

        self.prompt_builder = DiagramPromptBuilder()



    def run(self, request: Request) -> Response:


        if not self.validator.validate(request):

            return Response(
                success=False,
                message="Invalid diagram request"
            )


        specification = self.analyzer.analyze(request)


        prompt = self.prompt_builder.build(
            specification
        )


        return Response(

            success=True,

            message="Diagram prompt created",

            payload={
                "specification":
                    specification.model_dump(),

                "prompt":
                    prompt
            }

        )