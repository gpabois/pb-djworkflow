from .nodes  import BaseNode, End
from .engine import ENGINE
from . import exceptions

class SelfClassAttribute:
    def __init__(self, name):
        self.name = name
    
    def __call__(self, cls):
        return getattr(cls, self.name)

class SelfObject:
    def __getattr__(self, name):
        return SelfClassAttribute(name)
    
    def resolve(self, target, source):
        for name, value in {**target.__dict__}.items():
            if isinstance(value, SelfClassAttribute):
                setattr(target, name, value(source))
        
        return target

Self = SelfObject()

class WorkflowMeta(type):   
    def __new__(cls, name, bases, attrs, abstract=False):
        cls = super().__new__(cls, name, bases, attrs)

        for key, value in attrs.items():
            if isinstance(value, BaseNode):
                cls.steps[key] = Self.resolve(value, cls)  
                value.flow = cls
                value.name = key
                value.resolve(cls)

        if not abstract:
            ENGINE.register(cls)
        
        return cls

class SimpleContextFactory:
    requires_form_submission = False
    
    def __call__(self, context_class, process, **kwargs):
        context = context_class(process=process)
        context.save()
        result.set_context(context)
        return context

class FormBasedContextFactory:
    requires_form_submission = True

    def __init__(self, form_class):
        self.form_class = form_class

    def __call__(self, context_class, process, files=None, **kwargs):
        form = self.form_class(**kwargs['form_kwargs'])

        if form.is_valid():
            context = form.save(commit=False)
            context.process = process
            context.save()
            return context

        else:
            raise exceptions.InvalidForm(form)
        
class Workflow(metaclass=WorkflowMeta, abstract=True):
    context_class = None
    context_factory = SimpleContextFactory()
    
    steps = {
        'end': End()
    }

    def new_context(self, *args):
        return self.context_factory_class(self.context_class, *args)

    @classmethod
    def get_name(cls):
        if hasattr(cls, 'name'):
            return getattr(cls, 'name')
        else:
            return cls.__name__
            
    @classmethod
    def node(cls, step):
        return cls.steps[step]

    @classmethod
    def context(cls, process):
        return cls.context_class.objects.get(process=process)