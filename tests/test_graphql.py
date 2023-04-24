from itertools import chain
from django import test

from pb_djworkflow.models import Process
from pb_djworkflow.tasks import spawn_flow, activate, submit
from pb_djworkflow.status import STALL, DONE, FAILED, SUBMITTED, CLOSED
from pb_djworkflow.nodes import ActivationEdge

from .case import WorkflowTestCase
from .flows import SimpleFlow
from .models import SimpleContext
from .schema import schema

from graphene.test import Client

# Create your tests here.
class SimpleTestCase(WorkflowTestCase):
    def testSchema(self):
        client = Client(schema)
