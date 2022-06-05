import io

import boto3
import humanize
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import StreamingHttpResponse
from django.shortcuts import render


@staff_member_required
def list_backups(request):
    s3 = boto3.client('s3',
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    sql_versions = fetch_versions(s3, 'data.json')
    data_versions = fetch_versions(s3, 'media.zip')

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
def download_backup(request, backup_type, version_id):
    s3 = boto3.client('s3',
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    if backup_type == 'sql':
        key = 'data.json'
    else:
        key = 'media.zip'

    response_object = io.BytesIO()
    s3.download_fileobj(Bucket=settings.BACKUP_BUCKET, Key=key,
                        Fileobj=response_object,
                        ExtraArgs={'VersionId': version_id})
    response_object.seek(0)

    resp = StreamingHttpResponse(streaming_content=response_object)
    resp['Content-Disposition'] = 'attachment; ' \
                                  'filename="{}-{}"'.format(version_id, key)

    return resp


def fetch_versions(s3, key):
    versions = s3.list_object_versions(
        Bucket=settings.BACKUP_BUCKET, Prefix=key)

    sql_versions = []

    for item in versions['Versions']:
        sql_versions.append({'lastmodified': item['LastModified'],
                             'versionid': item['VersionId'],
                             'size': humanize.naturalsize(item['Size'])})

    return sql_versions
