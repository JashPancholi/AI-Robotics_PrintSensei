from backend.core.enums import TaskType
from backend.core.request import Request

from backend.engines.diagram.engine import DiagramEngine


def main():

    request = Request(
        task=TaskType.DIAGRAM,
        instruction="Create a labeled diagram of the human heart"
    )

    engine = DiagramEngine()

    response = engine.run(request)

    print("\n===== RESULT =====\n")

    print(response.model_dump())


if __name__ == "__main__":
    main()