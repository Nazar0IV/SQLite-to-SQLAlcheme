from flask_login import UserMixin
from flask import url_for
 
class UserLogin(UserMixin):
    def fromDB(self, user_id, db):
        """Берет из бд по id инфу о user, заносит инфу о user в защищенную переменную
        и возвращает экземпляр класса UserLogin"""
        self.__user = db.getUser(user_id)
        return self
    
    def create(self, user):
        """При авторизации создаем экземпляр класса UserLogin и возвращает его,
        а этот метод заносит инфу о user в защищенную переменную"""
        self.__user = user
        return self
    
    def get_id(self):
        return str(self.__user['id'])
    
    def getName(self):
        return self.__user['name'] if self.__user else "Без имени"
    
    def getEmail(self): 
        return self.__user['email'] if self.__user else "Без email"
    
    def getAvatar(self, app):
        """возвращает аватар юзера, если его нет - аватар по умолчанию из файла static/images/default.png"""
        img = None
        if not self.__user['avatar']:
            try:
                with app.open_resource(app.root_path + url_for('static', filename='images/default.png'), "rb") as f: #читаем в бинарном режиме
                    img = f.read()
            except FileNotFoundError as e:
                print("Не найден аватар по умолчанию: "+str(e))
        else:
            img = self.__user['avatar']
        
        return img
    
    def verifyExt(self, filename):
        """bool = расширение переданного файла соотв. png?"""
        ext = filename.rsplit('.', 1)[1] #разделяем имя файла с конца(реверс_сплит) до точки, [1]-(берем второй элемент из получившихся) = получаем расширение файла
        if ext == "png" or ext == "PNG":
            return True
        return False

"""Cтарый класс полностью прописан, в новом обязательные функции в родительском классе уже прописаны

class UserLogin:
    def fromDB(self, user_id, db):
        Берет из бд по id инфу о user, заносит инфу о user в защищенную переменную
         и возвращает экземпляр класса UserLogin
        self.__user = db.getUser(user_id)
        return self
 
    def create(self, user):
        При авторизации создаем экземпляр класса UserLogin и возвращает его,
        а этот метод заносит инфу о user в защищенную переменную
        self.__user = user
        return self
 
    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return str(self.__user['id'])

        """