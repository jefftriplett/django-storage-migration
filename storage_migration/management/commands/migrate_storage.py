import logging
from optparse import make_option

from django.conf import settings
from django.core.management.base import LabelCommand
from django.core.files.storage import get_storage_class, default_storage
from django.db.models import FileField, get_model

OLD_STORAGE = getattr(settings, 'OLD_STORAGE', {})
OLD_DEFAULT_FILE_STORAGE = getattr(settings, 'OLD_DEFAULT_FILE_STORAGE', default_storage)
if isinstance(OLD_DEFAULT_FILE_STORAGE, str):
    OLD_DEFAULT_FILE_STORAGE = get_storage_class(OLD_DEFAULT_FILE_STORAGE)()

NEW_STORAGE = getattr(settings, 'NEW_STORAGE', {})
NEW_DEFAULT_FILE_STORAGE = getattr(settings, 'NEW_DEFAULT_FILE_STORAGE', default_storage)
if isinstance(NEW_DEFAULT_FILE_STORAGE, str):
    NEW_DEFAULT_FILE_STORAGE = get_storage_class(NEW_DEFAULT_FILE_STORAGE)()

NEW_STORAGE = getattr(settings, 'NEW_STORAGE', {})
NEW_DEFAULT_FILE_STORAGE = getattr(settings, 'NEW_DEFAULT_FILE_STORAGE', default_storage)
if isinstance(NEW_DEFAULT_FILE_STORAGE, str):
    NEW_DEFAULT_FILE_STORAGE = get_storage_class(NEW_DEFAULT_FILE_STORAGE)()

class Command(LabelCommand):
    args = '<app_name.Model app_name.Model2 ...>'
    label = 'model (app_name.ModelName)'
    help = 'Migrate all the FileFields on a given Model to a new Storage backend'
    option_list = LabelCommand.option_list + (
        make_option('--overwrite', '-f', action='store_true', dest='overwrite', help='Overwrite file that exist in the new storage backend'),
        make_option('--to-new', action='store_true', dest='to_new', help='Copy files from the current storage backend to the new storage backend'),
    )

    def handle_label(self, label, **options):
        app_label,model_name = label.split('.')
        model_class = get_model(app_label, model_name)
        if model_class is None:
            return 'Skipped %s. Model not found.' % label
        field_names = []
        old_storages = {}
        for field in model_class._meta.fields:
            if isinstance(field, FileField):
                field_names.append(field.name)
                field_path = '%s.%s' % (label, field.name)
                if options['to_new']:
                    if field_path in NEW_STORAGE:
                        old_storages[field_path] = NEW_STORAGE[field_path]
                    else:
                        old_storages[field_path] = NEW_DEFAULT_FILE_STORAGE
                else:
                    if field_path in OLD_STORAGE:
                        old_storages[field_path] = OLD_STORAGE[field_path]
                    else:
                        old_storages[field_path] = OLD_DEFAULT_FILE_STORAGE
        for instance in model_class._default_manager.all():
            logging.debug('Handling "%s"' % instance)
            # check all field names
            for fn in field_names:
                field = getattr(instance, fn)
                if options['to_new']:
                    new_storage = old_storages['%s.%s' % (label, fn)]
                    old_storage = field.storage
                else:
                    old_storage = old_storages['%s.%s' % (label, fn)]
                    new_storage = field.storage

                if field.name == '':
                    logging.debug('Field is empty, ignoring file.')
                elif field.storage == old_storage:
                    logging.debug('Same storage engine, ignoring file.')
                # do we have multiple files?
                elif hasattr(field, 'names'):
                    for name in field.names:
                        self.move_file(field.storage, old_storage, name, options)
                else:
                    self.move_file(field.storage, old_storage, field.name, options)
        return ''

    def move_file(self, new_storage, old_storage, filename, options):
        'Move the file between storage engines'
        # check whether file exists in old storage
        if not old_storage.exists(filename):
            logging.info('File doesn\'t exist in old storage, ignoring file.')
        # check wether file alread exists in the new storage
        elif not options['overwrite'] and new_storage.exists(filename):
            logging.info('File already exists in storage, ignoring file.')
        else:
            logging.info('Moving file "%s" to new storage.' % filename)
            if not settings.DEBUG:
                f = old_storage.open(filename)
                new_storage.save(filename, f)
            else:
                print 'Created file: %s' % filename

