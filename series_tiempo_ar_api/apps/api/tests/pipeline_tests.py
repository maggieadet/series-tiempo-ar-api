#! coding: utf-8
from django.test import TestCase

from series_tiempo_ar_api.apps.api.pipeline import \
    NameAndRepMode, Collapse, Pagination, DateFilter
from series_tiempo_ar_api.apps.api.query.query import Query
from .helpers import setup_database


class NameAndRepModeTest(TestCase):
    """Testea el comando que se encarga del parámetro 'ids' de la
    query: el parseo de IDs de series y modos de representación de las
    mismas.
    """
    single_series = 'random-0'
    single_series_rep_mode = 'random-0:percent_change'

    @classmethod
    def setUpClass(cls):
        setup_database()
        super(cls, NameAndRepModeTest).setUpClass()

    def setUp(self):
        self.cmd = NameAndRepMode()
        self.query = Query()

    def test_invalid_series(self):
        invalid_series = 'invalid'
        self.cmd.run(self.query, {'ids': invalid_series})
        self.assertTrue(self.cmd.errors)

    def test_valid_series(self):
        self.cmd.run(self.query, {'ids': self.single_series})
        self.assertFalse(self.cmd.errors)


class CollapseTest(TestCase):
    single_series = 'random-0'

    def setUp(self):
        self.query = Query()
        self.cmd = Collapse()

    def test_valid_aggregation(self):
        self.cmd.run(self.query, {'ids': self.single_series,
                                  'collapse:': 'year',
                                  'collapse_aggregation': 'sum'})
        self.assertFalse(self.cmd.errors)

    def test_invalid_aggregation(self):
        self.cmd.run(self.query, {'ids': self.single_series,
                                  'collapse': 'year',
                                  'collapse_aggregation': 'INVALID'})
        self.assertTrue(self.cmd.errors)


class PaginationTests(TestCase):
    single_series = 'random-0'

    limit = 1000
    start = 50

    def setUp(self):
        self.query = Query()
        self.cmd = Pagination()

    @classmethod
    def setUpClass(cls):
        setup_database()
        super(cls, PaginationTests).setUpClass()

    def test_start(self):
        params = {'ids': self.single_series, 'limit': self.limit}

        # Query sin offset
        other_query = Query()
        self.cmd.run(other_query, params)
        other_query.run()

        # Query con un offset de 'start'
        params_start = params.copy()
        params_start['start'] = self.start
        self.cmd.run(self.query, params_start)
        self.query.run()

        self.assertEqual(self.query.data[0], other_query.data[self.start])

    def test_limit(self):
        self.cmd.run(self.query, {'ids': self.single_series,
                                  'limit': self.limit})
        self.query.run()
        self.assertEqual(len(self.query.data), self.limit)

    def test_invalid_start_parameter(self):
        self.cmd.run(self.query, {'ids': self.single_series,
                                  'start': 'not a number'})
        self.query.run()
        self.assertTrue(self.cmd.errors)

    def test_invalid_limit_parameter(self):
        self.cmd.run(self.query, {'ids': self.single_series,
                                  'limit': 'not a number'})
        self.assertTrue(self.cmd.errors)


class DateFilterTests(TestCase):
    single_series = 'random-0'

    start_date = '2010-01-01'
    end_date = '2015-01-01'

    def setUp(self):
        self.query = Query()
        self.cmd = DateFilter()

    @classmethod
    def setUpClass(cls):
        setup_database()
        super(cls, DateFilterTests).setUpClass()

    def test_start_date(self):
        self.cmd.run(self.query, {'start_date': self.start_date})

        self.query.run()

        first_timestamp = self.query.data[0][0]
        self.assertEqual(self.start_date, first_timestamp)

    def test_end_date(self):
        self.cmd.run(self.query, {'end_date': self.end_date})

        self.query.add_series('random-0', 'value')
        # Me aseguro que haya suficientes resultados
        self.query.add_pagination(start=0, limit=1000)
        self.query.run()

        last_timestamp = self.query.data[-1][0]
        self.assertEqual(self.end_date, last_timestamp)

    def test_invalid_start_date(self):
        self.cmd.run(self.query, {'start_date': 'not a date'})
        self.assertTrue(self.cmd.errors)

    def test_invalid_end_date(self):
        self.cmd.run(self.query, {'end_date': 'not a date'})
        self.assertTrue(self.cmd.errors)
