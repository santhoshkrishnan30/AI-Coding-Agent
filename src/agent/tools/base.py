from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json

class BaseTool(ABC):
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {}
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        required_params = self.parameters.get("required", [])
        optional_params = self.parameters.get("optional", {})
        
        errors = []
        validated_params = {}
        
        # Handle case where parameters might be nested
        if "required" in parameters:
            parameters = parameters["required"]
        elif "optional" in parameters:
            parameters = parameters["optional"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
            else:
                validated_params[param] = parameters[param]
        
        # Check optional parameters
        for param, default_value in optional_params.items():
            if param in parameters:
                # Handle case where parameter value might be a dict
                param_value = parameters[param]
                if isinstance(param_value, dict):
                    if "default" in param_value:
                        validated_params[param] = param_value["default"]
                    elif "value" in param_value:
                        validated_params[param] = param_value["value"]
                    else:
                        validated_params[param] = default_value
                else:
                    validated_params[param] = param_value
            else:
                validated_params[param] = default_value
        
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
        
        return {
            "valid": True,
            "parameters": validated_params
        }

class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]