#! coding: utf-8

from series_tiempo_ar_api.apps.api.models import \
    Catalog, Dataset, Distribution, Field


def setup_database():
    if Catalog.objects.count():  # Garantiza que solo corra una vez
        return

    catalog = Catalog.objects.create(title='test_catalog', metadata='{}')
    dataset = Dataset.objects.create(identifier="132",
                                     metadata={},
                                     catalog=catalog)

    distrib = Distribution.objects.create(identifier='132.1',
                                          metadata='{}',
                                          download_url="invalid_url",
                                          dataset=dataset)
    Field.objects.create(
        series_id='random-0',
        metadata='{}',
        distribution=distrib,
        title='random-0'
    )
