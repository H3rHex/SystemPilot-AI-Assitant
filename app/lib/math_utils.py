import ast
import math
from typing import cast 

# --- BASIC OPERATIONS ---

def add(a: float, b: float) -> float:
    return a + b

def subtract(a: float, b: float) -> float:
    return a - b

def multiply(a: float, b: float) -> float:
    return a * b

def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b

def power(base: float, exponent: float) -> float:
    return base ** exponent

def square_root(n: float) -> float:
    if n < 0:
        raise ValueError("Cannot calculate the square root of a negative number.")
    return math.sqrt(n)

# --- GEOMETRY HELPERS ---

def circle_area(radius: float) -> float:
    return multiply(math.pi, power(radius, 2))

def rectangle_perimeter(length: float, width: float) -> float:
    return multiply(2, add(length, width))

# --- AST EVALUATOR ENGINE ---

OPERATORS_MAP = {
    ast.Add: add,
    ast.Sub: subtract,
    ast.Mult: multiply,
    ast.Div: divide,
    ast.Pow: power,
}

FUNCTIONS_MAP = {
    "sqrt": square_root,
    "pi": math.pi,
    "e": math.e,
}

def _eval_ast_node(node: ast.AST) -> float:
    """Recursively evaluates an Abstract Syntax Tree (AST) node 
    using safe internal mathematical functions.
    """
    
    # Base Case: Literal numbers (e.g., 5, 3.14)
    if isinstance(node, ast.Constant):
        val = node.value
        # Ensure the value is a number, explicitly excluding booleans (True/False)
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            return float(val)
        raise ValueError(f"Invalid constant value: {val}")
    
    # Binary Operations: Expressions with two operands (e.g., a + b, x * y)
    if isinstance(node, ast.BinOp):
        # Recursively evaluate the left and right sub-expressions
        left_val = _eval_ast_node(node.left)
        right_val = _eval_ast_node(node.right)
        
        # Identify the operator type (ast.Add, ast.Sub, etc.) and fetch its handler function
        op_type = type(node.op)
        handler = OPERATORS_MAP.get(op_type)
        if not handler:
            raise ValueError(f"Unsupported operator: {op_type}")
            
        # Execute the corresponding function (e.g., add(left_val, right_val))
        return handler(left_val, right_val)
    
    # Unary Operations: Operations with a single operand (e.g., negative numbers like -5)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        # Evaluate the operand and multiply it by -1.0 to negate it
        operand_val = _eval_ast_node(node.operand)
        return multiply(-1.0, operand_val)
    
    # Function Calls: Functions with arguments (e.g., sqrt(144))
    if isinstance(node, ast.Call):
        func_node = node.func
        # Ensure the called entity is a named function
        if isinstance(func_node, ast.Name):
            func_name = str(func_node.id)
            target_func = FUNCTIONS_MAP.get(func_name)
            
            # Verify the function exists in our allowed dictionary and is callable
            if callable(target_func):
                # Recursively evaluate all arguments passed inside the function parentheses
                args_vals = [_eval_ast_node(arg) for arg in node.args]
                return cast(float,(target_func(*args_vals)))
                
            raise ValueError(f"Function not allowed or invalid: {func_name}")
        raise ValueError("Unsupported function call structure.")
    
    # 5. Named Identifiers: Constants represented by name (e.g., pi, e)
    if isinstance(node, ast.Name):
        var_name = str(node.id)
        symbol_val = FUNCTIONS_MAP.get(var_name)
        if isinstance(symbol_val, (int, float)):
            return float(symbol_val)
        raise ValueError(f"Symbol not allowed: {var_name}")
    
    # Fallback for any unsupported syntax structure (e.g., variable assignments, loops, imports)
    raise TypeError("Unsupported mathematical expression structure.")

def evaluate_expression(expression: str) -> float:
    """Public helper to parse and evaluate string math expressions."""
    clean_expr = expression.replace("^", "**").replace("x", "*")
    parsed = ast.parse(clean_expr, mode="eval")
    return _eval_ast_node(parsed.body)