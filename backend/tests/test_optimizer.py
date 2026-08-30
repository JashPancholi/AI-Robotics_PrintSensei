from backend.engines.diagram.optimizer import DiagramOptimizer
from backend.engines.diagram.analyzer import DiagramAnalyzer

from backend.core.enums import TaskType
from backend.core.request import Request


request = Request(

    task=TaskType.DIAGRAM,

    instruction=
    "Create a labeled diagram of the human heart"

)


analyzer = DiagramAnalyzer()

raw_spec = analyzer.analyze(request)


print("\nBEFORE:")
print(
    len(raw_spec.elements),
    "elements"
)


optimizer = DiagramOptimizer()


optimized = optimizer.optimize(
    raw_spec
)


print("\nAFTER:")
print(
    len(optimized.elements),
    "elements"
)


print(
    optimized.model_dump()
)