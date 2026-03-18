"""Theme helpers for the main window."""


def is_dark_palette(palette):
    background = palette.color(palette.Window)
    return background.lightness() < 128


def build_main_window_stylesheet(dark, mono_font_family):
    if dark:
        fg = "#e0e0e0"
        fg_dim = "#a0a0a0"
        fg_accent = "#6ab0f5"
        fg_danger = "#f47a7a"
        bg_btn = "#3a3a3a"
        bg_btn_h = "#4a4a4a"
        bg_btn_dis = "#2a2a2a"
        border = "#555555"
        bg_primary = "#1e3a6e"
        bg_prim_h = "#2a4e8e"
        bg_danger = "#5a1a1a"
        bg_danger_h = "#6e2020"
        tree_sel = "#1e3a5e"
        tree_sel_fg = "#6ab0f5"
        tree_hover = "#2a2a2a"
        tab_sel_top = "#6ab0f5"
        tab_fg_sel = "#6ab0f5"
        tab_fg = "#888888"
        out_fg = "#90d090"
    else:
        fg = "#1a1a1a"
        fg_dim = "#606060"
        fg_accent = "#1a56db"
        fg_danger = "#c0002a"
        bg_btn = "#e8e8e8"
        bg_btn_h = "#d8d8d8"
        bg_btn_dis = "#f0f0f0"
        border = "#b0b0b0"
        bg_primary = "#1a56db"
        bg_prim_h = "#1440b0"
        bg_danger = "#fff0f0"
        bg_danger_h = "#ffe0e0"
        tree_sel = "#c8daff"
        tree_sel_fg = "#1a1a8e"
        tree_hover = "#e8e8ff"
        tab_sel_top = "#1a56db"
        tab_fg_sel = "#1a56db"
        tab_fg = "#606060"
        out_fg = "#1a6e1a"

    return f"""
#logo      {{ font-size: 15px; font-weight: 700; letter-spacing: 1px; color: {fg_accent}; }}
#bar_label {{ color: {fg_dim}; font-size: 11px; font-weight: 600; }}
#bar_sep   {{ color: {border}; font-size: 18px; margin: 0 4px; }}

#bar_combo, QComboBox {{
    color: {fg}; border: 1px solid {border}; border-radius: 5px;
    padding: 4px 10px; font-size: 12px; min-height: 28px;
}}
#bar_combo QAbstractItemView, QComboBox QAbstractItemView {{
    color: {fg}; selection-color: {fg};
}}

#topbar_btn {{
    background: {bg_btn}; color: {fg};
    border: 1px solid {border}; border-radius: 5px;
    padding: 5px 12px; font-size: 12px; min-height: 28px;
}}
#topbar_btn:hover    {{ background: {bg_btn_h}; }}
#topbar_btn:disabled {{ background: {bg_btn_dis}; color: {fg_dim}; border-color: {border}; }}

#section_header {{
    color: {fg_dim}; font-size: 10px; font-weight: 700;
    letter-spacing: 1.5px; padding-left: 14px;
    border-bottom: 1px solid {border};
}}

#proj_tree {{
    color: {fg}; border: none; font-size: 13px;
    outline: none; padding: 4px 0;
}}
#proj_tree::item {{ padding: 5px 8px; border-radius: 4px; }}
#proj_tree::item:hover    {{ background: {tree_hover}; }}
#proj_tree::item:selected {{ background: {tree_sel}; color: {tree_sel_fg}; }}

#tree_add_btn {{
    color: {fg}; border: 1px solid {border}; border-radius: 5px;
    padding: 6px 0; font-size: 12px;
}}
#tree_add_btn:hover {{ color: {fg_accent}; border-color: {fg_accent}; }}

#page_title   {{ font-size: 20px; font-weight: 700; color: {fg_accent}; padding-bottom: 4px; }}
#info_label   {{ color: {fg_dim}; font-size: 12px; }}
#welcome_hint {{ color: {fg_dim}; font-size: 14px; line-height: 2; }}

#action_primary {{
    background: {bg_primary}; color: #ffffff;
    border: 1px solid {bg_prim_h}; border-radius: 6px;
    padding: 10px 16px; font-size: 13px; font-weight: 600; min-height: 40px;
}}
#action_primary:hover {{ background: {bg_prim_h}; }}

#action_default {{
    background: {bg_btn}; color: {fg};
    border: 1px solid {border}; border-radius: 6px;
    padding: 10px 16px; font-size: 13px; min-height: 40px;
}}
#action_default:hover {{ background: {bg_btn_h}; }}

#action_danger {{
    background: {bg_danger}; color: {fg_danger};
    border: 1px solid {fg_danger}; border-radius: 6px;
    padding: 10px 16px; font-size: 13px; min-height: 40px;
}}
#action_danger:hover {{ background: {bg_danger_h}; }}

#card_group {{
    border: 1px solid {border}; border-radius: 8px;
    margin-top: 8px; padding-top: 12px;
    font-size: 11px; font-weight: 700; letter-spacing: .5px;
}}

QLineEdit {{
    color: {fg}; border: 1px solid {border}; border-radius: 5px;
    padding: 7px 11px; font-size: 13px;
}}
QLineEdit:focus {{ border: 1px solid {fg_accent}; }}

#terminal_tabs QTabBar::tab {{
    color: {tab_fg};
    border: 1px solid {border}; border-bottom: none;
    padding: 5px 28px 5px 14px; font-size: 11px; min-width: 120px;
}}
#terminal_tabs QTabBar::tab:selected {{
    color: {tab_fg_sel};
    border-top: 2px solid {tab_sel_top};
}}
#terminal_tabs QTabBar::tab:hover {{ color: {fg}; }}
#terminal_tabs QTabBar::close-button {{
    subcontrol-position: right; subcontrol-origin: padding;
    width: 14px; height: 14px;
}}
#terminal_tabs QTabBar::close-button:hover {{
    background: {fg_danger}; border-radius: 3px;
}}

#output_text {{
    color: {out_fg};
    border: none; font-family: '{mono_font_family}'; font-size: 10px;
}}

QMenu::item:selected {{ color: {fg_accent}; }}
QStatusBar {{ color: {fg_dim}; font-size: 11px; }}
"""
