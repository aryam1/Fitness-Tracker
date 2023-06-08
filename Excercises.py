import bs4
import requests
import re

class Excercises():
    muscles = {'Chest': 1, 'Forearms': 2, 'Lats': 3, 'Middle Back': 4, 'Lower Back': 5, 'Neck': 6, 'Quadriceps': 7, 'Hamstrings': 8, 'Calves': 9, 'Triceps': 10, 'Traps': 11, 'Shoulders': 12, 'Abdominals': 13, 'Glutes': 14, 'Biceps': 15, 'Adductors': 17, 'Abductors': 18}
    types = {'Strength': 1, 'Cardio': 2, 'Stretching': 3, 'Plyometrics': 4, 'Strongman': 5, 'Olympic Weightlifting': 6, 'Powerlifting': 7} 
    equip = {'Dumbbell': 1, 'Barbell': 2, 'Other': 3, 'Cable': 4, 'Body': 5, 'Machine': 6, 'Excercise Ball': 7, 'Bands': 9, 'Kettlebells': 10, 'E-Z Curl Bar': 11, 'Foam Roller': 14, 'Medicine Ball': 15}
    page = 1
    url_extension = ''
    def __init__(self ):
        self.equip_num = ''
        self.muscle_num = ''
        self.type_num =''

    def Search(self,query):
        self.url = f'https://www.bodybuilding.com/exercises/search?query={query}'
        pages = requests.get(self.url)

        soup = bs4.BeautifulSoup(pages.content, 'html.parser')
            
        self.container = soup.find(class_="Search-results")
        self.CollateInfo()
            
    def GetList(self):
        self.url = f'https://www.bodybuilding.com/exercises/finder/{self.page}/?equipmentid={self.equip_num}&exercisetypeid={self.type_num}&muscleid={self.muscle_num}'
        pages = requests.get(self.url)

        soup = bs4.BeautifulSoup(pages.content, 'html.parser')
            
        self.container = soup.find(class_="ExCategory-results")
        self.CollateInfo()

    def CollateInfo(self):
        names_html=self.container.find_all(class_="ExHeading ExResult-resultsHeading")
        muscles_html=self.container.find_all(class_="ExResult-details ExResult-muscleTargeted")
        equip_html=self.container.find_all(class_="ExResult-details ExResult-equipmentType")
        rating_html=self.container.find_all(class_="ExRating")

        jsonparse = lambda a : (' '.join(a.get_text().split()))
        self.final_list=[]
        url_list=[]
        names_list=[]
        for i in range(len(names_html)):
            name=jsonparse(names_html[i])
            muscle= jsonparse(muscles_html[i]).split(': ')[1]
            equip=jsonparse(equip_html[i]).split(': ')
            if len(equip) >1:
                equip= equip[1]
            else:
                equip='None'
            rate=jsonparse(rating_html[i])
            url_list.append(names_html[i].find('a')['href'])
            names_list.append(name)
            self.final_list.append([name,muscle,equip,rate])
            
##
##        names_list = [(' '.join(i.get_text().split())) for i in names_html]
##        url_list = [i.find('a')['href'] for i in names_html]
##        muscles_list = [(' '.join(i.get_text().split())).split(': ')[1] for i in muscles_html]
##        equip_list =   [(' '.join(j.get_text().split())).split(': ')[1] for j in equip_html]
##        rating_list = [(' '.join(i.get_text().split())) for i in rating_html]
            
##        self.final_list = [[names_list[i],muscles_list[i],equip_list[i],rating_list[i]] for i in range(len(names_list))]
        self.url_dict = dict(zip(names_list, url_list))
        
    @classmethod
    def ChangePage(cls,page):
        cls.page = page
        
    def Refine(self,option):
        if option[0] == '1':
            num = self.muscles[option[1:]]
            self.muscle_num = str(num) if (self.muscle_num).isdigit() == 0 else ''
        else:
            num = self.equip[option[1:]]
            self.equip_num = str(num) if (self.equip_num).isdigit() == 0 else ''

    def Choose(self):
        #option = re.sub('[^a-zA-Z]+','-',option)
        option_url =f'https://www.bodybuilding.com{self.url_extension}'
        pages = requests.get(option_url)

        soup = bs4.BeautifulSoup(pages.content, 'html.parser')
        
        text_html = soup.find_all(class_='grid-8 grid-12-s grid-12-m')[1]
        instruction_html = text_html.find('ol')
        info_html = soup.find(class_ = 'bb-list--plain')
        images_html = soup.find(class_ ='flexo-container flexo-around').find_all(class_='ExDetail-imgWrap')
        
        fixed_instruction_html = [i for i in instruction_html if isinstance(i,bs4.element.Tag)]

        self.instruction_list = ([f'{x+1}. {y.get_text()}' for x,y in enumerate(fixed_instruction_html)])
        self.info_list = [i.get_text().split()[-1] for i in info_html.find_all('li')]            
        self.images_url = [i.find('img')['src'] for i in images_html]
        
        variation_html = text_html.find_all('p')[1:]
        if len(variation_html) >0:
            variation_text = [i.get_text() for i in variation_html]
            variation_text = (variation_text[0].split(':')+variation_text[1:])
            variation_text[0] = f'[font=Resources/fontbold]{variation_text[0]}:[/font]' if variation_text[0] == 'Variations' else variation_text[0]
            
            self.instruction_list +=  variation_text
        self.instruction_list = [i.replace('Tip:','[font=Resources/fontbold]Tip:[/font]') for i in self.instruction_list]
