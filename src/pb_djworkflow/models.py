from django.db import models
from django.contrib.auth.models import User, Group
from celery.result import AsyncResult
from graphql_relay.node.node import to_global_id
from .nodes import ActivationEdge
import datetime

class Process(models.Model):
    created_at = models.DateField(auto_now_add=True)
    closed_at = models.DateField(null=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    flow_class = models.CharField(max_length=255)
    
    status = models.CharField(max_length=20, default='init', choices=(
        ('init', 'Initialised'),
        ('running', 'Running'),
        ('aborted', 'Aborted'),
        ('failed', 'Failed'),
        ('done', 'Done')
    ))

    def get_context(self):
        from .engine import ENGINE
        return ENGINE.context(self)

    def __str__(self):
        return "{}({})".format(self.flow_class, self.pk)

    def aborted(self):
        self.status = 'aborted'

    def failed(self, error):
        self.status = 'failed'
        self.log = str(error)

    def done(self):
        self.status = 'done'
        self.closed_at = datetime.date.today()

class Task(models.Model):
    created_at = models.DateField(auto_now_add=True)
    closed_at = models.DateField(null=True, blank=True)

    done_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks_done')

    assigned_to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    
    process     = models.ForeignKey(Process, on_delete=models.CASCADE, related_name="tasks")
    subprocess  = models.ForeignKey(Process, on_delete=models.SET_NULL, null=True, related_name="supratasks", blank=True)

    deadline = models.DateField(null=True)

    step        = models.CharField(max_length=255)
    status      = models.CharField(max_length=20, default='init', choices=(
        ('init', 'Initalised'),
        ('ready', 'Ready'),
        ('stall', 'Stall'),
        ('submitted', 'Submitted'),
        ('aborted', 'Aborted'),
        ('failed', 'Failed'),
        ('done', 'Done'),
        ('closed', 'Closed')
    ))

    current_job = models.CharField(max_length=255, null=True, blank=True)
    previous = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name="followings", blank=True)

    def toJSON(self):
        return {
            'id': self.id,
            'step': self.id,
            'job': self.current_job
        }

    def __str__(self):
        return "{}::{}({}) [{}]".format(str(self.process), self.step, self.pk, self.status)

    log = models.TextField()

    @property
    def global_id(self):
        return to_global_id("task", self.id)
    
    def ready(self):
        self.status = 'ready'

    def closed(self):
        self.closed = 'closed'
        self.closed_at = datetime.date.today()

    def aborted(self):
        self.status = 'aborted'

    def failed(self, error):
        self.status = 'failed'
        self.log = str(error)

    def done(self):
        self.status = 'done'

    def get_edge(self, *args, **kwargs):
        from django_celery_results.models import TaskResult
        
        if self.current_job is not None:
            result = AsyncResult(self.current_job)
            result = result.get(*args, **kwargs)
            self.refresh_from_db()
            return ActivationEdge.from_json(result)
        
        else:
            self.refresh_from_db()
            return ActivationEdge(self)

class WorkflowContext(models.Model):
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    
    class Meta:
        abstract = True

