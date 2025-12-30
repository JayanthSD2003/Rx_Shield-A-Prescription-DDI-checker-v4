from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from core.auth_manager import login, register, change_password
from core.database import save_analysis, get_recent_analysis, get_all_users, update_user_approval, get_login_logs, get_analysis_logs, update_user_password
from core.gemini_client import analyze_prescription
from core.tts_manager import play_welcome_message
from core.exporter import create_markdown, create_word, create_pdf
import threading
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import ListProperty, StringProperty, ObjectProperty

from kivy.app import App
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import requests
from kivy_garden.mapview import MapView, MapMarker

class LoginScreen(Screen):
    def do_login(self, username, password, selected_role):
        success, message, role = login(username, password)
        if success:
            if role != selected_role:
                self.show_popup("Login Failed", f"Incorrect role selected. Account is {role}.")
                return

            # Store username in App state
            app = App.get_running_app()
            app.username = username
            app.role = role
            
            if role in ['Admin', 'RootAdmin']:
                self.manager.current = 'admin_dashboard'
            else:
                self.manager.current = 'home'
        else:
            self.show_popup("Login Failed", message)

    def show_popup(self, title, content):
        popup = Popup(title=title, content=Label(text=content), size_hint=(None, None), size=(400, 200))
        popup.open()

    def exit_app(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text="Do you want to exit?"))
        
        buttons = BoxLayout(spacing=10, size_hint_y=None, height=40)
        btn_yes = Button(text="Yes", on_press=lambda x: App.get_running_app().stop())
        btn_no = Button(text="No", on_press=lambda x: self.popup.dismiss())
        
        buttons.add_widget(btn_yes)
        buttons.add_widget(btn_no)
        content.add_widget(buttons)
        
        self.popup = Popup(title="Exit Confirmation", content=content, size_hint=(None, None), size=(300, 150))
        self.popup.open()

class RegisterScreen(Screen):
    def do_register(self, username, password, role='User'):
        success, message = register(username, password, role)
        if success:
            self.show_popup("Success", message)
            self.manager.current = 'login'
        else:
            self.show_popup("Registration Failed", message)

    def show_popup(self, title, content):
        popup = Popup(title=title, content=Label(text=content), size_hint=(None, None), size=(400, 200))
        popup.open()

class AdminDashboard(Screen):
    def on_enter(self):
        self.refresh_data()

    def refresh_data(self):
        # Refresh Approvals
        users = get_all_users()
        pending = [{'username': u['username'], 'role': u['role']} for u in users if not u['is_approved']]
        self.ids.rv_approvals.data = pending
        
        # Refresh All Users View
        # Use filtered list for display if needed, currently showing all
        all_users_view = [{'username': u['username'], 'role': u['role']} for u in users]
        self.ids.rv_users.data = all_users_view

        # Refresh Login Logs
        logs = get_login_logs()
        self.ids.rv_login_logs.data = [{'text': f"{l['timestamp']} - {l['username']}: {l['status']}"} for l in logs]

        # Refresh Analysis Logs
        analysis_logs = get_analysis_logs()
        self.ids.rv_analysis_logs.data = [
            {
                'timestamp': str(l['timestamp']),
                'username': l['username'],
                'preview': (f"[Approved by Dr. {l['approved_by_doctor']}] " if l['is_doctor_approved'] else "") + l['result_text'][:100].replace('\n', ' '),
                'full_text': l['result_text'] + (f"\n\n--- APPROVED BY DR. {l['approved_by_doctor']} ---" if l['is_doctor_approved'] else "")
            } for l in analysis_logs
        ]

    def create_account(self, username, password, role):
        app = App.get_running_app()
        if not hasattr(app, 'role'):
            self.show_popup("Error", "Session error. Please logout and login.")
            return

        from core.auth_manager import admin_create_user
        
        success, msg = admin_create_user(app.role, username, password, role)
        if success:
            self.show_popup("Success", msg)
            self.ids.create_username.text = ""
            self.ids.create_password.text = ""
        else:
            self.show_popup("Error", msg)

    def approve_user(self, username):
        update_user_approval(username, 1)
        self.refresh_data()
        self.show_popup("Success", f"User {username} approved.")

    def change_user_password(self, username, new_password):
        if not username or not new_password:
            self.show_popup("Error", "Username and new password required.")
            return
        
        success, msg = change_password(username, new_password)
        if success:
            self.show_popup("Success", msg)
        else:
            self.show_popup("Error", msg)

    def logout(self):
        app = App.get_running_app()
        if hasattr(app, 'username'): del app.username
        if hasattr(app, 'role'): del app.role
        self.manager.current = 'login'

    def show_popup(self, title, content):
        popup = Popup(title=title, content=Label(text=content), size_hint=(None, None), size=(400, 200))
        popup.open()

    def show_analysis_detail(self, full_text, username, timestamp):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.textinput import TextInput
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Info Label
        content.add_widget(Label(text=f"User: {username} | Date: {timestamp}", 
                                size_hint_y=None, height=30, bold=True))
        
        # Scrollable Text
        scroll = ScrollView(do_scroll_x=False)
        text_input = TextInput(text=full_text, readonly=True, background_color=(1,1,1,1),
                              size_hint_y=None, height=max(500, len(full_text)//2)) # approximate height
        scroll.add_widget(text_input)
        content.add_widget(scroll)
        
        # Close Button
        btn = Button(text='Close', size_hint_y=None, height=50)
        content.add_widget(btn)
        
        popup = Popup(title="Analysis Detail", content=content, size_hint=(0.8, 0.8))
        btn.bind(on_release=popup.dismiss)
        popup.open()

class HistoryScreen(Screen):
    def on_enter(self):
        try:
            app = App.get_running_app()
            if not hasattr(app, 'username'):
                print("History: No username found.")
                return
                
            from core.database import get_analyses_by_user
            logs = get_analyses_by_user(app.username)
            print(f"History: Loaded {len(logs)} logs.")
            
            # Format: timestamp - result snippet for display
            self.ids.rv_history.data = [
                {
                    'text': f"[b]{l['timestamp']}[/b]\n" + (f"[color=00aa00][Approved][/color] " if l['is_doctor_approved'] else "") + f"{l['result_text'][:60]}...",
                    'full_text': l['result_text'] + (f"\n\n--- APPROVED BY DR. {l['approved_by_doctor']} ---" if l['is_doctor_approved'] else ""),
                    'image_path': l['image_path']
                } 
                for l in logs
            ]
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"CRASH in HistoryScreen.on_enter: {e}")

    def show_full_text(self, text, image_path):
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.image import Image
        from kivy.uix.label import Label
        from kivy.graphics import Color, Rectangle
        
        # Get App theme colors
        app = App.get_running_app()
        bg_color = app.card_color
        text_color = app.text_color
        
        # Main Layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Image Section (Top, larger)
        if image_path and os.path.exists(image_path):
            img_box = BoxLayout(size_hint_y=None, height=300)
            img = Image(source=image_path, allow_stretch=True, keep_ratio=True)
            img_box.add_widget(img)
            layout.add_widget(img_box)
        
        # Text Section (Scrollable)
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content_box.bind(minimum_height=content_box.setter('height'))
        
        # Disclaimer Label
        lbl_disclaimer = Label(
            text="DISCLAIMER: This analysis is trained and working on a limited resource before droping or drawing into the conclusion make sure contact that doctor who wrote that particular prescription and take is verbal consent.",
            color=(1, 0, 0, 1),
            bold=True,
            size_hint_y=None,
            text_size=(450, None),
            halign='center'
        )
        lbl_disclaimer.bind(texture_size=lbl_disclaimer.setter('size'))
        content_box.add_widget(lbl_disclaimer)
        
        # Analysis Text Label - White Text
        # Ensuring text is string
        if not text: text = "No text content."
        
        lbl_text = Label(
            text=text,
            color=(1, 1, 1, 1), 
            size_hint_y=None,
            text_size=(450, None),
            halign='left',
            valign='top'
        )
        lbl_text.bind(texture_size=lbl_text.setter('size'))
        content_box.add_widget(lbl_text)
        
        scroll.add_widget(content_box)
        layout.add_widget(scroll)
        
        # Export Buttons Box
        export_box = BoxLayout(size_hint_y=None, height=40, spacing=10)
        
        def export_history(format_type):
            from datetime import datetime
            import tkinter as tk
            from tkinter import filedialog
            
            reports_dir = os.path.join(os.getcwd(), 'reports')
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"History_Report_{timestamp}"
            
            root = tk.Tk()
            root.withdraw()
            
            success = False
            file_path = ""
            
            if format_type == 'markdown':
                file_path = filedialog.asksaveasfilename(initialdir=reports_dir, initialfile=f"{default_filename}.md", filetypes=[("Markdown", "*.md")])
                if file_path: success = create_markdown(text, image_path, file_path)
            elif format_type == 'word':
                file_path = filedialog.asksaveasfilename(initialdir=reports_dir, initialfile=f"{default_filename}.docx", filetypes=[("Word", "*.docx")])
                if file_path: success = create_word(text, image_path, file_path)
            elif format_type == 'pdf':
                file_path = filedialog.asksaveasfilename(initialdir=reports_dir, initialfile=f"{default_filename}.pdf", filetypes=[("PDF", "*.pdf")])
                if file_path: success = create_pdf(text, image_path, file_path)
            
            root.destroy()
            
            if file_path:
                msg = f"Exported to {os.path.basename(file_path)}" if success else "Export failed"
                print(msg) 

        btn_pdf = Button(text="Export PDF", background_color=app.secondary_color, on_press=lambda x: export_history('pdf'))
        btn_word = Button(text="Export Word", background_color=app.secondary_color, on_press=lambda x: export_history('word'))
        btn_md = Button(text="Export MD", background_color=app.secondary_color, on_press=lambda x: export_history('markdown'))

        export_box.add_widget(btn_pdf)
        export_box.add_widget(btn_word)
        export_box.add_widget(btn_md)
        layout.add_widget(export_box)

        # Action Buttons Box
        action_box = BoxLayout(size_hint_y=None, height=50, spacing=20)

        # Close Button
        btn_close = Button(
            text="Close",
            size_hint_x=None, width=100,
            background_color=app.primary_color,
            color=(1,1,1,1),
            bold=True
        )
        
        # View Graph Button logic
        # Refined Drug Extraction Logic
        import re
        
        # 1. Isolate the "Medications" section if possible
        section_match = re.search(r'(?i)\*\*Identified Medications\*\*:?(.*?)(?:\n\n|\Z)', text, re.DOTALL)
        content_to_parse = section_match.group(1) if section_match else text
        
        # 2. Extract items (numbered lists)
        # Matches: "1. **DrugName**" or "1. DrugName"
        raw_matches = re.findall(r'\d+\.\s+(?:\*\*)?([A-Za-z0-9\-\s]+?)(?:\*\*)?(?:\s|$|\()', content_to_parse)
        
        # 3. Filter Junk (Blacklist)
        blacklist = {'phone', 'physician', 'patient', 'date', 'signature', 'tab', 'cap', 'tablet', 'capsule', 'name', 'age', 'sex', 'gender'}
        drug_matches = [
            d.strip() for d in raw_matches 
            if d.strip().lower() not in blacklist and len(d.strip()) > 2
        ]
        
        # Fallback: if section slice failed to find anything, try global but filtered
        if not drug_matches and section_match:
             # Try stricter regex on full text if section parse failed strangely
             pass 

        btn_graph = Button(
            text="View Knowledge Graph",
            size_hint_x=None, width=180,
            background_color=app.secondary_color,
            color=(1,1,1,1),
            bold=True
        )

        popup = Popup(
            title='Analysis Details',
            title_size=20,
            title_align='center',
            content=layout,
            size_hint=(0.8, 0.9),
            separator_color=app.primary_color,
            background_color=(0,0,0,0.9)
        )
        
        btn_close.bind(on_release=popup.dismiss)
        
        def open_history_graph(instance):
            popup.dismiss()
            if drug_matches:
                print(f"History Graph: Using extracted drugs: {drug_matches}")
                app.recent_drugs = drug_matches
            else:
                 print("History Graph: No specific drugs found.")
                 app.recent_drugs = []
                 
            app.generate_knowledge_graph()
            app.root.current = 'graph'
            
        btn_graph.bind(on_release=open_history_graph)
        
        action_box.add_widget(btn_close)
        if drug_matches:
            action_box.add_widget(btn_graph)
            
        layout.add_widget(action_box)
        popup.open()
        


class HomeScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        
        # Update Welcome Message
        if hasattr(app, 'username'):
            self.ids.welcome_label.text = f"Welcome, {app.username}!"
            
            # Play welcome message only once
            if not getattr(app, 'welcome_played', False):
                play_welcome_message(app.username)
                app.welcome_played = True

            # Load Recent Analysis from DB
            recent = get_recent_analysis(app.username)
            if recent:
                image_path, result_text = recent
                
                # Ensure image path is absolute and exists
                if image_path and os.path.exists(image_path):
                    self.ids.recent_image.source = image_path
                    
                    # Store in app state for export/viewing
                    app.recent_image = image_path
                    app.recent_text = result_text
                    
                    # Truncate text for preview
                    preview_text = result_text[:100] + "..." if len(result_text) > 100 else result_text
                    self.ids.recent_text.text = preview_text
                    
                    # Show filename
                    filename = os.path.basename(image_path)
                    self.ids.recent_filename.text = f"File: {filename}"
                else:
                    # Handle missing file case
                    self.ids.recent_image.source = ''
                    self.ids.recent_text.text = "Recent file not found."
                    self.ids.recent_filename.text = ''
            else:
                self.ids.recent_image.source = ''
                self.ids.recent_text.text = "No recent analysis found."
                self.ids.recent_filename.text = ''

    def logout(self):
        try:
            app = App.get_running_app()
            if hasattr(app, 'username'):
                del app.username
            if hasattr(app, 'welcome_played'):
                del app.welcome_played
            # Clear recent analysis on logout
            if hasattr(app, 'recent_image'): del app.recent_image
            if hasattr(app, 'recent_text'): del app.recent_text
            
            self.manager.current = 'login'
        except Exception as e:
            print(f"Error during logout: {e}")
            # Force switch even if error
            try: self.manager.current = 'login'
            except: pass

    def show_profile(self):
        app = App.get_running_app()
        if not hasattr(app, 'username'):
            return
            
        username = getattr(app, 'username', 'Unknown')
        role = getattr(app, 'role', 'User')
        
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.graphics import Color, Ellipse

        # Main Layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Profile Picture Section
        avatar_box = BoxLayout(size_hint_y=None, height=120, orientation='vertical')
        
        # Avatar Widget (Label with canvas background)
        initial = username[0].upper() if username else "?"
        
        # Using a centered label
        lbl_avatar = Label(text=initial, font_size=40, bold=True, size_hint=(None, None), size=(100, 100), pos_hint={'center_x': 0.5})
        
        # Draw circle on canvas
        with lbl_avatar.canvas.before:
            Color(0.2, 0.6, 1, 1) # Blue
            self.circle = Ellipse(pos=lbl_avatar.pos, size=lbl_avatar.size)
            
        def update_circle(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                 Color(0.2, 0.6, 1, 1) # Blue
                 Ellipse(pos=instance.pos, size=instance.size)

        lbl_avatar.bind(pos=update_circle, size=update_circle)
        
        avatar_box.add_widget(lbl_avatar)
        layout.add_widget(avatar_box)
        
        # Details
        info_box = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=80)
        
        # Ensure White text as requested
        name_lbl = Label(text=f"[b]{username}[/b]", markup=True, font_size=24, color=(1,1,1,1))
        role_lbl = Label(text=f"Role: {role}", font_size=16, color=(0.8, 0.8, 0.8, 1))
        
        info_box.add_widget(name_lbl)
        info_box.add_widget(role_lbl)
        
        layout.add_widget(info_box)
        
        # Close Button
        btn_close = Button(
            text="Close",
            size_hint_y=None,
            height=40,
            background_color=app.primary_color,
            color=(1,1,1,1)
        )
        layout.add_widget(btn_close)
        
        # Logout Button
        btn_logout = Button(
            text="Logout",
            size_hint_y=None,
            height=40,
            background_color=(0,0,0,0),
            color=(1, 0.2, 0.2, 1), # Red text
            bold=True
        )
        layout.add_widget(btn_logout)
        
        popup = Popup(
            title='User Profile',
            title_color=(1,1,1,1),
            content=layout,
            size_hint=(None, None),
            size=(300, 420), 
            separator_color=app.primary_color,
            background_color=(0.1, 0.1, 0.1, 1) # Dark background for white text
        )
        
        btn_close.bind(on_release=popup.dismiss)
        
        def do_logout(instance):
            popup.dismiss()
            self.logout()
            
        btn_logout.bind(on_release=do_logout)
        
        popup.open()

class WelcomeScreen(Screen):
    def set_user(self, username):
        self.ids.welcome_label.text = f"Welcome, {username}!"
        if hasattr(self.ids, 'welcome_label'):
             pass # Logic handled in HomeScreen now typically, but keeping for compatibility

class DashboardScreen(Screen):
    def on_enter(self):
        # Clear selection when entering dashboard
        if hasattr(self.ids, 'filechooser'):
            self.ids.filechooser.selection = []

    def analyze_image(self, selection):
        if not selection:
            return
        
        image_path = selection[0]
        self.show_patient_form(image_path)
        
    def show_patient_form(self, image_path):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.textinput import TextInput
        from kivy.uix.spinner import Spinner
        from kivy.uix.togglebutton import ToggleButton
        from kivy.uix.label import Label
        from kivy.uix.popup import Popup
        from kivy.graphics import Color, RoundedRectangle
        
        # Get App theme
        app = App.get_running_app()
        
        # Helper to style TextInput
        def get_styled_input(hint, input_filter=None):
            ti = TextInput(
                hint_text=hint, 
                multiline=False, 
                size_hint_y=None, 
                height=45,
                background_color=(0,0,0,0), # Transparent bg
                foreground_color=(0,0,0,1) if not app.is_dark_mode else (1,1,1,1),
                cursor_color=app.primary_color,
                input_filter=input_filter,
                padding=[10, 10]
            )
            # Add custom background
            with ti.canvas.after:
                Color(*app.primary_color)
                self.line = RoundedRectangle(pos=ti.pos, size=ti.size, radius=[8,])
                
            # Quick hack to draw border/bg: actually standard TextInput is hard to style perfectly without kv
            # Let's simple style: standard with hint color
            ti.background_color = (0.95, 0.95, 0.95, 1) if not app.is_dark_mode else (0.2, 0.2, 0.2, 1)
            ti.hint_text_color = (0.5, 0.5, 0.5, 1)
            return ti

        # Main Layout
        layout = BoxLayout(orientation='vertical', padding=[20, 20, 20, 20], spacing=15)
        
        # Title (Optional if Popup title is not enough)
        # layout.add_widget(Label(text="Patient Details", font_size=20, bold=True, color=app.primary_color, size_hint_y=None, height=40))
        
        # Name
        layout.add_widget(Label(text="Patient Name", color=(1,1,1,1), size_hint_y=None, height=25, halign='left', text_size=(360, None), bold=True))
        inp_name = get_styled_input("Enter Full Name")
        layout.add_widget(inp_name)
        
        # Row for Age & Gender
        row_ag = BoxLayout(spacing=15, size_hint_y=None, height=75)
        
        # Age
        box_age = BoxLayout(orientation='vertical', spacing=5)
        box_age.add_widget(Label(text="Age", color=(1,1,1,1), size_hint_y=None, height=25, halign='left', text_size=(100, None), bold=True))
        inp_age = get_styled_input("Years", 'int')
        box_age.add_widget(inp_age)
        
        # Gender
        box_gen = BoxLayout(orientation='vertical', spacing=5)
        box_gen.add_widget(Label(text="Gender", color=(1,1,1,1), size_hint_y=None, height=25, halign='left', text_size=(100, None), bold=True))
        spin_gender = Spinner(
            text='Select', 
            values=('Male', 'Female', 'Other'), 
            size_hint_y=None, 
            height=45,
            background_color=app.secondary_color,
            color=(1,1,1,1)
        )
        box_gen.add_widget(spin_gender)
        
        row_ag.add_widget(box_age)
        row_ag.add_widget(box_gen)
        layout.add_widget(row_ag)
        
        # Weight
        layout.add_widget(Label(text="Body Weight (kg)", color=(1,1,1,1), size_hint_y=None, height=25, halign='left', text_size=(360, None), bold=True))
        inp_weight = get_styled_input("e.g. 70.5", 'float')
        layout.add_widget(inp_weight)
        
        # Body Type (Radio)
        layout.add_widget(Label(text="Body Type", color=(1,1,1,1), size_hint_y=None, height=25, halign='left', text_size=(360, None), bold=True))
        type_box = BoxLayout(size_hint_y=None, height=45, spacing=10)
        
        self.selected_body_type = "Fit" # Default
        
        def on_type_select(instance):
             self.selected_body_type = instance.text
        
        for b_type in ['Fat', 'Lean', 'Fit']:
            # Styling toggle buttons
            btn = ToggleButton(
                text=b_type, 
                group='body_type', 
                state='down' if b_type == 'Fit' else 'normal',
                on_press=on_type_select,
                background_color=(0,0,0,0), # custom bg
                color=(1,1,1,1)
            )
            # Add simple canvas background
            # Note: Detailed button styling in python is verbose. Relying on default Toggle but adding color.
            # actually let's just use background_color
            btn.background_color = (0.3, 0.3, 0.3, 1) # Dark grey default
            
            # This logic updates color on state change would require bind.
            # Simplified:
            btn.background_normal = ''
            btn.background_down = ''
            btn.background_color = app.secondary_color if b_type == 'Fit' else (0.5, 0.5, 0.5, 1) 
            
            # Ideally bind state to color update
            def update_color(instance, value):
                instance.background_color = app.primary_color if instance.state == 'down' else (0.6, 0.6, 0.6, 1)
            
            btn.bind(state=update_color)
            # Trigger once
            update_color(btn, btn.state)
            
            type_box.add_widget(btn)
            
        layout.add_widget(type_box)
        
        # Spacer
        layout.add_widget(Label(size_hint_y=None, height=10))
        
        # Proceed Button
        btn_proceed = Button(
            text="Start Analysis",
            size_hint_y=None,
            height=50,
            background_color=app.primary_color,
            color=(1,1,1,1),
            bold=True,
            background_normal=''
        )
        
        layout.add_widget(btn_proceed)
        
        # Popup Styling
        popup = Popup(
            title='Patient Details Check',
            title_color=(1,1,1,1),
            title_size=20,
            title_align='center',
            content=layout,
            size_hint=(None, None),
            size=(450, 600), # Increased Size
            auto_dismiss=False,
            separator_color=app.primary_color,
            background_color=(0.1, 0.1, 0.1, 1) # Dark background for white text
        )
        
        def start_analysis(instance):
            # Basic validation
            if not inp_name.text or not inp_age.text or not inp_weight.text:
                 # Provide visual feedback and STOP
                 btn_proceed.text = "Missing Data!"
                 def reset_text(dt): btn_proceed.text = "Start Analysis"
                 from kivy.clock import Clock
                 Clock.schedule_once(reset_text, 1.5)
                 return
            
            details = {
                'name': inp_name.text,
                'age': inp_age.text,
                'gender': spin_gender.text,
                'weight': inp_weight.text,
                'body_type': self.selected_body_type
            }
            popup.dismiss()
            self.manager.current = 'results'
            self.manager.get_screen('results').process_image(image_path, details)
            


        btn_proceed.bind(on_release=start_analysis)
        popup.open()
from kivy.clock import mainthread

class ResultsScreen(Screen):

    def reset_and_back(self):
        self.ids.results_label.text = "Processing..."
        self.ids.result_image.source = ''
        self.manager.current = 'dashboard'

    def go_home(self):
        self.ids.results_label.text = "Processing..."
        self.ids.result_image.source = ''
        self.manager.current = 'home'

    def approve_prescription(self):
        app = App.get_running_app()
        if not hasattr(self, 'current_analysis_id') or not self.current_analysis_id:
            self.show_popup("Error", "No analysis to approve.")
            return
            
        from core.database import approve_analysis
        success = approve_analysis(self.current_analysis_id, app.username)
        if success:
            self.show_popup("Success", f"Prescription approved by Dr. {app.username}")
            # Potentially update the label to show approval
            self.ids.results_label.text += f"\n\n[b][color=00ff00]✓ Approved by Dr. {app.username}[/color][/b]"
        else:
            self.show_popup("Error", "Failed to save approval.")

    def export_result(self, format_type):
        app = App.get_running_app()
        if not hasattr(app, 'recent_text') or not app.recent_text:
            self.show_popup("Error", "No analysis to export.")
            return

        text = app.recent_text
        image_path = getattr(app, 'recent_image', None)
        graph_path = getattr(app, 'recent_graph_path', None)
        
        # Ensure reports directory exists
        reports_dir = os.path.join(os.getcwd(), 'reports')
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"Report_{timestamp}"
        
        # Initialize Tkinter root (hidden)
        root = tk.Tk()
        root.withdraw()
        
        if format_type == 'markdown':
            file_path = filedialog.asksaveasfilename(
                initialdir=reports_dir,
                initialfile=f"{default_filename}.md",
                title="Save Analysis Report",
                filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
            )
            if file_path:
                success = create_markdown(text, image_path, file_path, graph_path)
                msg = f"Exported to {os.path.basename(file_path)}" if success else "Export failed"
            else:
                return # User cancelled

        elif format_type == 'word':
            file_path = filedialog.asksaveasfilename(
                initialdir=reports_dir,
                initialfile=f"{default_filename}.docx",
                title="Save Analysis Report",
                filetypes=[("Word Documents", "*.docx"), ("All files", "*.*")]
            )
            if file_path:
                success = create_word(text, image_path, file_path, graph_path)
                msg = f"Exported to {os.path.basename(file_path)}" if success else "Export failed"
            else:
                return # User cancelled
                return # User cancelled
        elif format_type == 'pdf':
            file_path = filedialog.asksaveasfilename(
                initialdir=reports_dir,
                initialfile=f"{default_filename}.pdf",
                title="Save Analysis Report",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if file_path:
                success = create_pdf(text, image_path, file_path, graph_path)
                msg = f"Exported to {os.path.basename(file_path)}" if success else "Export failed"
            else:
                return # User cancelled
        else:
            msg = "Unknown format"
            
        root.destroy()
        self.show_popup("Export", msg)

    def show_popup(self, title, content):
        popup = Popup(title=title, content=Label(text=content), size_hint=(None, None), size=(400, 200))
        popup.open()

    @mainthread
    def update_ui(self, final_text, image_path, drugs_found):
        self.ids.results_label.text = final_text
        
        # Update App State
        app = App.get_running_app()
        if "Error" not in final_text:
             app.recent_drugs = drugs_found
             # Trigger Graph Generation on Main Thread (safe for UI)
             # Pass the full analysis text for better context extraction
             graph_path = app.generate_knowledge_graph(context_text=final_text)
             if graph_path:
                 app.recent_graph_path = graph_path # Store for export
        
        if image_path and os.path.exists(image_path):
            self.ids.result_image.source = image_path
            self.ids.result_image.reload()

    def process_image(self, image_path, patient_details=None):
        self.ids.results_label.text = "Processing image... Please wait."
        self.ids.result_image.source = '' 
        
        def _process():
            # Combined Analysis (OCR + DDI)
            from core.gemini_client import analyze_prescription
            # Unpack tuple: (Text, DrugList)
            final_text, drugs_found = analyze_prescription(image_path, patient_details)
            
            # Update UI on main thread
            self.update_ui(final_text, image_path if "Error" not in final_text else None, drugs_found)
            
            # Save to App state and DB
            if "Error" not in final_text:
                from kivy.app import App
                app = App.get_running_app()
                app.recent_image = image_path
                app.recent_text = final_text
                # recent_drugs set in update_ui
                
                # Save to DB
                if hasattr(app, 'username'):
                    self.current_analysis_id = save_analysis(app.username, image_path, final_text)

        threading.Thread(target=_process).start()

class PharmacyLocatorScreen(Screen):
    def on_enter(self):
        # Initialize map if not already done
        if not hasattr(self, 'map_view'):
            # Default to Bangalore
            self.map_view = MapView(zoom=13, lat=12.9716, lon=77.5946) 
            
            # Add map using internal ID if possible, else direct add
            if 'map_container' in self.ids:
                self.ids.map_container.add_widget(self.map_view)
        
        if not hasattr(self, 'current_markers'):
            self.current_markers = []

    def search_pharmacies(self, location_name):
        if not location_name:
            return
        
        # Clear list
        self.ids.rv_pharmacies.data = []
        # Removing manual clear of map internals which causes crash
        # self.ids.map_container.children[-1].clear_widgets() 
            
        threading.Thread(target=self._search_background, args=(location_name,)).start()

    def _search_background(self, location_name):
        try:
            # 1. Geocode Location (Nominatim)
            geo_url = "https://nominatim.openstreetmap.org/search"
            headers = {'User-Agent': 'RxShieldApp/1.0'}
            
            # Use raw query
            params = {
                'q': location_name, 
                'format': 'json', 
                'limit': 1
            }
            
            resp = requests.get(geo_url, params=params, headers=headers)
            data = resp.json()
            
            if not data:
                print(f"Location not found: {location_name}")
                return
                
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            
            # Update Map Center
            self.update_map_center(lat, lon)
            
            # 2. Find Pharmacies (Overpass API)
            overpass_url = "http://overpass-api.de/api/interpreter"
            # Query for pharmacies around 5km radius
            query = f"""
            [out:json];
            node["amenity"="pharmacy"](around:5000, {lat}, {lon});
            out body;
            """
            
            resp_op = requests.get(overpass_url, params={'data': query})
            data_op = resp_op.json()
            
            elements = data_op.get('elements', [])
            self.update_pharmacy_list(elements, lat, lon)
            
        except Exception as e:
            print(f"Error searching pharmacies: {e}")

    @mainthread
    def update_map_center(self, lat, lon):
        if hasattr(self, 'map_view'):
            # Clear previous markers
            self.clear_markers()
            
            self.map_view.center_on(lat, lon)
            
            # Add User Marker
            marker = MapMarker(lat=lat, lon=lon)
            self.map_view.add_marker(marker)
            self.current_markers.append(marker)
            
    def clear_markers(self):
        if not hasattr(self, 'current_markers'):
            self.current_markers = []
            
        for marker in self.current_markers:
            try:
                self.map_view.remove_marker(marker)
            except:
                pass
        self.current_markers = []
            
    @mainthread
    def update_pharmacy_list(self, pharmacies, center_lat, center_lon):
        if not hasattr(self, 'map_view'): return

        # Note: We don't clear user marker here, assuming we want to keep it?
        # But 'clear_markers' clears ALL. 
        # Ideally we want to keep user marker. 
        # Let's simple re-add user marker or just let pharmacies be added.
        # Check: update_map_center called first, adds User marker to current_markers.
        # If we don't clear here, we just add more. That's fine.
        
        list_data = []
        count = 0 
        
        min_lat, max_lat = center_lat, center_lat
        min_lon, max_lon = center_lon, center_lon
        
        for p in pharmacies:
            if count > 20: break # Limit results
            
            p_lat = p['lat']
            p_lon = p['lon']
            name = p.get('tags', {}).get('name', 'Unknown Pharmacy')
            
            # Extend bounds
            min_lat = min(min_lat, p_lat)
            max_lat = max(max_lat, p_lat)
            min_lon = min(min_lon, p_lon)
            max_lon = max(max_lon, p_lon)
            
            # Add Marker
            marker = MapMarker(lat=p_lat, lon=p_lon)
            self.map_view.add_marker(marker)
            self.current_markers.append(marker)
            
            # Calculate rough distance
            dist = ((p_lat - center_lat)**2 + (p_lon - center_lon)**2)**0.5 * 111 # km approx
            
            list_data.append({
                'name': name,
                'address': f"Lat: {p_lat}, Lon: {p_lon}", 
                'lat': p_lat,
                'lon': p_lon,
                'distance': f"{dist:.1f} km"
            })
            count += 1
            
        self.ids.rv_pharmacies.data = list_data
        
        # Zoom to fit
        if count > 0:
            # Simple zoom logic: find span
            lat_span = max_lat - min_lat
            lon_span = max_lon - min_lon
            max_span = max(lat_span, lon_span)
            
            # Rough zoom level map
            # 0.01 deg ~= 1km
            new_zoom = 13
            if max_span > 1.0: new_zoom = 8
            elif max_span > 0.5: new_zoom = 9
            elif max_span > 0.1: new_zoom = 11
            elif max_span > 0.05: new_zoom = 12
            elif max_span > 0.02: new_zoom = 13
            else: new_zoom = 14
            
            self.map_view.zoom = new_zoom
            # Center on midpoint
            self.map_view.center_on((min_lat + max_lat)/2, (min_lon + max_lon)/2)

    def open_pharmacy(self, lat, lon):
        import webbrowser
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        webbrowser.open(google_maps_url)

    def text_zoom_in(self):
        if hasattr(self, 'map_view') and self.map_view.zoom < 19:
            self.map_view.zoom += 1
            
    def text_zoom_out(self):
        if hasattr(self, 'map_view') and self.map_view.zoom > 2:
            self.map_view.zoom -= 1

class BenchmarkScreen(Screen):
    def run_tests(self):
        self.ids.benchmark_log.text = "Running benchmark... Please wait."
        threading.Thread(target=self._run_task).start()

    def _run_task(self):
        try:
            from benchmark_analysis import run_benchmark
            report = run_benchmark()
            self._update_log(report)
        except Exception as e:
            self._update_log(f"Error running benchmark: {str(e)}")

    @mainthread
    def _update_log(self, text):
        self.ids.benchmark_log.text = text

class ManualEntryScreen(Screen):
    def analyze_manual_text(self):
        text = self.ids.manual_input.text
        if not text.strip():
            return
            
        # Show patient details form before processing
        self.show_patient_form(text)
        
    def show_patient_form(self, text_content):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.textinput import TextInput
        from kivy.uix.spinner import Spinner
        from kivy.uix.togglebutton import ToggleButton
        from kivy.uix.label import Label
        from kivy.uix.popup import Popup
        from kivy.uix.button import Button
        from kivy.graphics import Color, RoundedRectangle
        
        app = App.get_running_app()
        
        # Helper to style TextInput
        def get_styled_input(hint, input_filter=None):
            ti = TextInput(
                hint_text=hint, multiline=False, size_hint_y=None, height=50,
                background_color=(0,0,0,0),
                foreground_color=(1,1,1,1), # Force white text for dark popup
                cursor_color=app.primary_color, input_filter=input_filter, padding=[15, 15]
            )
            with ti.canvas.after:
                Color(*app.primary_color)
                RoundedRectangle(pos=ti.pos, size=ti.size, radius=[8,])
            ti.hint_text_color = (0.7, 0.7, 0.7, 1) # Light grey hint
            return ti

        # Main Layout
        layout = BoxLayout(orientation='vertical', padding=[25, 25, 25, 25], spacing=20)
        with layout.canvas.before:
            Color(0.15, 0.15, 0.15, 1) # Dark background
            RoundedRectangle(pos=layout.pos, size=layout.size, radius=[15,])
            
        def update_layout_bg(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[15,])
        layout.bind(pos=update_layout_bg, size=update_layout_bg)

        # Header
        layout.add_widget(Label(text="Patient Details", font_size=22, bold=True, color=app.primary_color, size_hint_y=None, height=40, halign='center'))

        # Name Section
        box_name = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None, height=80)
        box_name.add_widget(Label(text="Full Name", color=(1,1,1,1), size_hint_y=None, height=20, halign='left', text_size=(350, None), bold=True))
        inp_name = get_styled_input("e.g. John Doe")
        box_name.add_widget(inp_name)
        layout.add_widget(box_name)
        
        # Row for Age & Gender
        row_ag = BoxLayout(spacing=20, size_hint_y=None, height=80)
        
        # Age
        box_age = BoxLayout(orientation='vertical', spacing=8)
        box_age.add_widget(Label(text="Age", color=(1,1,1,1), size_hint_y=None, height=20, halign='left', text_size=(100, None), bold=True))
        inp_age = get_styled_input("Years", 'int')
        box_age.add_widget(inp_age)
        
        # Gender
        box_gen = BoxLayout(orientation='vertical', spacing=8)
        box_gen.add_widget(Label(text="Gender", color=(1,1,1,1), size_hint_y=None, height=20, halign='left', text_size=(100, None), bold=True))
        # Spinner styling needs care. background_color handles button bg. color handles text.
        spin_gender = Spinner(
            text='Select', values=('Male', 'Female', 'Other'), 
            size_hint_y=None, height=50, 
            background_color=app.secondary_color, 
            color=(1,1,1,1)
        )
        box_gen.add_widget(spin_gender)
        
        row_ag.add_widget(box_age)
        row_ag.add_widget(box_gen)
        layout.add_widget(row_ag)
        
        # Weight Section
        box_weight = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None, height=80)
        box_weight.add_widget(Label(text="Weight (kg)", color=(1,1,1,1), size_hint_y=None, height=20, halign='left', text_size=(350, None), bold=True))
        inp_weight = get_styled_input("e.g. 70.5", 'float')
        box_weight.add_widget(inp_weight)
        layout.add_widget(box_weight)
        
        # Body Type
        box_type = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None, height=80)
        box_type.add_widget(Label(text="Body Type", color=(1,1,1,1), size_hint_y=None, height=20, halign='left', text_size=(350, None), bold=True))
        type_btn_box = BoxLayout(size_hint_y=None, height=45, spacing=15)
        self.selected_body_type = "Fit"
        
        def on_type_select(instance):
             self.selected_body_type = instance.text
        
        for b_type in ['Fat', 'Lean', 'Fit']:
            # Using ToggleButton directly
            btn = ToggleButton(
                text=b_type, group='body_type', state='down' if b_type == 'Fit' else 'normal',
                on_press=on_type_select,
                background_color=(0,0,0,0), color=(1,1,1,1), font_size=14
            )
            # Custom styling callback
            def update_btn_color(instance, value):
                bg_col = app.primary_color if instance.state == 'down' else (0.4, 0.4, 0.4, 1)
                instance.canvas.before.clear()
                with instance.canvas.before:
                    Color(*bg_col)
                    RoundedRectangle(pos=instance.pos, size=instance.size, radius=[6,])
            
            btn.bind(pos=update_btn_color, size=update_btn_color, state=update_btn_color)
            type_btn_box.add_widget(btn)
            
        box_type.add_widget(type_btn_box)
        layout.add_widget(box_type)
        
        # Proceed Button
        btn_proceed = Button(
            text="Verify & Analyze", size_hint_y=None, height=55,
            background_color=(0,0,0,0), color=(1,1,1,1), bold=True, font_size=16
        )
        with btn_proceed.canvas.before:
            Color(*app.primary_color)
            RoundedRectangle(pos=btn_proceed.pos, size=btn_proceed.size, radius=[10,])
            
        def update_proceed_rect(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*app.primary_color)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10,])
        btn_proceed.bind(pos=update_proceed_rect, size=update_proceed_rect)

        layout.add_widget(btn_proceed)
        
        # Popup Window
        popup = Popup(
            title='', separator_height=0,
            content=layout, size_hint=(None, None), size=(420, 650),
            background = '', # Remove default image
            background_color = (0,0,0,0), # Transparent container
            auto_dismiss=True
        )
        
        def start_analysis(instance):
            # Enforce validation
            if not inp_name.text or not inp_age.text or not inp_weight.text:
                 # Provide visual feedback and STOP
                 btn_proceed.text = "Missing Data!"
                 def reset_text(dt): btn_proceed.text = "Verify & Analyze"
                 from kivy.clock import Clock
                 Clock.schedule_once(reset_text, 1.5)
                 return

            details = {
                'name': inp_name.text,
                'age': inp_age.text,
                'gender': spin_gender.text,
                'weight': inp_weight.text,
                'body_type': self.selected_body_type
            }
            popup.dismiss()
            self._process_manual_text(text_content, details)
            
        btn_proceed.bind(on_release=start_analysis)
        popup.open()
        
    def _process_manual_text(self, text_content, patient_details):
        import threading
        self.ids.results_label.text = "Running Analysis..."
        
        # Switch to Results Screen immediately to show progress? 
        # Actually manual entry stays on same screen or goes to results?
        # Let's verify `_process_manual_text` original behavior.
        # It was just setting label.
        # But for full report, we might want ResultsScreen?
        # Let's stick to updating label and maybe showing popup or saving data.
        
        def run_analysis():
            from core.gemini_client import analyze_text
            from core.drug_client import check_interactions_for_list, extract_potential_drugs
            from core.local_data import db
            from core.database import save_analysis # Import save function
            
            try:
                # 1. Gemini Analysis
                # Pass raw text and patient_details dict directly to analyze_text
                analysis_result = analyze_text(text_content, patient_details)
                
                # 2. Local DDI Check (Optional but good)
                extracted_drugs = extract_potential_drugs(text_content)
                resolved_drugs = []
                for d in extracted_drugs:
                    res, conf = db.resolve_drug_name(d)
                    if conf > 80: resolved_drugs.append(res)
                
                ddi_report = ""
                if resolved_drugs:
                    ddi_report = check_interactions_for_list(resolved_drugs)
                    
                    # Fetch Local Details for each resolved generic
                    for gen_drug in resolved_drugs:
                        local_info = db.get_drug_details_by_generic(gen_drug)
                        if local_info:
                            ddi_report += f"\n\n**Local Data for {gen_drug}:**\n"
                            if local_info['uses']: ddi_report += f"- Uses: {local_info['uses']}\n"
                            if local_info['side_effects']: ddi_report += f"- Side Effects: {local_info['side_effects']}\n"
                            if local_info['brands_sample']: ddi_report += f"- Common Brands: {local_info['brands_sample']}\n"

                # Need helper to clean markdown
                from core.gemini_client import clean_markdown_to_text
                analysis_result_clean = clean_markdown_to_text(analysis_result)

                # Format the output to match image analysis structure
                final_output = f"""Prescription_OCR_Results : 
{text_content}
===============================================================================================
(Accuracy Score: 100% - Manual Entry)
===============================================================================================

Analysis of the prescription image:

{analysis_result_clean}

================================================================================================

Prescription Preview from searching the datasets(datasets from this project directory) and matching the prescription image and say whether they're safe or not:
{ddi_report if ddi_report else "No local data found matching the identified drugs."}
================================================================================================
(Powered by AI Analysis)"""
                
                @mainthread
                def update_ui(result):
                    # For manual entry, maybe we should navigate to ResultsScreen to show full markdown?
                    # Or just show in a popup? 
                    # Navigating to ResultsScreen is better reused.
                    
                    app = App.get_running_app()
                    app.recent_text = result
                    app.recent_image = "Manual Entry"
                    # Update recent_drugs for Graph
                    app.recent_drugs = resolved_drugs
                    
                    # Save to History
                    if hasattr(app, 'username'):
                        save_analysis(app.username, "Manual Entry", result)
                    
                    # Store data in ResultsScreen and switch
                    results_screen = self.manager.get_screen('results')
                    results_screen.ids.result_image.source = '' # No image
                    results_screen.update_ui(result, None, resolved_drugs)
                    self.manager.current = 'results'
                    self.ids.results_label.text = "" # Reset
                    
                update_ui(final_output)

            except Exception as e:
                @mainthread
                def show_error(err):
                    self.ids.results_label.text = f"Error: {err}"
                show_error(str(e))
                
        threading.Thread(target=run_analysis).start()

class KnowledgeGraphScreen(Screen):
    pass

class BootScreen(Screen):
    def on_enter(self):
        from kivy.clock import Clock
        from kivy.app import App
        from kivy.animation import Animation
        
        # Start Spinner Animation
        if 'spinner' in self.ids:
            anim = Animation(angle=-360, duration=2, t='linear') 
            anim.repeat = True
            anim.start(self.ids.spinner)
        
        # Schedule transition to Login Screen
        Clock.schedule_once(lambda dt: self.go_next(), 30)
        
    def go_next(self):
        from kivy.uix.screenmanager import FadeTransition
        self.manager.transition = FadeTransition(duration=1.0)
        self.manager.current = 'login'

class RemindersScreen(Screen):
    breakfast_input = ObjectProperty(None)
    lunch_input = ObjectProperty(None)
    dinner_input = ObjectProperty(None)
    alert_toggle = ObjectProperty(None)
    clock_event = None
    
    def on_pre_enter(self):
        # Load settings from App
        app = App.get_running_app()
        if hasattr(app, 'notification_manager'):
            timings = app.notification_manager.timings
            if self.breakfast_input: self.breakfast_input.text = timings.get('breakfast', '08:00')
            if self.lunch_input: self.lunch_input.text = timings.get('lunch', '13:00')
            if self.dinner_input: self.dinner_input.text = timings.get('dinner', '20:00')
            if self.alert_toggle: self.alert_toggle.active = timings.get('enabled', False)
        
        # Start Clock
        self.update_clock()
        self.clock_event = Clock.schedule_interval(self.update_clock, 1)

    def on_leave(self):
        if self.clock_event:
            self.clock_event.cancel()

    def update_clock(self, dt=None):
        if hasattr(self.ids, 'clock_label'):
             self.ids.clock_label.text = datetime.now().strftime("%H:%M:%S")

    def schedule_demo(self):
        app = App.get_running_app()
        if hasattr(app, 'notification_manager'):
            app.notification_manager.schedule_demo_alert(10)
            
            from kivy.uix.popup import Popup
            content = BoxLayout(padding=10)
            content.add_widget(Label(text="Demo Alert Scheduled in 10 seconds."))
            p = Popup(title='Test Started', content=content, size_hint=(None, None), size=(300, 150), auto_dismiss=True)
            p.open()

    def save_settings(self):
        app = App.get_running_app()
        if hasattr(app, 'notification_manager'):
            app.notification_manager.save_settings(
                self.breakfast_input.text,
                self.lunch_input.text,
                self.dinner_input.text,
                self.alert_toggle.active
            )
            
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            msg = 'Settings Saved!' if self.alert_toggle.active else 'Settings Saved (Alerts Disabled)'
            
            content = BoxLayout(padding=10)
            content.add_widget(Label(text=msg))
            
            p = Popup(title='Saved', content=content, size_hint=(None, None), size=(300, 150), auto_dismiss=True)
            p.open()

