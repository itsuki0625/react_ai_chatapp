from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import uuid
from pydantic import BaseModel
import asyncio

if TYPE_CHECKING:
    from ..base_agent import BaseAgent

class WorkflowEngine(BaseModel):
    async def execute_workflow(self, workflow_definition: Any, agent: 'BaseAgent', initial_data: Dict, session_id: Optional[uuid.UUID] = None) -> Any:
        """
        Execute a workflow definition with dependency management, parallel and sequential step execution.
        """
        # Parse workflow definition (supports dicts with optional 'workflow' wrapper)
        wf = workflow_definition.get('workflow', workflow_definition)
        steps = wf.get('steps', [])

        # Build mapping of task names to definitions
        tasks = {step['name']: step for step in steps}
        # Compute indegree and dependents graph
        indegree = {name: len(step.get('depends_on', [])) for name, step in tasks.items()}
        dependents: Dict[str, List[str]] = {name: [] for name in tasks}
        for name, step in tasks.items():
            for dep in step.get('depends_on', []):
                if dep in dependents:
                    dependents[dep].append(name)

        results: Dict[str, Any] = {}
        executed = set()
        # Initialize execution queue with tasks with no dependencies
        to_execute = [name for name, deg in indegree.items() if deg == 0]

        async def run_step(name: str) -> Any:
            step = tasks[name]
            # Check condition (only 'always' supported for now)
            cond = step.get('condition', 'always')
            if cond != 'always':
                print(f"[WorkflowEngine] Skipping step '{name}' due to condition '{cond}'")
                return None
            tool_name = step['tool']
            # Prepare parameters using initial_data and step-specific parameters
            params = dict(initial_data) if initial_data else {}
            params.update(step.get('parameters', {}))
            try:
                return agent.tool_registry.execute_tool(tool_name, params)
            except Exception as e:
                print(f"[WorkflowEngine] Error executing step '{name}': {e}")
                return {"error": str(e)}

        # Execute tasks in batches respecting dependencies
        while to_execute:
            # Split tasks into parallel and sequential
            parallel_tasks = [n for n in to_execute if tasks[n].get('parallel', False)]
            sequential_tasks = [n for n in to_execute if n not in parallel_tasks]

            # Execute parallel tasks concurrently
            if parallel_tasks:
                coros = [run_step(n) for n in parallel_tasks]
                results_list = await asyncio.gather(*coros)
                for name, res in zip(parallel_tasks, results_list):
                    results[name] = res
                    executed.add(name)

            # Execute sequential tasks one after another
            for name in sequential_tasks:
                res = await run_step(name)
                results[name] = res
                executed.add(name)

            # Update indegree for dependents
            for name in list(executed):
                for dep in dependents.get(name, []):
                    indegree[dep] -= 1

            # Determine next set of tasks to execute
            to_execute = [n for n, deg in indegree.items() if deg == 0 and n not in executed]

        return {"workflow": wf, "results": results} 