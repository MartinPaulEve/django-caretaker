import humanize
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import StreamingHttpResponse, HttpRequest, HttpResponse
from django.shortcuts import render

from caretaker.backend.abstract_backend import BackendFactory, AbstractBackend


@staff_member_required
def list_backups(request: HttpRequest) -> HttpResponse:
    backend = BackendFactory.get_backend()

    sql_versions = fetch_versions(backend, 'data.json')
    data_versions = fetch_versions(backend, 'media.zip')

    template = 'backup_list.html'

    context = {'sql_versions': sql_versions,
               'data_versions': data_versions,
               }

    return render(
        request,
        template,
        context,
    )


@staff_member_required
def download_backup(request: HttpRequest, backup_type: str, version_id: str) \
        -> StreamingHttpResponse:
    backend = BackendFactory.get_backend()

    if backup_type == 'sql':
        key = 'data.json'
    else:
        key = 'media.zip'

    response_object = backend.get_object(
        bucket_name=settings.CARETAKER_BACKUP_BUCKET,
        remote_key=key, version_id=version_id)

    resp = StreamingHttpResponse(streaming_content=response_object)
    resp['Content-Disposition'] = 'attachment; ' \
                                  'filename="{}-{}"'.format(version_id, key)

    return resp


def fetch_versions(backend: AbstractBackend, key) -> list[dict]:
    versions = backend.versions(
        bucket_name=settings.CARETAKER_BACKUP_BUCKET,
        remote_key=key)

    sql_versions = []

    for item in versions:
        sql_versions.append({'lastmodified': item['last_modified'],
                             'versionid': item['version_id'],
                             'size': humanize.naturalsize(item['size'])})

    return sql_versions
