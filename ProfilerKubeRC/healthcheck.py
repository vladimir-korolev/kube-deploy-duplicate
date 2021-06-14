from abc import ABC, abstractmethod
import time
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

from dependency_injector.wiring import inject, Provide
from ProfilerKubeRC.logger import LoggerContainer
from ProfilerKubeRC.logger import SLogger
from ProfilerKubeRC.TasksManager import TasksManager
from ProfilerKubeRC.container import TasksContainer


class HealthCheck(BaseHTTPRequestHandler):
    """
    Healthcheck for kubernetes probes

    Public methods:
        - do_GET(): processing get request
        - init(): Initialize class
            - set a function to check service
            - add start http server method to task list (It will be  started later)
        - startHttp(): start http server method

    """

    service_check = None                                                    # Test function
    logger: SLogger = Provide[LoggerContainer.logger_svc]                   # Logger
    tasks_manager: TasksManager = Provide[TasksContainer.tasks_manager]     # Inject multithread tasks manager

    @classmethod
    def init(cls, service_check):
        cls.service_check = service_check
        cls.tasks_manager.addTask(cls.startHttp, ())       # Add task to mulitasks pool to submit. Must be run in a separate thread from the main task

    #
    # Test is service working
    # Checks number of replicas
    # Returns HTTP 200 if success
    #
    def do_GET(self):
        health = HealthCheck.service_check.healthCheck()
        # Do multiple checks because of clone can being refreshed in this time exactly
        i = 0
        while not health and i < 5:
            HealthCheck.logger.info("Healthcheck is potentially failed")
            time.sleep(10)
            health = HealthCheck.service_check.healthCheck()
            i += 1
        HealthCheck.logger.info("Healthcheck is success" if health else "Healthcheck is failed")
        self.send_response(200) if health else self.send_response(204)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    @classmethod
    def startHttp(cls):
        webServer = HTTPServer(('localhost', 8234), cls)
        webServer.serve_forever()


