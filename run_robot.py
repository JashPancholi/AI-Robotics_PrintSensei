import logging

from app.hardware.simulator import RobotSimulator


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    RobotSimulator().start(interactive=True)


if __name__ == "__main__":
    main()
