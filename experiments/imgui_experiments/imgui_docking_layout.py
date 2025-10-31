from imgui_bundle import imgui, immapp

def gui():
    imgui.get_io().config_flags |= imgui.ConfigFlags_.docking_enable

    flags =  (
        imgui.WindowFlags_.menu_bar
        | imgui.WindowFlags_.no_title_bar
        | imgui.WindowFlags_.no_collapse
        | imgui.WindowFlags_.no_resize
        | imgui.WindowFlags_.no_move
        | imgui.WindowFlags_.no_background
        # | imgui.WindowFlags_.no_bring_to_front_on_focus
        | imgui.WindowFlags_.no_nav_focus
    )

    viewport = imgui.get_main_viewport()
    
    imgui.set_next_window_pos(viewport.pos)
    imgui.set_next_window_size(viewport.size)
    imgui.begin("MainDockSpace", flags=flags)

    # imgui.dock_space()
    imgui.dock_space_over_viewport(
        dockspace_id=0,
        viewport=imgui.get_main_viewport(),
        flags=imgui.DockNodeFlags_.passthru_central_node
    )
    imgui.end()

    imgui.set_next_window_dock_id(0)
    imgui.begin("Left sidebar")
    imgui.end()

    imgui.set_next_window_dock_id(0)
    imgui.begin("Main area")
    imgui.end()

    imgui.set_next_window_dock_id(0)
    imgui.begin("Right sidebar")
    imgui.end()

    imgui.show_style_editor()

if __name__ == "__main__":
    immapp.run(gui)