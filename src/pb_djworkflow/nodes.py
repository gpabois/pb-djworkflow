from .tasks import activate, spawn_flow
from .status import READY, INIT, DONE, CLOSED, STALL, FAILED, ABORTED, SUBMITTED, REENTERING
from . import signals, exceptions, models
from contextlib import contextmanager
from django.db import transaction

@contextmanager
def node_activation(task, engine, context):
    activation = NodeActivation(task, engine, context)

    try:
        yield activation
    
    except Exception as e:
        activation.failed(e)
        raise e
    
    finally:
        activation.commit()

class ActivationEdge:
    
    class NotFound(Exception):
        def __init__(self, step):
            super().__init__(f'missing "{step}"')

    """
        An edge between a task activation and the next scheduled activations
    """
    def __init__(self, task, *nexts):
        self.task = task
        self.nexts = nexts
    
    def is_step(self, step):
        return self.task.step == step
    
    def follow(self, step, *args, **kwargs):
        """
            Follow a task based on its name, and return the activation edge.
        """
        try:
            task = next(
                filter(
                    lambda task: task.step == step, 
                    self.nexts
                )
            )
            return task.get_edge(*args, **kwargs)
        
        except StopIteration:
            raise ActivationEdge.NotFound(step)

    def loopback(self):
        """
            Loopback on a task.
        """
        
        for task in self.nexts:
            if task.id == self.task.id:
                return task.get_edge()
        
        return None

    def until(self, status):
        if self.task.status == status:
            return self
        
        return self.loopback().until(status)

    def until_closed(self):
        return self.until(CLOSED)

    def until_stall(self):
        return self.until(STALL)

    def get_edges(self, *args, **kwargs):
        """
            Wait for the next activations and returns their links
        """   
        yield from map(lambda task: task.get_edge(*args, **kwargs), self.nexts)

    @staticmethod
    def from_flow_spawn(flow_spawn):
        return ActivationEdge(flow_spawn.start_spawn.task, flow_spawn.start_spawn.task)

    @staticmethod
    def from_json(json):
        task = models.Task.objects.get(id=json['current'])
        nexts = list(map(
            lambda t: models.Task.objects.get(id=t), 
            json['nexts']
        ))
        return ActivationEdge(task, *nexts)

    def to_json(self):
        return {
            'current': self.task.id,
            'nexts': list(map(lambda n: n.id, self.nexts))
        }

class NodeActivation:
    def __init__(self, task, engine, context, **kwargs):
        self.engine = engine
        self.task = task
        self.spawn_cmds = []
        self.context = context
        self.nexts = []

    def to_edge(self):
        return ActivationEdge(self.task, *self.nexts)

    def __iter__(self):
        return iter(self.nexts)

    def commit(self):
        self.task.save()
        self.task.process.save()
        self.context.save()

        if self.task.status in (READY, SUBMITTED):
            job = activate.delay(
                self.task.id
            ) 
            self.task.current_job = job.task_id
            self.task.save()
            job.forget()
            self.nexts.append(self.task)

        for cmd in self.spawn_cmds:
            task_spawn = cmd()
            self.nexts.append(task_spawn.task)
            
    def spawn_task(self, step):
        self.spawn_cmds.append(
            lambda: self.engine.spawn_task(
                step, 
                self.task.process, 
                previous=self.task
            )
        )

    def close_workflow(self):
        self.task.done()
        self.task.process.done()
        # Notify closure
        signals.closed_workflow.send(self, process=self.task.process)

    def can_be_activated(self):
        return self.task.status in (READY, STALL, SUBMITTED, REENTERING)

    def is_entering(self):
        return self.task.status == INIT

    def is_leaving(self):
        return self.task.status == DONE

    def is_running(self):
        return self.task.status == READY
    
    def submitted(self):
        self.task.status = SUBMITTED

    def done(self):
        self.task.status = DONE
    
    def aborted(self):
        self.task.status = ABORTED
        self.process.status = ABORTED
    
    def failed(self, error):
        self.task.process.status = FAILED
        self.task.status = FAILED
        self.task.log = str(error)
        # Notify failure
        signals.failed_task.send(self, task=self.task)
        signals.failed_workflow.send(self, process=self.task.process)
    
    def ready(self):
        self.task.status = READY
    
    def stall(self):
        self.task.status = STALL
    
    def close(self):
        self.task.status = CLOSED

class BaseNode:
    def __init__(self, **options):
        if 'enter' in options:
            self.enter = options['enter']
            del options['enter']
        else:
            self.enter = None
        
        if 'leave' in options:
            self.leave = options['leave']
            del options['leave']
        else:
            self.leave = None

    def resolve(self, flow_class):
        pass

    def __call__(self, activation, **input):
        if activation.is_entering():
            self.on_entering(activation, **input)
            activation.ready()          

        if activation.can_be_activated():
            self.activate(
                activation=activation, 
                **input
            )

        if activation.is_leaving():
            self.on_leaving(activation, **input)
            activation.close()

        return activation

    def on_entering(self, activation, **input):
        signals.entering_task.send(sender=self.__class__, task=activation.task)
        
        if self.enter:
            self.enter(activation, **input)

    def on_leaving(self, activation, **input):
        signals.leaving_task.send(sender=self.__class__, task=activation.task)
        
        if self.leave:
            self.leave(activation, **input)

class Branch(BaseNode):
    def __init__(self, default, **kwargs):
        super().__init__(**kwargs)
        exclude = ['enter', 'leave']
        self.default = default
        branches = {}
        
        for k, v in kwargs.items():
            if k not in exclude:
                branches[k] = v
        
        self.branches = branches
    
    def resolve(self, flow_class):
        from . import flows
        for branch_name, branch in self.branches.items():
            if isinstance(branch, flows.SelfClassAttribute):
                self.branches[branch_name] = branch(flow_class)

    def activate(self, activation, **kwargs):
        for branch, predicate in self.branches.items():
            if predicate(activation, **kwargs):
                activation.spawn_task(branch)
                activation.done()
                return
        
        activation.spawn_task(self.default)
        activation.done()

class Job(BaseNode):
    def __init__(self, fn, next, **options):
        super().__init__(**options)
        self.fn = fn
        self.next = next
    
    def activate(self, activation, **input):
        self.fn(activation, **input)
        activation.spawn_task(self.next)
        activation.done()

class Subprocess(BaseNode):
    def __init__(self, subflow, get_spawn_kwargs, on_result, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.get_spawn_kwargs = get_spawn_kwargs
        self.subflow = subflow
        self.on_result = on_result

    def reenter(self, activation, **input):
        """
            Reenter from subprocess, propagate any failures
        """
        if activation.task.subprocess.status == FAILED:
            activation.failed(f'subprocess failed: "{activation.task.subprocess}"')
        
        else:
            self.on_result(activation)
            activation.context.save()
            activation.done()

    def spawn_subprocess(self, activation, **kwargs):
        spawn_kwargs = self.get_spawn_kwargs(activation)
        spawn = spawn_flow(self.subflow, **spawn_kwargs)
        
        # Goes into stall
        activation.task.subprocess = spawn.process
        activation.stall()

    def activate(self, activation, **input):
        if activation.task.status == READY:
            self.spawn_subprocess(activation, **kwargs)

        if activation.task.status == REENTERING:
            self.reenter(activation)

class UserAction(BaseNode):
    def __init__(self, form_class, next, **options):
        super().__init__(**options)
        self.form_class = form_class
        self.next = next

    def submit(self, activation, **kwargs):
        # Cannot submit if the task is not in a stall state.
        if activation.task.status != STALL:
            raise exceptions.TaskNotStall()

        form_kwargs = kwargs['form_kwargs']

        form = self.form_class(
            **form_kwargs,
            instance=activation.context
        )

        form.task = activation.task

        if form.is_valid():
            activation.context = form.save()
            activation.submitted()        
        else:
            raise exceptions.InvalidForm(form)

    def activate(self, activation, **input):
        if activation.task.status == READY:
            activation.task.status = STALL
        
        elif activation.task.status == SUBMITTED:
            activation.done()
            activation.spawn_task(self.next)     

class End(BaseNode):
    def activate(self, activation, **input):
        activation.close_workflow()
