from typing  import Type
from collections import namedtuple
from django.db import transaction

from . import exceptions, models

TaskSpawn = namedtuple('TaskSpawn', ['task', 'job'])
FlowSpawn = namedtuple('FlowSpawn', ['context', 'process', 'start_spawn'])

class Engine:
    def __init__(self):
        self.flows = {}

    def register(self, cls):
        self.flows[cls.get_name()] = cls

    def flow(self, flow):
        if isinstance(flow, str):
            return self.flows[flow]
        else:
            if flow.get_name() not in self.flows:
                self.register(flow)   
            
            return self.flow(flow.get_name())         

    def context(self, process):
        """
            Returns the context behind a process
        """
        flow = self.flow(process.flow_class)
        return flow.context(process)        
    
    def spawn_flow(self, flow, **kwargs):
        """
            Spawn a workflow

            Returns: context, process, start_task
        """
        flow = self.flow(flow)
        process = models.Process(flow_class=flow.get_name())

        if "user" in kwargs:
            process.created_by = kwargs['user']
            
        process.save()

        context = flow.context_factory(
            context_class=flow.context_class, 
            process=process, 
            **kwargs
        )
        
        task_spawn = self.spawn_task(
            "start", 
            process, 
            **kwargs
        )
        
        return FlowSpawn(context=context, process=process, start_spawn=task_spawn)
            
    def spawn_task(self, step, process, previous=None, **kwargs):
        """
            Create a task
        """
        from .tasks import activate
        
        flow = self.flow(process.flow_class)
        node = flow.node(step)
        
        task = models.Task(process=process, step=step)
        
        if "user" in kwargs:
            task.assigned_to_user = kwargs['user']
            del kwargs['user']
            
        task.previous = previous
        task.save()
        
        job = activate.delay(task.id)
        
        task.current_job = job.task_id
        task.save()
        
        job.forget()

        return TaskSpawn(task=task, job=job)

    def submit(self, task: models.Task, **kwargs):
        from .nodes import node_activation
        
        try:
            flow    = self.flow(task.process.flow_class)
            context = flow.context(task.process)
            node    = flow.node(task.step)

            if "user" in kwargs:
                task.done_by = kwargs['user']

            with node_activation(task=task, engine=self, context=context) as activation:
                node.submit(activation=activation, **kwargs)
                return activation
        
        except exceptions.TaskNotStall as e:
            raise e
        
        except exceptions.InvalidForm as e:
            raise e
        
        except Exception as e:
            task.failed(e)
            task.save()
            task.process.failed(e)
            task.process.save()
            raise e

    def activate(self, task: models.Task, **kwargs):       
        from .nodes import node_activation
        
        try:
            flow    = self.flow(task.process.flow_class)
            context = flow.context(task.process)
            node    = flow.node(task.step)
            
            with node_activation(task=task, engine=self, context=context) as activation:
                node(activation=activation, **kwargs)
                return activation

        except Exception as e:
            task.failed(e)
            task.process.failed(e)
            task.save()
            task.process.save()
            raise e

ENGINE = Engine()