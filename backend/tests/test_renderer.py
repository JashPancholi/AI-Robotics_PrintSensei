from backend.renderers.strategy import RenderStrategy

from backend.engines.diagram.models import (
    DiagramSpecification
)


spec = DiagramSpecification(

    title="DC Motor",

    description="Educational diagram",

    style="educational"

)


strategy = RenderStrategy()


result = strategy.choose(spec)


print(result)