from django.urls import path

from diary.views import (EntryCreateView, EntryDeleteView, EntryDetailView, EntryListView, EntryUpdateView,
                         delete_media, load_entries_ajax, upload_media)

app_name = "diary"

urlpatterns = [
    path("", EntryListView.as_view(), name="entry_list"),
    path("entry/<int:pk>/", EntryDetailView.as_view(), name="entry_detail"),
    path("entry/new/", EntryCreateView.as_view(), name="entry_create"),
    path("entry/<int:pk>/edit/", EntryUpdateView.as_view(), name="entry_update"),
    path("entry/<int:pk>/delete/", EntryDeleteView.as_view(), name="entry_delete"),
    path("upload-media/", upload_media, name="upload_media"),
    path("media/<int:pk>/delete/", delete_media, name="delete_media"),
    path("entries/ajax/", load_entries_ajax, name="entries_ajax"),
]
