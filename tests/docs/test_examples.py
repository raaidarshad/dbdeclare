from dbdeclare.entities.entity import Entity
from docs_src.guide.databases import main as databases_main
from docs_src.guide.grants import main as grants_main
from docs_src.guide.roles import main as roles_main
from docs_src.guide.schemas import main as schemas_main
from docs_src.guide.tables import main as content_main


def test_databases_main() -> None:
    databases_main()
    Entity.entities = []


def test_roles_main() -> None:
    roles_main()
    Entity.entities = []


def test_schemas_main() -> None:
    schemas_main()
    Entity.entities = []


def test_content_main() -> None:
    content_main()
    Entity.entities = []


def test_grants_main() -> None:
    grants_main()
    Entity.entities = []


def test_controller_main() -> None:
    pass
