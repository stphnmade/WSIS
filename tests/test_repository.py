from wsis.data.repositories.factory import get_city_repository
from wsis.data.repositories.normalized import NormalizedCityRepository


def test_normalized_repository_returns_city_metrics() -> None:
    repository = NormalizedCityRepository()

    cities = repository.list_city_metrics()

    assert len(cities) == 10
    assert any(city.slug == "raleigh-nc" for city in cities)


def test_repository_factory_defaults_to_normalized_backend() -> None:
    repository = get_city_repository()

    assert isinstance(repository, NormalizedCityRepository)
