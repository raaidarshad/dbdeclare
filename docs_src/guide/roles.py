from dbdeclare.entities import Database, Role


def define_stage(stage: str) -> None:
    Database(name=stage)  # (1)!

    # "groups" aka non-login roles
    etl_writer = Role(name=f"{stage}_etl_writer")
    ml_writer = Role(name=f"{stage}_ml_writer")
    reader = Role(name=f"{stage}_reader")

    # "users" aka login roles
    Role(name=f"{stage}_etl", login=True, password="fake", in_role=[etl_writer, reader])
    Role(name=f"{stage}_ml", login=True, password="fake", in_role=[ml_writer, reader])

    # create log role and grant privileges if not test stage
    if stage != "test":
        log_role = Role(name=f"{stage}_logger")
        Role(name=f"{stage}_api", login=True, password="fake", in_role=[log_role, reader])


def main() -> None:  # (2)!
    stages = ["test", "dev", "prod"]
    for stage in stages:
        define_stage(stage)


if __name__ == "__main__":
    main()
