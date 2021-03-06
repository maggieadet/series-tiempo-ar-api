#! coding: utf-8
import os

from pydatajson import DataJson
from django.test import TestCase
from nose.tools import raises
from series_tiempo_ar.custom_exceptions import FieldFewValuesError

from series_tiempo_ar_api.apps.management.models import ReadDataJsonTask
from series_tiempo_ar_api.libs.indexing.constants import IDENTIFIER, DOWNLOAD_URL, DATASET_IDENTIFIER
from series_tiempo_ar_api.libs.indexing.scraping import Scraper
from series_tiempo_ar_api.libs.indexing.tests.reader_tests import SAMPLES_DIR


class MockDistribution:

    class Dataset:
        def __init__(self, identifier):
            self.identifier = identifier

    def __init__(self, distribution: dict):
        self.identifier = distribution[IDENTIFIER]
        self.download_url = distribution[DOWNLOAD_URL]
        self.dataset = self.Dataset(distribution[DATASET_IDENTIFIER])


class ScrapperTests(TestCase):
    def setUp(self):
        self.task = ReadDataJsonTask()
        self.task.save()
        self.scrapper = Scraper(read_local=True)

    def test_scrapper(self):
        catalog = DataJson(os.path.join(SAMPLES_DIR, 'full_ts_data.json'))
        distribution = catalog.get_distributions(only_time_series=True)[0]

        distribution = MockDistribution(distribution)
        result = self.scrapper.run(distribution, catalog)

        self.assertTrue(result)

    def test_missing_metadata_field(self):
        """No importa que un field no esté en metadatos, se scrapea
        igual, para obtener todas las series posibles
        """

        catalog = DataJson(os.path.join(SAMPLES_DIR, 'missing_field.json'))
        distribution = catalog.get_distributions(only_time_series=True)[0]

        distribution = MockDistribution(distribution)
        result = self.scrapper.run(distribution, catalog)
        self.assertTrue(result)

    @raises(Exception)
    def test_missing_dataframe_column(self):
        """Si falta una columna indicada por los metadatos, no se
        scrapea la distribución
        """

        catalog = DataJson(os.path.join(
            SAMPLES_DIR, 'distribution_missing_column.json'
        ))
        distribution = catalog.get_distributions(only_time_series=True)[0]

        distribution = MockDistribution(distribution)
        self.scrapper.run(distribution, catalog)

    def test_validate_all_zero_series(self):
        catalog = DataJson(os.path.join(
            SAMPLES_DIR, 'ts_all_zero_series.json'
        ))
        distribution = catalog.get_distributions(only_time_series=True)[0]

        distribution = MockDistribution(distribution)
        result = self.scrapper.run(distribution, catalog)
        self.assertTrue(result)

    @raises(FieldFewValuesError)
    def test_validate_all_null_series(self):
        catalog = DataJson(os.path.join(
            SAMPLES_DIR, 'ts_all_null_series.json'
        ))
        distribution = catalog.get_distributions(only_time_series=True)[0]

        distribution = MockDistribution(distribution)
        self.scrapper.run(distribution, catalog)
