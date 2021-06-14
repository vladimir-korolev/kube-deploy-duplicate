import concurrent.futures

class TasksManager:

    def __init__(self):
        self.tasks = []

    def addTask(self, task, arguments=None):
        self.tasks.append((task, arguments))

    def runTasks(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for task in self.tasks:
                executor.submit(task[0], *task[1])
