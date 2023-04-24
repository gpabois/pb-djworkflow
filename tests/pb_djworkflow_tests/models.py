from pb_djworkflow.models import WorkflowContext
from django.db import models

class SimpleContext(WorkflowContext):
    approval_decision = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
