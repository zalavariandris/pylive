from imgui_bundle import imgui

# COLOR CONSTANTS
_dimmed_alpha = 0.4
RED = imgui.color_convert_float4_to_u32((1,0,0, 1.0))
RED_DIMMED = imgui.color_convert_float4_to_u32((1,0,0, _dimmed_alpha))
BLUE = imgui.color_convert_float4_to_u32((0.3,0.3,1, 1.0))
BLUE_DIMMED = imgui.color_convert_float4_to_u32((0.3,.3,1, _dimmed_alpha))
GREEN = imgui.color_convert_float4_to_u32((0,1,0, 1.0))
GREEN_DIMMED = imgui.color_convert_float4_to_u32((0,1,0, _dimmed_alpha))
WHITE = imgui.color_convert_float4_to_u32((1,1,1, 1.0))
WHITE_DIMMED = imgui.color_convert_float4_to_u32((1,1,1, _dimmed_alpha))
PINK = imgui.color_convert_float4_to_u32((1,0,1, 1.0))
PINK_DIMMED = imgui.color_convert_float4_to_u32((1,0,1, _dimmed_alpha))
YELLOW = imgui.color_convert_float4_to_u32((1,1,0, 1.0))
YELLOW_DIMMED = imgui.color_convert_float4_to_u32((1,1,0, _dimmed_alpha))