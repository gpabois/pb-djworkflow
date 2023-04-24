import django.dispatch

entering_task   = django.dispatch.Signal()
task_done       = django.dispatch.Signal()
leaving_task    = django.dispatch.Signal()
failed_task     = django.dispatch.Signal()

closed_workflow = django.dispatch.Signal()
failed_workflow = django.dispatch.Signal()