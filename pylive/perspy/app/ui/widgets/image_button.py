from imgui_bundle import imgui

from typing import Optional, Literal

def image_button(
    str_id: str,
    tex_ref: imgui.ImTextureRef,
    image_size: imgui.ImVec2Like,
    button_size: imgui.ImVec2Like,
    fit: Literal['stretch', 'fill', 'contain'] = 'contain',
    bg_col: Optional[imgui.ImVec4Like] = None,
    tint_col: Optional[imgui.ImVec4Like] = None,
) -> bool:
    
    image_aspect = image_size.x / image_size.y
    button_aspect = button_size.x / button_size.y

    imgui.calc_item_width()
    match fit:
        case "fill":
            # Fill mode: crop to fit the button (keep aspect ratio)
            aspect_ratio = image_aspect / button_aspect
            if aspect_ratio > 1:  # Image is wider relative to button: fit height, crop width
                uv0 = imgui.ImVec2((1 - 1/aspect_ratio) / 2, 0)
                uv1 = imgui.ImVec2((1 + 1/aspect_ratio) / 2, 1)
            else:  # Image is taller relative to button: fit width, crop height
                uv0 = imgui.ImVec2(0, (1 - aspect_ratio) / 2)
                uv1 = imgui.ImVec2(1, (1 + aspect_ratio) / 2)
                
        case "contain":
            # Contain mode: show entire image with letterboxing/pillarboxing
            aspect_ratio = image_aspect / button_aspect
            if aspect_ratio > 1:  # Image is wider: add letterboxing top/bottom
                uv0 = imgui.ImVec2(0, -0.5 * (aspect_ratio - 1))
                uv1 = imgui.ImVec2(1, 1 + 0.5 * (aspect_ratio - 1))
            else:  # Image is taller: add pillarboxing left/right
                uv0 = imgui.ImVec2(-0.5 * (1/aspect_ratio - 1), 0)
                uv1 = imgui.ImVec2(1 + 0.5 * (1/aspect_ratio - 1), 1)

        case "stretch":
            # Stretch mode: ignore aspect ratio
            uv0 = imgui.ImVec2(0, 0)
            uv1 = imgui.ImVec2(1, 1)


    return imgui.image_button(
        str_id,
        tex_ref,
        button_size,
        uv0=uv0,
        uv1=uv1,
        bg_col=bg_col,
        tint_col=tint_col,
    )