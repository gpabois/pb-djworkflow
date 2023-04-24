class InvalidForm(Exception):
    def __init__(self, form):
        self.form = form

class TaskNotStall(Exception):
    pass
