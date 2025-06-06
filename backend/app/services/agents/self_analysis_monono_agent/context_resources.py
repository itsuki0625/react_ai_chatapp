import logging

from app.services.agents.monono_agent.components.context_manager import ContextManager
from app.services.agents.monono_agent.components.resource_manager import ResourceManager
from app.services.agents.monono_agent.components.trace_logger import TraceLogger

# シングルトンインスタンスを作成
ctx_mgr = ContextManager()
rm = ResourceManager(token_cost_per_token=0.000002)
trace = TraceLogger(logger=logging.getLogger("self_analysis_trace")) 