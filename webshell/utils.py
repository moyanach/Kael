from threading import Thread

import kubernetes.client
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from kubernetes.stream.ws_client import WSClient

from Kael.config import config


class K8SStreamThread(Thread):
    def __init__(self, websocket, container_stream):
        Thread.__init__(self)
        self.websocket = websocket
        self.stream = container_stream

    def run(self):
        try:
            while self.stream.is_open():
                if self.stream.peek_stdout():
                    stdout = self.stream.read_stdout()
                    self.websocket.send(stdout)
                if self.stream.peek_stderr():
                    stderr = self.stream.read_stderr()
                    self.websocket.send(stderr)
        except Exception:
            pass
        finally:
            try:
                self.websocket.close()
            except Exception:
                pass


class K8SApiTools(Thread):
    def __init__(self, rw: bool = False, admin: bool = False, cluster: str = "152"):
        self.admin = admin
        self.cluster = cluster
        self.rw = rw
        self.configuration = None

        # Moved from hardcoded dict to environment config
        if admin:
            K8S_TOKEN = config.K8S_ADMIN_TOKEN
        elif rw:
            K8S_TOKEN = config.K8S_TOKEN
        else:
            K8S_TOKEN = config.K8S_TOKEN_READ

        if not K8S_TOKEN:
            raise ValueError("K8S_TOKEN is not configured. Set K8S_TOKEN, K8S_ADMIN_TOKEN, or K8S_TOKEN_READ environment variable.")

        self.api_key = {"authorization": "Bearer " + K8S_TOKEN}
        self.api_host = config.K8S_HOST
        if not self.api_host:
            raise ValueError("K8S_HOST is not configured. Set K8S_HOST environment variable.")

        # Fixed: respect SSL verification from config instead of hardcoding False
        self.verify_ssl = config.K8S_VERIFY_SSL
        self.k8s_configure()

    def k8s_configure(self):
        self.configuration = kubernetes.client.Configuration()
        self.configuration.api_key = self.api_key
        self.configuration.verify_ssl = self.verify_ssl
        self.configuration.host = self.api_host
        self.configuration.assert_hostname = False  # type: ignore

    def get_core_api(self) -> kubernetes.client.CoreV1Api:
        api_client = kubernetes.client.ApiClient(self.configuration)
        core_api = kubernetes.client.CoreV1Api(api_client)
        return core_api

    def create_attatch_pod_exec_stream(
        self,
        namespace: str = "dcp",
        pod_name: str = "app-guard-admin-api-7cc7b8f97f-hzlw9",
        container: str = "app-guard-admin-api",
    ) -> WSClient:
        core_api = self.get_core_api()

        try:
            core_api.read_namespaced_pod(name=pod_name, namespace=namespace)
        except ApiException as err:
            raise ValueError(f"Failed to read pod {pod_name} in namespace {namespace}: {err}")

        try:
            exec_command = [
                "/bin/sh",
                "-c",
                "TERM=xterm-256color; export TERM; [ -x /bin/bash ] "
                "&& ([ -x /usr/bin/script ] "
                '&& /usr/bin/script -q -c "/bin/bash" /dev/null || exec /bin/bash) '
                "|| exec /bin/sh",
            ]
            resp = stream(
                core_api.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                container=container,
                command=exec_command,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=True,
                _preload_content=False,
            )
        except ApiException as err:
            raise InterruptedError(f"Failed to exec into pod {pod_name}: {err}")
        return resp
