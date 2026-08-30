from .models import (
    DiagramSpecification,
    DiagramElement,
    DiagramRelationship
)


class DiagramOptimizer:

    """
    Converts a complex diagram specification
    into a thermal-printer-friendly specification.
    """

    DETAIL_LIMITS = {

    "low": 5,

    "medium": 8,

    "high": 14

}


    def optimize(
        self,
        specification: DiagramSpecification,
        detail_level: str = "medium"
    ) -> DiagramSpecification:


        elements = self._reduce_elements(
            specification.elements,
        detail_level
        )


        relationships = self._reduce_relationships(
            specification.relationships,
            elements
        )


        return DiagramSpecification(

            title=specification.title,

            description=(
                specification.description
                + " Simplified for thermal printing."
            ),

            style="thermal educational line art",

            orientation=specification.orientation,

            labels=True,

            elements=elements,

            relationships=relationships,

            rendering_notes=(
                "Black and white high contrast. "
                "Large labels. Minimal details."
            )
        )


    def _reduce_elements(
    self,
    elements,
    detail_level
    ):

        limit = self.DETAIL_LIMITS.get(
            detail_level,
            8
        )


        sorted_elements = sorted(
            elements,
            key=lambda x: x.importance,
            reverse=True
        )


        return sorted_elements[:limit]


    def _reduce_relationships(
        self,
        relationships: list[DiagramRelationship],
        elements: list[DiagramElement]
    ):

        names = {
            element.name
            for element in elements
        }


        filtered = []


        for relation in relationships:

            if (
                relation.source in names
                and relation.target in names
            ):
                filtered.append(relation)


        return filtered
    