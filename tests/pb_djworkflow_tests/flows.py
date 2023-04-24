from pb_djworkflow.flows import Workflow, Self, FormBasedContextFactory
from pb_djworkflow import nodes

from .models import SimpleContext
from .forms import SimpleForm, CreateForm

class SimpleFlow(Workflow):
    name = 'simple'
    context_class = SimpleContext
    context_factory = FormBasedContextFactory(CreateForm)

    start = nodes.Branch('to_approve')
    to_approve = nodes.UserAction(SimpleForm, next='check_approval')
    check_approval = nodes.Branch('reject', approve=Self.fn_check_approve)
    approve = nodes.Job(Self.fn_approve, next='end')
    reject = nodes.Job(Self.fn_reject, next='end')
   
    @staticmethod
    def fn_check_approve(activation, **kwargs):
        return activation.context.approval_decision
        
    @staticmethod
    def fn_approve(activation, **kwargs):
        activation.context.approved = True
        activation.context.save()
    
    @staticmethod
    def fn_reject(activation, **kwargs):
        activation.context.approved = False
        activation.context.save()