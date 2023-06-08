import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.graphics import Line, Color
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.utils import *
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image, AsyncImage
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
import re, threading, time, requests
from datetime import datetime
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange, date2num
import numpy as np
import DB, FoodAPI
from Excercises import Excercises 

Builder.load_string("""
<Widget>
    text_size: self.width, self.height
    font_name: 'Resources/font'
    background_active: 'Resources/white_active.png'
    write_tab: False
    multiline: False
    valign: 'middle'
    halign: 'center'
""")

##^ Overwrites the Main Widget Class in Kivy Lang 

class Label(Label):     #Overwrites the Main Label Class
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.font_name = 'Resources/font'       #Text Font
        self.app = App.get_running_app()        #Gets Reference to Main App Class
        self.color = self.app.col       #Text Colour
        
    def on_size(self,*args):
        self.font_size = self.font_size     #Scales Font Size When Screen is Scaled

class Button(Button):       #Overwrites the Main Button Class
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()        #Gets Reference to Main App Class
        self.text_size = (self.width, self.height)      #Constricts Text to Button Bounding Box
        self.background_down = 'atlas://data/images/defaulttheme/button'        #Removes Default Blue Tint of Kivy Buttons When Pressed
        self.background_color = self.app.col_light      #Sets Themed Background Colour

    def on_size(self,*args):
        self.text_size = (self.width, self.height)
        self.font_size = (self.height*.45)

    def on_press(self,*args):
        self.background_color = self.app.col        #Darkens Background on Press

    def on_release(self,*args):
        self.background_color = self.app.col_light      #Reverts to Normal Colour on Release

class SpinnerButton(SpinnerOption,Button):     #Defines a Button Class for Dropdown Menus
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Spinner(Spinner):     #Defines Dropdown Menu Class
    sync_height = True      #Sets Dropdown Menu Button Height so it Fits Text
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()        #Gets Reference to Main App Class
        self.background_normal = ''     #Sets Background Image to None
        self.background_down = f'Resources/{self.app.theme}/back_active_small.png'      #Sets Pressed Down Background Image 
        self.background_color = (1,1,1.1)  if self.app.theme == 'light' else get_color_from_hex('2a2b2e')       #Sets Themed Background Colour
        self.color = (0,0,0,1) if self.app.theme == 'light' else (1,1,1,1)      #Sets Themed Text Colour 
        
    def on_size(self,*args):
        self.font_size = (self.height*.475)
        
class TitleLabel(Label):        #Defines Screen Title Class
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9,0.2)      #Sets Size of Label Bounding Box Relative to Parent
        self.valign = 'top'     #Aligns the Text With the Top of the Label Box
        self.pos_hint = {'center_x':0.5,'center_y':.89}     #Positions the Label Relative to Parent
        self.font_name = 'Resources/fontbold'

    def on_size(self,*args):
        divisor = len(self.text)//15
        self.font_size = (self.height*(.5-divisor/10))      #Sets Font Size Dependant on Screen Size and Text Length

class RegisterLabel(Label):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.425,0.1)
        self.valign = 'top'
        self.halign = 'center'      #Aligns the Text with the Centre of the Label Box
        self.font_name = 'Resources/fontbold.ttf'

    def on_size(self,*args):
        self.font_size = (self.height*.5)

class RegisterText(TextInput):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.42,0.1)
        self.app = App.get_running_app()
        self.background_normal = ''
        self.hint_text_color = self.app.col     #Sets Colour of Default Text
        self.background_color = (1,1,1,1)  if self.app.theme == 'light' else get_color_from_hex('2a2b2e')
        self.background_active = f'Resources/{self.app.theme}/back_active_small.png'        #Sets Background Image for Label When Focused
        self.foreground_color = (0,0,0,1) if self.app.theme == 'light' else (1,1,1,1)       #Sets Themed Text Colour

    def on_size(self,*args):
        self.font_size = (self.height*.5)

class MeasureTextInput(RegisterText):       #Defines Body Fat Textbox Class
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.04,0.3)
        self.pos_hint = {'center_y':.5}
        self.input_filter = 'float'        #Only Allows Digits and . to be Inputted
        self.hint_text = '?????'        #Textbox Will Show ???? Unless User Inputs Data
        self.hint_text_color = (1,0,0,1) if self.app.theme == 'dark' else get_color_from_hex('7C0A02')

    def insert_text(self, substring, from_undo = False):
        ##This Function is Called When Any Key is Pressed on Textbox
        ##The 'substring' Variable is the Pressed Key
        length = len(self.text)
        if ('.' not in self.text):
            if length == 2:
                substring = '' if (self.text[0:2] == '00' and substring == '0') else substring
                substring = '' if (self.text[0] == '1' and self.text[1] != '0' and substring != '.') else substring
                substring = '' if (self.text[0:2] == '10' and substring != '0') else substring
                substring = '' if (int(self.text[0]) > 1 and substring != '.') else substring
            substring = '' if length >2 else substring       #Restricts Label Text to 3 s.f If It's Not Float          
        if length > 3:      #Restricts Label Text to 2 d.p If It's Float
            substring = ''
        return super(MeasureTextInput, self).insert_text(substring, from_undo=from_undo)        #Once All Conditions Have Been Met, Adds Susbtring Onto Widget Text

class ToggleButton(ToggleButtonBehavior,Button):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        
    def on_release(self,*args):
        widgets = (self.get_widgets(self.group))        #Gets Array of All Widgets In the Same Button Group 
        for i in widgets:
            i.background_color = self.app.col_light     #Resets All Button Backgrounds
        self.background_color = self.app.col if self.state == 'down' else self.app.col_light        #Darken Button If Pressed

class IMGButton(ButtonBehavior,Image):
    def __init__(self, source, x, y, size,**kwargs):
        super().__init__(**kwargs)
        self.source = source        #Sets the Instance Source
        self.keep_ratio = True      #Disallows Stretchng of Image
        self.pos_hint = {'center_x':x,'center_y':y}
        self.size_hint = size

    def on_press(self,*args):
        self.disabled = True        #Disables Button Functionality
        time_delay = threading.Thread(target = self.wait)       #Start Timer on Side Thread
        time_delay.start()
        
    def wait(self):
        time.sleep(1)
        self.disabled = False       #Re-Enables Button Functionailty After 1 Second

class IMGTButton(ToggleButtonBehavior,Image):
    def __init__(self,x, y, size,**kwargs):
        super().__init__(**kwargs)
        self.keep_ratio = True
        self.pos_hint = {'center_x':x,'center_y':y}
        self.size_hint = size

    def on_state(self,*args):
        ##Switches Image on Button Toggle, From Light To Dark And Back
        self.source = self.source.replace('light','dark') if 'light' in self.source else self.source.replace('dark','light')
        
class RedirectButton(Button):       #Defines Button Class That Changes Screen
    def __init__(self,target,direction,**kwargs):
        super().__init__(**kwargs)
        self.target = target
        self.direction = direction
        self.size_hint = (.25,0.08)
        self.validation = False
        self.pos_hint = {'center_x':0.868,'center_y':0.05}
        self.background_color = self.app.col_light

    def on_size(self,*args):
        self.font_size = (self.height*.4)
        
    def on_release(self,*args):
        if self.validation != True:        #If Instance Doesn't Require Further Validation on Click
            self.parent.manager.transition.direction = self.direction       #Defines Transition Direction
            self.parent.manager.current = self.target       #Defines Target Screen To Transition To

class MenuButton(RedirectButton):       #Defines Redirect Button But Bigger
    def __init__(self,target,direction,**kwargs):
        super().__init__(target,direction,**kwargs)
        self.size_hint = (0.4,0.3)

    def on_size(self,*args):
        self.font_size = (self.height*.25)

class DOBInput(RegisterText):       #Defines DOB Entry Class
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.hint_text = 'dd/mm/yyyy:'
    
    def do_backspace(self, from_undo=False, mode='bkspc'):        #When Backspace is Pressed
        if len(self.text)>1:
            if self.text[-1] == '/':        #If the Last Character is /
                self.text = self.text[:-2]      #Remove The Last 2 Characters
                return True        #Indicate That The Backspace Has Been Handled
        return super(DOBInput, self).do_backspace(from_undo, mode)        #Else, Do The Backspace
    
    def insert_text(self, substring, from_undo = False):
        if not re.fullmatch('[0-9]',substring):        #If Substring Is Not Digit
            return super(DOBInput, self).insert_text('', from_undo=from_undo)       #Reject Substring and Break

        length = len(self.text)
        num = int(substring)
        
        substring = '' if (length == 0 and not num<4) else substring
        if length == 1:
            if (self.text.endswith('3') and num>1):
                substring = ''
            elif (self.text.endswith('0') and num ==0):
                substring = ''
            else:
                substring += '/' 
        ##^The Above 3 Lines Ensures That The Text Input Accepts 0-31 Only For First 2 Characters And Appends a /
    
        substring = '' if (length == 3 and num>1) else substring
        if length == 4:
            if ((self.text.endswith('1')) and num >2):
                substring = '' 
            elif (self.text.endswith('0') and num ==0):
                substring = ''
            else:
                substring += '/'
        ##^The Above 8 Lines Ensures That The Text Input Accepts 0-12 Only For 4th and 5th Characters And Appends a /
                
        substring = '' if ((length == 6) and not 0<num<3) else substring
        if length >6:
            if self.text[6] == '1':
                substring = '' if (length == 7 and num !=9) else substring
                substring = '' if (length == 8 and num<7) else substring
            elif self.text[6] == '2':
                substring = '' if (length == 7 and num !=0) else substring
                substring = '' if (length == 8 and num>1) else substring
        ##^The Above 8 Lines Ensures That The Text Input Accepts 1970-2019 Only For 7th-10th Characters
                
        if length > 9:
            substring = ''      #Stops Accepting Characters Once Length Is 9
        return super(DOBInput, self).insert_text(substring, from_undo=from_undo)

class HeightInput(RegisterText):        #Defines Height Entry Class
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        
    def do_backspace(self, from_undo=False, mode='bkspc'):      #When Backspace is Pressed
        if len(self.text)>1:
            if self.text[-1] == "'" or self.text[-1] == '.':        #If The Last Character is ' or .
                self.text = self.text[:-2]        #Remove The Last 2 Characters
                return True        #Indicate That The Backspace Has Been Handled
        return super(HeightInput, self).do_backspace(from_undo, mode)       #Else, Do The Backspace
        
    def insert_text(self, substring, from_undo = False):
        length = len(self.text)        
        if not re.fullmatch('[0-9]',substring):        #If Substring Is Not Digit
            return super(HeightInput, self).insert_text('', from_undo=from_undo)        #Reject Substring and Break

        num = int(substring)        #Gets Integer Value of Substring
        if not self.app.metric:
            if length == 0:
                substring = substring+"'" if 2<num<8 else ''        #Appends ' To Substring If It's The First Character And Between 2 And 8
            elif length ==2:
                substring = substring if num != 0 else ''       #Allows Substring If It's Not 0
            elif length == 3:
                substring = substring if (int(self.text[-1]) == 1 and num<2) else ''      #Allows Substring If Previous Character Was 1 And Substring <2
            substring = substring if length<4 else '' 

        else:
            if substring == '.':
                substring = substring if length==0 else ''        #Only Allows . As Entry If It's First Character
            else:
                num = int(substring)
                if length == 0:
                    substring = substring+ '.' if num<3 else ''        #Allows First Character Between 0 And 3 And Appends . 
            substring = substring if length<4 else ''
        return super(HeightInput, self).insert_text(substring, from_undo=from_undo)


class TableLabel(Label):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.color = (0,0,0,1) if self.app.theme =='light' else (1,1,1,1)
        self.markup = True        #Enables Markup References In Text
        self.multiline = False        #Forces All Text To Be On One Line

    def on_ref_press(self,choice):
        self.app.scrns[5].text_press(choice)
        #Detects When Text Is Pressed And Calls The Appropriate Method From The Excercises Class With Markup Reference As Parameter

    def on_size(self,*args):
        self.font_size = (self.height*.6)

class TableButton(ToggleButton):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.size_hint = (.9,0.075)

    def on_size(self,*args):
        self.font_size = self.height*.35
        
    def on_release(self,*args):
        self.background_color = self.app.col if self.state == 'down' else self.app.col_light
        excercises = self.app.scrns[5].excercises       #Gets Reference to Excercises Class From Excercises Screen

        if self.text in excercises.equip:
            num = f'{excercises.equip[self.text]},'
            excercises.equip_num = excercises.equip_num.replace(num,'') if num in excercises.equip_num else excercises.equip_num+num
        elif self.text in excercises.types:
            num = f'{excercises.types[self.text]},'
            excercises.type_num = excercises.type_num.replace(num,'') if num in excercises.type_num else excercises.type_num+num
        else:
            num = f'{excercises.muscles[self.text]},'
            excercises.muscle_num = excercises.muscle_num.replace(num,'') if num in excercises.muscle_num else excercises.muscle_num+num
            
        ##If The Button Text Is a Key In A Dictionary Then Get The Index And Append ,
        ##Then Check If The Index+, Is Already In A Specific String; If So Then Remove It, Otherwise Add It On
        
class InstructionLabel(TableLabel):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.multiline = True
        
    def on_size(self,*args):
        self.font_size = (Window.height*.03)
        min = Window.height*.15        #Defines Minimum Height
        self.height = len(self.text)*.75 if len(self.text) > min else min       #Sets Label Height With Respect To Text Length But Also A Minimum Value

class WebImage(ButtonBehavior,AsyncImage):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.keep_ratio = True

    def on_release(self,*args):
        big_source = self.source.replace('/m/','/l/')       #On Press, Switches The Source Image
        img = AsyncImage(source = big_source)       #Reloads Image Into Memory
        imgpopup = IMGPopup(img)        #Opens Popup With Big Image
        imgpopup.open()
        
class ImageLayout(RecycleGridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs,cols = 1, default_size=(0,300), default_size_hint=(1, None), size_hint_y=None)
        #Defines Special Grid Layouts, Forcing The Above Attributes 
        self.bind(minimum_height=self._min)
        
    def _min(self, inst, val):
        self.height = val        #Scales Layout Height To Minimum Value Needed
                         
class TableLayout(RecycleGridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs, cols= 2,default_size=(0, 28), default_size_hint=(1, None), size_hint_y=None)
        #Defines Special Grid Layouts, Forcing The Above Attributes
        self.bind(minimum_height=self._min)
        
    def _min(self, inst, val):
        self.height = val        #Scales Layout Height To Minimum Value Needed

class WorkoutLayout(RecycleGridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs, cols= 4,cols_minimum = {0:self.width*3, 1:self.width*.00075, 2:self.width*.00075, 3:self.width*.00075},default_size=(0, 28), default_size_hint=(1, None), size_hint_y=None)
        #Defines Special Grid Layouts, Forcing The Above Attributes 
        self.bind(minimum_height=self._height)
        self.bind(cols_minimum=self._width)
 
    def _width(self,*args):
        self.cols_minimum = {0:self.width*3, 1:self.width*.00075, 2:self.width*.00075, 3:self.width*.00075}
        #Sizes Layout Columns Individually With Respect To Screen Width
        
    def _height(self, inst, val):
        self.height = val        #Scales Layout Height To Minimum Value Needed

class InstructionLayout(RecycleGridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs, cols= 1,default_size=(0, 50), default_size_hint=(1, None), size_hint_y=None)
        #Defines Special Grid Layouts, Forcing The Above Attributes 
        self.bind(minimum_height=self._min)
        
    def _min(self, inst, val):
        self.height = val        #Scales Layout Height To Minimum Value Needed
    
class Scroll(RecycleView):      #Defines Scrolling Widget Class
    def __init__(self,layout,view, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(layout)        #Sets The Layout The Scroll Uses
        self.viewclass = view        #Sets The Widget Class That Layout Uses

class LoginPopup(ModalView):        #Popup That's Called When Login Details Are Incorrect
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.5,0.5)
        self.popup_title = Label(text = 'Wrong details entered',size_hint = (0.9,0.9),pos_hint= {"center_x":0.5,"center_y":0.5})
        self.popup_title.color = [1,1,1,1]
        self.add_widget(self.popup_title)
        
    def on_size(self,*args):
        self.popup_title.font_size = (self.height/5)

class MenuPopup(ModalView):        #Popup That's Called When User Wants To Sign Out
    def __init__(self,parent_widget,**kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.5,0.4)

        self.pwidget = parent_widget
        content = FloatLayout()        #Sub-Layout For All The Widgets Since Popup Widget Only Accepts 1 Widget
        self.popup_title = Label(text = 'Are you sure you want to sign out?',size_hint = (0.9,0.6),pos_hint= {"center_x":0.5,"center_y":0.6},font_size= (self.width/10))
        self.popup_title.color = [1,1,1,1]
        self.yes = Button(size_hint = (0.47,0.2),pos_hint= {"center_x":0.26,"center_y":0.15},text = 'Yes',on_release = self.sign_out)
        self.no = Button(size_hint = (0.47,0.2),pos_hint= {"center_x":0.74,"center_y":0.15},text = 'No',on_release = self.dismiss)
        content.add_widget(self.popup_title)
        content.add_widget(self.yes)
        content.add_widget(self.no) 
        self.add_widget(content)

    def sign_out(self,instance):
        ##Closes The Popup And Switches The Screen
        self.dismiss()
        self.pwidget.manager.transition.direction = 'down'
        self.pwidget.manager.current = 'login'

    def on_size(self,*args):
        self.popup_title.font_size = (self.height/7)

class IMGPopup(ButtonBehavior,ModalView):
    def __init__(self,img,**kwargs):
        super().__init__(**kwargs)
        self.img = img
        self.size_hint = (0.9,0.9)
        self.background = 'Resources/trans.png' if isinstance(img,AsyncImage) else ''
        ##Sets Image Transparent Temporarily If Image Is From Web So It Can Be Loaded 
        self.add_widget(self.img)

    def on_touch_down(self,*args):
        self.dismiss()
        
class FoodPopup(ModalView):
    def __init__(self,name,nutrients,db,**kwargs):
        self.app = App.get_running_app()
        super().__init__(**kwargs)
        self.size_hint = (0.6,0.6)
        self.name = name
        self.nutrients = nutrients
        
        content = FloatLayout()
        self.title = Label(text = self.name.title(),size_hint = (0.9,0.3),pos_hint= {"center_x":0.5,"center_y":0.85})
        self.title.color = [1,1,1,1]

        self.amount = RegisterText(text = '100',input_filter = 'int',on_text_validate = self.calc_values)
        self.amount.size_hint = (0.15,0.1)
        self.amount.pos_hint= {"center_x":0.5,"center_y":0.72}
        self.amount.background_color = (0,0,0,0)
        self.amount.foreground_color = (1,0,0,1)
        self.amount.bind(focus= self.calc_values)       #When The Amount Text Input Is Selected, Call Self.Calc_Values

        self.g = Label(text = 'g',size_hint = (0.05,0.1),pos_hint= {"center_x":0.56,"center_y":0.72})
        self.g.color = [1,1,1,1]

        self.info = Label(text = '',size_hint = (0.9,0.6),pos_hint= {"center_x":0.5,"center_y":0.45})
        self.info.color = [1,1,1,1]
        for x,y in self.nutrients.items():
            self.info.text += (x+': '+str(y)[:7]+'\n')        #Appends Key-Value Pairs Of Nutrition Dict In Fancily Formatted String To Main Text Box
        self.close = Button(text ='Close',size_hint = (0.475,0.11),on_release = self.dismiss)
        self.add = Button(text ='Add to Records',size_hint = (0.475,0.11),pos_hint = {"center_x":0.74,"center_y":0.09},on_release = self.addtodb)
        self.add.color = [1,1,1,1]
        self.close.color = [1,1,1,1]
        if db:      #If Class Is Passed DB Parameter During Instantiation, Add Extra Button For DB CRUD Functionality
            self.close.pos_hint = {"center_x":0.26,"center_y":0.09}
            content.add_widget(self.add)
        else:
            self.close.pos_hint = {"center_x":0.5,"center_y":0.09}

        content.add_widget(self.g)
        content.add_widget(self.amount)
        content.add_widget(self.title)
        content.add_widget(self.info)
        content.add_widget(self.close)
        self.add_widget(content)
        
    def addtodb(self,*args):
        self.calc_values()        #Works Out Amounts Of Nutrients Based On How Much User Enters In Amount Box 
        DB.LogFood(self.app.username,self.final_nutrients)        #Stores Current Food Nutrients In User's DB
        self.dismiss()
        
    def on_size(self,*args):
        self.g.font_size = self.height/16
        self.amount.font_size = self.height/10
        self.close.font_size = (self.height/18)
        self.add.font_size = (self.height/18)
        self.info.font_size = (self.height/14)
        self.title.font_size = (self.height/14)

    def calc_values(self,*args):
        focused = args[1] if len(args)>1 else True        #Works Out If Method Was Called Normally Or Via Widget Callback
        multiplier = int(self.amount.text)/100
        self.final_nutrients = {k: v*multiplier for k,v in self.nutrients.items()}        #Multiplies All Default Nutrient Values By Multiplier For Correct Amount Of Nutrients 
        self.info.text = ''         #Clears Nutrient Label
        for x,y in self.final_nutrients.items():
            self.info.text += (x+': '+str(y)[:7]+'\n')      #Writes New Values To Nutrient Label
        
class NutrientPopup(ModalView):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9,0.8)
        with self.canvas:
            self.divider1=Line(points=[0,0,0,0], width=1)
            self.divider2=Line(points=[0,0,0,0], width=1)
        ##Canvas Instructions To Draw 2 Lines On Screen For Table Seperators
            
        content = FloatLayout()
        self.title = Label(text = 'Nutrient Info',size_hint = (0.9,0.3),pos_hint= {"center_x":0.5,"center_y":0.87})
        self.title.color = [1,1,1,1]

        self.info = Label(text = 'NTR Code          Name            Unit        NTR Code        Name        Unit',size_hint = (1,0.6),pos_hint= {"center_x":0.5,"center_y":0.77})
        self.columns= []
        self.columns.append(Label(text='CA \n ENERC_KCAL \n CHOCDF \n NIA \n CHOLE \n P \n FAMS \n PROCNT \n FAPU \n RIBF \n FASAT \n SUGAR \n FAT \n THIA',size_hint = (0.2,0.8),pos_hint= {"center_x":0.135,"center_y":0.45}))
        self.columns.append(Label(text='Calcium \n Energy \n Carbs \n Niacin (B3) \n Cholesterol \n Phosphorus \n Monounsaturated \n Protein \n Polyunsaturated \n Riboflavin (B2) \n Saturated \n Sugars \n Fat \n Thiamin (B1)',size_hint = (0.2,0.8),pos_hint= {"center_x":0.32,"center_y":0.45}))
        self.columns.append(Label(text='mg \n kcal \n g \n mg \n mg \n mg \n g \n g \n g \n mg \n g \n g \n g \n mg',size_hint = (0.2,0.8),pos_hint= {"center_x":0.475,"center_y":0.45}))
        self.columns.append(Label(text='FATRN \n TOCPHA \n FE \n VITA_RAE \n FIBTG \n VITB12 \n FOLDFE \n VITB6A \n K \n VITC \n MG \n VITD \n NA \n VITK1',size_hint = (0.2,0.8),pos_hint= {"center_x":0.62,"center_y":0.45}))
        self.columns.append(Label(text='Trans \n Vitamin E \n Iron \n Vitamin A \n Fiber \n Vitamin B12 \n Folate (Equivalent) \n Vitamin B6 \n Potassium \n Vitamin C \n Magnesium \n Vitamin D \n Sodium \n Vitamin K',size_hint = (0.3,0.8),pos_hint= {"center_x":0.78,"center_y":0.45}))
        self.columns.append(Label(text='g \n mg \n mg \n æg \n g \n æg \n æg \n mg \n mg \n mg \n mg \n æg \n mg \n æg',size_hint = (0.2,0.8),pos_hint= {"center_x":0.915,"center_y":0.45}))
        ##^Lots Of Label Widgets To Construct A Table Column By Column Once Added To Layout  
        self.info.color = [1,1,1,1]
        
        self.info.font_name = 'Resources/fontbold'
        self.close = Button(text ='Close',size_hint = (0.475,0.11),on_release = self.dismiss)
        self.close.color = [1,1,1,1]
        self.close.pos_hint = {"center_x":0.5,"center_y":0.09}
        
        content.add_widget(self.title)
        content.add_widget(self.info)
        content.add_widget(self.close)
        for i in self.columns:
            i.color = [1,1,1,1]
            content.add_widget(i)
        self.add_widget(content)

    def on_size(self,*args):
        self.divider1.points = [self.width*.59,self.height*.91,self.width*.59,self.height*.3]
        self.divider2.points = [self.width*.12,self.height*.87,self.width,self.height*.87]
        #Sets Co-Ordinates For Lines In Relation To Screen Size
        self.close.font_size = (self.height/18)
        self.info.font_size = (self.height/28)
        self.title.font_size = (self.height/14)
        for i in self.columns:
            i.font_size = (self.height/30)
        
class RegisterPopup(ModalView):        #Popup Called When Account Is Registered/Registration is Attempted
    def __init__(self,error,user,**kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.6,0.6)
        self.errors = Label(multiline = True,size_hint = (0.9,0.9),pos_hint= {"center_x":0.5,"center_y":0.6})
        self.errors.color = [1,1,1,1]
        self.username = Label(size_hint = (0.9,0.6),pos_hint= {"center_x":0.5,"center_y":0.6})
        self.username.color = [1,1,1,1]
        self.content=FloatLayout()
        self.ok = Button(size_hint = (0.94,0.15),pos_hint= {"center_x":0.5,"center_y":0.125},text = 'Ok',on_release = self.dismiss)
        self.val = 0
        if error == True:
            self.val = user.count(None)
            self.size_hint_y = (self.val*.1) if self.val > 4 else 0.65      #Scales Popup Size To Amount Of Errors But With Minimum
            self.errors.text = (self.error_print(user))       #Gets All Erorrs
            self.content.add_widget(self.errors)

        else:
            self.username.text = f'Your username is: {user}'
            self.content.add_widget(self.username)
        #Main Content Will Either Be User's Username or All Form Errors During Registration Process
            
        self.content.add_widget(self.ok)
        self.add_widget(self.content)
        
    @staticmethod
    def error_print(user):
        ##Handles Loading The Relevant Error Messages Depending on Which Text Inputs Have Data That Doesn't Match Certain Criterias
        error_message = ''
        errors = ['Forename must be between 1 and 30 characters long without spaces',
                  'Surname must be between 1 and 30 characters long without spaces',
                  'Password must contain at least 8 characters which must include uppercase, lowercase and numbers',
                  'DOB is invalid',
                  'Weight is invalid',
                  'Height is invalid',
                  'You must choose a body type',
                  'You must choose a gender by selecting one of the figures']
        for i in range(len(user)):
            if user[i] == None:
                error_message += (u'\u2022{} \n').format(errors[i])        #Adds Bullet Point To Each Erorr Message To Be Displayed
        return error_message.rstrip('\n')

    def on_size(self,*args):
        self.ok.font_size = 100
        self.errors.font_size = (self.height/(1+3*self.val)) if self.val>4 else (self.height*.07)       #Scales Popup Font Size To Amount Of Errors But With Minimum
        self.username.font_size = (self.height*.175)

class RefinePopup(ModalView):       #Popup That Allows User To Refine The Excercises Presented To Them On Excercise Screen
    def __init__(self,excercises,**kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.size_hint = (0.6,0.9)
        self.content = FloatLayout()
        self.excercises = excercises

        self.muscle_label = Label(text = 'Muscle Group',size_hint = (0.25,0.15),pos_hint= {"center_x":.2,"center_y":0.925})
        self.muscle_label.color = 1,1,1,1
        self.types_label = Label(text = 'Excercise Type',size_hint = (0.25,0.15),pos_hint= {"center_x":.5,"center_y":0.925})
        self.types_label.color = 1,1,1,1
        self.equip_label = Label(text = 'Equipment',size_hint = (0.25,0.15),pos_hint= {"center_x":.8,"center_y":0.925})
        self.equip_label.color = 1,1,1,1
        
        self.muscle_layout = Scroll(InstructionLayout(spacing = (0,2)),'TableButton',size_hint = (0.3,0.75),pos_hint= {"center_x":.2,"center_y":0.5})
        self.types_layout = Scroll(InstructionLayout(spacing = (0,2)),'TableButton',size_hint = (0.3,0.75),pos_hint= {"center_x":.5,"center_y":0.5})
        self.equip_layout = Scroll(InstructionLayout(spacing = (0,2)),'TableButton',size_hint = (0.3,0.75),pos_hint= {"center_x":.8,"center_y":0.5})
        ##Defines Scrollable Grid Layouts With Buttons As Layout Widgets
        
        self.muscle_layout.data = [{'text': i} for i in self.excercises.muscles.keys()]
        self.types_layout.data = [{'text': i} for i in self.excercises.types.keys()]
        self.equip_layout.data = [{'text': i} for i in self.excercises.equip.keys()]
        ##List Comprehensions To Allocate The Labels For All The Buttons In All The Scroll Layouts
        
        self.ok = Button(size_hint = (0.94,0.075),pos_hint= {"center_x":0.5,"center_y":0.06125},text = 'Apply',on_release = self.apply_choices)

        self.content.add_widget(self.muscle_label)
        self.content.add_widget(self.types_label)
        self.content.add_widget(self.equip_label)
        
        self.content.add_widget(self.muscle_layout)
        self.content.add_widget(self.types_layout)
        self.content.add_widget(self.equip_layout)

        self.content.add_widget(self.ok)
        self.add_widget(self.content)

    def apply_choices(self,*args):
        self.app.scrns[5].generate_list()       #Calls Method Of Excercise Screen When Any Button From The Scroll Layouts Are Pressed
        self.dismiss()
        
    def on_size(self,*args):
        self.muscle_label.font_size = self.height*.04
        self.types_label.font_size = self.height*.04
        self.equip_label.font_size = self.height*.04

class BodyPopup(ModalView):        #Popup That Checks If User Wants To Store Newly Calculated Values From Body Screen
    def __init__(self,username,data,**kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.data = data 
        self.size_hint = (0.5,0.4)

        self.content = FloatLayout()
        self.popup_title = Label(text = 'Do you want to store these new values?',size_hint = (0.9,0.6),pos_hint= {"center_x":0.5,"center_y":0.6},font_size= (self.width/10))
        self.popup_title.color = [1,1,1,1]
        self.yes = Button(size_hint = (0.47,0.2),pos_hint= {"center_x":0.26,"center_y":0.15},text = 'Yes',on_release = self.add_to_db)
        self.no = Button(size_hint = (0.47,0.2),pos_hint= {"center_x":0.74,"center_y":0.15},text = 'No',on_release = self.dismiss)
        self.content.add_widget(self.popup_title)
        self.content.add_widget(self.yes)
        self.content.add_widget(self.no) 
        self.add_widget(self.content)

    def add_to_db(self,*args):
        DB.LogMeasurements(self.username,self.data)        #Updates/Creates User's Record For That Day In DB 
        self.dismiss()
        
    def on_size(self,*args):
        self.popup_title.font_size = (self.height/7)

class RecordPopup(BodyPopup):
    def __init__(self,username,**kwargs):
        super().__init__(username,None,**kwargs)
        self.app = App.get_running_app()
    def add_to_db(self,*args):
        self.app.scrns[-1].update()

class InternetPopup(LoginPopup):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.popup_title.text = 'No Internet Connection - Limited Features'
        
class LoginScreen(Screen):        #One Of The Main Screen Classes, First Screen That The User Sees When Starting The Program
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widget_setup()
        
    def set_initial_focus(self,*args):
        self.username.focus = True
    
    def widget_setup(self):
        self.app = App.get_running_app()
        self.clear_widgets()

        self.icon = Image(source=f'Resources/{self.app.theme}/icon.png',keep_ratio=True, opacity=0.8, size_hint= (0.5,0.5),pos_hint = {'center_x':0.5,'center_y':0.65})
        self.username = RegisterText(pos_hint = {"center_x":0.5,"center_y":0.3}, hint_text= 'Enter Username:',on_text_validate = self.get_text)
        self.username.size_hint = (0.35, 0.09)
        self.password = RegisterText(pos_hint= {"center_x":0.5,"center_y":0.2},hint_text= 'Enter Password:',password= True,on_text_validate = self.get_text)
        self.password.size_hint=(0.35, 0.09)
        if self.app.theme == 'dark':
            self.username.bind(focus= self.focus_reset)
            self.password.bind(focus= self.focus_reset)
        
        self.login_button = RedirectButton(text= 'Log In',target='menu',direction= 'up')
        self.login_button.validation = True
        self.login_button.pos_hint = {"center_x":0.5,"center_y":0.05}
        self.login_button.size_hint = (0.35, 0.08)
        self.login_button.bind(on_release = self.get_text)

        self.theme_toggle = IMGButton(f'Resources/{self.app.theme}/theme_icon.png',0.04,0.055,(0.075,0.075),on_release = self.app.switch_theme)
        self.popup = LoginPopup()
        
        Clock.schedule_once(self.set_initial_focus,.2)
        
        self.create_button = RedirectButton(text= 'Create New Account',target='register',direction= 'left')
    
        self.add_widget(self.username)
        self.add_widget(self.password)
        self.add_widget(self.icon)
        self.add_widget(self.login_button)        
        self.add_widget(self.create_button)
        self.add_widget(self.theme_toggle)

    def on_pre_enter(self):
        self.widget_setup()
        
    def focus_reset(self,input,focus):
        input.background_color = (1,1,1,1) if focus else get_color_from_hex('2a2b2e')    
        
    def get_text(self, instance):
        username = self.username.text if self.username.text else None
        password = self.password.text.encode() if self.password.text else ''.encode()
        redirect = DB.Login(username,password)
        if redirect:
            self.app.update_username(username)
            self.manager.current = 'menu'
            self.manager.transition.direction = 'up'
        else:
            loginthread = threading.Thread(target=self.popup_delay)
            loginthread.start()
            self.popup.open()

    def popup_delay(self,*args):
        time.sleep(1)
        self.popup.dismiss()

class RegisterScreen(Screen):    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widget_setup()

    def metric_switch(self,*args):
        self.app.switch_metric()
        self.userweight.hint_text = 'Enter in kg:' if self.app.metric else 'Enter in lbs'
        self.userheight.hint_text = 'Enter in m' if self.app.metric else 'Enter in ft'
 
    def widget_setup(self):
        self.app= App.get_running_app()
        self.clear_widgets()
        self.add_widget(TitleLabel(text= 'Create New Account'))
        
        self.man = IMGTButton(0.14,0.5,(0.25,0.6))
        self.man.source = f'Resources/{self.app.theme}/m.png'
        self.man.group = 'gender'
        self.woman = IMGTButton(0.86, 0.5,(0.25,0.6))
        self.woman.source = f'Resources/{self.app.theme}/f.png'
        self.woman.group = 'gender'
        
        self.redirect_button = RedirectButton(text= 'Return To Login',target = 'login',direction = 'right')
        self.register_button = RedirectButton(text = 'Create Account',target = 'menu',direction = 'up')

        self.register_button.validation = True
        self.register_button.pos_hint = {'center_x':0.5,'center_y':0.05}
        self.register_button.size_hint = (0.35, 0.08)
        self.register_button.bind(on_release = self.gettext)
        
        self.inner_layout = StackLayout(size_hint=(0.6,0.8),pos_hint= {"center_x":0.525,"center_y":0.4},spacing=(0,10),orientation= ("lr-tb"))
        
        self.fname=RegisterText(hint_text= 'Enter Forename:')
        self.sname=RegisterText(hint_text= 'Enter Surname:')
        self.pword=RegisterText(hint_text= 'Enter Password:')
        self.dob=DOBInput()

        self.userweight = RegisterText(hint_text= 'Enter in kg:',input_filter = 'float')
        self.userheight = HeightInput(hint_text= 'Enter in m:')
        
        self.metric_toggle = IMGButton(f'Resources/{self.app.theme}/metric_icon.png',0.04,0.055,(0.15,0.15))
        self.metric_toggle.bind(on_release = self.metric_switch)
        self.add_widget(self.metric_toggle)
        
        self.inputs = {"Forename":self.fname,"Surname":self.sname,"Password":self.pword,"DOB":self.dob,"Weight":self.userweight,"Height":self.userheight}
        for x,y in self.inputs.items():
            self.inner_layout.add_widget(RegisterLabel(text= x))
            self.inner_layout.add_widget(y)
            if self.app.theme == 'dark':
                y.bind(focus= self.focus_reset)

        self.pword.bind(focus= self.pword_focus)
            
        self.inner_layout.add_widget(RegisterLabel(text="Body Type"))
        self.btype = Spinner(text=" Select:",halign = 'left', values= [" Ectomorph", " Mesomorph", " Endomorph"," Don't Know"], size_hint= (.42, .1),font_size = (self.height*.1))
        self.btype.option_cls = 'SpinnerButton'
        if self.app.theme == 'dark':
            self.btype.bind(state  = self.focus_reset )
        self.inner_layout.add_widget(self.btype)
        
        self.add_widget(self.woman)
        self.add_widget(self.man)
        self.add_widget(self.inner_layout)
        self.add_widget(self.redirect_button)
        self.add_widget(self.register_button)
    
    def on_pre_enter(self):
        self.widget_setup()

    def pword_focus(self,input,focus):
        input.password = False if focus else True 
        if self.app.theme == 'dark':
            self.focus_reset(input,focus)
            
    def focus_reset(self,input,focus):
        if (focus== 'down'):
            input.background_color = (1,1,1,1)
        elif focus == 'normal':
            input.background_color = get_color_from_hex('2a2b2e')
        elif focus:
            input.background_color = (1,1,1,1)
        else:
            input.background_color = get_color_from_hex('2a2b2e')            
        
    def gettext(self,instance):
        instance.background_color = self.app.col_light
        
        user = [None]*8
        errors = ['Forename must be between 1 and 30 characters long without spaces',
                  'Surname must be between 1 and 30 characters long without spaces',
                  'Password must contain at least 8 characters which must include uppercase, lowercase and numbers',
                  'Date is invalid',
                  'Weight is invalid',
                  'Height is invalid',
                  'You must choose a body type',
                  'You must choose a gender by selecting one of the figures']

        if (self.man.state == 'down'): user[7] = 'M' 
        if (self.woman.state == 'down'): user[7] = 'F' 
  
        passcheck = re.compile("^(.{0,7}|[^0-9]*|[^A-Z]*|[^a-z]*)$")
        
        if 1<(len(self.fname.text))<30:
            user[0] = (''.join(self.fname.text.strip(''))).title()

        if 1<(len(self.sname.text))<30:
            user[1] = (''.join(self.sname.text.strip(''))).title()
            
        if not (passcheck.search(self.pword.text)):
            user[2] = ''.join(self.pword.text.strip(''))
        try:
            dob = datetime.strptime((self.dob.text),'%d/%m/%Y')
            user[3] = (dob.date())
        except:
            pass

        if  (len(self.userweight.text)) > 0:
            if self.app.metric:
                user[4] = float(self.userweight.text) if  20<(float(self.userweight.text)) < 300 else None
            else:
                user[4] = float(self.userweight.text)/2.205 if  44<(float(self.userweight.text)) < 660 else None
                
        if  (len(self.userheight.text)) > 0:
            if self.app.metric:
                user[5] = float(self.userheight.text) if 0<float(self.userheight.text)<3 else None
            else:
                height = list(map(float,(self.userheight.text).split('"')))
                inchify = lambda x,y : x*12 + y
                meters = (inchify(height[0],height[1]))/39.37
                user[5] = meters if 0<meters<3 else None 
                
        if self.btype.text != (' Select:'):
            user[6] = (self.btype.text).strip(' ')
        if None in user:
            self.popup = RegisterPopup(True,user)
            self.popup.open()
        else:
            user[0] = ' '.join([user[0],user[1]])
            user[1] = (user[0][0]+user[1][:3]+user[3].strftime("%y"))
            username = DB.Register(user)
            self.popup = RegisterPopup(False,username)
            self.popup.open()
            self.app.update_username(username)
            self.manager.transition.direction = 'up'
            self.manager.current = 'menu'


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            page = requests.get('http://google.com')
            self.internet = True
        except:
            self.internet = False
            self.internet_popup =InternetPopup()
        self.widget_setup()

    def on_pre_enter(self):
        self.widget_setup()
        try:
            if not self.internet:
                self.internet_popup.open()
                del self.internet_popup
        except:pass

    def widget_setup(self):
        self.app = App.get_running_app()
        self.clear_widgets()

        self.add_widget(TitleLabel(text= 'Main Menu'))

        food = MenuButton('foodtracker','right',text='Food Tracker')
        food.pos_hint={"center_x":0.26,"center_y":0.7}
        food.validation = True if not self.internet else False

        graph = MenuButton('graphs','left',text='Graphs')
        graph.pos_hint={"center_x":0.73,"center_y":0.7}

        workout = MenuButton('workouts','right',text='Workouts',)
        workout.pos_hint={"center_x":0.26,"center_y":0.3}
        workout.validation = True if not self.internet else False

        body = MenuButton('body', 'left',text='Body Composition')
        body.pos_hint={"center_x":0.73,"center_y":0.3}

        record = MenuButton('record','up', text = 'Record Data')
        record.pos_hint = {'center_x':0.5,'center_y':0.075}
        record.size_hint = (0.3,0.13)

        self.popup = MenuPopup(self)

        sign = RedirectButton('login','down',text='Sign Out')
        sign.validation = True
        sign.bind(on_release = self.popup.open)

        self.theme_toggle = IMGButton(f'Resources/{self.app.theme}/theme_icon.png',0.04,0.055,(0.075,0.075),on_release = self.app.switch_theme)

        self.add_widget(self.theme_toggle)
        self.add_widget(food)
        self.add_widget(graph)
        self.add_widget(workout)
        self.add_widget(sign)
        self.add_widget(body)
        self.add_widget(record)


class RecordScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widget_setup()

    def on_pre_enter(self):
        self.widget_setup()
        
    def widget_setup(self):
        self.app = App.get_running_app()
        self.clear_widgets()
        self.saved = False

        self.inner_layout = StackLayout(size_hint=(0.5,0.8),pos_hint= {"center_x":0.55,"center_y":0.475},spacing=(0,10),orientation= ("lr-tb"))
        
        self.cals_in=RegisterText(hint_text= 'Calories In:')
        self.cals_out=RegisterText(hint_text= 'Calories Out:')
        self.prot=RegisterText(hint_text= 'Protein (g):')
        self.carbs=RegisterText(hint_text= 'Carbs (g):')
        self.weight=RegisterText(hint_text= 'Weight (kg):')
        self.fat=MeasureTextInput()
        self.fat.hint_text= 'Body Fat (%):'
        self.fat.hint_text_color = self.app.col

        self.inputs= [self.cals_in,self.cals_out,self.prot,self.carbs,self.weight,self.fat]
        for i in self.inputs:
            i.bind(text = self.text_change)
            i.input_filter = 'float'
            i.size_hint = (.8,0.145)
            self.inner_layout.add_widget(i)
            if self.app.theme == 'dark':
                i.bind(focus= self.focus_reset)
                
        self.add_widget(self.inner_layout)

        self.add_button = RedirectButton(text= 'Save',target= None, direction = None)
        self.add_button.validation = True
        self.add_button.bind(on_release = self.on_release)
        self.add_button.pos_hint['center_x'] = 0.5
        
        self.add_widget(self.add_button)
        self.add_widget(TitleLabel(text= 'Record Data'))
        self.redirect_button = RedirectButton(text= 'Return To Menu',target= 'menu', direction = 'down')
        self.redirect_button.validation = True
        self.redirect_button.bind(on_release = self.on_release)
        self.add_widget(self.redirect_button)

    def focus_reset(self,input,focus):
        input.background_color = (1,1,1,1) if focus else get_color_from_hex('2a2b2e')            

    def text_change(self,*args):
        self.saved = False

    def on_release(self,button):
        button.background_color = self.app.col_light
        self.popup = RecordPopup(self.app.username)
        if button.target == 'menu':
            if self.saved != True:
                self.popup.open()
            self.manager.transition.direction = button.direction
            self.manager.current = button.target
        else:
            if self.saved != True:
                self.update()
            self.saved = True
            
    def update(self,*args):
        self.popup.dismiss()
        data = [float(i.text) if len(i.text) >0 else 0 for i in self.inputs]
        if len(set(data))>1:
            DB.RecordData(self.app.username,data)
        for i in self.inputs:
            i.text = ''
        
class FoodTrackerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.page_number = 0
        self.nutrients = {'CA': ['Calcium', 'mg'], 'ENERC_KCAL': ['Energy', 'kcal'], 'CHOCDF': ['Carbs', 'g'], 'NIA': ['Niacin (B3)', 'mg'], 'CHOLE': ['Cholesterol', 'mg'], 'P': ['Phosphorus', 'mg'], 'FAMS': ['Monounsaturated', 'g'], 'PROCNT': ['Protein', 'g'], 'FAPU': ['Polyunsaturated', 'g'], 'RIBF': ['Riboflavin (B2)', 'mg'], 'FASAT': ['Saturated', 'g'], 'SUGAR': ['Sugars', 'g'], 'FAT': ['Fat', 'g'], 'THIA': ['Thiamin (B1)', 'mg'], 'FATRN': ['Trans', 'g'], 'TOCPHA': ['Vitamin E', 'mg'], 'FE': ['Iron', 'mg'], 'VITA_RAE': ['Vitamin A', 'æg'], 'FIBTG': ['Fiber', 'g'], 'VITB12': ['Vitamin B12', 'æg'], 'FOLDFE': ['Folate (Equivalent)', 'æg'], 'VITB6A': ['Vitamin B6', 'mg'], 'K': ['Potassium', 'mg'], 'VITC': ['Vitamin C', 'mg'], 'MG': ['Magnesium', 'mg'], 'VITD': ['Vitamin D', 'æg'], 'NA': ['Sodium', 'mg'], 'VITK1': ['Vitamin K', 'æg']}
        self.widget_setup()
    
    def on_pre_enter(self):
        self.widget_setup()

    def on_size(self,*args):
        for kids in list(self.children):
            if isinstance(kids, StackLayout):
                self.help_label.font_size = (self.height/35)
                self.food_textl.font_size = (self.height/35)
                self.food_textr.font_size = (self.height/35)

        self.page.font_size = (self.height/30)
        self.serving_text.font_size = (self.height/25)

    def focus_reset(self,input,focus):
        if focus:
            input.background_color = (1,1,1,1)
        else:
            input.background_color = get_color_from_hex('2a2b2e')

    def pagechange(self,button):
        current = int(self.page.text)
        direction = button.direction
        invalid_query = False
        if (self.items == 0 and self.page_number == 0):
            invalid_query = True
        self.page_number = 0 if (current + direction) <0 or invalid_query == True else (current + direction)
        self.food_submit(None)

    def info_popup(self,*args):
        self.popup = NutrientPopup()
        self.popup.open()
        
    def widget_setup(self):
        self.app = App.get_running_app()
        self.clear_widgets()
        self.add_widget(TitleLabel(text= 'Food Tracker'))
        
        self.redirect_button = RedirectButton(text= 'Return To Menu',target= 'menu', direction = 'left')
        self.search_food = Button(size_hint = (0.6,0.25),pos_hint = {"center_x":0.5,"center_y":0.35},text= 'Search Foods',on_release= self.food_lookup)
        self.add_food = Button(size_hint = (0.6,0.25),pos_hint = {"center_x":0.5,"center_y":0.65},text= 'Update Foods',on_release= self.food_lookup)
        self.serving_text = (Label(text = 'All food data is given in reference to a 100g serving',size_hint = (0.5,0.2),pos_hint={"center_x":0.5,"center_y":0.175},font_size = (self.height/25)))

        self.info_button = RedirectButton(text = 'Help',target = None,direction = None)

        self.info_button.validation = True
        self.info_button.pos_hint = {'center_x': 0.132,'center_y':0.05}
        self.info_button.bind(on_release = self.info_popup)

        self.page = Label(text='0',size_hint = (0.2,0.1),pos_hint = {"center_x":0.5,"center_y":0.05})
        self.left_butt = IMGButton(f'Resources/{self.app.theme}/left.png',0.45,0.05,(0.1,0.1),on_release = self.pagechange)
        self.left_butt.direction = -1
        self.right_butt = IMGButton(f'Resources/{self.app.theme}/right.png',0.55,0.05,(0.1,0.1),on_release = self.pagechange)
        self.right_butt.direction = +1
        self.loading = Image(source =f'Resources/{self.app.theme}/loading.gif',pos_hint = {"center_x":0.5,"center_y":0.4},size_hint= (0.5,0.5),anim_delay = 0)
        
        self.add_widget(self.redirect_button)
        self.add_widget(self.add_food)
        self.add_widget(self.search_food)
        self.add_widget(self.serving_text)
        self.add_widget(self.info_button)
        
    def food_lookup(self,instance):
        self.search = True if instance.text == 'Search Foods' else False
        self.remove_widget(self.serving_text)
        self.remove_widget(self.search_food)
        self.remove_widget(self.add_food)
        
        self.search_layout = StackLayout(orientation = 'lr-tb',size_hint = (0.95,0.9))
        self.search_layout.pos_hint = {"center_x":0.5,"center_y":0.4}

        self.search_box = RegisterText(hint_text = 'Enter Food Name / UPC Number: ',on_text_validate = self.food_submit)
        self.search_box.size_hint = (0.8,0.1)
        if self.app.theme == 'dark':
            self.search_box.bind(focus = self.focus_reset)
        self.search_button = Button(text = 'Submit',size_hint = (0.2,0.1), on_release = self.food_submit)
        self.help_label = Label(size_hint = (1,0.1),font_size = (self.height/35),opacity = 0)
        self.food_textl = Label(text='',size_hint = (0.45,0.6),font_size = (self.height/35),line_height = 1.5,markup = True,on_ref_press=self.choose_food)
        self.food_textr = Label(text='',size_hint = (0.45,0.6),font_size = (self.height/35),line_height = 1.5,markup = True,on_ref_press=self.choose_food)

        self.search_layout = StackLayout(orientation = 'lr-tb',size_hint = (0.95,0.9))
        self.search_layout.pos_hint = {"center_x":0.5,"center_y":0.4}

        self.search_layout.add_widget(self.search_box)
        self.search_layout.add_widget(self.search_button)
        self.search_layout.add_widget(self.help_label)
        self.search_layout.add_widget(self.food_textl)
        self.search_layout.add_widget(self.food_textr)
        
        self.add_widget(self.left_butt)
        self.add_widget(self.right_butt)
        self.add_widget(self.page)
        self.add_widget(self.search_layout)
        
    def choose_food(self,instance,value):
        if self.search:
            self.popup = FoodPopup(self.foods.names[int(value)],self.foods.nutrients[int(value)],False)
        else:
            self.popup = FoodPopup(self.foods.names[int(value)],self.foods.nutrients[int(value)],True)
        self.popup.open()

    def food_add(self,*args):
        self.query = self.search_box.text.replace(' ','%20')
        self.foods = FoodAPI.FoodAPI(self.query,self.page_number)
        self.items = len(self.foods.names)
        if self.items == 0:
            if self.foods.internet == False:
                self.help_label.text = "Sorry, you're not connected to the Internet"
            else:
                self.help_label.text = 'Sorry, no results were found'
        else:
            self.help_label.text = 'Multiple results were found, please click the most accurate one '
            self.help_label.text += 'for more info' if self.search else 'to add to your records'
     
        if self.items == 1:
            self.help_label.opacity = 0
        for i in range(self.items):
            food_item = (self.foods.names[i][:35].title()+ '...') if len(self.foods.names[i]) >35 else self.foods.names[i].title()
            if i <int((self.items+1)/2):
                self.food_textl.text += ('\n [ref={}]'+food_item+'[/ref]').format(i)
            else:
                self.food_textr.text += ('\n [ref={}]'+food_item+'[/ref]').format(i)
        self.food_textl.text = self.food_textl.text.lstrip('\n')
        self.food_textr.text = self.food_textr.text.lstrip('\n')
        self.remove_widget(self.loading)
                
    def food_submit(self,instance,*args):
        self.page_number = 0 if instance != None else self.page_number
        self.page.text = str(self.page_number)
        self.food_textl.text = ''
        self.food_textr.text = ''
        self.help_label.opacity = 1
        try:
            self.add_widget(self.loading)
        except:
            pass
        foodthread = threading.Thread(target=self.food_add)
        foodthread.start()
        
class GraphScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widget_setup()
        self.units = {'Calories In':'kcal','Calories Out':'kcal','Protein':'g','Carbs':'g','Fat':'g','Weight':'kg','Body Fat':'%'}
            
    def on_pre_enter(self):
        self.widget_setup()

    def widget_setup(self):
        self.app = App.get_running_app()
        self.clear_widgets()
        self.canvas.clear()
        self.table_show = False
        if self.app.theme == 'light':
            with self.canvas:
                Color(0,0,0,1)
                self.divider = Line(points=[0,0,0,0], width=1)
        else:
            with self.canvas:
                Color(1,1,1,1)
                self.divider = Line(points=[0,0,0,0], width=1)
        self.add_widget(TitleLabel(text= 'Graphs'))    
        redirect_button = RedirectButton(text= 'Return To Menu',target= 'menu', direction = 'right')
        self.button_row = StackLayout(size_hint=(.98,0.15),pos_hint= {"center_x":0.5,"center_y":0.775},spacing=(1,0),orientation= ("lr-tb"))
        graph_options = ['Calories In','Calories Out','Protein','Carbs','Fat','Weight','Body Fat']
        for i in graph_options:
            self.button_row.add_widget(ToggleButton(text = i,group='graph',size_hint =(1/7,.45),on_release = self.buttonpress))

        self.graph_layout = FloatLayout(size_hint = (0.75,0.75))
        self.add_widget(self.graph_layout)
            
        self.table = Scroll(TableLayout(),'TableLabel',size_hint = (0.275,0.62),pos_hint = {'center_x':0.86,'center_y':0.42})
        
        self.add_widget(self.table)
        self.add_widget(self.button_row)
        self.add_widget(redirect_button)

    def on_size(self,*args):
        self.divider.points = [self.width*.86,self.height*.73,self.width*.86,self.height*.1] if self.table_show else [0,0,0,0]

    def draw_graph(self,button):
        self.graph_layout.size_hint = (0.8,0.75) if button.text == 'Body Fat' else (0.75,0.75)
        self.graph_layout.clear_widgets()
        fig, ax = plt.subplots()
        try:
            ax.plot_date(self.graph_data[0],self.graph_data[1],color = self.app.col,linestyle='dashdot')
            plt.ylabel(f'{button.text} ({self.units[button.text]})',labelpad =5)
            ax.xaxis.set_major_locator(DayLocator())
            ax.xaxis.set_minor_locator(HourLocator(np.arange(0, 25, 6)))
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))

            ax.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
            fig.autofmt_xdate()
            if self.app.theme == 'light':
                fig.set_facecolor('white')
                ax.set_facecolor('white')
            else:
                for i in ax.spines:
                    ax.spines[i].set_color(self.app.col)
                ax.xaxis.label.set_color(self.app.col)
                ax.tick_params(axis='x', colors=self.app.col)
                ax.yaxis.label.set_color(self.app.col)
                ax.tick_params(axis='y', colors=self.app.col)
                fig.set_facecolor('#2a2b2e')
                ax.set_facecolor('#2a2b2e')
            graph = FigureCanvasKivyAgg(plt.gcf())
            self.graph_layout.add_widget(graph)
        except:
            pass

    def buttonpress(self,button,*args):
        self.table_show = True
        self.on_size()
        column = 'Cals' if button.text.startswith('Calories') else button.text 
        self.results = DB.GraphSelect(self.app.username,button.text.upper())
        self.table.data = [{'text':'Date'},{'text':f'{column} ({self.units[button.text]})'},{'text':'_'*100},{'text':'_'*100}]
        self.graph_data = [[],[]]
        for x,y in self.results.items():
            self.graph_data[0].append(x)
            self.graph_data[1].append(y)
            rounded_y = ("%.4f" % float(y))
            try:
                self.table.data += [{'text':f'{x}'},{'text':f'{rounded_y}'}]
            except:
                pass
        self.draw_graph(button)

class ExcerciseScreen(Screen):
    def __init__(self,choice, excercises,**kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.choice = choice
        self.excercises = excercises
        self.title = TitleLabel(text= choice)
        self.add_widget(self.title)
        self.add_widget(RedirectButton(text= 'Return To Workouts',target= 'workouts', direction = 'down'))
        self.loading = Image(source =f'Resources/{self.app.theme}/loading.gif',pos_hint = {"center_x":0.5,"center_y":0.4},size_hint= (0.5,0.5),anim_delay = 0)

    def on_pre_enter(self,*args):
        self.add_widget(self.loading)
        contentThread = threading.Thread(target=self.get_content)
        contentThread.start()

    def on_size(self,*args):
        try:
            self.type_label.font_size = self.height*.03
            self.muscle_label.font_size = self.height*.03
            self.equipment_label.font_size = self.height*.03
            self.level_label.font_size = self.height*.03
        except:pass

    def images_load(self,*args):
        images_thread = threading.Thread(target = self.images_get)
        self.remove_widget(self.load_images)
        self.add_widget(self.loading)
        images_thread.start()

    def images_get(self):
        self.images = Scroll(ImageLayout(),'WebImage',size_hint = (0.4,0.5),pos_hint = {'center_x':0.225,'center_y':0.3})
        self.images.data = [{'source':i} for i in self.excercises.images_url]
        self.add_widget(self.images)
        self.remove_widget(self.loading)
        
    def get_content(self,*args):
        self.excercises.Choose()
        self.steps = Scroll(InstructionLayout(spacing = -20),'InstructionLabel',size_hint = (0.5,0.7),pos_hint = {'center_x':0.7,'center_y':0.5})
        self.steps.data = [{'text':'[font=Resources/fontbold]Steps:[/font]'}]+[{'text':i} for i in self.excercises.instruction_list]
        self.add_widget(self.steps)
    
        self.type_label = Label(text = f'[font=Resources/fontbold]Excercise Type:[/font]  {self.excercises.info_list[0]}',size_hint = (0.5,0.05), pos_hint = {'center_x':.275,'center_y':.815},halign = 'left',markup = True)
        self.muscle_label = Label(text = f'[font=Resources/fontbold]Main Muscle Group:[/font]  {self.excercises.info_list[1]}',size_hint = (0.5,0.05), pos_hint = {'center_x':.275,'center_y':.74},halign = 'left',markup = True)
        self.equipment_label = Label(text = f'[font=Resources/fontbold]Equipment:[/font]  {self.excercises.info_list[2]}',size_hint = (0.5,0.05), pos_hint = {'center_x':.275,'center_y':.665},halign = 'left',markup = True)
        self.level_label = Label(text = f'[font=Resources/fontbold]Level:[/font]  {self.excercises.info_list[3]}',size_hint = (0.5,0.05), pos_hint = {'center_x':.275,'center_y':.59},halign = 'left',markup = True)

        self.load_images = Button(text = 'Load Images', size_hint = (0.3,0.1), pos_hint = {'center_x':.2,'center_y':.33},on_release = self.images_load)
        self.add_widget(self.load_images)
        self.add_widget(self.type_label)
        self.add_widget(self.muscle_label)
        self.add_widget(self.equipment_label)
        self.add_widget(self.level_label)
        
        self.on_size()
        self.remove_widget(self.loading)
        
class WorkoutsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.widget_setup()

    def on_pre_enter(self,*args):
        self.page_number = 1
        try:
            self.app.sm.remove_widget(self.workout_page)
            del self.workout_page
        except:
            self.widget_setup()
            self.add_widget(self.loading)
            self.listthread = threading.Thread(target=self.generate_list)
            self.listthread.start()

    def focus_reset(self,input,focus):
        if (focus== 'down'):
            input.background_color = (1,1,1,1)
        elif focus == 'normal':
            input.background_color = get_color_from_hex('2a2b2e')
        elif focus:
            input.background_color = (1,1,1,1)
        else:
            input.background_color = get_color_from_hex('2a2b2e')
            
    def text_press(self,choice):
        if choice[0] != '0':
            self.choice = choice
            self.excercises.Refine(self.choice)
            refinethread = threading.Thread(target= self.generate_list)
            refinethread.start()
            try:
                self.add_widget(self.loading)
            except:pass
        else:
            self.excercises.url_extension = self.excercises.url_dict[choice[1:]]
            self.workout_page = ExcerciseScreen(choice[1:],self.excercises,name= 'excercise')
            self.app.sm.add_widget(self.workout_page)

            self.manager.current = 'excercise'
            self.manager.transition.direction = 'up'
            
    def generate_list(self,*args):
        self.table.data = self.table.data[:8]
        self.excercises.Search(self.query) if self.search else self.excercises.GetList() 
        for i in self.excercises.final_list:
            for count,value in enumerate(i):
                if count % 4 != 3:
                    self.table.data.append({'text':f'[ref={count%4}{value}]{value}[/ref]'})
                else:
                    self.table.data.append({'text':f'{value}'})
        self.items = len(self.excercises.final_list)
        self.remove_widget(self.loading)
        
    def page_change(self,button):
        current = int(self.page.text)
        direction = button.direction
        invalid_query = False
        if (self.items == 0 and self.page_number == 1):
            invalid_query = True
        self.page_number = 1 if (current + direction) <1 or invalid_query == True else (current + direction)
        self.excercises.ChangePage(self.page_number)
        self.listthread = threading.Thread(target=self.generate_list)
        self.listthread.start()
        try:self.add_widget(self.loading)
        except:pass
        self.page.text = str(self.page_number)

    def search_excercise(self,*args):
        try:self.add_widget(self.loading)
        except:pass
        if len(self.search_box.text) > 1:
            self.search = True
            self.query = self.search_box.text
            self.listthread = threading.Thread(target=self.generate_list)
            self.listthread.start()
            try:
                self.remove_widget(self.left_butt)
                self.remove_widget(self.right_butt)
                self.remove_widget(self.page)
            except:pass
        else:
            self.widget_setup()
            self.add_widget(self.loading)
            self.listthread = threading.Thread(target=self.generate_list)
            self.listthread.start()
            
    def widget_setup(self):
        self.search = False
        self.clear_widgets()
        self.add_widget(TitleLabel(text= 'Workouts'))
        self.excercises = Excercises()

        self.table = Scroll(WorkoutLayout(),'TableLabel',size_hint = (0.90,0.62),pos_hint = {'center_x':0.5,'center_y':0.425})
        self.table.data = [{'text':'Name'},{'text':'Muscle'},{'text':'Equipment'},{'text':'Rating'},{'text':'_'*500},{'text':'_'*100},{'text':'_'*100},{'text':'_'*100}]
        self.add_widget(self.table)

        self.page = Label(text='1',size_hint = (0.2,0.1),pos_hint = {"center_x":0.5,"center_y":0.05})
        self.left_butt = IMGButton(f'Resources/{self.app.theme}/left.png',0.45,0.05,(0.1,0.1),on_release = self.page_change)
        self.left_butt.direction = -1
        self.right_butt = IMGButton(f'Resources/{self.app.theme}/right.png',0.55,0.05,(0.1,0.1),on_release = self.page_change)
        self.right_butt.direction = +1
        self.loading = Image(source =f'Resources/{self.app.theme}/loading.gif',pos_hint = {"center_x":0.5,"center_y":0.4},size_hint= (0.5,0.5),anim_delay = 0)

        self.search_layout = StackLayout(orientation = 'lr-tb',size_hint = (0.9,0.9))
        self.search_layout.pos_hint = {"center_x":0.5,"center_y":0.4}

        self.search_box = RegisterText(hint_text = 'Search Excercises:',on_text_validate = self.search_excercise)
        self.search_box.size_hint = (0.6,0.1)
        if self.app.theme == 'dark':
            self.search_box.bind(focus = self.focus_reset)
            
        self.refine_popup = RefinePopup(self.excercises)
        self.search_button = Button(text = 'Submit',size_hint = (0.2,0.1), on_release = self.search_excercise)
        self.filter_button = Button(text = 'Filter',size_hint = (0.2,0.1),on_release = self.refine_popup.open)
        
        self.search_layout.add_widget(self.search_box)
        self.search_layout.add_widget(self.filter_button)
        self.search_layout.add_widget(self.search_button)
        
        self.add_widget(self.search_layout)
        self.add_widget(self.page)
        self.add_widget(self.left_butt)
        self.add_widget(self.right_butt)
        redirect_button = RedirectButton(text= 'Return To Menu',target= 'menu', direction = 'left')
        self.add_widget(redirect_button)

class BodyScreen(Screen):       #Body Stats Screen Class
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()        #Gets Reference To Main App Class and Associated Atributes and Methods

    def on_pre_enter(self):     #This Ensures the Screen is Refreshed On Every Entry
        self.default_data = DB.GetMeasurements(self.app.username)       #Gets User's Last Recorded Body Measurements
        self.widget_setup()     #Sets Up All Screen Widgets

    def on_pre_leave(self):
        try:
            self.db_popup = BodyPopup(self.app.username,self.new_data)      #Opens a Popup to Ensure User Wants to Save Data Before Leaving
            self.db_popup.open()
        except:pass

    def on_size(self,*args):
        self.divider1.points = [self.width*.66,self.height*.5,self.width*.66,self.height*.15] if self.macros_show else [0,0,0,0]        #Sets the New Co-ordinates for the Table Lines
        self.divider2.points = [self.width*.81,self.height*.5,self.width*.81,self.height*.15] if self.macros_show else [0,0,0,0]
        
        for i in self.info_row.children:        #Defines Font Sizes for the Widgets in the Main Info Row
            if isinstance(i,TextInput):
                i.font_size = self.height*.025
            elif isinstance(i,Spinner):
                i.font_size = self.height*.02375
            else:
                i.font_size = self.height*.026
        for i in self.table.children:       #Defines Font Sizes for the Widgets in the Table
            i.font_size = self.height*.027
        for i in self.button_row.children:      #Defines Font Sizes for the Macro Buttons
            i.font_size = self.height*.027

        ## Sets Font Sizes for all Other Widgets on Screen 

        self.tdee_box.font_size = self.height*.04
        self.twee_box.font_size = self.height*.04
        self.bmi_box.font_size = self.height*.04

        self.calories_label.font_size = self.height*.025
        self.weekly_label.font_size = self.height*.025
        self.bmi_label.font_size = self.height*.025
        
        self.protein_label.font_size = self.height*.037
        self.carbs_label.font_size = self.height*.037
        self.fats_label.font_size = self.height*.037

        self.moderate_label.font_size = self.height*.02
        self.lower_label.font_size = self.height*.02
        self.high_label.font_size = self.height*.02

        self.maintain.font_size = self.height*.03375
        self.cut.font_size = self.height*.03375
        self.bulk.font_size = self.height*.03375
        
        self.ratio_help.font_size = self.height*.02
        self.macro_help.font_size = self.height*.02

        self.ideal.font_size = self.height*.037
        
    def focus_reset(self,input,focus):      #Special Background Colour Handling for Text Inputs and Buttons in Dark Mode
        if (focus== 'down'):
            input.background_color = (1,1,1,1)
        elif focus == 'normal':
            input.background_color = get_color_from_hex('2a2b2e')
        elif focus:
            input.background_color = (1,1,1,1)
        else:
            input.background_color = get_color_from_hex('2a2b2e')
    
    @staticmethod
    def macro_splitter(percentages,cals):
        ratio = map(lambda x,y : x/y, percentages, [4,4,9])     #Lambda Function That Takes Ratios and Converts them to Percentages
        return [round(i*cals) for i in ratio]       #Returns the Correct Percentages of Calories in Accordance to Ratios
    
    def show_labels(self):      #If the Calculated Values Aren't Already On Screen, Add Them
        try:
            self.add_widget(self.calories_label)
            self.add_widget(self.tdee_box)
            self.add_widget(self.weekly_label)
            self.add_widget(self.twee_box)
            self.add_widget(self.bmi_label)
            self.add_widget(self.bmi_box)                
            self.add_widget(self.table)
            self.add_widget(self.protein_label)
            self.add_widget(self.carbs_label)
            self.add_widget(self.fats_label)
            self.add_widget(self.moderate_label)
            self.add_widget(self.lower_label)
            self.add_widget(self.high_label)
            self.add_widget(self.button_row)
            self.add_widget(self.ratio_help)
            self.add_widget(self.macro_help)
            self.add_widget(self.ideal)
            self.add_widget(self.bmi_button)
        except:
            pass
        
    @staticmethod
    def Sort(data_set):     #Simple Sorting Algorithm
        for position,currentvalue in enumerate(data_set):
            while position > 0 and data_set[position-1]>currentvalue:       #If The Current Element Isn't the Last One And The Previous List Element is Greater Than the Current
                data_set[position] = data_set[position-1]       #Move the Previous Item Forward in the List
                position -= 1       #Iterate Position Value Back until It's the 2nd Element
            data_set[position] = currentvalue       #Set the Final Value as the 1st Element

    def start_calculate(self,*args):        #Method That Does All the Maths 
        self.new_data = [None] * 4
        invalid = LoginPopup()      #Utilises Custom Popup Class for Different Purpose
        invalid.popup_title.text = 'Invalid details entered'
        if  (len(self.weight_box.text)) > 0:
            if self.app.metric:
                weight = float(self.weight_box.text) if  20<(float(self.weight_box.text)) < 300 else None       #Checks if Input Weight is Within Suitable Region for Metric
            else:
                weight = float(self.weight_box.text)/2.205 if  44<(float(self.weight_box.text)) < 660 else None     #Checks if Input Weight is Within Suitable Region for Imperial
        else:
            invalid.open()      #Open Popup if Wrong Weight
            return
                
        if  (len(self.height_box.text)) > 0:
            if self.app.metric:
                height = float(self.height_box.text) if 0<float(self.height_box.text)<3 else None       #Checks if Input Height is Within Suitable Region for Metric
            else:
                feet = list(map(float,(self.height_box.text).split("'")))       #Converts Text to Feet and Inches in List
                inchify = lambda x,y : x*12 + y     #Lambda to Turn Feet and Inches to Just Inches
                meters = (inchify(feet[0],feet[1]))/39.37       #Converts Inches Entered to Meters
                height = meters if 0<meters<3 else None     #Checks if Input Height is Within Suitable Region for Metric
        else:
            invalid.open()      #Open Popup if Wrong Height
            return
        if height == None or weight == None:
            invalid.open()      #Open Popup if Any Text Input is Empty
            return
        
        self.show_labels()
        self.macros_show = True     #Enables Condition that Shows the Macros Table
        self.on_size()      #Calls Sizing Method to Ensure Everything is Correct Size
        try:        #See if Body Fat Input has a Value in it =
            if 0<float(self.fat_box.text)<100:  
                self.new_data[2] = round(float(self.fat_box.text),2)
                self.bmr = 370 + ((21.6* weight)) *((100- float(self.fat_box.text))/100)        #Calculates Basal Metabolic Rate of User Using Weight Height and Body Fat
            else:raise
        except:
            constant = +5 if self.default_data[1] == 'Male' else -161       #Allocates Correct Constant for Users Gender
            self.bmr = (10* weight)+(625* height)-(5*self.default_data[0]) + constant       #Calculates Basal Metabolic Rate of User Using Weight Height and Gender

        self.tdee = self.bmr * self.multipliers[self.modifier.text]         #Calculates User's Total Daily Energy Expenditure Based on BMR and Daily Activity
        self.bmi = weight/ height**2

        #Updates the User's Body Info List for DB Storage
        self.new_data[0] = weight
        self.new_data[1] = height
        self.new_data[3] = self.tdee
        
        ##Puts Calcualted Values in the Relevant Labels On Screen
        self.tdee_box.text = str(round(self.tdee,2))
        self.twee_box.text = str(round(self.tdee*7,2))
        self.bmi_box.text = str(round(self.bmi,2))

        for i in self.table.children:
            nonbold = re.sub('\[[^\[\]]+\]','',i.text)      #Removes all Previous Markup Tags in the Current Row's Text
            prev = (nonbold.split(':'))[0]      #Gets Only the Row Descriptor and not the Value
            if prev[0] == 'B':      #Checks if that Row is BMR
                i.text = (f'{prev}: {round(self.bmr,2)}')       #Updates with New BMR Value
            elif prev[0] == self.modifier.text[0]:      #Checks if Current Row is the Same as the One That's Selected
                if '[' not in prev:     #If it Doesn't Have Markup Tags
                    i.text = (f'[font=Resources/fontbold]{prev}: {round(self.tdee,2)} [/font]')     #Update The Row's Data With New Values and Markup for Bold Font
            else:
                for word in list(self.multipliers.keys()):
                    if prev[0] in word:
                        multiplier = (self.multipliers[word])
                i.text = (f'{prev}: {round(self.bmr*multiplier,2)}')        #Sets the rest of the TDEE Rows Based on Their Unique Multipliers and BMR

        ideal_weight = (lambda constant,step : constant+((height-1.524)*39.37*step))        #Lambda that Generalises all Ideal Weight Equations

        ##Generates a Range of Ideal Weights for User, With Differing Values Based on Their Gender
        if self.default_data[1] == 'Male':   
            hamwi = ideal_weight(48,2.7)
            devine = ideal_weight(50,2.3)
            robinson = ideal_weight(52,1.9)
            miller = ideal_weight(56.2,1.41)
        else:
            hamwi = ideal_weight(45.5,2.2)
            devine = ideal_weight(45.5,2.3)
            robinson = ideal_weight(49.5,1.7)
            miller = ideal_weight(53.1,1.36)

        weights = [hamwi,devine,robinson,miller]
        self.Sort(weights)      #Sorts all Weights
        self.ideal.text = (f'{self.ideal.text.split(":")[0]}: [font=Resources/fontbold] {round(weights[0],1)} - {round(weights[-1],1)} kg [/font]') if self.app.metric else (f'{self.ideal.text.split(":")[0]}: [font=Resources/fontbold] {round(weights[0]*2.205,1)} - {round(weights[-1]*2.205,1)} lbs [/font]')
        #^Displays the Range of Ideal Weights for the User on Screen
        
    def macroswitch(self,button):       #Method Called When User Switches Macro Table from Cutting, Bulking or Maintenance
        cals = self.tdee
        ##Reduces or Increases User's TDEE Based on Cut or Bulk
        if button.text == 'Cutting':        
            cals -= 500
        elif button.text == 'Bulking':
            cals += 500
            
        ##Gets Users Caloric Needs as Percenatges in Proteins, Carbs and Fats
        macros = self.macro_splitter([.3,.35,.35],cals)     
        macros_low = self.macro_splitter([.4,.2,.4],cals)
        macros_high  = self.macro_splitter([.3,.5,.2],cals)
        
        final_macros=[]
        for i in range(3):
            final_macros += macros[i],macros_low[i],macros_high[i]
        final_macros = list(reversed(final_macros))     #Puts All Calculated Values in Correct Order for Table
        
        for count,widget in enumerate(self.macros_box.children):
            widget.text = str(final_macros[count])+'g'      #Adds Values to Table Textboxes

    def metric_switch(self,*args):      #Switches System to and from Metric and Imperial
        self.app.switch_metric()
        self.widget_setup()

    def widget_setup(self):
        self.clear_widgets()
        self.canvas.clear()
        self.macros_show = False
        if self.app.theme == 'light':
            with self.canvas:
                Color(0,0,0,1)
                self.divider1 = Line(points=[0,0,0,0], width=1)
                self.divider2 = Line(points=[0,0,0,0], width=1)
        else:
            with self.canvas:
                Color(1,1,1,1)
                self.divider1 = Line(points=[0,0,0,0], width=1)
                self.divider2 = Line(points=[0,0,0,0], width=1)
        
        self.add_widget(TitleLabel(text= 'Body Composition'))
        
        redirect_button = RedirectButton(text= 'Return To Menu',target= 'menu', direction = 'right')
        self.info_row = BoxLayout(orientation = 'horizontal',size_hint = (0.975,None),pos_hint = {'center_x':0.5,'center_y':0.84})
        self.multipliers = {"Sedentary (Office Job)":1.1,"Light (1-2 times/week)":1.25, "Moderate (3-5 times/week)":1.4, "Heavy (6-7 times/week)":1.6,"Athlete (2x a day)":1.8}
        try:
            self.info_row.add_widget(Label(text= f"You're a {self.default_data[0]} y/o {self.default_data[1]} who's", size_hint = (0.21,None),pos_hint = {'center_x':.2}))
            if not self.app.metric:
                def_weight = str(round(self.default_data[2] *2.205))
                def_height = list(divmod(self.default_data[3]*3.281,1))
                def_height[1] *= 12
                def_height = list(map(str,(map(round,def_height))))
                def_height = "'".join(def_height)
            else:
                def_weight = str(round(self.default_data[2],2))
                def_height = str(round(self.default_data[3],2))

            self.weight_box  = MeasureTextInput(text = def_weight)
            self.info_row.add_widget(self.weight_box)
            self.info_row.add_widget(Label(text='kg and' if self.app.metric else 'lbs and',size_hint = (0.06,None)))
            
            self.height_box = HeightInput(text = def_height)
            self.height_box.size_hint = (0.04,0.3)
            self.height_box.pos_hint = {'center_y':.5}
            self.height_box.hint_text = 'Enter'
            self.info_row.add_widget(self.height_box)
            self.info_row.add_widget(Label(text='m with' if self.app.metric else 'ft with',size_hint = (0.05,None)))

            self.modifier = Spinner(text="Sedentary (Office Job)", values= list(self.multipliers.keys()), size_hint= (.18,0.3),pos_hint = {'center_y':.5})
            self.modifier.option_cls = 'SpinnerButton'
            if self.app.theme == 'dark':
                self.modifier.bind(state  = self.focus_reset )
            self.info_row.add_widget(self.modifier)
            
            self.info_row.add_widget(Label(text = 'and', size_hint = (0.04,None)))
            
            self.fat_box = MeasureTextInput()
            self.fat_box.text =str(self.default_data[4]) if len(self.default_data)>4 else ''
            self.info_row.add_widget(self.fat_box)
            self.info_row.add_widget(Label(text = '% body fat', size_hint = (0.09,None)))

            for i in self.info_row.children:
                if (isinstance(i,MeasureTextInput)) and self.app.theme == 'dark':
                    i.bind(focus= self.focus_reset)
                    
            self.add_widget(self.info_row)
            
        except:pass
        
        calculate_button = RedirectButton(text= 'Calculate',target=None,direction= None)
        calculate_button.validation = True
        calculate_button.pos_hint = {"center_x":0.5,"center_y":0.05}
        calculate_button.size_hint = (0.35, 0.08)
        calculate_button.bind(on_release = self.start_calculate)
        
        self.add_widget(calculate_button)
        self.add_widget(redirect_button)

        self.calories_label = Label(text = 'Total Daily Calories:',size_hint = (0.125,0.05), pos_hint = {'center_x':.1,'center_y':.765})
        self.tdee_box = Label(size_hint = (0.125,0.05), pos_hint = {'center_x':.25,'center_y':.765})
        self.tdee_box.font_name = 'Resources/fontbold'
        
        self.weekly_label = Label(text = 'Total Weekly Calories:',size_hint = (0.15,0.05), pos_hint = {'center_x':.1,'center_y':.69})
        self.twee_box = Label(size_hint = (0.15,0.05), pos_hint = {'center_x':.25,'center_y':.69})
        self.twee_box.font_name = 'Resources/fontbold'
        
        self.bmi_label = Label(text = 'BMI:',size_hint = (0.125,0.05), pos_hint = {'center_x':.1,'center_y':.615})
        self.bmi_box = Label(size_hint = (0.125,0.05), pos_hint = {'center_x':.25,'center_y':.615})
        self.bmi_box.font_name = 'Resources/fontbold'

        self.bmi_button = RedirectButton(text = 'BMI Chart',target = None,direction = None)
        self.bmi_button.validation = True
        self.bmi_button.pos_hint = {"center_x":0.18,"center_y":0.55}
        bmi_img = Image(source  ='Resources/bmi.png')
        bmipopup = IMGPopup(bmi_img)
        self.bmi_button.bind(on_release = bmipopup.open)

        self.table = StackLayout(size_hint = (0.4,0.3),pos_hint = {'center_x':.25,'center_y':.35},spacing = 10)
        self.table.add_widget(Label(halign = 'left',text = 'Basal Metabolic Rate : ',size_hint = (1,1/6)))
        for i in list(self.multipliers.keys()):
            i = i.split('(')[0]
            self.table.add_widget(Label(halign = 'left',markup = True, text = i+'Activity Level : ',size_hint = (1,1/6)))
            
        self.macros_box = GridLayout(cols = 3,size_hint = (0.6,0.6),pos_hint = {'center_x':0.73,'center_y':0.33},spacing = [-100,-100])
        self.protein_label =Label(text='Protein:',size_hint  = (0.2,0.1),pos_hint = {'center_x':0.47,'center_y':0.48})
        self.carbs_label = Label(text='Carbs:',size_hint  = (0.2,0.1),pos_hint = {'center_x':0.47,'center_y':0.33})
        self.fats_label = Label(text='Fats:',size_hint  = (0.2,0.1),pos_hint = {'center_x':0.47,'center_y':0.18})

        self.moderate_label = Label(text='Moderate Carbs (30/35/35)',size_hint  = (0.15,0.1),pos_hint = {'center_x':0.575,'center_y':0.535})
        self.lower_label = Label(text='Lower Carbs (40/20/40)',size_hint  = (0.15,0.1),pos_hint = {'center_x':0.725,'center_y':0.535})
        self.high_label = Label(text='High Carbs (30/50/20)',size_hint  = (0.15,0.1),pos_hint = {'center_x':0.88,'center_y':0.535})

        self.button_row = StackLayout(size_hint=(.54,0.15),pos_hint= {"center_x":.76,"center_y":0.575},spacing=(5,0),orientation= ("lr-tb"))
        self.maintain = ToggleButton(text = 'Maintenance',group='macros',size_hint =(0.3,.5),on_release = self.macroswitch)
        self.cut  = ToggleButton(text = 'Cutting',group='macros',size_hint =(0.3,.5),on_release = self.macroswitch)
        self.bulk = ToggleButton(text = 'Bulking',group='macros',size_hint =(0.3,.5),on_release = self.macroswitch)

        self.button_row.add_widget(self.maintain)
        self.button_row.add_widget(self.cut)
        self.button_row.add_widget(self.bulk)
        for _ in range(9):
            i=Label()
            i.font_name = 'Resources/fontbold.ttf'
            self.macros_box.add_widget(i)
            i.font_size = i.parent.height*.3
        self.add_widget(self.macros_box)

        self.ratio_help = Label(text ='30/35/35 means 30% protein, 35% carbs, 35% fats',size_hint = (0.35,0.05),pos_hint = {"center_x":.725,"center_y":0.675})
        self.macro_help = Label(text ='There are 4 calories per gram of both protein and carbohydrates, and 9 calories per gram of fats.',size_hint = (0.5,0.05),pos_hint = {"center_x":.725,"center_y":0.125})

        self.ideal = Label(markup = True,text='Ideal Weight: ',size_hint  = (0.5,0.1),pos_hint = {'center_x':0.75,'center_y':0.765})

        self.metric_toggle = IMGButton(f'Resources/{self.app.theme}/metric_icon.png',0.04,0.055,(0.15,0.15))
        self.metric_toggle.bind(on_release = self.metric_switch)
        self.add_widget(self.metric_toggle)
        
        self.on_size()

class MyApp(App):       #Base App/Window class
    title = "Fitness Program"
    theme = 'light'
    username = ''
    metric = True
    col_light = get_color_from_hex('797E84')
    col = get_color_from_hex('2a2b2e')
    col_dark = get_color_from_hex('2e2d2a')
    
    Window.clearcolor = get_color_from_hex('FFFFFF')
    Window.minimum_height = 500
    Window.minimum_width = 700
    
    def build(self):        #Sets up the Kivy mainloop and instantiates all screens
        self.sm = ScreenManager(transition=SlideTransition())
        self.scrns  = [LoginScreen(name='login'),RegisterScreen(name='register'),MenuScreen(name='menu'),FoodTrackerScreen(name='foodtracker'),GraphScreen(name='graphs'),WorkoutsScreen(name='workouts'),BodyScreen(name='body'),RecordScreen(name='record')]
        for i in self.scrns:
            self.sm.add_widget(i)
        self.icon = 'Resources/icon.png'
        return self.sm     
    
    @classmethod
    def update_username(cls,username):
        cls.username = username

    @classmethod
    def switch_metric(cls):     #Switches measurement mode from Metric to Imperial
        cls.metric = not cls.metric

    def switch_theme(self,*args):       #Switches program colours to and from light to dark when called 
        if self.theme == 'light':
            self.theme = 'dark'
            self.col_light = get_color_from_hex('585858')
            self.col = get_color_from_hex('D1D1D1')
            self.col_dark = get_color_from_hex('aaaaaa')
            Window.clearcolor = get_color_from_hex('2a2b2e')
        else:
            self.theme = 'light'
            self.col_light = get_color_from_hex('797E84')
            self.col = get_color_from_hex('2a2b2e')
            self.col_dark = get_color_from_hex('2e2d2a')
            Window.clearcolor = get_color_from_hex('FFFFFF')
            
        for i in self.scrns:
            i.widget_setup()

if __name__ == "__main__":
    MyApp().run()
