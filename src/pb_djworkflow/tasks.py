from celery import shared_task
from celery.utils.log import get_task_logger
from .status import REENTERING

logger = get_task_logger(__name__)

@shared_task
def activate(task_id, **options):
    from .engine import ENGINE
    from .models import Task

    logger.debug("Activating task {}".format(str(task_id)))
    task = Task.objects.get(id=int(task_id))
    act = ENGINE.activate(task, **options)
    
    return act.to_edge().to_json()

@shared_task
def reenter(task_id, **options):
    """
        Reenter a supratask, executed when the subprocess closes or fails
    """
    from .engine import ENGINE
    from .models import Task

    logger.debug("Activating task {}".format(str(task_id)))
    task = Task.objects.get(id=int(task_id))
    task.status = REENTERING
    act = ENGINE.activate(task, **options)
    
    return act.to_edge().to_json()

def submit(task, **kwargs):
    from .engine import ENGINE
    return ENGINE.submit(task, **kwargs)

def spawn_flow(flow, **kwargs):
    from .engine import ENGINE
    return ENGINE.spawn_flow(flow, **kwargs)