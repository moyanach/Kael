# Create your views here.
import json

from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

from webshell.utils import K8SStreamThread, K8SApiTools
from audit.utils import write_audit_log


class SSHConsumer(WebsocketConsumer):

    def connect(self):
        # Extract parameters from query string
        query_string = self.scope.get('query_string', b'').decode()
        params = {}
        if query_string:
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value

        # Required parameters for targeting a pod
        self.namespace = params.get('namespace', 'default')
        self.pod_name = params.get('pod_name', '')
        self.container = params.get('container', '')

        if not self.pod_name:
            self.close(code=4001)
            return

        # TODO: Add authentication here. For example, validate a token from query params.
        # token = params.get('token', '')
        # if not self._validate_token(token):
        #     self.close(code=4003)
        #     return

        # 获取当前用户
        user = self.scope.get("user", None)
        username = user.username if user and user.is_authenticated else "anonymous"

        try:
            # Create K8s exec stream with dynamic pod params
            k8s_tools = K8SApiTools(rw=True)
            self.stream = k8s_tools.create_attatch_pod_exec_stream(
                namespace=self.namespace,
                pod_name=self.pod_name,
                container=self.container or self.pod_name,
            )
            kub_stream = K8SStreamThread(self, self.stream)
            kub_stream.start()
            self.accept()

            # 记录 Webshell 连接审计
            write_audit_log(
                action="connect",
                resource_type="K8sPod",
                resource_name=f"{self.namespace}/{self.pod_name}",
                resource_instance=self.pod_name,
                detail=f"用户 {username} 通过 Webshell 连接到 {self.namespace}/{self.pod_name} 容器 {self.container or self.pod_name}",
                operator=username,
            )
        except Exception as err:
            # 记录连接失败审计
            write_audit_log(
                action="connect",
                resource_type="K8sPod",
                resource_name=f"{self.namespace}/{self.pod_name}",
                detail=f"用户 {username} 连接 {self.namespace}/{self.pod_name} 失败: {err}",
                operator=username,
            )
            self.close(code=4002)

    def disconnect(self, close_code):
        if hasattr(self, 'stream') and self.stream:
            try:
                self.stream.write_stdin('exit\r')
            except Exception:
                pass

    def receive(self, text_data):
        try:
            text_data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        op = text_data.get('op')
        data = text_data.get('data')
        if op == 'stdin' and data:
            try:
                self.stream.write_stdin(data)
            except Exception:
                pass
        elif op == 'resize' and isinstance(data, dict):
            try:
                rows = data.get("rows")
                cols = data.get("cols")
                if rows and cols:
                    self.stream.write_channel(
                        4, json.dumps({"Height": int(rows), "Width": int(cols)})
                    )
            except Exception:
                pass