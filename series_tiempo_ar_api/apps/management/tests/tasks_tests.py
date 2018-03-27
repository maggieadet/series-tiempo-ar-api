#!coding=utf8
import os

import mock
import requests
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from unittest import skipIf

from series_tiempo_ar_api.apps.api.models import Field
from series_tiempo_ar_api.apps.management.tasks import read_datajson
from series_tiempo_ar_api.apps.management.models import ReadDataJsonTask, Node

dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'samples')

skip = False
try:
    requests.head('http://infra.datos.gob.ar/catalog/sspm/data.json', timeout=1).raise_for_status()
except requests.exceptions.RequestException:
    skip = True


@skipIf(skip, "Distribuciones remotas caídas")
class ReadDataJsonTest(TestCase):

    def setUp(self):
        self.user = User(username='test', password='test', email='test@test.com', is_staff=True)
        self.user.save()

    def test_read(self):
        identifier = 'test_id'
        Node(catalog_id=identifier,
             catalog_url=os.path.join(dir_path, 'sample_data.json'),
             indexable=True).save()
        task = ReadDataJsonTask()
        task.save()
        read_datajson(task, whitelist=True)
        self.assertTrue(Field.objects.filter(distribution__dataset__catalog__identifier=identifier))

    def test_read_datajson_command(self):
        identifier = 'test_id'
        Node(catalog_id=identifier,
             catalog_url=os.path.join(dir_path, 'sample_data.json'),
             indexable=True).save()
        # Esperado: mismo comportamiento que llamando la función read_datajson
        call_command('read_datajson', whitelist=True)
        self.assertTrue(Field.objects.filter(distribution__dataset__catalog__identifier=identifier))

    def test_read_datajson_while_indexing(self):
        identifier = 'test_id'
        Node(catalog_id=identifier,
             catalog_url=os.path.join(dir_path, 'sample_data.json'),
             indexable=True).save()

        ReadDataJsonTask(status=ReadDataJsonTask.INDEXING).save()

        # Esperado: no se crea una segunda tarea
        call_command('read_datajson')
        self.assertEqual(ReadDataJsonTask.objects.all().count(), 1)

    def test_report_sent(self):
        identifier = 'test_id'
        Node(catalog_id=identifier,
             catalog_url=os.path.join(dir_path, 'sample_data.json'),
             indexable=True).save()

        group = Group.objects.get(name=settings.READ_DATAJSON_RECIPIENT_GROUP)
        self.user.groups.add(group)
        self.user.save()
        from django_rq.queues import Queue
        with mock.patch.object(Queue, 'jobs', 0):
            call_command('read_datajson')

        self.assertEqual(len(mail.outbox), 1)