import os
import sys
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from ui.screens import LoginScreen, RegisterScreen, WelcomeScreen, DashboardScreen, ResultsScreen, HomeScreen, AdminDashboard, HistoryScreen, PharmacyLocatorScreen, BenchmarkScreen, ManualEntryScreen, BootScreen, KnowledgeGraphScreen, RemindersScreen

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

from kivy.properties import ListProperty, StringProperty
from kivy.core.window import Window
Window.icon = 'icon.ico'

class RxShieldApp(App):
    # Theme Properties
    bg_color = ListProperty([0.94, 0.97, 1, 1]) # Light Medical Blue
    card_color = ListProperty([1, 1, 1, 1])
    text_color = ListProperty([0, 0, 0, 1])
    primary_color = ListProperty([0.0, 0.6, 0.6, 1]) # Teal
    secondary_color = ListProperty([0.2, 0.5, 0.8, 1]) # Blue
    is_dark_mode = False
    
    # Theme Icon: 🌤️ for Light Mode, 🛌 for Dark Mode (as requested)
    theme_icon = StringProperty('🌤️')

    theme_icon = StringProperty('🌤️')
    
    recent_text = StringProperty("")
    recent_drugs = ListProperty([]) # Track identified drugs
    
    def on_start(self):
        # Initialize KG Manager
        from core.knowledge_graph import KnowledgeGraphManager
        self.kg_manager = KnowledgeGraphManager()
        # Trigger Default Graph
        self.generate_knowledge_graph()
        
        # Initialize Notification Manager
        from core.scheduler import NotificationManager
        self.notification_manager = NotificationManager()
        self.notification_manager.start_service()

        # [PRESENTATION MODE] Open Landing Page
        import webbrowser
        import os
        try:
            # Construct absolute path to the landing page
            landing_page = resource_path(os.path.join('presentation', 'landing.html'))
            if os.path.exists(landing_page):
                webbrowser.open(f'file://{landing_page}')
        except Exception as e:
            print(f"Failed to open presentation page: {e}")

    def generate_knowledge_graph(self, context_text=None, **kwargs):
        """
        Generates the graph based on recent analysis or defaults to universal.
        Returns the path to the generated image.
        """
        # Falls back to universal if empty
        print(f"Generating Knowledge Graph. Context len: {len(context_text) if context_text else 0}")
        path = self.kg_manager.generate_graph(self.recent_drugs, full_text=context_text)
        
        if path:
            try:
                # Update GraphScreen
                if self.root.has_screen('graph'):
                    screen = self.root.get_screen('graph')
                    if hasattr(screen.ids, 'graph_image'):
                        screen.ids.graph_image.source = path
                        screen.ids.graph_image.reload()
                
                # Update ResultsScreen preview
                if self.root.has_screen('results'):
                     res_screen = self.root.get_screen('results')
                     if hasattr(res_screen.ids, 'graph_preview'):
                         # Force refresh logic
                         res_screen.ids.graph_preview.source = ''
                         res_screen.ids.graph_preview.source = path
                         res_screen.ids.graph_preview.reload()
            except Exception as e: 
                print(f"Graph UI Update Error: {e}")
            
        return path



    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.bg_color = [0.12, 0.12, 0.12, 1] # Dark Grey
            self.card_color = [0.18, 0.18, 0.18, 1]
            self.text_color = [0.9, 0.9, 0.9, 1]
            self.primary_color = [0.0, 0.8, 0.8, 1] # Brighter Teal
            self.secondary_color = [0.4, 0.7, 1, 1] # Brighter Blue
            self.theme_icon = '🛌'
        else:
            self.bg_color = [0.94, 0.97, 1, 1]
            self.card_color = [1, 1, 1, 1]
            self.text_color = [0, 0, 0, 1]
            self.primary_color = [0.0, 0.6, 0.6, 1]
            self.secondary_color = [0.2, 0.5, 0.8, 1]
            self.theme_icon = '🌤️'  
            


    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)

    def build(self):
        self.title = 'Rx Shield'
        self.icon = 'icon.ico'
        
        # Load KV
        Builder.load_file(resource_path('ui/rx_shield.kv'))
        
        # Screen Manager
        sm = ScreenManager()
        
        # Add Screens
        sm.add_widget(BootScreen(name='boot')) # First screen = Initial
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(ResultsScreen(name='results'))
        sm.add_widget(AdminDashboard(name='admin_dashboard'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(PharmacyLocatorScreen(name='pharmacy_locator'))
        sm.add_widget(BenchmarkScreen(name='benchmark'))
        sm.add_widget(ManualEntryScreen(name='manual_entry'))
        sm.add_widget(KnowledgeGraphScreen(name='graph'))
        sm.add_widget(RemindersScreen(name='reminders'))
        
        return sm

if __name__ == '__main__':
    RxShieldApp().run()
