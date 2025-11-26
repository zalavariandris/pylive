from imgui_bundle import hello_imgui
from imgui_bundle import imgui
from imgui_bundle import icons_fontawesome_4
import logging

logger = logging.getLogger(__name__)
# Setup HelloImGui application parameters
def create_fontawesome_assets_folder(self):
    """Create the proper assets folder structure for FontAwesome fonts"""
    from pathlib import Path
    
    # Create the assets/fonts directory structure
    demo_dir = Path(__file__).parent
    assets_fonts_dir = demo_dir / "assets" / "fonts"
    
    try:
        assets_fonts_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Created directory: {assets_fonts_dir}")
        
        # Create a README file with instructions
        readme_file = assets_fonts_dir / "README_FontAwesome.txt"
        readme_content = """FontAwesome Font Setup for ImGui Bundle

This folder should contain: fontawesome-webfont.ttf

HOW TO GET FontAwesome FONT:

1. Download FontAwesome 4 Web Font:
Visit: https://fontawesome.com/v4/get-started/
Download the web font package
Extract fontawesome-webfont.ttf from the fonts/ folder

2. Download ImGui Bundle default assets (includes FontAwesome):
Visit: https://traineq.org/ImGuiBundle/assets.zip
Extract to get the complete assets folder with fonts

3. Use wget/curl (if available):
wget https://github.com/FortAwesome/Font-Awesome/raw/v4.7.0/fonts/fontawesome-webfont.ttf

Once you have fontawesome-webfont.ttf, place it in this folder.
Then restart your application to load FontAwesome icons!
"""
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"✓ Created instructions: {readme_file}")
        logger.info("📁 Assets folder structure created!")
        logger.info("📋 Check README_FontAwesome.txt for detailed instructions")
        logger.info("")
        logger.info("🚀 Next steps:")
        logger.info("   1. Download fontawesome-webfont.ttf (see README)")
        logger.info(f"   2. Place it in: {assets_fonts_dir}/")
        logger.info("   3. Restart the application")
        
    except Exception as e:
        logger.error(f"Failed to create assets folder: {e}")
        import traceback
        traceback.print_exc()

def load_additional_fonts():
    """Load FiraCode fonts with emoji support"""
    from pathlib import Path
    try:
        # Get the fonts directory
        script_dir = Path(__file__).parent
        fonts_dir = Path("fonts/FiraCode")
        
        io = imgui.get_io()

        # Get DPI scale factor
        dpi_scale = hello_imgui.dpi_window_size_factor()
        # logger.info(f"DPI scale factor: {dpi_scale}")
        
        # Scale font sizes by DPI
        print("dpi_scale:", dpi_scale)
        base_size = 12.0*dpi_scale
        
        # Check if FiraCode exists
        fira_regular = fonts_dir / "FiraCode-Regular.ttf"
        fira_bold = fonts_dir / "FiraCode-Bold.ttf"
        
        if fira_regular.exists():
            # Configure font to merge with system emoji font
            font_cfg = imgui.ImFontConfig()
            font_cfg.merge_mode = False  # First font, don't merge
            
            # Add FiraCode as primary font
            font = io.fonts.add_font_from_file_ttf(str(fira_regular), base_size, font_cfg)
            logger.info(f"✓ Loaded FiraCode Regular from {fira_regular} at {base_size}px")
            
            # Add FontAwesome icons as merged font
            # Try different FontAwesome loading methods based on imgui_bundle version
            fa_loaded = False
            
            try:
                # Method 1: Check if immapp has FontAwesome functions
                from imgui_bundle import immapp
                if hasattr(immapp, 'add_font_awesome_to_font_atlas'):
                    immapp.add_font_awesome_to_font_atlas()
                    fa_loaded = True
                    logger.info("✓ Loaded FontAwesome via immapp.add_font_awesome_to_font_atlas()")
                elif hasattr(immapp, 'load_font_awesome'):
                    immapp.load_font_awesome(base_size)
                    fa_loaded = True
                    logger.info("✓ Loaded FontAwesome via immapp.load_font_awesome()")
            except Exception as e1:
                logger.warning(f"immapp FontAwesome loading failed: {e1}")
            
            if not fa_loaded:
                try:
                    # Method 2: Try manual font file approach
                    import os
                    from pathlib import Path
                    
                    # Look for FontAwesome font file per imgui_bundle conventions
                    script_dir = Path(__file__).parent
                    possible_fa_paths = [
                        # imgui_bundle expects FontAwesome in assets/fonts/ folder
                        script_dir / "assets" / "fonts" / "fontawesome-webfont.ttf",
                        script_dir / "assets" / "fonts" / "fa-solid-900.ttf",  # FontAwesome 5/6
                        script_dir / "assets" / "fonts" / "FontAwesome.ttf",
                        # Also check the fonts/ folder you already have
                        script_dir / "fonts" / "fontawesome-webfont.ttf",
                        script_dir / "fonts" / "FontAwesome.ttf",
                        # Check parent directory assets (common pattern)
                        script_dir.parent / "assets" / "fonts" / "fontawesome-webfont.ttf",
                        # Try system fonts
                        Path("C:/Windows/Fonts/fontawesome-webfont.ttf"),
                    ]
                    
                    fa_font_loaded = False
                    for fa_path in possible_fa_paths:
                        if fa_path.exists():
                            try:
                                # Method 1: Try with glyph ranges
                                fa_config = imgui.ImFontConfig()
                                fa_config.merge_mode = True
                                
                                # Create glyph ranges properly for imgui_bundle
                                fa_ranges = imgui.GlyphRangesBuilder()
                                fa_ranges.add_ranges(imgui.get_io().fonts.get_glyph_ranges_default())
                                # Add FontAwesome range
                                fa_ranges.add_char(ord(icons_fontawesome_4.ICON_MIN_FA))
                                fa_ranges.add_char(ord(icons_fontawesome_4.ICON_MAX_FA))
                                ranges = fa_ranges.build_ranges()
                                
                                font = io.fonts.add_font_from_file_ttf(str(fa_path), base_size, fa_config, ranges)
                                if font:
                                    logger.info(f"✓ Loaded FontAwesome from file (with ranges): {fa_path}")
                                    fa_font_loaded = True
                                    fa_loaded = True
                                    break
                            except Exception as e3a:
                                logger.warning(f"Failed to load FontAwesome with ranges from {fa_path}: {e3a}")
                                try:
                                    # Method 2: Try without ranges (simpler)
                                    fa_config_simple = imgui.ImFontConfig()
                                    fa_config_simple.merge_mode = True
                                    font = io.fonts.add_font_from_file_ttf(str(fa_path), base_size, fa_config_simple)
                                    if font:
                                        logger.info(f"✓ Loaded FontAwesome from file (no ranges): {fa_path}")
                                        fa_font_loaded = True
                                        fa_loaded = True
                                        break
                                except Exception as e3b:
                                    logger.warning(f"Failed to load FontAwesome without ranges from {fa_path}: {e3b}")
                                try:
                                    # Method 3: Try with None config (most basic)
                                    font = io.fonts.add_font_from_file_ttf(str(fa_path), base_size)
                                    if font:
                                        logger.info(f"✓ Loaded FontAwesome from file (basic): {fa_path}")
                                        fa_font_loaded = True
                                        fa_loaded = True
                                        break
                                except Exception as e3c:
                                    logger.warning(f"All FontAwesome loading methods failed for {fa_path}: {e3c}")
                    
                    if not fa_font_loaded and not fa_loaded:
                        logger.warning("No FontAwesome font loaded. Icons will appear as boxes or empty spaces.")
                        logger.info("FontAwesome constants are available but need the font file to render properly.")
                        logger.info("")
                        logger.info("📁 WHERE TO PLACE FontAwesome FONT:")
                        demo_dir = Path(__file__).parent
                        logger.info(f"   Create: {demo_dir}/assets/fonts/")
                        logger.info(f"   Place fontawesome-webfont.ttf in that folder")
                        logger.info("")
                        logger.info("📦 HOW TO GET FontAwesome FONT:")
                        logger.info("   1. Download from: https://fontawesome.com/v4/get-started/")
                        logger.info("   2. Or download default assets: https://traineq.org/ImGuiBundle/assets.zip")
                        logger.info("   3. Or pip install fonttools and get from CDN")
                        logger.info("")
                        logger.info("🔧 CHECKED THESE LOCATIONS:")
                        for path in possible_fa_paths:
                            exists_str = "✓" if path.exists() else "✗"
                            logger.info(f"   {exists_str} {path}")
                        logger.info("")
                        logger.info("💡 Alternative: Use Unicode symbols instead of FontAwesome icons")
                        
                except Exception as e2:
                    logger.warning(f"Manual FontAwesome loading failed: {e2}")
                    logger.info("FontAwesome icons will not be available")
            
            # Try to add system emoji font as fallback
            try:
                import platform
                system = platform.system()
                
                emoji_font_cfg = imgui.ImFontConfig()
                emoji_font_cfg.merge_mode = True  # Merge with previous font
                emoji_font_cfg.pixel_snap_h = True
                
                emoji_font_path = None
                if system == "Windows":
                    # Try Windows emoji fonts
                    for font_name in ["seguiemj.ttf", "NotoColorEmoji.ttf"]:
                        font_path = Path(f"C:/Windows/Fonts/{font_name}")
                        if font_path.exists():
                            emoji_font_path = str(font_path)
                            break
                elif system == "Darwin":  # macOS
                    emoji_font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
                elif system == "Linux":
                    # Try common Linux emoji fonts
                    for font_path in ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                                    "/usr/share/fonts/TTF/NotoColorEmoji.ttf"]:
                        if Path(font_path).exists():
                            emoji_font_path = font_path
                            break
                
                if emoji_font_path and Path(emoji_font_path).exists():
                    # Try to load emoji font without specific ranges first (simpler approach)
                    try:
                        io.fonts.add_font_from_file_ttf(emoji_font_path, base_size, emoji_font_cfg)
                        logger.info(f"✓ Loaded emoji font: {emoji_font_path}")
                    except Exception as e:
                        logger.warning(f"Could not load emoji font {emoji_font_path}: {e}")
                        # Fallback: try with default glyph ranges
                        try:
                            emoji_font_cfg_simple = imgui.ImFontConfig()
                            emoji_font_cfg_simple.merge_mode = True
                            io.fonts.add_font_from_file_ttf(emoji_font_path, base_size, emoji_font_cfg_simple)
                            logger.info(f"✓ Loaded emoji font (fallback): {emoji_font_path}")
                        except Exception as e2:
                            logger.warning(f"Emoji font fallback also failed: {e2}")
                else:
                    logger.warning(f"No emoji font found for {system}")
                    
            except Exception as e:
                logger.warning(f"Could not load emoji font: {e}")
            
            if fira_bold.exists():
                io.fonts.add_font_from_file_ttf(str(fira_bold), base_size)
                logger.info(f"✓ Loaded FiraCode Bold from {fira_bold} at {base_size}px")
        else:
            logger.warning(f"FiraCode font not found at {fira_regular.absolute()}")
            # Fallback to default font
            io.fonts.add_font_default()
            
    except Exception as e:
        logger.error(f"Failed to load fonts: {e}")
        import traceback
        traceback.print_exc()

def setup_imgui_config():
    """Setup ImGui configuration before initialization"""
    io = imgui.get_io()
    # Disable docking completely
    io.config_flags &= ~imgui.ConfigFlags_.docking_enable
    io.config_flags &= ~imgui.ConfigFlags_.viewports_enable  # Also disable viewports

def setup_imgui_style():
    style = imgui.get_style()
    imgui.style_colors_dark(style)

    style.anti_aliased_lines = True
    style.anti_aliased_lines_use_tex = True
    style.anti_aliased_fill = True

    levels = [
        0.08,   # really deep
        0.09,   # deep
        0.11,   # medium
        0.15,   # shallow
    ]

    windows_dark_titlebar_color = [ 32/255,  32/255, 32/255, 1.0]
    levels = [
        22/255,   # really deep
        32/255,   # deep
        43/255,   # medium
        57/255,   # shallow
    ]
    windows_dark_text_color =     [255/255, 255/255, 255/255, 1.0]

    style.set_color_(imgui.Col_.text ,               windows_dark_text_color)
    style.set_color_(imgui.Col_.title_bg ,           imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.title_bg_active ,    imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.title_bg_collapsed , imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.window_bg,           imgui.ImVec4(*[levels[1]]*3,1.00))
    style.set_color_(imgui.Col_.scrollbar_bg,         imgui.ImVec4(*[levels[1]]*3,1.00))


    style.set_color_(imgui.Col_.child_bg ,           imgui.ImVec4(*[levels[2]]*3,1.00))
    style.set_color_(imgui.Col_.frame_bg ,           imgui.ImVec4(*[levels[3]]*3,1.00))
    style.set_color_(imgui.Col_.button   ,           imgui.ImVec4(*[levels[3]]*3,1.00))
    style.set_color_(imgui.Col_.popup_bg ,           imgui.ImVec4(*[levels[1]]*3,1.00))

    # now the checkbox frame and dropdown button has the same color
    style.set_color_(imgui.Col_.button_hovered,         style.color_(imgui.Col_.frame_bg_hovered))

    # Remove the dark border by setting menu bar background to match the menu bar
    style.set_color_(imgui.Col_.menu_bar_bg,         windows_dark_titlebar_color)
    
    style.window_padding = imgui.ImVec2(12, 12)
    style.frame_padding = imgui.ImVec2(6, 6)
    style.item_spacing = imgui.ImVec2(12, 12)

    style.frame_border_size = 0

    style.child_border_size = 0
    style.window_border_size = 0
    style.set_color_(imgui.Col_.border   , imgui.ImVec4(*[levels[2]]*3,1.00))
    style.popup_border_size = 1

    style.grab_min_size = 4

    
    style.grab_rounding = 4
    style.frame_rounding = 4
    style.frame_rounding = 4
    style.popup_rounding = 4
    style.child_rounding = 4
    style.window_rounding = 4
    style.scrollbar_rounding = 4

    style.window_title_align = imgui.ImVec2(0.5, 0.5)
    style.window_menu_button_position = imgui.Dir.right

    style.separator_text_border_size = 1
    style.separator_text_align = imgui.ImVec2(0.0, 0.5)
    style.separator_text_padding = imgui.ImVec2(0, 3)

    logger.info("✓ ImGui theme applied")

def _setup_file_drop_callback_for_glfw(callback):
    """Setup GLFW file drop callback"""
    try:
        import glfw
        # Method 2: Try getting current context window
        window = glfw.get_current_context()

        if not window:
            logger.warning("Could not get GLFW window handle")
            return

        glfw.set_drop_callback(window, callback)
        logger.info("✓ File drop callback installed successfully (method2)")
        return
            
    except ImportError:
        logger.warning("glfw module not available. Install with: pip install glfw")
    except Exception as e:
        logger.warning(f"Could not setup file drop: {e}")
        import traceback
        traceback.print_exc()

def _set_dark_mode_on_windows(enable: bool | None = None):
    """Set dark mode on Windows for the application window
    
    Args:
        enable: True for dark mode, False for light mode, None to detect system settings
    """
    import platform
    if platform.system() != "Windows":
        logger.info("Dark mode API only available on Windows")
        return
        
    try:
        import ctypes
        from ctypes import wintypes
        import winreg
        import glfw
        
        # Determine which mode to use
        if enable is None:
            # Auto-detect system dark mode setting
            def is_system_dark_mode():
                try:
                    # Check registry for current theme
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    winreg.CloseKey(key)
                    # Value is 0 for dark mode, 1 for light mode
                    return value == 0
                except Exception:
                    # Fallback: assume light mode if we can't read registry
                    return False
            
            use_dark_mode_bool = is_system_dark_mode()
            logger.info(f"System dark mode detected: {use_dark_mode_bool}")
        else:
            # Use explicitly provided setting
            use_dark_mode_bool = bool(enable)
            source = "explicit setting" if enable is not None else "system detection"
            logger.info(f"Dark mode set to {use_dark_mode_bool} via {source}")
        
        # Get the GLFW window handle
        window = glfw.get_current_context()
        if not window:
            logger.warning("Could not get GLFW window for dark mode setup")
            return
            
        # Get the native Windows window handle (HWND)
        hwnd = glfw.get_win32_window(window)
        if not hwnd:
            logger.warning("Could not get Windows HWND")
            return
        
        # Define Windows constants for dark mode
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        
        # Load DWM library
        dwmapi = ctypes.windll.dwmapi
        
        # Set up DwmSetWindowAttribute function
        dwmapi.DwmSetWindowAttribute.argtypes = [
            wintypes.HWND,      # hwnd
            wintypes.DWORD,     # dwAttribute  
            ctypes.c_void_p,    # pvAttribute
            wintypes.DWORD      # cbAttribute
        ]
        
        # Set dark mode based on determined setting
        use_dark_mode = wintypes.BOOL(use_dark_mode_bool)
        
        # Try the newer attribute first (Windows 10 build 20H1+)
        result = dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(use_dark_mode),
            ctypes.sizeof(use_dark_mode)
        )
        
        # If that fails, try the older attribute (Windows 10 earlier builds)
        if result != 0:
            result = dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                ctypes.byref(use_dark_mode),
                ctypes.sizeof(use_dark_mode)
            )
        
        if result == 0:  # S_OK
            mode_str = "dark" if use_dark_mode_bool else "light"
            logger.info(f"✓ Windows {mode_str} mode applied to title bar")
        else:
            logger.warning(f"Failed to set window theme: DWM error {result}")
            
    except ImportError as e:
        logger.warning(f"Windows API not available: {e}")
    except Exception as e:
        logger.warning(f"Failed to setup window theme: {e}")
        import traceback
        traceback.print_exc()

def _set_titlebar_color_on_macos():
    """Set custom titlebar color for the application window macOS"""
    import platform
    if platform.system() != "Darwin":
        logger.info("macOS window styling only available on macOS")
        return
        
    try:
        import glfw
        
        # Get the GLFW window handle
        window = glfw.get_current_context()
        if not window:
            logger.warning("Could not get GLFW window for macOS styling")
            return
        
        # Access the native NSWindow through pyobjc
        try:
            from AppKit import NSApp, NSColor, NSWindowStyleMaskFullSizeContentView
            import objc
            
            
            def get_ns_window():
                """Try multiple methods to get the NSWindow"""
                # Method 1: Get main window
                ns_window = NSApp.mainWindow()
                if ns_window:
                    logger.info("Got NSWindow from NSApp mainWindow")
                    return ns_window
                
                # Method 2: Try key window if main window is None
                ns_window = NSApp.keyWindow()
                if ns_window:
                    logger.info("Got NSWindow from NSApp keyWindow")
                    return ns_window

                # Method 3: Get from windows array
                windows = NSApp.windows()
                if windows and len(windows) > 0:
                    ns_window = windows[0]
                    if ns_window:
                        logger.info("Got NSWindow from NSApp windows array")
                        return ns_window
                
                # Method 4: Use GLFW's Cocoa window directly
                try:
                    cocoa_window = glfw.get_cocoa_window(window)
                    if cocoa_window:
                        ns_window = objc.objc_object(c_void_p=cocoa_window)
                        if ns_window:
                            logger.info("Got NSWindow from GLFW Cocoa window")
                            return ns_window
                except Exception as e:
                    logger.warning(f"Failed to get NSWindow from GLFW Cocoa window: {e}")
                
                if not ns_window:
                    logger.warning("Could not get NSWindow - window may not be fully initialized yet")
                    logger.info("Titlebar styling skipped - window will use default appearance")
                    return
                
            ns_window = get_ns_window()
            if not ns_window:
                logger.warning("NSWindow is None - cannot apply macOS styling")
                return
            
            # Remove titlebar border and set custom color
            ns_window.setTitlebarAppearsTransparent_(True) # setting titlebar transparent removes the little border between titlebar and content
            dark_gray = NSColor.colorWithRed_green_blue_alpha_(32/255, 32/255, 32/255, 1.0) # we can also set our own color.
            ns_window.setBackgroundColor_(dark_gray)

            default_titlebar_color = NSColor.controlBackgroundColor() 
            
            # Set titlebar appearance (dark or light) - this affects text color
            # NSAppearance options: 
            # - NSAppearanceNameAqua (light mode - dark text)
            # - NSAppearanceNameDarkAqua (dark mode - light text)
            from AppKit import NSAppearance
            dark_appearance = NSAppearance.appearanceNamed_("NSAppearanceNameDarkAqua")
            ns_window.setAppearance_(dark_appearance)  # This makes titlebar text white/light
            
            # Alternative: Set title text color directly
            # Note: This requires accessing the titlebar's text field, which is more complex
            # The appearance setting above is the recommended approach
            
        except ImportError:
            logger.warning("pyobjc not available. Install with: pip install pyobjc-framework-Cocoa")
            logger.info("Basic window styling still applied via GLFW")
        except Exception as e:
            logger.warning(f"Advanced macOS styling failed: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        logger.warning(f"GLFW not available: {e}")
    except Exception as e:
        logger.warning(f"Failed to setup macOS window styling: {e}")
        import traceback
        traceback.print_exc()

def post_init_add_platform_backend_callbacks():
    """Called after platform backend is initialized - best time for native window customization"""
    import platform
    if platform.system() == "Darwin":
        _set_titlebar_color_on_macos()
    elif platform.system() == "Windows":
        _set_dark_mode_on_windows(True)

def create_my_runner_params(gui_function: callable, setup_function:callable, on_file_drop: callable, window_title: str) -> hello_imgui.RunnerParams:
    """Create HelloImGui application configuration"""
    runner_params = hello_imgui.RunnerParams(
        callbacks=hello_imgui.RunnerCallbacks(
            show_gui = lambda: gui_function(),
            # show_menus=None,
            # show_app_menu_items=None,
            # show_status=None,
            post_init_add_platform_backend_callbacks = post_init_add_platform_backend_callbacks,
            post_init = lambda: (_setup_file_drop_callback_for_glfw(on_file_drop), setup_function() if setup_function else None),
            load_additional_fonts = load_additional_fonts,
            # default_icon_font=hello_imgui.DefaultIconFont.font_awesome4,
            setup_imgui_config = setup_imgui_config,
            setup_imgui_style = setup_imgui_style,
            # register_tests=None,
            # register_tests_called=False,
            # before_exit=None,
            # before_exit_post_cleanup=None,
            # pre_new_frame=None,
            # before_imgui_render=None,
            # after_swap=None,
            # custom_background=None,
            # post_render_dockable_windows=None,
            any_backend_event_callback=None
        ),
        app_window_params=hello_imgui.AppWindowParams(
            window_title=window_title,
            # window_geometry=hello_imgui.WindowGeometry(
            #     position=(100, 100),
            #     size=(1200, 512),
            # ),
            restore_previous_geometry=True
            # repaint_during_resize_gotcha_reentrant_repaint=True,
            # borderless=True,
            # borderless_movable=True,
            # borderless_resizable=True,
            # borderless_closable=True,
        ),
        imgui_window_params=hello_imgui.ImGuiWindowParams(
            menu_app_title="Perspy v0.5.0",
            background_color=[27/255, 27/255, 27/255, 1.0], # a little bit darker than windows sytem titlebar color
            default_imgui_window_type=hello_imgui.DefaultImGuiWindowType.no_default_window,
        ),
        dpi_aware_params=hello_imgui.DpiAwareParams(
            # dpi_window_size_factor=1.0 # Enable DPI awareness: 1.0 is Auto-detect?
        ),
        docking_params=hello_imgui.DockingParams(
            layout_condition=hello_imgui.DockingLayoutCondition.never # Completely disable docking at the hello_imgui level
        ),
    )
    return runner_params