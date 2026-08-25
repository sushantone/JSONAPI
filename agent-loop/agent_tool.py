from inspect import signature
from typing import Any, Callable, Type
from jsonschema import ValidationError
from openai import BaseModel

class AgentTool:
    """Encapsulates a Python function with Pydantic validation."""
    def __init__(self, func: Callable, args_model: Type[BaseModel], name: str = None):
        self.func = func
        self.args_model = args_model
        self.name = name or func.__name__
        self.description = func.__doc__ #or self.args_schema.get('description', '')

    def to_openai_function_call_definition(self) -> dict:
        """Converts the tool to OpenAI Function Calling format."""
        # schema_dict = self.args_schema
        # description = schema_dict.pop("description", "")
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.args_model,
            },
        }

    @property
    def args_schema(self) -> dict:
        """Returns the tool's function argument schema as a dictionary."""
        schema = self.args_model.model_json_schema()
        schema.pop("title", None)
        return schema

    def validate_json_args(self, json_string: str) -> bool:
        """Validate JSON string using the Pydantic model."""
        try:
            validated_args = self.args_model.model_validate_json(json_string)
            return isinstance(validated_args, self.args_model)
        except ValidationError:
            return False

    def run(self, *args, **kwargs) -> Any:
        """Execute the function with validated arguments."""
        try:
            # Handle positional arguments by converting them to keyword arguments
            if args:
                sig = signature(self.func)
                arg_names = list(sig.parameters.keys())
                kwargs.update(dict(zip(arg_names, args)))

            # Validate arguments with the provided Pydantic schema
            validated_args = self.args_model(**kwargs)
            return self.func(**validated_args.model_dump())
        except ValidationError as e:
            raise ValueError(f"Argument validation failed for tool '{self.name}': {str(e)}")
        except Exception as e:
            raise ValueError(f"An error occurred during the execution of tool '{self.name}': {str(e)}")

    def __call__(self, *args, **kwargs) -> Any:
        """Allow the AgentTool instance to be called like a regular function."""
        return self.run(*args, **kwargs)
