from backend.core.request import Request

from .models import (
    DiagramElement,
    DiagramSpecification
)


class DiagramAnalyzer:

    def analyze(
        self,
        request: Request
    ) -> DiagramSpecification:

        return DiagramSpecification(
            title=request.instruction,
            style="educational",
            orientation="portrait",
            labels=True,
            elements=[
                DiagramElement(
                    name="Placeholder Component",
                    description="Temporary component"
                )
            ]
        )