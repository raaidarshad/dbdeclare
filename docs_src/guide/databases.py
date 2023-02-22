from dbdeclare.entities import Database


def define_stage(stage: str) -> None:
    Database(name=stage)


def main() -> None:
    stages = ["test", "dev", "prod"]
    for stage in stages:
        define_stage(stage)


if __name__ == "__main__":
    main()
