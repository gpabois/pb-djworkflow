from django import test

from celery.result import AsyncResult
from celery.contrib.testing.worker import start_worker
from .celery import app

class WorkflowTestCase(test.TransactionTestCase):
    class Meta:
        abstract=True
        
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.celery_worker = start_worker(
            app, 
            pool="solo", 
            logfile="test.log", 
            loglevel="debug", 
            ping_task_timeout=5
        )
        cls.celery_worker.__enter__()
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.celery_worker.__exit__(None, None, None)
