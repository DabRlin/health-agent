"""
Dify API 客户端 - 用于调用 Dify 工作流实现智能问诊
"""
import os
import requests
from typing import Generator, Optional

# 清除环境变量中的代理设置，避免被 Surge 等代理软件拦截
for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
    os.environ.pop(proxy_var, None)


class DifyClient:
    """Dify API 客户端"""
    
    # 禁用代理
    NO_PROXY = {"http": None, "https": None, "all": None}
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://127.0.0.1/v1"
    ):
        self.api_key = api_key or os.getenv("DIFY_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(
        self,
        query: str,
        user: str = "default_user",
        conversation_id: Optional[str] = None,
        inputs: Optional[dict] = None,
        stream: bool = False
    ) -> dict:
        """
        发送聊天消息到 Dify
        
        Args:
            query: 用户消息
            user: 用户标识
            conversation_id: 会话 ID（可选，用于多轮对话）
            inputs: 额外输入变量
            stream: 是否流式返回
            
        Returns:
            Dify API 响应
        """
        url = f"{self.base_url}/chat-messages"
        
        payload = {
            "query": query,
            "user": user,
            "response_mode": "streaming" if stream else "blocking",
            "inputs": inputs or {}
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        try:
            if stream:
                return self._stream_chat(url, payload)
            else:
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=60,
                    proxies=self.NO_PROXY
                )
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": True,
                "message": f"Dify API 调用失败: {str(e)}"
            }
    
    def _stream_chat(self, url: str, payload: dict) -> Generator[dict, None, None]:
        """流式聊天（内部方法）"""
        try:
            with requests.post(
                url,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=60,
                proxies=self.NO_PROXY
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        yield {"chunk": line.decode("utf-8")}
        except requests.exceptions.RequestException as e:
            yield {"error": True, "message": str(e)}
    
    def chat_stream(
        self,
        query: str,
        user: str = "default_user",
        conversation_id: Optional[str] = None,
        inputs: Optional[dict] = None
    ) -> Generator[dict, None, None]:
        """
        流式聊天 - 解析 SSE 事件并返回文本块
        
        Yields:
            dict: {"text": "..."} 或 {"error": True, "message": "..."}
        """
        import json as json_lib
        
        url = f"{self.base_url}/chat-messages"
        
        payload = {
            "query": query,
            "user": user,
            "response_mode": "streaming",
            "inputs": inputs or {}
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        try:
            with requests.post(
                url,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=120,
                proxies=self.NO_PROXY
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    line_str = line.decode("utf-8")
                    
                    # SSE 格式: data: {...}
                    if line_str.startswith("data: "):
                        try:
                            data = json_lib.loads(line_str[6:])
                            event = data.get("event", "")
                            
                            if event == "message":
                                # 消息块
                                answer = data.get("answer", "")
                                if answer:
                                    yield {"text": answer}
                            elif event == "message_end":
                                # 消息结束
                                break
                            elif event == "error":
                                yield {"error": True, "message": data.get("message", "Unknown error")}
                                break
                        except json_lib.JSONDecodeError:
                            continue
                            
        except requests.exceptions.RequestException as e:
            yield {"error": True, "message": f"Dify API 流式调用失败: {str(e)}"}
    
    def run_workflow(
        self,
        inputs: dict,
        user: str = "default_user",
        stream: bool = False
    ) -> dict:
        """
        运行 Dify 工作流
        
        Args:
            inputs: 工作流输入变量
            user: 用户标识
            stream: 是否流式返回
            
        Returns:
            工作流执行结果
        """
        url = f"{self.base_url}/workflows/run"
        
        payload = {
            "inputs": inputs,
            "user": user,
            "response_mode": "streaming" if stream else "blocking"
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=120,
                proxies=self.NO_PROXY
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": True,
                "message": f"Dify 工作流调用失败: {str(e)}"
            }
    
    def is_available(self) -> bool:
        """检查 Dify 服务是否可用"""
        if not self.api_key:
            return False
        try:
            # 尝试获取应用信息
            response = requests.get(
                f"{self.base_url}/parameters",
                headers=self.headers,
                timeout=5,
                proxies=self.NO_PROXY
            )
            return response.status_code == 200
        except:
            return False


# 全局客户端实例
dify_client: Optional[DifyClient] = None


def get_dify_client() -> DifyClient:
    """获取 Dify 客户端实例"""
    global dify_client
    if dify_client is None:
        dify_client = DifyClient(
            api_key=os.getenv("DIFY_API_KEY", ""),
            base_url=os.getenv("DIFY_BASE_URL", "http://127.0.0.1/v1")
        )
    return dify_client


def init_dify_client(api_key: str, base_url: str = "http://127.0.0.1/v1"):
    """初始化 Dify 客户端"""
    global dify_client
    dify_client = DifyClient(api_key=api_key, base_url=base_url)
    return dify_client
