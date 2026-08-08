from backend.core.request import Request


class DiagramValidator:

    def validate(self, request: Request) -> bool:

        if not request.instruction:
            return False

        if request.instruction.strip() == "":
            return False

        return True