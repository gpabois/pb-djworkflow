from . import signals, tasks, status
from .engine import ENGINE
from .models import Task

from django.dispatch import receiver

@receiver(signals.closed_workflow)
def reenter_on_closure_supratasks(sender, process, **kwargs):
    for task in Task.objects.filter(subprocess=process):
        tasks.reenter(task.id)
        
@receiver(signals.failed_workflow)
def reenter_on_failure_supratasks(sender, process, **kwargs):
    for task in Task.objects.filter(subprocess=process):
        tasks.reenter(task.id)