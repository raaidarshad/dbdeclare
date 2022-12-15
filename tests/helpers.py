from typing import Generator, TypeVar

T = TypeVar("T")
YieldFixture = Generator[T, None, None]
