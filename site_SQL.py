import sqlite3
import os
from flask import Flask, render_template, url_for, request, g, flash, abort, session, redirect, make_response
from FDataBase import FDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from UserLogin import UserLogin
from forms import LoginForm, RegisterForm
from admin.admin import admin  # импортируем экземпляр класса! BluePrint

#конфигурация
DATABASE = '/tmp/flsite.db'
DEBUG = True
SECRET_KEY = 'fdgdfgdfggf786hfg6hfg6h7f'
USERNAME = 'admin'
PASSWORD = '123'
MAX_CONTENT_LENGTH = 1024 * 1024 #ограничивать максимальный размер загружаемого файла, в данном случае 1 Мб.

app = Flask(__name__)
app.config.from_object(__name__) #загружаем конфигурацию из этого же файла(выше)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))  #обновляем адрес бд - тек папка/имя.db (в ф. передаем объект словаря)

app.register_blueprint(admin, url_prefix='/admin')

login_manager = LoginManager(app)
login_manager.login_view = 'login' #g=перенаправляет на страницу login если неавторизованный юзер заходит на закрытую для неавторизованных юзеров страницу
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам" #мгновенное сообщение в предыдущей ситуации
login_manager.login_message_category = "success"  #категория мгновенного сообщения

@login_manager.user_loader
def load_user(user_id):
    """Создает вновь и возвращает экземпляр класса UserLogin,подгружая данные о user по БД, 
    ищет по user_id из session-подцепляемой на каждый запрос пользователя к серверу декоратором """
    print("load_user")
    return UserLogin().fromDB(user_id, dbase)


def connect_db():
    """ ф. установления соединения с бд"""
    conn = sqlite3.connect(app.config['DATABASE'])   # устанавливаем соединение с бд по адресу из ключевого слова словаря конфиг
    conn.row_factory = sqlite3.Row              # записи из бд хотим представлять не в виде кортежей tupl, а в виде словаря
    return conn                            #ф. возвращает установленное соединение

def create_db():
    """Вспом ф. для создания таблиц бд"""
    db = connect_db()
    with app.open_resource('sq_db.sql',mode='r') as f:  #менеджер контекста читает файл sq_db.sql из раб.каталога нашего приложения, в нем записан набор sql скриптов для создания таблиц для нашего сайта.
        db.cursor().executescript(f.read())  # из соединения с бд вызываем класс cursor(), из него выполняем метод executescript(),выполняющий скрипты из прочитанного файла
    db.commit()  #записываем изменения в бд
    db.close()

def get_db():
    """Соединение с БД, если оно еще не установлено"""
    if not hasattr(g, 'link_db'):   #есть ли в g свойство link_db,если есть,то соединение с БД уже есть.
        g.link_db = connect_db()   # если нет, то в g запишем инфу о установлении соединения с бд
    return g.link_db

dbase = None
@app.before_request
def before_request():
    """Установление соединения с БД перед выполнением любого запроса"""
    global dbase
    db = get_db()   
    dbase = FDataBase(db)   #создаем экземпляр нашего класса бд

@app.route("/")
def index():
    return render_template("index.html", menu = dbase.getMenu(), posts=dbase.getPostsAnnonce())
    #return render_template("index.html", menu = [{"name": 'Установка', "url": "install-flask"}])

@app.route("/add_post", methods=["POST", "GET"])
def addPost():
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['post']) > 10: #если имя>4 & пост>10
            res = dbase.addPost(request.form['name'], request.form['post'], request.form['url'])  #добавляем пост в нашу бд
            if not res:
                flash('Ошибка добавления статьи', category = 'error')
            else:
                flash('Статья добавлена успешно', category = 'success')
        else:
            flash('Ошибка добавления статьи', category = 'error')
    return render_template("add_post.html", menu = dbase.getMenu(), title='Добавление статьи')


@app.route("/post/<alias>")
@login_required
def showPost(alias):
    """Закрываем посты от неавторизованных user декоратором"""
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)
    
    return render_template("post.html", menu = dbase.getMenu(), title=title, post=post)

@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated: #если тек пользователь авторизован
        return redirect(url_for('profile')) 
    
    form = LoginForm() #создаем экземпляр класса LoginForm(FlaskForm) из файла forms.py
    if form.validate_on_submit():  #проверяет все валидаторы формы после нажатия кнопки.
        user = dbase.getUserByEmail(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            userlogin = UserLogin().create(user)  #при первой удачной авторизации создает объект класса UserLogin
            rm = form.remember.data
            login_user(userlogin, remember=rm)    #заносит в сессию инфу о тек.пользователе, ф. из flask_login
            return redirect(request.args.get("next") or url_for("profile"))  #если в аргументах запроса get есть next(когда страница перенаправила сюда неавторизованного usera),то перейти по этому get запросу
        
        flash("Неверная пара логин/пароль", "error")
    return render_template("login.html", menu=dbase.getMenu(), title="Авторизация", form=form)  #передаем экземпляр класса LoginForm(FlaskForm) в HTML шаблон
    
    """
    if request.method == "POST":
        user = dbase.getUserByEmail(request.form['email'])
        if user and check_password_hash(user['psw'], request.form['psw']):
            userlogin = UserLogin().create(user) #при первой удачной авторизации создает объект класса UserLogin
            rm = True if request.form.get('remainme') else False
            login_user(userlogin, remember=rm)    #заносит в сессию инфу о тек.пользователе, ф. из flask_login
            return redirect(request.args.get("next") or url_for("profile"))  #если в аргументах запроса get есть next(когда страница перенаправила сюда неавторизованного usera),то перейти по этому get запросу
 
        flash("Неверная пара логин/пароль", "error")
 
    return render_template("login.html", menu=dbase.getMenu(), title="Авторизация")
    """

@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
            hash = generate_password_hash(request.form['psw'])
            res = dbase.addUser(form.name.data, form.email.data, hash)
            if res:
                flash("Вы успешно зарегистрированы", "success")
                return redirect(url_for('login'))
            else:
                flash("Ошибка при добавлении в БД", "error")
    
    return render_template("register.html", menu=dbase.getMenu(), title="Регистрация", form=form)    
"""
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        session.pop('_flashes', None)
        if len(request.form['name']) > 4 and len(request.form['email']) > 4 \
            and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2']:
            hash = generate_password_hash(request.form['psw'])
            res = dbase.addUser(request.form['name'], request.form['email'], hash)
            if res:
                flash("Вы успешно зарегистрированы", "success")
                return redirect(url_for('login'))
            else:
                flash("Ошибка при добавлении в БД", "error")
        else:
            flash("Неверно заполнены поля", "error")
 
    return render_template("register.html", menu=dbase.getMenu(), title="Регистрация")
"""


@app.teardown_appcontext  #по завершению контектса приложения
def close_db(error):
    """Закрываем соединение с БД, если оно было установлено"""
    if hasattr(g, 'link_db'):   #есть ли в g свойство link_db,если есть,то соединение с БД уже есть.
        g.link_db.close()

@app.route('/profile')
@login_required
def profile():
    """Страница профайла userа"""
    return render_template("profile.html", menu=dbase.getMenu(), title="Профиль")
    #return f"""<a href="{url_for('logout')}">Выйти из профиля</a>
    #            <p>user info: {current_user.get_id()}""" #{current_user.get_id()} #current_user - из библ.flask_login, ~ как глобальная переменная, через которую можно обращаться к методам класса UserLogin

@app.route('/logout')
@login_required
def logout():
    logout_user()            #logout_user - из библ.flask_login, разлогинивает тек. usera
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))

@app.route('/userava')
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""
 
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h

@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):  #если файл загружен-есть и его расширение соотв. png. current_user-прям экземпляр нашего класса UserLogin с теми же методами
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id()) # изменение аватара пользователя в бд
                if not res:
                    flash("Ошибка обновления аватара", "error")
                    #return redirect(url_for('profile'))
                flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")
    
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)
    #create_db()
