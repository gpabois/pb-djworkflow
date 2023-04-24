from itertools import chain
from django import test

from pb_djworkflow.models import Process
from pb_djworkflow.tasks import spawn_flow, activate, submit
from pb_djworkflow.status import STALL, DONE, FAILED, SUBMITTED, CLOSED
from pb_djworkflow.nodes import ActivationEdge

from .case import WorkflowTestCase
from .flows import SimpleFlow
from .models import SimpleContext


# Create your tests here.
class SimpleTestCase(WorkflowTestCase):
    def testUserAction(self):
        # Spawn a new workflow
        edge = ActivationEdge.from_flow_spawn(
            spawn_flow(
                SimpleFlow, 
                form_kwargs={'data': {}}
            )
        )
        
        user_action = edge\
            .follow('start')\
            .follow('to_approve')\
            .until_stall().task

        # Submit data
        edge = submit(
            user_action, 
            form_kwargs={
                'data': {
                    'approval_decision': True
                }
            }
        ).to_edge().until_closed()

        assert edge.task.status == CLOSED, edge.task.status
        assert edge.task.process.get_context().approval_decision

        edge\
            .follow('check_approval')\
            .follow('approve')\
            .follow('end')
