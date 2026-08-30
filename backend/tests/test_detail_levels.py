from backend.core.enums import TaskType
from backend.core.request import Request

from backend.engines.diagram.analyzer import DiagramAnalyzer
from backend.engines.diagram.optimizer import DiagramOptimizer


instruction = (
    "Create a labeled diagram of the human heart"
)


analyzer = DiagramAnalyzer()

optimizer = DiagramOptimizer()



for level in [
    "low",
    "medium",
    "high"
]:

    print("\n================")
    print(level.upper())
    print("================")


    request = Request(
        task=TaskType.DIAGRAM,
        instruction=instruction,
        detail_level=level
    )


    spec = analyzer.analyze(request)


    optimized = optimizer.optimize(
        spec,
        request.detail_level
    )


    print(
        "Elements:",
        len(optimized.elements)
    )


    for element in optimized.elements:
        print(
            "-",
            element.name,
            element.importance
        )