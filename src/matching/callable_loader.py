"""Callable loader for pattern matching.

Loads Python functions from module:function strings and validates their signatures.
"""

import importlib
import inspect
from typing import Callable, Any


def load_callable(callable_string: str) -> Callable:
    """Load a Python callable from module:function string.

    Args:
        callable_string: String in format "module.path:function_name"

    Returns:
        The loaded callable function

    Raises:
        ImportError: If the module cannot be imported
        AttributeError: If the function doesn't exist in the module
        ValueError: If the callable_string format is invalid

    Examples:
        >>> func = load_callable("math:sqrt")
        >>> func(4)
        2.0

        >>> func = load_callable("mypackage.mymodule:my_function")
    """
    if ":" not in callable_string:
        raise ValueError(
            f"Invalid callable format: {callable_string}. "
            "Must be in 'module:function' format"
        )

    parts = callable_string.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid callable format: {callable_string}. "
            "Must contain exactly one ':' separator"
        )

    module_path, function_name = parts

    if not module_path or not function_name:
        raise ValueError(
            f"Invalid callable format: {callable_string}. "
            "Both module path and function name must be non-empty"
        )

    # Import the module
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(
            f"Cannot import module '{module_path}': {e}"
        ) from e

    # Get the function from the module
    try:
        func = getattr(module, function_name)
    except AttributeError as e:
        raise AttributeError(
            f"Module '{module_path}' has no function '{function_name}': {e}"
        ) from e

    if not callable(func):
        raise TypeError(
            f"'{callable_string}' does not refer to a callable object"
        )

    return func


def validate_callable_signature(func: Callable) -> bool:
    """Validate that a callable has the expected signature for pattern matching.

    Expected signatures:
    - (text: str) -> bool
    - (text: str) -> List[Match]

    Args:
        func: The callable to validate

    Returns:
        True if signature is valid, False otherwise

    Raises:
        TypeError: If func is not callable
    """
    if not callable(func):
        raise TypeError(f"{func} is not callable")

    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        # Some built-in functions don't have signatures
        return False

    params = list(sig.parameters.values())

    # Must have exactly one parameter
    if len(params) != 1:
        return False

    # First parameter should accept str
    param = params[0]

    # Check if parameter has type annotation
    if param.annotation != inspect.Parameter.empty:
        # If annotated, should be str
        if param.annotation != str:
            return False

    return True
