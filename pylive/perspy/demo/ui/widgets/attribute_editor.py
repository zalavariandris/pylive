from imgui_bundle import imgui

def begin_attribute_editor(str_id:str):
    imgui.set_next_item_width(200)
    if imgui.begin_table(str_id, 2):
        imgui.table_setup_column("name", imgui.TableColumnFlags_.width_fixed)
        imgui.table_setup_column("value", imgui.TableColumnFlags_.width_stretch | imgui.TableColumnFlags_.no_clip)
        return True
    return False

def end_attribute_editor():
    imgui.end_table()

def next_attribute(string:str=""):
    imgui.table_next_row()
    imgui.table_next_column()
    imgui.push_style_var(imgui.StyleVar_.selectable_text_align, imgui.ImVec2(1.0,0))
    imgui.push_style_color(imgui.Col_.header_hovered, (0, 0, 0, 0))
    imgui.push_style_color(imgui.Col_.header_active,  (0, 0, 0, 0))
    imgui.selectable(string, False)
    imgui.pop_style_var()
    imgui.pop_style_color(2)
    imgui.table_next_column()
    imgui.set_next_item_width(-1) # stretch item to fill cell
