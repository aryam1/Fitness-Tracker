import requests

class FoodAPI():
    def __init__(self, request, page):
        self.request = request
        self.page = page * 40
        self.get_info()

    def get_info(self):
        self.names = []
        self.nutrients = []
        self.request = 'upc=' + self.request if self.request.isdigit() else 'ingr=' + self.request
        self.url = f'https://api.edamam.com/api/food-database/parser?session={self.page}&nutrition-type=logging&{self.request}&app_id=d90b0608&app_key=9a46819223c52590884dc9a63cafe84a'
        try:
            self.data = requests.get(self.url)
            self.internet = True
        except:
            self.internet = False
        try:
            self.json = self.data.json()['hints']
        except:
            self.json = []
        self.items = len(self.json)
        for i in range(self.items):
            if self.json[i]['food']['category'] != 'Generic foods':
                try:
                    name = self.json[i]['food']['brand'] + ' ' + self.json[i]['food']['label']
                    self.names.append(name)
                except:
                    self.names.append(self.json[i]['food']['label'])
            else:
                self.names.append(self.json[i]['food']['label'])
            self.nutrients.append(self.json[i]['food']['nutrients'])
