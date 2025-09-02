from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DeleteView, TemplateView
from django.urls import reverse_lazy

from ..models import TimeBlock
from ..forms import TimeBlockForm


class AvailabilityView(LoginRequiredMixin, TemplateView):
    """Manage user's time availability."""
    template_name = 'planner/availability.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_blocks'] = self.request.user.time_blocks.all().order_by('start_time')
        context['form'] = TimeBlockForm()
        return context


class TimeBlockCreateView(LoginRequiredMixin, CreateView):
    """Create a new time block."""
    model = TimeBlock
    form_class = TimeBlockForm
    template_name = 'planner/timeblock_form.html'
    success_url = reverse_lazy('planner:availability')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TimeBlockDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a time block."""
    model = TimeBlock
    template_name = 'planner/timeblock_confirm_delete.html'
    success_url = reverse_lazy('planner:availability')

    def get_queryset(self):
        return TimeBlock.objects.filter(user=self.request.user)
