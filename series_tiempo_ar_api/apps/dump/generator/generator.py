import os
import json

from django.conf import settings
from django_datajsonar.models import Field, Catalog

from series_tiempo_ar_api.apps.dump.generator.metadata import MetadataCsvGenerator
from series_tiempo_ar_api.apps.dump.generator.sources import SourcesCsvGenerator
from series_tiempo_ar_api.apps.dump.generator.values_csv import ValuesCsvGenerator
from series_tiempo_ar_api.apps.management import meta_keys
from series_tiempo_ar_api.apps.dump.models import GenerateDumpTask

from .full_csv import FullCsvGenerator


class DumpGenerator:
    dump_dir = os.path.join(settings.MEDIA_ROOT, 'dump')

    def __init__(self, task: GenerateDumpTask, catalog: str = None):
        self.fields = {}
        self.themes = {}

        self.task = task
        self.catalog = catalog
        self.init_data()

        if not os.path.exists(self.dump_dir):
            os.makedirs(self.dump_dir)

    def init_data(self):
        """Inicializa en un diccionario con IDs de series como clave los valores a escribir en cada
        uno de los CSV.
        """
        fields = Field.objects.all()

        if self.catalog:
            try:
                catalog = Catalog.objects.get(identifier=self.catalog)
            except Catalog.DoesNotExist:
                return

            fields = Field.objects.filter(
                distribution__dataset__catalog=catalog
            )

        fields = fields.filter(
            enhanced_meta__key=meta_keys.AVAILABLE,
        ).prefetch_related(
            'distribution',
            'distribution__dataset',
            'distribution__dataset__catalog',
            'enhanced_meta',
        )

        for field in fields:
            meta = json.loads(field.metadata)
            dist_meta = json.loads(field.distribution.metadata)
            dataset_meta = json.loads(field.distribution.dataset.metadata)
            themes = field.distribution.dataset.themes
            theme_labels = get_theme_labels(json.loads(themes)) if themes else ''

            self.fields[field.identifier] = {
                'dataset': field.distribution.dataset,
                'distribution': field.distribution,
                'serie': field,
                'serie_titulo': field.title,
                'serie_unidades': meta.get('units'),
                'serie_descripcion': meta.get('description'),
                'distribucion_titulo': dist_meta.get('title'),
                'distribucion_descripcion': dist_meta.get('description'),
                'distribucion_url_descarga': field.distribution.download_url,
                'dataset_responsable': dataset_meta.get('publisher', {}).get('name'),
                'dataset_fuente': dataset_meta.get('source'),
                'dataset_titulo': field.distribution.dataset.title,
                'dataset_descripcion': dataset_meta.get('description'),
                'dataset_tema': theme_labels,
            }

    def generate(self):
        if not self.fields:
            GenerateDumpTask.info(self.task, f"No hay series cargadas para el catálogo {self.catalog}")
            return

        FullCsvGenerator(self.task, self.fields, self.catalog).generate()
        ValuesCsvGenerator(self.task, self.fields, self.catalog).generate()
        SourcesCsvGenerator(self.task, self.fields, self.catalog).generate()
        MetadataCsvGenerator(self.task, self.fields, self.catalog).generate()


def get_theme_labels(themes: list):
    """Devuelve un string con los labels de themes del dataset separados por comas"""
    labels = []
    for theme in themes:
        labels.append(theme['label'])

    return ','.join(labels)
