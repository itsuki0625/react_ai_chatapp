# monono_agent/components/tool_registry.py

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, create_model, ValidationError, ConfigDict
import inspect
import json

class ToolParameterError(ValueError):
    """Tool parameter validation error."""
    pass

class ToolNotFoundError(ValueError):
    """Tool not found error."""
    pass

class ToolExecutionError(RuntimeError):
    """Tool execution error."""
    pass


class ToolDefinition(BaseModel):
    model_config = ConfigDict(extra='allow')

    type: str = "function"
    function: Dict[str, Any]


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_definitions: Dict[str, ToolDefinition] = {}
        self._tool_schemas: Dict[str, Optional[BaseModel]] = {}

    def register_tool(self, tool_func: Callable, name: Optional[str] = None, description: Optional[str] = None, schema: Optional[BaseModel] = None):
        """
        Registers a tool (function) with the registry.

        Args:
            tool_func: The function to register.
            name: The name of the tool. If None, uses the function's __name__.
            description: A description of the tool. If None, tries to use the function's docstring.
            schema: A Pydantic model for validating the tool's arguments.
                    If None, it will be inferred from type hints.
        """
        tool_name = name or tool_func.__name__
        if tool_name in self._tools:
            # TODO: Add proper logging/warning
            print(f"Warning: Tool '{tool_name}' is already registered and will be overridden.")

        self._tools[tool_name] = tool_func
        
        if description is None:
            description = inspect.getdoc(tool_func)
        
        param_schema = self._generate_parameter_schema(tool_func, schema)
        self._tool_schemas[tool_name] = param_schema

        # Create tool definition based on OpenAI's format
        func_def = {
            "name": tool_name,
            "description": description or "",
            "parameters": param_schema.model_json_schema() if param_schema else {"type": "object", "properties": {}}
        }
        self._tool_definitions[tool_name] = ToolDefinition(function=func_def)
        print(f"Tool '{tool_name}' registered.")


    def _generate_parameter_schema(self, func: Callable, explicit_schema: Optional[BaseModel]) -> Optional[BaseModel]:
        """
        Generates a Pydantic model for the function's parameters if no explicit schema is provided.
        """
        if explicit_schema:
            return explicit_schema

        sig = inspect.signature(func)
        fields = {}
        has_params = False
        for name, param in sig.parameters.items():
            if param.name == 'self' or param.name == 'cls': # Skip self/cls for methods
                continue
            has_params = True
            param_type = param.annotation if param.annotation is not inspect.Parameter.empty else Any
            if param.default is inspect.Parameter.empty:
                fields[name] = (param_type, ...) # Required parameter
            else:
                fields[name] = (param_type, param.default) # Optional parameter
        
        if not has_params: # No parameters other than self/cls
            return None 
            
        return create_model(
            f"{func.__name__}Params",
            **fields,
            __base__=BaseModel
        )

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns a list of tool definitions in a format suitable for LLMs (e.g., OpenAI).
        """
        return [definition.model_dump(exclude_none=True) for definition in self._tool_definitions.values()]

    def parse_arguments(self, tool_name: str, arguments_str: str) -> Dict[str, Any]:
        """
        Parses the JSON string arguments for a tool and validates them against its schema.

        Args:
            tool_name: The name of the tool.
            arguments_str: A JSON string of arguments.

        Returns:
            A dictionary of parsed and validated arguments.

        Raises:
            ToolNotFoundError: If the tool is not found.
            ToolParameterError: If argument parsing or validation fails.
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found.")

        schema_model = self._tool_schemas.get(tool_name)
        if not schema_model: # Tool has no parameters
            if arguments_str and arguments_str.strip() and arguments_str.strip() != '{}':
                 raise ToolParameterError(f"Tool '{tool_name}' expects no arguments, but received: {arguments_str}")
            return {}

        try:
            args_dict = json.loads(arguments_str)
        except json.JSONDecodeError as e:
            raise ToolParameterError(f"Failed to parse arguments for tool '{tool_name}'. Invalid JSON: {e}")

        try:
            validated_args = schema_model(**args_dict)
            return validated_args.model_dump()
        except ValidationError as e:
            raise ToolParameterError(f"Argument validation failed for tool '{tool_name}': {e}")


    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Executes a registered tool with the given arguments.

        Args:
            tool_name: The name of the tool to execute.
            arguments: A dictionary of arguments for the tool, already parsed and validated.

        Returns:
            The result of the tool execution.

        Raises:
            ToolNotFoundError: If the tool is not found.
            ToolExecutionError: If an error occurs during tool execution.
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found.")

        tool_func = self._tools[tool_name]
        
        # Inspect the function signature to pass arguments correctly
        sig = inspect.signature(tool_func)
        tool_params = sig.parameters
        
        # Handle cases where the tool might expect no arguments or only specific ones
        args_to_pass = {}
        if not arguments and len(tool_params) == 0: # No args expected, none provided
             pass
        elif arguments:
            for param_name in tool_params:
                if param_name in arguments:
                    args_to_pass[param_name] = arguments[param_name]
                # else: if param is not in arguments and has no default, it might be an issue
                # Pydantic validation should ideally catch missing required args beforehand

        try:
            # If the function is a method bound to an object (e.g. from a class instance)
            # or a class method, inspect will handle 'self' or 'cls' correctly.
            # For simple functions, it just passes the arguments.
            return tool_func(**args_to_pass)
        except Exception as e:
            # TODO: Add proper logging
            print(f"Error executing tool '{tool_name}': {e}")
            raise ToolExecutionError(f"Error during execution of tool '{tool_name}': {str(e)}")

    def get_tool_schema(self, tool_name: str) -> Optional[BaseModel]:
        """Returns the Pydantic schema for a tool's parameters."""
        if tool_name not in self._tool_schemas:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found or has no schema.")
        return self._tool_schemas[tool_name] 