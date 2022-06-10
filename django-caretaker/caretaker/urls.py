from django.urls import path

from caretaker import views

urlpatterns = [
    path('list/', views.list_backups, name='list_backups'),
    path('download/<str:backup_type>/version/<str:version_id>/',
         views.download_backup, name='download_backup'),
]
