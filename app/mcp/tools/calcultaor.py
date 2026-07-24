import json
from app.mcp.server_instance import mcp
import app.lib.math_utils as math_utils


@mcp.tool()
def calculate_expression(expression: str) -> str:
    """Evaluate arithmetic expressions and math formulas safely.
    Supports basic operations (+, -, *, /), exponents (^ or **), trigonometric/math functions (sqrt, sin, cos, etc.), and constants (pi, e).
    Use this tool whenever you need to compute numbers accurately."""
    try:
        result = math_utils.evaluate_expression(expression)
        return json.dumps({
            "status": "success",
            "expression": expression,
            "result": round(result, 6) if isinstance(result, float) else result
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
def geometry_calculator(shape: str, calculation: str, radius: float = 0.0, length: float = 0.0, width: float = 0.0) -> str:
    """Calculate geometric properties like area or perimeter.
    Supported shapes: 'circle', 'rectangle'.
    Supported calculations: 'area', 'perimeter'."""
    try:
        shape_clean = shape.lower()
        calc_clean = calculation.lower()

        if shape_clean == "circle" and calc_clean == "area":
            result = math_utils.circle_area(radius)
        elif shape_clean == "rectangle" and calc_clean == "perimeter":
            result = math_utils.rectangle_perimeter(length, width)
        else:
            return json.dumps({"status": "error", "message": "Unsupported shape or calculation method."})

        return json.dumps({
            "status": "success",
            "shape": shape_clean,
            "calculation": calc_clean,
            "result": round(result, 4)
        }, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)