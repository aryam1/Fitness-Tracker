import sqlite3
import os
import hashlib
import random
import datetime

def DatabaseChecker():
    if not os.path.isfile("Main.DB"):
        db = sqlite3.connect("Main.DB",detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        with db:
            cursor = db.cursor()
            cursor.execute('''CREATE TABLE Users
               (USERNAME TEXT NOT NULL PRIMARY KEY, 
                PASSWORD TEXT NOT NULL,
                DOB DATE NOT NULL,
                WEIGHT REAL NOT NULL,
                HEIGHT REAL NOT NULL,
                BTYPE TEXT,
                GENDER TEXT NOT NULL,
                SALT CLOB)''')
            cursor.execute('''CREATE TABLE Records
                (ENTRY_DATE DATE NOT NULL,
                USERNAME TEXT NOT NULL,
                CALORIES_IN REAL,
                CALORIES_OUT REAL,
                PROTEIN REAL,
                CARBS REAL,
                FAT REAL,
                WEIGHT REAL,
                HEIGHT REAL,
                BODY_FAT REAL,
                PRIMARY KEY (ENTRY_DATE,USERNAME),
                FOREIGN KEY (USERNAME) REFERENCES Users(USERNAME) ON DELETE CASCADE)''')
    else:
        pass

def Register(user):
    db = sqlite3.connect("Main.DB")
    
    password = (user[2]).encode('utf-8')
    salt = os.urandom(16)
    password += salt
    password = hashlib.sha512(password).hexdigest()

    user[2] = password
    user.append(salt)
    with db:
        cursor = db.cursor()
        cursor.execute('SELECT USERNAME,DOB from Users')
        for i in cursor.fetchall():
            if user[1] in i[0]:
                user[1] = user[1] + str(random.randint(0,1000))       
        del user[0]
        cursor.execute('INSERT INTO Users VALUES(?,?,?,?,?,?,?,?)',user)
        
    return(user[0])


def Login(username,password):
    db = sqlite3.connect("Main.DB")
    cursor = db.cursor()

    try:
        cursor.execute('''SELECT PASSWORD, SALT
                      FROM Users
                      WHERE USERNAME=?''',
                      (str(username),))
        userData = cursor.fetchone()
        db_password = userData[0]
        salt = userData[1]

    except:
        return(False)
    
    password +=salt
    password = hashlib.sha512(password).hexdigest()
    
    return True if password == db_password else False

def LogFood(username,nutrients):
    db = sqlite3.connect("Main.DB",detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    
    today = datetime.date.today()
    cals = nutrients['ENERC_KCAL']
    prot = nutrients['PROCNT'] if 'PROCNT' in nutrients else 0
    carbs = nutrients['CHOCDF'] if 'CHOCDF' in nutrients else 0
    fat = nutrients['FAT'] if 'FAT' in nutrients else 0

    with db:
        cursor = db.cursor()
        try:
            cursor.execute('SELECT * FROM Records WHERE ENTRY_DATE=? AND USERNAME =?',(today,username))
            previous_record = cursor.fetchone()
            cals += previous_record[2]
            prot += previous_record[4]
            carbs += previous_record[5]
            fat += previous_record[6]
            cursor.execute('UPDATE Records SET CALORIES_IN = ?, PROTEIN = ?, CARBS = ?,FAT = ? WHERE ENTRY_DATE = ? AND USERNAME = ?',(cals,prot,carbs,fat,today,username))
        except:
            cursor.execute('INSERT INTO Records VALUES (?,?,?,?,?,?,?,?,?,?)',(today,username,cals,0,prot,carbs,fat,0,0,0))

def GraphSelect(username,column_name):
    db = sqlite3.connect("Main.DB",detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)    
    cursor = db.cursor()
    results ={}
    column_name = column_name.replace(' ','_')
    for x,y in cursor.execute(f"SELECT ENTRY_DATE,{column_name} FROM Records WHERE USERNAME =?",(username,)):
        if (y != None and y >0):
            results[x]=y
    return results

def GetMeasurements(username):
    db = sqlite3.connect("Main.db",detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    with db:
            cursor = db.cursor()
            cursor.execute('''SELECT DOB,GENDER,WEIGHT,HEIGHT from Users WHERE USERNAME = ?''',(username,))
            first_data = list(cursor.fetchone())
    today = datetime.date.today()
    born =first_data[0]
    first_data[0] = (today.year - born.year - ((today.month, today.day) < (born.month, born.day)))
    first_data[1] = 'Male' if first_data[1] =='M' else 'Female'
    with db:
        cursor = db.cursor()
        cursor.execute("SELECT WEIGHT,HEIGHT,BODY_FAT FROM Records WHERE USERNAME = ? ORDER BY ENTRY_DATE DESC",(username,))
        last = cursor.fetchone()
        last = last if isinstance(last,tuple) else (last,)
    if 0 not in last:
        first_data = first_data[:-2] + list(last)

    return first_data

def LogMeasurements(username,data):
    db = sqlite3.connect("Main.db",detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    today = datetime.date.today()
    #delta_data = set(old_data[2:]) - set(new_data)
    #if len(delta_data) != 0:
     #   fin_data[3] = old_data[3] if fin_data[3] == None else fin_data[3]
    with db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Records WHERE ENTRY_DATE=? AND USERNAME =?',(today,username))
        previous_record = cursor.fetchone()
        if previous_record != None:
            cursor.execute('UPDATE Records SET CALORIES_OUT = ?, WEIGHT = ?, HEIGHT = ?, BODY_FAT = ? WHERE ENTRY_DATE = ? AND USERNAME = ?',(float(data[3])+float(previous_record[3]),data[0],data[1],data[2],today,username))
        else:
            cursor.execute('INSERT INTO Records VALUES (?,?,?,?,?,?,?,?,?,?)',(today,username,0,data[3],0,0,0,data[0],data[1],data[2]))

def RecordData(username,data):
    db = sqlite3.connect("Main.db",detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    today = datetime.date.today()
    new_data = [today,username] + data[:-2]+[0,data[4],0,data[5]]
    with db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Records WHERE ENTRY_DATE=? AND USERNAME =?',(today,username))
        previous_record = list(cursor.fetchone())
        final_record = new_data
        if previous_record != None:
            prev_record = [0 if previous_record[i] == None else previous_record[i] for i in range(len(previous_record))]
            for i in (2,3,4,5):
                final_record[i] += prev_record[i]
            for i in (6,7,8,9):
                final_record[i] = prev_record[i] if final_record[i] == 0 else final_record[i] 
        cursor.execute('INSERT OR REPLACE INTO Records VALUES (?,?,?,?,?,?,?,?,?,?)',final_record)
            
DatabaseChecker()
