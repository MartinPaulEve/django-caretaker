import humanize
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import StreamingHttpResponse, HttpRequest, HttpResponse
from django.shortcuts import render

from caretaker.backend.abstract_backend import BackendFactory, AbstractBackend


@staff_member_required
def list_backups(request: HttpRequest) -> HttpResponse:
    """
    A Django view showing the list of objects
    :param request: the HttpRequest object
    :return: an HttpResponse
    """
    backend = BackendFactory.get_backend()

    sql_versions = _fetch_versions(backend, 'data.json')
    data_versions = _fetch_versions(backend, 'media.zip')

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
    """
    A view that allows the user to download a backup
    :param request: the HttpRequest object
    :param backup_type: the type of backup ('sql' or 'media.zip')
    :param version_id: the version ID to download
    :return: a StreamingHttpResponse
    """
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


def _fetch_versions(backend: AbstractBackend, key) -> list[dict]:
    """
    Fetches the version list for a remote key from the backend
    :param backend: the backend to use
    :param key: the remote key (filename)
    :return: a list of dictionaries containing 'version_id',
        'last_modified', and 'size'
    """
    versions = backend.versions(
        bucket_name=settings.CARETAKER_BACKUP_BUCKET,
        remote_key=key)

    sql_versions = []

    for item in versions:
        sql_versions.append({'last_modified': item['last_modified'],
                             'version_id': item['version_id'],
                             'size': humanize.naturalsize(item['size'])})

    return sql_versions
