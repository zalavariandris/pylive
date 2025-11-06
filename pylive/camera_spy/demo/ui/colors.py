from imgui_bundle import imgui


def _set_alpha(color:int, alpha:float) -> int:
    r, g, b, _ = imgui.color_convert_u32_to_float4(color)
    return imgui.color_convert_float4_to_u32((r, g, b, alpha))

# COLOR CONSTANTS
_dimmed_alpha = 0.4
RED = imgui.color_convert_float4_to_u32((1,0.1,0, 1.0))
RED_DIMMED = _set_alpha(RED, _dimmed_alpha)

BLUE = imgui.color_convert_float4_to_u32((0.0,0.5,1, 1.0))
BLUE_DIMMED = _set_alpha(BLUE, _dimmed_alpha)

GREEN = imgui.color_convert_float4_to_u32((0,1,0, 1.0))
GREEN_DIMMED = _set_alpha(GREEN, _dimmed_alpha)

WHITE = imgui.color_convert_float4_to_u32((1,1,1, 1.0))
WHITE_DIMMED = _set_alpha(WHITE, _dimmed_alpha)

BLACK = imgui.color_convert_float4_to_u32((0,0,0, 1.0))
BLACK_DIMMED = _set_alpha(BLACK, _dimmed_alpha)

PINK = imgui.color_convert_float4_to_u32((1,0,1, 1.0))
PINK_DIMMED = _set_alpha(PINK, _dimmed_alpha)

YELLOW = imgui.color_convert_float4_to_u32((1,1,0, 1.0))
YELLOW_DIMMED = _set_alpha(YELLOW, _dimmed_alpha)

CYAN = imgui.color_convert_float4_to_u32((0,1,1, 1.0))
CYAN_DIMMED = _set_alpha(CYAN, _dimmed_alpha)