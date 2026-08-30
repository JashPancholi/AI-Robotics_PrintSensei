from enum import Enum
from backend.engines.diagram.models import DiagramSpecification

class RenderType(str, Enum):

    PILLOW = "pillow"

    AI_IMAGE = "ai_image"


class RenderStrategy:


    def choose(
        self,
        specification: DiagramSpecification
    ) -> RenderType:


        if self._can_render_locally(specification):
            return RenderType.PILLOW


        return RenderType.AI_IMAGE



    def _can_render_locally(
        self,
        specification: DiagramSpecification
    ) -> bool:


        simple_styles = [
            "educational",
            "technical",
            "diagram"
        ]


        return (
            specification.style
            in simple_styles
        )