import flet as ft
import os
import threading
import queue
import time
from src.config_manager import ConfigManager
from src.license_manager import LicenseManager
from src.localization import LocalizationManager
from src.upload_manager import UploadManager
from src.history_helpers import get_video_history
from main import run_batch

# PREMIUM CONFIGURATION
BG_COLOR = "#111318"         # Deep Dark Blue-Black
SIDEBAR_COLOR = "#1a1d26"     # Slightly lighter
CARD_COLOR = "#21252e"        # Card background
ACCENT_COLOR = "#4E75FF"      # Vivid Blue
ACCENT_GRADIENT = ft.LinearGradient(
    begin=ft.Alignment(-1.0, -1.0),
    end=ft.Alignment(1.0, 1.0),
    colors=["#4E75FF", "#8A4EFF"], # Blue to Purple
)
TEXT_COLOR = ft.Colors.WHITE
TEXT_SUBTITLE = ft.Colors.GREY_400

class AppState:
    def __init__(self):
        self.config = ConfigManager()
        self.license_manager = LicenseManager(self.config)
        self.loc = LocalizationManager(language=self.config.get_preference("language", "en"))
        self.uploader = UploadManager(log_callback=self.log_buffer, loc=self.loc)
        self.log_queue = queue.Queue()

    def log_buffer(self, msg):
        self.log_queue.put(msg)

state = AppState()

def main(page: ft.Page):
    page.title = "AI YouTube Shorts Generator - Pro Edition"
    try: page.window.icon = "assets/logo.png"
    except: pass
    try: page.icon = "assets/logo.png"
    except: pass
    try: page.window_icon = "assets/logo.png"
    except: pass

    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_COLOR
    page.padding = 0
    page.window_width = 1200
    page.window_height = 850
    page.window.center()
    
    # Custom Fonts via Google Fonts (Loaded automatically by Flet usually, or use system fonts with nice stack)
    page.fonts = {
        "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
        "Roboto Bold": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    }
    page.theme = ft.Theme(font_family="Roboto")

    # --- LOGGING SYSTEM ---
    log_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    
    def log_updater():
        while True:
            try:
                msg = state.log_queue.get_nowait()
                now = time.strftime("%H:%M:%S")
                log_column.controls.append(
                    ft.Text(f"[{now}] {str(msg)}", font_family="Consolas", size=12, color="#00FF00" if "Done" in str(msg) else "#E0E0E0")
                )
                page.update()
            except queue.Empty:
                time.sleep(0.1)

    threading.Thread(target=log_updater, daemon=True).start()

    def log_message(msg):
        state.log_queue.put(msg)
        
    def show_snack(msg, color=ft.Colors.GREEN):
        snack = ft.SnackBar(ft.Text(msg, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def open_folder(path):
        import platform, subprocess
        try:
            folder = os.path.dirname(os.path.abspath(path))
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            show_snack(f"Error opening folder: {e}", ft.Colors.RED)

    # --- REUSABLE COMPONENTS ---
    def create_card(content, padding=30):
        return ft.Container(
            content=content,
            bgcolor=CARD_COLOR,
            padding=padding,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            ),
            border=ft.border.all(1, "#2b303b")
        )

    def create_stat_card(icon, value, label):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=30, color=ft.Colors.WHITE),
                    padding=15,
                    bgcolor=ACCENT_COLOR, # Solid fallback or gradient
                    gradient=ACCENT_GRADIENT,
                    border_radius=12
                ),
                ft.Column([
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(label, size=12, color=TEXT_SUBTITLE)
                ], spacing=2)
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor=CARD_COLOR,
            padding=20,
            border_radius=16,
            expand=True,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))
        )

    # --- VIEWS ---
    
    def get_home_view():
        # Helpers for pixel-perfect design
        def create_gradient_stat_card_dyn(icon, text_widget, label, gradient_colors):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=28, color=ft.Colors.WHITE),
                        padding=10,
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        border_radius=10
                    ),
                    ft.Column([
                        text_widget,
                        ft.Text(label, size=11, color=ft.Colors.WHITE70)
                    ], spacing=1)
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1.0, -1.0),
                    end=ft.Alignment(1.0, 1.0),
                    colors=gradient_colors,
                ),
                padding=15,
                border_radius=16,
                expand=True,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.3, gradient_colors[0]))
            )

        def create_quick_action(icon, label, on_click_action):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=ft.Colors.WHITE, size=20),
                        padding=8,
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                        border_radius=8
                    ),
                    ft.Text(label, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.WHITE54, size=16)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15,
                bgcolor="#1E1E24",
                border_radius=12,
                border=ft.border.all(1, "#2F2F3B"),
                on_click=on_click_action,
                expand=True
            )

        # Stats Interface
        # Stats Interface
        total_vid_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        last_gen_text = ft.Text("N/A", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        uploaded_videos = 0

        # Recent Generations List
        recent_list = ft.Column(spacing=10)
        recent_list.controls.append(ft.Text(state.loc.get("msg_loading_hist"), color=ft.Colors.GREY_500, italic=True))

        def load_home_data():
            out_dir = os.path.join(os.getcwd(), "output")
            raw_history = get_video_history(out_dir)
            
            # Filter valid videos to match generator stats
            history_items = [i for i in raw_history if i.get("status") != "cancelled"] if raw_history else []
            
            total_videos = len(history_items)
            last_generated = history_items[0]["date"] if history_items else "N/A"

            total_vid_text.value = str(total_videos)
            last_gen_text.value = last_generated

            recent_list.controls.clear()
            recent_items_count = 0
            if history_items:
                for i, item in enumerate(history_items[:3]): # Top 3 recent
                     recent_items_count += 1
                     
                     mood_str = str(item.get("mood", "curiosity")).lower()
                     title_str = str(item.get("title", "")).lower()
                     
                     if "what" in mood_str or "pasaría" in mood_str or "what" in title_str or "pasaría" in title_str: thumb_file = "what_if.png"
                     elif "top" in mood_str or "ranking" in mood_str or "top" in title_str or "ranking" in title_str: thumb_file = "top3.png"
                     else: thumb_file = "curiosity.png"
                          
                     thumb_path = f"assets/{thumb_file}"
                     
                     recent_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Row([
                                    ft.Container(
                                        content=ft.Image(src=thumb_path, width=60, height=40, fit="cover", border_radius=6),
                                        width=60, height=40, bgcolor="#2A2A35", border_radius=6, alignment=ft.Alignment(0,0)
                                    ),
                                    ft.Column([
                                        ft.Text(item["title"][:40] + ("..." if len(item["title"]) > 40 else ""), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14),
                                        ft.Row([
                                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=12, color=ft.Colors.GREY_500),
                                            ft.Text(state.loc.get("lbl_ideas"), size=10, color=ft.Colors.GREY_500),
                                            ft.Text("•", size=10, color=ft.Colors.GREY_500),
                                            ft.Text(item["date"], size=10, color=ft.Colors.GREY_500)
                                        ], spacing=5)
                                    ], spacing=2)
                                ]),
                                ft.Row([
                                     ft.IconButton(ft.Icons.FOLDER_OPEN, icon_color=ft.Colors.GREY_400, tooltip="Open Folder", on_click=lambda e, p=item["path"]: open_folder(p)),
                                     ft.Text(item["date"], size=12, color=ft.Colors.GREY_400),
                                     ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=ft.Colors.GREY_600)
                                ])
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=10,
                            bgcolor="transparent",
                            border=ft.border.only(bottom=ft.border.BorderSide(1, "#2F2F3B")) if i < 2 else None
                        )
                     )
            
            if recent_items_count == 0:
                recent_list.controls.append(ft.Text(state.loc.get("msg_no_recent_gen"), color=ft.Colors.GREY_500, italic=True))
            
            # Since update is called outside of page context sometimes, use page.update safely
            if page: page.update()

        load_home_data()

        uploaded_videos = 0 # Future: Count successful uploads from history

        return ft.Column([
            # Header Section
            ft.Row([
                ft.Column([
                    ft.Text(state.loc.get("home_title"), size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(state.loc.get("home_subtitle1"), size=16, weight=ft.FontWeight.NORMAL, color=ft.Colors.WHITE70),
                    ft.Text(state.loc.get("home_subtitle2"), size=12, color=ft.Colors.GREY_500),
                ], spacing=5),
                ft.Container(
                    content=ft.Row([ft.Icon(ft.Icons.ROCKET_LAUNCH, size=14, color="#FFB6C1"), ft.Text(state.loc.get("tag_ai_powered"), color="#FFB6C1", size=11, weight=ft.FontWeight.BOLD)], spacing=5),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border=ft.border.all(1, "#FFB6C1"),
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.1, "#FFB6C1")
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
            
            ft.Container(height=20),
            
            # Stats Row
            ft.Row([
                create_gradient_stat_card_dyn(ft.Icons.VIDEO_LIBRARY, total_vid_text, state.loc.get("stat_total_videos"), ["#4343CA", "#6D39D1"]), # Deep Blue/Purple
                create_gradient_stat_card_dyn(ft.Icons.PLAY_ARROW, ft.Text(str(uploaded_videos), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), state.loc.get("stat_uploaded_videos"), ["#D91E5B", "#9A1F9C"]), # Red/Pink
                create_gradient_stat_card_dyn(ft.Icons.ACCESS_TIME, last_gen_text, state.loc.get("stat_last_gen"), ["#7F00FF", "#E100FF"]), # Purple/Pink
                create_gradient_stat_card_dyn(ft.Icons.TRENDING_UP, ft.Text("Pro", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), state.loc.get("stat_pro"), ["#8E2DE2", "#4A00E0"]), # Purple/Blue
            ], spacing=15),
            
            ft.Container(height=30),
            
            # Main Action Button
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE),
                    ft.Text(state.loc.get("btn_create_new"), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ], alignment=ft.MainAxisAlignment.CENTER),
                gradient=ft.LinearGradient(colors=["#2b5876", "#4e4376"]), # Deep Ocean to Purple
                height=60,
                border_radius=30,
                alignment=ft.Alignment(0, 0),
                on_click=lambda e: change_view(1), # Go to Generator
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.4, "#4e4376"))
            ),
            
            ft.Container(height=30),
            
            # Quick Actions Section
            ft.Row([ft.Text(state.loc.get("lbl_quick_actions"), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Text(state.loc.get("lbl_view_all"), color=ft.Colors.GREY_500, size=12)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=10),
            ft.Row([
                create_quick_action(ft.Icons.VIDEO_LIBRARY, state.loc.get("qa_generate"), lambda e: change_view(1)), 
                create_quick_action(ft.Icons.CLOUD_UPLOAD, state.loc.get("qa_upload"), lambda e: change_view(2)), 
                create_quick_action(ft.Icons.HISTORY, state.loc.get("qa_history"), lambda e: change_view(3))
            ], spacing=15),

            ft.Container(height=30),

            # Recent Generations Section
            ft.Text(state.loc.get("lbl_recent_gen"), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Container(height=10),
            ft.Container(
                content=recent_list,
                padding=15,
                bgcolor="#191921",
                border_radius=16,
                border=ft.border.all(1, "#2F2F3B")
            )
        ], scroll=ft.ScrollMode.HIDDEN)

    def get_generator_view():
        # Stats Row (3 Cards) - Async Load
        total_vid_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        last_gen_text = ft.Text("N/A", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        upload_vid_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

        def load_generator_data():
            out_dir = os.path.join(os.getcwd(), "output")
            raw_history = get_video_history(out_dir)
            
            # Filter valid videos
            history_items = [i for i in raw_history if i.get("status") != "cancelled"] if raw_history else []
            
            total_videos = len(history_items)
            last_generated = history_items[0]["date"] if history_items else "N/A"
            uploaded_videos = len([i for i in history_items if i.get("status") == "uploaded"])

            total_vid_text.value = str(total_videos)
            last_gen_text.value = last_generated
            upload_vid_text.value = str(uploaded_videos)
            if page: page.update()

        load_generator_data()

        # Helpers
        def create_stat_dyn(icon, text_widget, label, color_start, color_end):
             return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=24, color=ft.Colors.WHITE),
                        padding=12,
                        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        border_radius=10
                    ),
                    ft.Column([
                        text_widget,
                        ft.Text(label, size=11, color=ft.Colors.WHITE70)
                    ], spacing=1)
                ]),
                gradient=ft.LinearGradient(colors=[color_start, color_end]),
                padding=20,
                border_radius=14,
                expand=True
             )
        def log_message(msg):
            print(msg)

        cancel_flag = [False]
        
        def is_cancelled_check():
            return cancel_flag[0]

        # Logic
        def on_generate_click(e):
            gen_btn.content.value = "Generating..."
            gen_btn.disabled = True
            test_btn.disabled = True # Disable test button during generation
            cancel_btn.visible = True
            cancel_btn.disabled = False
            cancel_flag[0] = False # Reset cancel flag
            page.update()
            
            count = int(count_input.value) if count_input.value.isdigit() else 1
            topic = topic_input.value if topic_input.value else None
            style_val = mode_dropdown.value.lower() if mode_dropdown.value else "curiosity"
            if "what" in style_val or "pasaría" in style_val: style = "what_if"
            elif "top" in style_val: style = "top_3"
            else: style = "curiosity"
            
            watermark = watermark_input.value
            progress_text.visible = True
            progress_text.value = f"Status: Starting generation for {count} video(s) in {style} mode..."
            page.update()
            
            def progress_callback(pct, title="", status=""):
                if title: progress_title.value = f"📹 {title}"
                if status: progress_text.value = status
                progress_bar.value = pct
                page.update()

            def run(is_test=False):
                log_message(f"--- Starting {'TEST ' if is_test else ''}Batch: {count} videos | {style} ---")
                progress_text.value = f"Status: Processing {count} video(s). Please check logs for details."
                progress_bar.visible = True
                progress_title.visible = True
                progress_bar.value = 0
                progress_title.value = "⏳ Initializing..."
                page.update()
                
                try:
                    # Actually we need to set API keys as env vars BEFORE run_batch
                    os.environ["GOOGLE_API_KEY"] = state.config.get_api_key("google_gemini")
                    if state.config.get_api_key("pexels"):
                        os.environ["PEXELS_API_KEY"] = state.config.get_api_key("pexels")
                    
                    use_trends = (style == 'curiosity')
                    current_lang = state.config.get_preference("language", "en")
                    run_batch(count, topic=topic, use_trends=use_trends, style=style, log_func=log_message, watermark_text=watermark, lang=current_lang, is_test=is_test, progress_callback=progress_callback, is_cancelled=is_cancelled_check, loc=state.loc)
                    
                    if cancel_flag[0]:
                        log_message("Generation Cancelled!")
                        progress_text.value = "Status: Cancelled by user."
                    else:
                        log_message("Done!")
                        progress_text.value = "Status: Completed successfully!"
                        progress_bar.value = 1.0
                    page.update()
                except Exception as ex:
                    log_message(f"Error: {ex}")
                    progress_text.value = f"Status: Error occurred ({ex})"
                    page.update()
                finally:
                    gen_btn.disabled = False
                    gen_btn.content.value = state.loc.get("btn_generate")
                    test_btn.disabled = False
                    test_btn.content.value = state.loc.get("gen_test_btn")
                    cancel_btn.visible = False
                    page.update()

            threading.Thread(target=run, kwargs={"is_test": False}, daemon=True).start()

        def on_test_click(e):
            test_btn.content.value = "Testing..."
            cancel_flag[0] = False # Reset cancel flag
            cancel_btn.visible = True
            cancel_btn.disabled = False
            test_btn.disabled = True
            gen_btn.disabled = True
            page.update()
            
            count = 1 # Force 1 video for tests
            topic = topic_input.value if topic_input.value else None
            style_val = mode_dropdown.value.lower() if mode_dropdown.value else "curiosity"
            if "what" in style_val or "pasaría" in style_val: style = "what_if"
            elif "top" in style_val: style = "top_3"
            else: style = "curiosity"
            
            watermark = watermark_input.value
            progress_text.visible = True
            progress_text.value = f"Status: Starting TEST generation in {style} mode..."
            page.update()
            
            def test_progress_callback(pct, title="", status=""):
                if title: progress_title.value = f"⚡ {title}"
                if status: progress_text.value = status
                progress_bar.value = pct
                page.update()

            # Reuse the run function but with is_test=True
            def test_run():
                log_message(f"--- Starting TEST Batch: 1 video | {style} ---")
                progress_text.value = f"Status: Processing 1 TEST video. Please check logs for details."
                # Show UI
                progress_bar.visible = True
                progress_title.visible = True
                progress_bar.value = 0
                progress_title.value = "⏳ Testing..."
                page.update()
                
                try:
                    os.environ["GOOGLE_API_KEY"] = state.config.get_api_key("google_gemini")
                    if state.config.get_api_key("pexels"):
                        os.environ["PEXELS_API_KEY"] = state.config.get_api_key("pexels")
                    
                    use_trends = (style == 'curiosity')
                    current_lang = state.config.get_preference("language", "en")
                    run_batch(1, topic=topic, use_trends=use_trends, style=style, log_func=log_message, watermark_text=watermark, lang=current_lang, is_test=True, progress_callback=test_progress_callback, is_cancelled=is_cancelled_check, loc=state.loc)
                    
                    if cancel_flag[0]:
                        progress_text.value = "Status: Test Cancelled."
                    else:
                        log_message("Test Done!")
                        progress_text.value = "Status: Test Completed successfully!"
                        progress_bar.value = 1.0
                    open_output_btn.visible = True
                    page.update()
                except Exception as ex:
                    log_message(f"Error: {ex}")
                    progress_text.value = f"Status: Error occurred ({ex})"
                    page.update()
                finally:
                    gen_btn.disabled = False
                    gen_btn.content.value = state.loc.get("btn_generate")
                    test_btn.disabled = False
                    test_btn.content.value = state.loc.get("gen_test_btn")
                    cancel_btn.visible = False
                    page.update()
            
            threading.Thread(target=test_run, daemon=True).start()

        # Inputs
        count_input = ft.TextField(label=state.loc.get("lbl_count"), value="1", width=120, border_color="#5C5C5C", text_size=16, content_padding=15, border_radius=10)
        topic_input = ft.TextField(label=state.loc.get("lbl_topic"), hint_text=state.loc.get("ph_topic"), expand=True, border_color="#5C5C5C", text_size=16, content_padding=15, border_radius=10)
        
        modes = ["Curiosity", "What If?", "Top 3"]
        mode_dropdown = ft.Dropdown(
            label=state.loc.get("lbl_style"),
            options=[ft.dropdown.Option(m) for m in modes],
            value="Curiosity",
            expand=True,
            border_color="#5C5C5C",
            text_size=16,
            border_radius=10,
            content_padding=15
        )
        watermark_input = ft.TextField(label=state.loc.get("lbl_watermark"), value="@AIShortsGenerator", expand=True, border_color="#5C5C5C", text_size=16, content_padding=15, border_radius=10)
        gen_btn = ft.Container(
            content=ft.Text(state.loc.get("btn_generate"), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            alignment=ft.Alignment(0, 0),
            gradient=ft.LinearGradient(colors=["#5C258D", "#4389A2"]), # Purposeful Purple to Blue
            height=60,
            border_radius=12,
            on_click=on_generate_click,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.4, "#5C258D"))
        )
        
        test_btn = ft.Container(
            content=ft.Text(state.loc.get("gen_test_btn"), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            alignment=ft.Alignment(0, 0),
            gradient=ft.LinearGradient(colors=["#FF8008", "#FFC837"]), # Fast Orange
            height=60,
            border_radius=12,
            on_click=on_test_click,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.4, "#FF8008")),
            expand=1
        )
        
        gen_btn.expand = 2
        buttons_row = ft.Row([gen_btn, test_btn], spacing=15)

        def on_cancel_click(e):
             cancel_flag[0] = True
             progress_text.value = "Status: Cancelling... Please wait for current step to abort..."
             cancel_btn.disabled = True
             page.update()

        cancel_btn = ft.Container(
             content=ft.Row([ft.Icon(ft.Icons.STOP_CIRCLE_OUTLINED, color=ft.Colors.WHITE, size=18), ft.Text(state.loc.get("gen_cancel_btn"), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)], spacing=5),
             bgcolor=ft.Colors.RED_700,
             padding=ft.padding.symmetric(horizontal=15, vertical=5),
             border_radius=8,
             visible=False,
             on_click=on_cancel_click,
             ink=True
        )
        
        open_output_btn = ft.Container(
             content=ft.Row([ft.Icon(ft.Icons.FOLDER_OPEN, color=ft.Colors.WHITE, size=18), ft.Text("Open Output", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)], spacing=5),
             bgcolor=ft.Colors.BLUE_700,
             padding=ft.padding.symmetric(horizontal=15, vertical=5),
             border_radius=8,
             visible=False,
             on_click=lambda e: open_folder(os.path.join(os.getcwd(), "output", "test.mp4")), # Passes default output folder dir
             ink=True
        )

        # Progress UI
        progress_title = ft.Text(value="", visible=False, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=18)
        progress_text = ft.Text(value="", visible=False, color=ft.Colors.GREEN_400, italic=True)
        progress_bar = ft.ProgressBar(value=0, visible=False, color="#F857A6", bgcolor="#2F2F3B", height=10, border_radius=5, expand=True)
        
        progress_container = ft.Column([
            ft.Row([progress_title, ft.Row([open_output_btn, cancel_btn], spacing=10)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([progress_bar]),
            progress_text
        ], spacing=5)

        generator_col = ft.Column([
            ft.Row([
                ft.Text(state.loc.get("title_generator"), size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(
                    content=ft.Row([ft.Icon(ft.Icons.ROCKET, size=14, color="#F857A6"), ft.Text(state.loc.get("tag_ai_powered"), color="#F857A6", size=11, weight=ft.FontWeight.BOLD)], spacing=5),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border=ft.border.all(1, "#F857A6"),
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.1, "#F857A6")
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(height=20),
            
            ft.Row([
                create_stat_dyn(ft.Icons.VIDEO_LIBRARY, total_vid_text, "Total Videos Generated", "#3A1C71", "#D76D77"),
                create_stat_dyn(ft.Icons.PLAY_ARROW, upload_vid_text, "Videos Uploaded to YouTube", "#4E54C8", "#8F94FB"),
                create_stat_dyn(ft.Icons.ACCESS_TIME, last_gen_text, "Last Generation", "#11998e", "#38ef7d"),
            ], spacing=20),
            
            ft.Container(height=30),
            
            ft.Container(
                content=ft.Column([
                    ft.Text(state.loc.get("sidebar_settings"), size=16, weight=ft.FontWeight.BOLD, color="#8F94FB"),
                    ft.Container(height=10),
                    ft.Row([count_input, topic_input], spacing=20),
                    ft.Container(height=10),
                    ft.Row([mode_dropdown]),
                    ft.Container(height=10),
                    ft.Row([watermark_input]),
                    ft.Container(height=25),
                    buttons_row,
                    ft.Container(height=15),
                    progress_container
                ]),
                bgcolor="#191921",
                padding=35,
                border_radius=20,
                border=ft.border.all(1, "#2F2F3B"),
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK))
            )
        ], scroll=ft.ScrollMode.HIDDEN)
        
        generator_col.update_stats = load_generator_data
        return generator_col



    def get_history_view():
        # Helpers
        def create_badge(text, color):
            return ft.Container(
                content=ft.Row([ft.Container(width=8, height=8, border_radius=4, bgcolor=color), ft.Text(text, color=ft.Colors.WHITE, size=12)], spacing=5),
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.1, color)
            )

        history_col = ft.Column(spacing=10)
        
        def create_badge(text, color):
            return ft.Container(
                content=ft.Row([ft.Container(width=8, height=8, border_radius=4, bgcolor=color), ft.Text(text, color=ft.Colors.WHITE, size=12)], spacing=5),
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.1, color)
            )

        def sync_load_history():
            try:
                out_dir = os.path.join(os.getcwd(), "output")
                items = get_video_history(out_dir)
                
                if not items:
                    history_col.controls.append(ft.Text(state.loc.get("msg_no_history"), color=ft.Colors.GREY_500, italic=True))
                else:
                    for i, item in enumerate(items[:50]):
                        is_uploaded = item.get("status") == "uploaded"
                        
                        mood_str = str(item.get("mood", "curiosity")).lower()
                        title_str = str(item.get("title", "")).lower()
                        
                        if "what" in mood_str or "pasaría" in mood_str or "what" in title_str or "pasaría" in title_str: thumb_file = "what_if.png"
                        elif "top" in mood_str or "ranking" in mood_str or "top" in title_str or "ranking" in title_str: thumb_file = "top3.png"
                        else: thumb_file = "curiosity.png"
                             
                        thumb_path = f"assets/{thumb_file}"
                        is_cancelled = item.get("status") == "cancelled"
                    
                        history_col.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    # Video Info (Width 300 to match header)
                                    ft.Container(
                                        content=ft.Row([
                                            ft.Container(
                                                content=ft.Image(src=thumb_path, width=80, height=50, fit="cover", border_radius=8),
                                                width=80, height=50, bgcolor="#2A2A35", border_radius=8, alignment=ft.Alignment(0,0)
                                            ),
                                            ft.Column([
                                                ft.Text(item["title"][:40] + ("..." if len(item["title"]) > 40 else ""), size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, width=200),
                                            ], spacing=3)
                                        ]),
                                        width=300
                                    ),
                                    
                                    # Statuses (Width 100)
                                    ft.Container(
                                        content=ft.Column([
                                            create_badge(state.loc.get("badge_cancelled"), ft.Colors.RED_400) if is_cancelled else create_badge(state.loc.get("badge_generated"), ft.Colors.YELLOW_400),
                                            create_badge(state.loc.get("badge_uploaded"), ft.Colors.GREEN_400) if is_uploaded and not is_cancelled else ft.Container()
                                        ], spacing=5),
                                        width=100
                                    ),
                                    
                                    # Times (Width 100)
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text(item["date"], size=12, color=ft.Colors.WHITE70)
                                        ], spacing=5),
                                        width=100
                                    ),
                                    
                                    # Actions (Width 120)
                                    ft.Container(
                                        content=ft.Row(
                                            [
                                                ft.IconButton(ft.Icons.FOLDER_OPEN, icon_color=ft.Colors.BLUE_200, tooltip="Open Folder", on_click=lambda e, p=item["path"]: open_folder(p)),
                                                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.PURPLE_200, tooltip="Delete")
                                            ] if not is_cancelled else [],
                                            alignment=ft.MainAxisAlignment.END
                                        ),
                                        width=120
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                padding=15,
                                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                border_radius=12,
                                border=ft.border.all(1, "#2F2F3B")
                            )
                        )
            except Exception as e:
                import traceback
                traceback.print_exc()
                history_col.controls.append(ft.Text(f"Error loading history UI: {e}", color=ft.Colors.RED))

        sync_load_history()

        filter_tabs = ft.Row([
            ft.Container(content=ft.Text(state.loc.get("hist_filter_all"), color=ft.Colors.WHITE), bgcolor="#4E75FF", padding=ft.padding.symmetric(horizontal=20, vertical=8), border_radius=8),
            ft.Container(content=ft.Text(state.loc.get("hist_filter_gen"), color=ft.Colors.GREY_400), padding=ft.padding.symmetric(horizontal=20, vertical=8)),
            ft.Container(content=ft.Text(state.loc.get("hist_filter_up"), color=ft.Colors.GREY_400), padding=ft.padding.symmetric(horizontal=20, vertical=8)),
            ft.Container(content=ft.Text(state.loc.get("hist_filter_del"), color=ft.Colors.GREY_400), padding=ft.padding.symmetric(horizontal=20, vertical=8)),
        ], spacing=10)

        headers = ft.Container(
            content=ft.Row([
                 ft.Text(state.loc.get("hist_col_video"), color=ft.Colors.GREY_400, width=300),
                 ft.Text(state.loc.get("hist_col_status"), color=ft.Colors.GREY_400, width=100),
                 ft.Text(state.loc.get("hist_col_time"), color=ft.Colors.GREY_400, width=100),
                 ft.Text("", color=ft.Colors.GREY_400),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20)
        )

        return ft.Column([
            ft.Row([
                ft.Text(state.loc.get("title_history"), size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(
                    content=ft.Row([ft.Icon(ft.Icons.ROCKET, size=14, color="#F857A6"), ft.Text(state.loc.get("tag_ai_powered"), color="#F857A6", size=11, weight=ft.FontWeight.BOLD)], spacing=5),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border=ft.border.all(1, "#F857A6"),
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.1, "#F857A6")
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Text(state.loc.get("msg_history_desc"), size=16, color=ft.Colors.GREY_500),
            ft.Container(height=20),
            
            filter_tabs,
            ft.Container(height=20),
            
            ft.Container(
                content=ft.Column([
                    headers,
                    ft.Divider(color="#2F2F3B"),
                    history_col
                ]),
                bgcolor="#191921",
                padding=20,
                border_radius=20,
                border=ft.border.all(1, "#2F2F3B"),
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK))
            )
        ], scroll=ft.ScrollMode.HIDDEN)

    def get_upload_view():
        video_list_ui = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        checkboxes = []
        
        def sync_upload_data():
            try:
                out_dir = os.path.join(os.getcwd(), "output")
                history_items = get_video_history(out_dir)
                
                if not history_items:
                    video_list_ui.controls.append(ft.Text(state.loc.get("msg_no_files"), color=ft.Colors.GREY_500))
                else:
                    for item in history_items[:50]:
                        mood_str = str(item.get("mood", "curiosity")).lower()
                        title_str = str(item.get("title", "")).lower()
                        
                        if "what" in mood_str or "pasaría" in mood_str or "what" in title_str or "pasaría" in title_str: thumb_file = "what_if.png"
                        elif "top" in mood_str or "ranking" in mood_str or "top" in title_str or "ranking" in title_str: thumb_file = "top3.png"
                        else: thumb_file = "curiosity.png"
                        thumb_path = f"assets/{thumb_file}"
                        
                        is_cancelled = item.get("status") == "cancelled"
                        
                        # Only show successfully generated videos in the upload list
                        if is_cancelled: continue
                        
                        meta_dict = {"title": item["title"], "description": "", "tags": []}
                        json_path = os.path.join(os.path.dirname(item["path"]), "metadata.json")
                        txt_path = os.path.join(os.path.dirname(item["path"]), "metadata.txt")
                        
                        import json
                        if os.path.exists(json_path):
                             try:
                                 with open(json_path, 'r', encoding='utf-8') as f:
                                     jdata = json.load(f)
                                     meta_dict["description"] = jdata.get("seo_description", "")
                                     meta_dict["tags"] = jdata.get("tags", [])
                             except: pass
                        elif os.path.exists(txt_path):
                             try:
                                 from src.upload_utils import parse_metadata
                                 txt_meta = parse_metadata(txt_path)
                                 if txt_meta: meta_dict.update(txt_meta)
                             except: pass
                        
                        payload = {"path": item["path"], "meta": meta_dict}
                        cb = ft.Checkbox(
                            value=False, 
                            data=payload, 
                            fill_color={"selected": ft.Colors.GREEN_500, "": ft.Colors.TRANSPARENT},
                            check_color=ft.Colors.WHITE
                        )
                        checkboxes.append(cb)
                        
                        def make_delete_click(v_path):
                            def on_click(e):
                                def confirm(e_dlg):
                                    import shutil
                                    try:
                                        shutil.rmtree(os.path.dirname(v_path))
                                        dlg.open = False
                                        page.update()
                                        show_snack(state.loc.get("msg_video_deleted"), ft.Colors.GREEN)
                                        change_view(2) 
                                    except Exception as ex:
                                        show_snack(f"{state.loc.get('msg_error_deleting')}: {ex}", ft.Colors.RED)
                                        dlg.open = False
                                        page.update()
                                        
                                def cancel(e_dlg):
                                    dlg.open = False
                                    page.update()
                                    
                                dlg = ft.AlertDialog(
                                    title=ft.Text(state.loc.get("title_confirm_deletion")),
                                    content=ft.Text(state.loc.get("msg_confirm_delete_video")),
                                    actions=[
                                        ft.TextButton(state.loc.get("btn_delete"), on_click=confirm, style=ft.ButtonStyle(color=ft.Colors.RED)),
                                        ft.TextButton(state.loc.get("btn_cancel"), on_click=cancel)
                                    ]
                                )
                                page.dialog = dlg
                                dlg.open = True
                                page.update()
                            return on_click
                        
                        def toggle_row(e, checkbox=cb):
                            # Don't toggle if they clicked the action buttons
                            if isinstance(e.control, ft.IconButton): return
                            checkbox.value = not checkbox.value
                            page.update()
                        
                        row = ft.Container(
                            content=ft.Row([
                                ft.Row([
                                    cb,
                                    ft.Image(src=thumb_path, width=80, height=50, fit="cover", border_radius=8),
                                    ft.Column([
                                        ft.Text(item["title"][:50] + ("..." if len(item["title"]) > 50 else ""), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                                        ft.Text(item["date"], color=ft.Colors.GREY_500, size=12)
                                    ], spacing=2)
                                ]),
                                ft.Row([
                                    ft.IconButton(ft.Icons.FOLDER_OPEN, icon_color=ft.Colors.BLUE_200, tooltip=state.loc.get("tooltip_open_folder"), on_click=lambda e, p=item["path"]: open_folder(p)),
                                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, tooltip=state.loc.get("tooltip_delete_video"), on_click=make_delete_click(item["path"]))
                                ], spacing=5)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=10,
                            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                            border_radius=8,
                            on_click=toggle_row,
                            ink=True
                        )
                        video_list_ui.controls.append(row)
            except Exception as e:
                import traceback
                traceback.print_exc()
                video_list_ui.controls.append(ft.Text(f"Error loading upload UI: {e}", color=ft.Colors.RED))
                
        sync_upload_data()

        def on_login(e):
            open_dialog = ft.AlertDialog(title=ft.Text(state.loc.get("lbl_info")), content=ft.Text(state.loc.get("msg_login_open")))
            page.dialog = open_dialog
            open_dialog.open = True
            page.update()
            state.uploader.open_login_window()
            
        def on_select_all(e):
            all_checked = all(cb.value for cb in checkboxes)
            for cb in checkboxes:
                cb.value = not all_checked
            page.update()

        main_upload_ui = ft.Container(visible=True, expand=True)

        def open_upload_dialog(e):
            from datetime import datetime, date
            with open("debug.log", "a") as f:
                f.write(f"Button clicked at {datetime.now()}\n")
            try:
                selected = [cb.data for cb in checkboxes if cb.value]
                if not selected:
                    with open("debug.log", "a") as f: f.write("No video selected. Aborting.\n")
                    show_snack(state.loc.get("msg_select_video"), ft.Colors.RED)
                    return
                
                now = datetime.now()
                
                # --- GLOBAL SCHEDULE SETTINGS (hidden by default) ---
                g_date_tf = ft.TextField(value=f"{now.day:02d}/{now.month:02d}/{now.year} {(now.hour+1)%24:02d}:00", width=140, text_size=12, text_align=ft.TextAlign.CENTER, dense=True, label=state.loc.get("lbl_start_date"))
                g_interval_dd = ft.Dropdown(options=[
                    ft.dropdown.Option("0", state.loc.get("opt_same_time")),
                    ft.dropdown.Option("1", state.loc.get("opt_1_hour")),
                    ft.dropdown.Option("2", state.loc.get("opt_2_hours")),
                    ft.dropdown.Option("3", state.loc.get("opt_3_hours")),
                    ft.dropdown.Option("4", state.loc.get("opt_4_hours")),
                    ft.dropdown.Option("6", state.loc.get("opt_6_hours")),
                    ft.dropdown.Option("12", state.loc.get("opt_12_hours")),
                    ft.dropdown.Option("24", state.loc.get("opt_24_hours"))
                ], value="2", width=140, text_size=12, dense=True)

                g_settings_row = ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.BLUE_400, size=20),
                    ft.Text(state.loc.get("lbl_from"), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    g_date_tf,
                    ft.Container(width=10),
                    ft.Icon(ft.Icons.TIMER, color=ft.Colors.AMBER_400, size=20),
                    ft.Text(state.loc.get("lbl_interval"), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    g_interval_dd
                ], visible=False, spacing=5, alignment=ft.MainAxisAlignment.CENTER,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER)

                list_view = ft.Column([], scroll=ft.ScrollMode.AUTO, spacing=10)
                list_container = ft.Container(content=list_view, height=350)
                video_state_map = [] 

                # --- PER-VIDEO CONFIG ---
                for idx, s in enumerate(selected):
                    title = s.get("meta", {}).get("title", f"Video {idx+1}")
                    if len(title) > 60: title = title[:57] + "..."
                    
                    v_date_tf = ft.TextField(
                        value=f"{now.day:02d}/{now.month:02d}/{now.year} {(now.hour+1)%24:02d}:00", 
                        width=140, text_size=11, 
                        text_align=ft.TextAlign.CENTER, 
                        dense=True, content_padding=5
                    )
                    
                    # Calendar row - starts hidden
                    calendar_row = ft.Row([
                        ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=ft.Colors.BLUE_200),
                        v_date_tf
                    ], visible=False, spacing=5)

                    v_dd = ft.Dropdown(
                        options=[
                            ft.dropdown.Option("now", state.loc.get("opt_upload_now")),
                            ft.dropdown.Option("schedule", state.loc.get("opt_schedule"))
                        ],
                        value="now",
                        width=140, text_size=12,
                        content_padding=5,
                        dense=True
                    )

                    # Calendar toggle button
                    def make_cal_toggle(dd, cal):
                        def toggle(e):
                            if dd.value == "now":
                                dd.value = "schedule"
                                cal.visible = True
                            else:
                                dd.value = "now"
                                cal.visible = False
                            dlg.update()
                        return toggle

                    cal_btn = ft.IconButton(
                        icon=ft.Icons.CALENDAR_MONTH,
                        icon_color=ft.Colors.BLUE_400,
                        icon_size=20,
                        tooltip=state.loc.get("tooltip_schedule_date"),
                        on_click=make_cal_toggle(v_dd, calendar_row),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        )
                    )
                    
                    video_state_map.append({
                        "item": s, "dd": v_dd, "date_tf": v_date_tf
                    })
                    
                    list_view.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"{idx+1}. {title}", size=13, expand=True, no_wrap=True, color=ft.Colors.WHITE),
                                    cal_btn,
                                ], spacing=8, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
                                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                calendar_row
                            ], spacing=5, tight=True),
                            padding=12,
                            bgcolor="#1A1A1A",
                            border_radius=8,
                            border=ft.border.all(1, "#333333")
                        )
                    )

                def close_panel(e_btn=None):
                    dlg.open = False
                    page.update()

                # --- "Programar con Intervalos" button ---
                def on_schedule_intervals(e_btn):
                    g_settings_row.visible = not g_settings_row.visible
                    dlg.update()

                def on_apply_intervals(e_btn):
                    try:
                        parts = g_date_tf.value.split(" ")
                        d_parts = parts[0].split("/")
                        t_parts = parts[1].split(":")
                        sd = date(int(d_parts[2]), int(d_parts[1]), int(d_parts[0]))
                        sh = int(t_parts[0])
                        ih = int(g_interval_dd.value)
                    except Exception:
                        show_snack(state.loc.get("msg_invalid_date_format"), ft.Colors.RED)
                        return
                    close_panel()
                    progress_row.visible = True
                    page.update()
                    log_message(f"Starting scheduled upload for {len(selected)} videos.")
                    threading.Thread(target=lambda: state.uploader.start_process(selected, mode="schedule", start_date=sd, start_hour=sh, interval_hours=ih, progress_callback=on_progress), daemon=True).start()

                # --- "Confirmar" button (per-video custom action) ---
                def do_apply(e_btn):
                    close_panel()
                    progress_row.visible = True
                    page.update()

                    # Build a unified list with per-video schedule info
                    upload_items = []
                    for st in video_state_map:
                        item = st["item"].copy()
                        if st["dd"].value == "schedule":
                            try:
                                parts = st["date_tf"].value.split(" ")
                                d_parts = parts[0].split("/")
                                t_parts = parts[1].split(":")
                                item["_schedule_date"] = date(int(d_parts[2]), int(d_parts[1]), int(d_parts[0]))
                                item["_schedule_hour"] = int(t_parts[0])
                                item["_mode"] = "schedule"
                            except Exception:
                                show_snack(state.loc.get("msg_invalid_date_for_video").format(video_title=st['item'].get('meta', {}).get('title', 'Video')), ft.Colors.RED)
                                continue
                        else:
                            item["_mode"] = "now"
                        upload_items.append(item)
                    
                    if upload_items:
                        cancel_btn.visible = True
                        threading.Thread(
                            target=lambda items=upload_items: state.uploader.start_process_mixed(items, progress_callback=on_progress),
                            daemon=True
                        ).start()

                # --- Info text ---
                info_text = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ft.Colors.AMBER_400),
                        ft.Text(state.loc.get("msg_unprogrammed_upload_now"), size=12, color=ft.Colors.AMBER_400, italic=True)
                    ], spacing=5),
                    padding=ft.padding.only(top=5, bottom=5)
                )

                dlg = ft.AlertDialog(
                    title=ft.Text(state.loc.get("title_upload_config"), size=24, weight=ft.FontWeight.BOLD),
                    content=ft.Container(
                        width=850,
                        height=500,
                        content=ft.Column([
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.ElevatedButton(
                                            state.loc.get("btn_schedule_intervals"),
                                            icon=ft.Icons.SCHEDULE,
                                            on_click=on_schedule_intervals,
                                            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                                            height=40
                                        ),
                                    ], alignment=ft.MainAxisAlignment.START, spacing=10),
                                    g_settings_row,
                                    ft.Row([
                                        ft.ElevatedButton(
                                            state.loc.get("btn_apply_intervals"),
                                            icon=ft.Icons.CHECK,
                                            on_click=on_apply_intervals,
                                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
                                            height=35,
                                            visible=True
                                        ),
                                    ], alignment=ft.MainAxisAlignment.START) if False else ft.Container(),
                                    info_text,
                                    ft.Divider(),
                                    list_container
                                ], spacing=10),
                                bgcolor="#191921",
                                padding=20,
                                border_radius=12,
                                border=ft.border.all(1, "#2F2F3B")
                            )
                        ], scroll=ft.ScrollMode.AUTO)
                    ),
                    actions=[
                        ft.ElevatedButton(state.loc.get("btn_confirm"), on_click=do_apply, icon=ft.Icons.CHECK_CIRCLE, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE), height=45),
                        ft.ElevatedButton(state.loc.get("btn_cancel"), on_click=close_panel, style=ft.ButtonStyle(color=ft.Colors.WHITE), height=45)
                    ],
                    actions_alignment=ft.MainAxisAlignment.END
                )

                try:
                    page.open(dlg)
                except AttributeError:
                    page.overlay.append(dlg)
                    dlg.open = True
                    page.update()
                    
                with open("debug.log", "a") as f: f.write("Dialog opened successfully.\n")
                    
            except Exception as fatal_err:
                import traceback
                with open("crash.log", "w") as f:
                    f.write(traceback.format_exc())
                show_snack(f"{state.loc.get('msg_error_opening_panel')}: {str(fatal_err)[:100]}", ft.Colors.RED)

        # --- Progress UI ---
        progress_text = ft.Text(state.loc.get("progress_preparing"), color=ft.Colors.GREEN, size=13, weight=ft.FontWeight.BOLD)
        progress_count = ft.Text("0/0", color=ft.Colors.WHITE, size=13)
        progress_bar = ft.ProgressBar(value=0, color=ft.Colors.GREEN, bgcolor="#2A2A35", bar_height=8)
        progress_video_name = ft.Text("", color=ft.Colors.GREY_400, size=11, italic=True)
        
        def cancel_upload(e):
            state.uploader.stop()
            progress_text.value = state.loc.get("progress_cancelled")
            progress_text.color = ft.Colors.RED
            progress_bar.color = ft.Colors.RED
            try:
                page.update()
            except: pass

        cancel_btn = ft.IconButton(
            icon=ft.Icons.CANCEL,
            icon_color=ft.Colors.RED_400,
            icon_size=18,
            tooltip=state.loc.get("tooltip_cancel"),
            on_click=cancel_upload,
        )
        
        def on_progress(current, total, video_name, status):
            if state.uploader.stop_flag: return
            try:
                if status == "starting":
                    progress_text.value = state.loc.get("progress_starting")
                    progress_text.color = ft.Colors.GREEN
                    progress_bar.color = ft.Colors.GREEN
                    progress_count.value = f"0/{total}"
                    progress_bar.value = 0
                elif status == "uploading":
                    progress_text.value = state.loc.get("progress_uploading")
                    progress_count.value = f"{current}/{total}"
                    progress_video_name.value = video_name
                    progress_bar.value = current / total if total > 0 else 0
                elif status == "done":
                    progress_count.value = f"{current}/{total}"
                    progress_bar.value = current / total if total > 0 else 1
                    progress_video_name.value = f"✅ {video_name}"
                elif status == "failed":
                    progress_count.value = f"{current}/{total}"
                    progress_bar.value = current / total if total > 0 else 1
                    progress_video_name.value = f"❌ {video_name}"
                elif status == "completed":
                    progress_text.value = state.loc.get("progress_completed")
                    progress_count.value = f"{current}/{total}"
                    progress_bar.value = 1
                    progress_video_name.value = ""
                    cancel_btn.visible = False
                page.update()
            except: pass

        progress_row = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CLOUD_UPLOAD, size=16, color=ft.Colors.GREEN),
                    progress_text,
                    progress_count,
                    ft.Container(expand=True),
                    progress_video_name,
                    cancel_btn,
                ], spacing=8, alignment=ft.MainAxisAlignment.START),
                progress_bar,
            ], spacing=6),
            visible=False,
            padding=ft.padding.symmetric(vertical=10, horizontal=5),
            bgcolor=ft.Colors.with_opacity(0.3, "#1a1a2e"),
            border_radius=8,
        )

        main_upload_ui.content = ft.Column([
             ft.Row([
                ft.Text(state.loc.get("title_upload"), size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(
                    content=ft.Row([ft.Icon(ft.Icons.ROCKET, size=14, color="#F857A6"), ft.Text("AI Powered Automation", color="#F857A6", size=11, weight=ft.FontWeight.BOLD)], spacing=5),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border=ft.border.all(1, "#F857A6"),
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.1, "#F857A6")
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Text("Select videos, authenticate, and choose your release strategy.", size=14, color=ft.Colors.GREY_500),
            
            ft.Container(height=10),

            ft.Container(
                content=ft.Column([
                    ft.Row([
                         ft.Text(state.loc.get("upload_folder_msg"), size=18, weight=ft.FontWeight.BOLD, color="#4E75FF"),
                         ft.TextButton(state.loc.get("upload_select_all"), on_click=on_select_all, style=ft.ButtonStyle(color="#4E75FF"))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=10),
                    
                    ft.Container(
                        content=video_list_ui,
                        border=ft.border.all(1, "#333"),
                        border_radius=8,
                        padding=10,
                        bgcolor="#121212",
                        height=280
                    ),
                    
                    ft.Container(height=20),
                    
                    ft.Row([
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Image(src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg", width=20, height=20), 
                                ft.Text(state.loc.get("btn_login_google"), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14)
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                            on_click=on_login, 
                            style=ft.ButtonStyle(
                                bgcolor="#1F1F1F", 
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=15
                            ),
                            expand=True
                        ),
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CLOUD_UPLOAD, color=ft.Colors.WHITE, size=18), 
                                ft.Text("Upload Videos", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14)
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                            on_click=open_upload_dialog, 
                            style=ft.ButtonStyle(
                                bgcolor="#43A047", 
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=15
                            ),
                            expand=True
                        )
                    ], spacing=15),
                    
                    progress_row
                ]),
                bgcolor="#191921",
                padding=25,
                border_radius=20,
                border=ft.border.all(1, "#2F2F3B"),
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK))
            )
        ])

        return ft.Column([main_upload_ui], expand=True)

    def get_logs_view():
        return ft.Column([
            ft.Text(state.loc.get("title_logs"), size=28, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Container(
                content=log_column,
                bgcolor="#000000", # Pure black for terminal feel
                padding=20,
                border_radius=12,
                expand=True,
                border=ft.border.all(1, "#333333"),
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK))
            )
        ], expand=True)

    def get_settings_view():
        google_api = ft.TextField(label=state.loc.get("lbl_google_key"), value=state.config.get_api_key("google_gemini"), password=True, can_reveal_password=True, border_color=ACCENT_COLOR)
        pexels_api = ft.TextField(label=state.loc.get("lbl_pexels_key"), value=state.config.get_api_key("pexels"), password=True, can_reveal_password=True, border_color=ACCENT_COLOR)
        
        languages = [ft.dropdown.Option("English"), ft.dropdown.Option("Español")]
        
        # Load the raw 2-letter code from prefs (e.g. "en" or "es")
        raw_lang = state.config.get_preference("language", "en")
        
        # Reconstruct exactly what the dropdown string should be
        current_lang = "English" if raw_lang == "en" else "Español"
        
        lang_drop = ft.Dropdown(label=state.loc.get("lbl_language"), options=languages, value=current_lang, border_color=ACCENT_COLOR)
        
        watermark = ft.TextField(label=state.loc.get("lbl_watermark"), value=state.config.get_preference("watermark"), border_color=ACCENT_COLOR)

        def on_save(e):
            try:
                state.config.set_api_key("google_gemini", google_api.value)
                state.config.set_api_key("pexels", pexels_api.value)
                
                
                # We expect the exact literal string "English" or "Español"
                lang_code = "en" if lang_drop.value.strip() == "English" else "es"
                state.config.set_preference("language", lang_code)
                state.config.set_preference("watermark", watermark.value)
                
                # Update live localization for the UI
                state.loc.set_language(lang_code)
                
                # Update Sidebar/Rail instantly via closure
                rail.destinations[0].label = state.loc.get("sidebar_home")
                rail.destinations[1].label = state.loc.get("title_generator")
                rail.destinations[2].label = state.loc.get("sidebar_upload")
                rail.destinations[3].label = state.loc.get("sidebar_history")
                rail.destinations[4].label = state.loc.get("sidebar_settings")
                rail.update()
                
                # Force a rapid rebuild of the current view to instantly update translation strings
                change_view(4)
                
                # Show customized translation for the success message
                success_msg = "Ajustes Guardados y Aplicados." if lang_code == "es" else "Settings Saved & Applied."
                show_snack(success_msg, ft.Colors.GREEN_600)
            except Exception as _ex:
                import traceback
                traceback.print_exc()
                show_snack(f"Error: {str(_ex)}", ft.Colors.RED_500)

        return ft.Column([
            ft.Text(state.loc.get("title_settings"), size=28, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            create_card(
                 ft.Column([
                     ft.Text(state.loc.get("lbl_api_keys"), size=14, weight=ft.FontWeight.BOLD, color=ACCENT_COLOR),
                     ft.Container(height=10),
                     google_api,
                     pexels_api,
                     ft.Container(height=20),
                     ft.Divider(color="#2b303b"),
                     ft.Container(height=10),
                     ft.Text(state.loc.get("lbl_preferences"), size=14, weight=ft.FontWeight.BOLD, color=ACCENT_COLOR),
                     ft.Container(height=10),
                     lang_drop,
                     watermark,
                     ft.Container(height=20),
                     ft.Container(
                        content=ft.Text(state.loc.get("btn_save"), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                        alignment=ft.Alignment(0,0),
                        bgcolor=ft.Colors.GREEN_600,
                        height=50,
                        border_radius=12,
                        on_click=on_save,
                        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.3, ft.Colors.GREEN_600))
                     )
                 ])
            )
        ], scroll=ft.ScrollMode.AUTO)

    # --- UPDATE / UPGRADE VIEW ---
    def get_update_view():
        loc = state.loc
        def feature_row(feature, pro_val, premium_val, pro_icon=ft.Icons.CHECK_CIRCLE, premium_icon=ft.Icons.STAR):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(feature, size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                        expand=2
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(pro_icon, size=16, color=ft.Colors.BLUE_400),
                            ft.Text(pro_val, size=12, color=ft.Colors.GREY_300)
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                        expand=1
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(premium_icon, size=16, color=ft.Colors.AMBER_400),
                            ft.Text(premium_val, size=12, color=ft.Colors.AMBER_200, weight=ft.FontWeight.BOLD)
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                        expand=1
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_800))
            )

        features = [
            (loc.get("update_feat_duration"), loc.get("update_feat_duration_pro"), loc.get("update_feat_duration_prem")),
            (loc.get("update_feat_effects"), loc.get("update_feat_effects_pro"), loc.get("update_feat_effects_prem")),
            (loc.get("update_feat_transitions"), loc.get("update_feat_transitions_pro"), loc.get("update_feat_transitions_prem")),
            (loc.get("update_feat_quality"), loc.get("update_feat_quality_pro"), loc.get("update_feat_quality_prem")),
            (loc.get("update_feat_speed"), loc.get("update_feat_speed_pro"), loc.get("update_feat_speed_prem")),
            (loc.get("update_feat_support"), loc.get("update_feat_support_pro"), loc.get("update_feat_support_prem")),
            (loc.get("update_feat_updates"), loc.get("update_feat_updates_pro"), loc.get("update_feat_updates_prem")),
        ]

        table_header = ft.Container(
            content=ft.Row([
                ft.Container(content=ft.Text(loc.get("update_col_feature"), size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400), expand=2),
                ft.Container(content=ft.Text("PRO", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400), expand=1, alignment=ft.Alignment(0,0)),
                ft.Container(content=ft.Text("PREMIUM", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400), expand=1, alignment=ft.Alignment(0,0)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor="#1A1A2E",
            border_radius=ft.border_radius.only(top_left=12, top_right=12)
        )

        table_rows = [feature_row(f, p, pm) for f, p, pm in features]

        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.UPGRADE, size=28, color=ACCENT_COLOR),
                ft.Text(loc.get("update_title"), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            ], spacing=10),
            ft.Container(height=5),
            ft.Text(loc.get("update_subtitle"), size=14, color=ft.Colors.GREY_400),
            ft.Container(height=20),
            # Comparison card
            ft.Container(
                content=ft.Column([
                    # Title bar with gradient
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.WORKSPACE_PREMIUM, size=24, color=ft.Colors.WHITE),
                            ft.Text("PRO vs PREMIUM", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        padding=15,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(-1, 0),
                            end=ft.Alignment(1, 0),
                            colors=["#4E75FF", "#8A4EFF", "#FFB347"]
                        ),
                        border_radius=ft.border_radius.only(top_left=12, top_right=12)
                    ),
                    table_header,
                    *table_rows,
                    ft.Container(height=10),
                ], spacing=0),
                bgcolor=CARD_COLOR,
                border_radius=12,
                border=ft.border.all(1, "#333333"),
                shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.2, "#8A4EFF"))
            ),
            ft.Container(height=20),
            # Upgrade CTA button
            ft.Container(
                content=ft.Container(
                    content=ft.Text(loc.get("update_btn_get"), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                    bgcolor=ft.Colors.AMBER_700,
                    height=50,
                    width=250,
                    border_radius=12,
                    alignment=ft.Alignment(0, 0),
                    on_click=lambda e: show_snack(loc.get("update_snack_contact"), ft.Colors.AMBER_700),
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.3, ft.Colors.AMBER_700))
                ),
                alignment=ft.Alignment(0, 0)
            )
        ], scroll=ft.ScrollMode.AUTO)

    # --- NAVIGATION ---
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        bgcolor=SIDEBAR_COLOR,
        group_alignment=-0.9,
        expand=True,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME_OUTLINED, 
                selected_icon=ft.Icons.HOME, 
                label=state.loc.get("sidebar_home")
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.VIDEO_LIBRARY_OUTLINED, 
                selected_icon=ft.Icons.VIDEO_LIBRARY, 
                label=state.loc.get("title_generator")
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CLOUD_UPLOAD_OUTLINED, 
                selected_icon=ft.Icons.CLOUD_UPLOAD, 
                label=state.loc.get("sidebar_upload")
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.HISTORY_OUTLINED, 
                selected_icon=ft.Icons.HISTORY, 
                label=state.loc.get("sidebar_history")
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED, 
                selected_icon=ft.Icons.SETTINGS, 
                label=state.loc.get("sidebar_settings")
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.UPGRADE_OUTLINED, 
                selected_icon=ft.Icons.UPGRADE, 
                label=state.loc.get("sidebar_update")
            ),
        ],
        on_change=lambda e: change_view(e.control.selected_index)
    )

    # Logo Logic (Stylish Text & Icons)
    header = ft.Container(
        content=ft.Column([
            ft.Image(src="assets/logo.png", width=54, height=54, fit="contain"),
            ft.Container(height=5),
            ft.Row([
                ft.Text(state.loc.get("logo_ai_shorts"), size=20, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE, italic=True),
                ft.Icon(ft.Icons.ROCKET_LAUNCH, color=ACCENT_COLOR, size=20)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
            ft.Text(state.loc.get("logo_generator"), size=14, weight=ft.FontWeight.BOLD, color=TEXT_SUBTITLE),
            ft.Container(
                content=ft.Text(state.loc.get("logo_pro"), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                bgcolor=ACCENT_COLOR,
                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                border_radius=6
            )
        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.only(left=15, top=30, bottom=30),
        alignment=ft.Alignment(0, 0)
    )
    rail.leading = header
    
    # Contact Footer
    support_footer = ft.Container(
        content=ft.Column([
             ft.Divider(color=ft.Colors.GREY_800),
             ft.Row([
                 ft.Icon(ft.Icons.EMAIL, size=14, color=ft.Colors.GREY_500),
                 ft.Text(state.loc.get("lbl_support"), size=12, color=ft.Colors.GREY_500, weight=ft.FontWeight.BOLD),
             ], alignment=ft.MainAxisAlignment.CENTER),
             ft.Text("tiagoaccotos@gmail.com", size=10, color=ft.Colors.GREY_600),
        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
        padding=20
    )

    generator_view_instance = get_generator_view()
    
    view_map = {
        0: get_home_view,
        1: lambda: generator_view_instance,
        2: get_upload_view,
        3: get_history_view,
        4: get_settings_view,
        5: get_update_view
    }

    def change_view(index):
        try:
            content = view_map[index]()
            if hasattr(content, 'update_stats'):
                content.update_stats()
            main_content.content = content
            page.update()
        except Exception as e:
            import traceback
            traceback.print_exc()
        
    main_content = ft.Container(expand=True, padding=30) # More padding for "breathing room"

    # Layout
    page.add(
        ft.Row(
            [
                ft.Container(
                    content=ft.Column([
                        rail,
                        support_footer
                    ]),
                    bgcolor=SIDEBAR_COLOR,
                ),
                ft.VerticalDivider(width=1, color=ft.Colors.TRANSPARENT), # Invisible divider
                main_content
            ],
            expand=True,
        )
    )
    
    # Init
    change_view(0)

# START

if __name__ == "__main__":
    ft.app(target=main, assets_dir=".")
