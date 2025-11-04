from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.urls import reverse_lazy
from diary.models import DiaryEntry
from diary.forms import DiaryEntryForm


class EntryListView(LoginRequiredMixin, ListView):
    model = DiaryEntry
    template_name = 'diary/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(author=self.request.user)

        # Поиск
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset


class EntryDetailView(LoginRequiredMixin, DetailView):
    model = DiaryEntry
    template_name = 'diary/entry_detail.html'
    context_object_name = 'entry'

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)


class EntryCreateView(LoginRequiredMixin, CreateView):
    model = DiaryEntry
    form_class = DiaryEntryForm
    template_name = 'diary/entry_form.html'
    success_url = reverse_lazy('diary:entry_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EntryUpdateView(LoginRequiredMixin, UpdateView):
    model = DiaryEntry
    form_class = DiaryEntryForm
    template_name = 'diary/entry_form.html'
    context_object_name = 'entry'

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('diary:entry_detail', kwargs={'pk': self.object.pk})


class EntryDeleteView(LoginRequiredMixin, DeleteView):
    model = DiaryEntry
    template_name = 'diary/entry_confirm_delete.html'
    success_url = reverse_lazy('diary:entry_list')
    context_object_name = 'entry'

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)
