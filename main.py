from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField, TextAreaField
from wtforms.validators import DataRequired
from flask import Flask, url_for, render_template, request, redirect
from data import db_session
from data import users
from data import newss
import requests
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

@app.route("/")
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(newss.News).filter(newss.News.is_private != True)
    if current_user.is_authenticated:
        news = db_sess.query(newss.News).filter(
            (newss.News.user == current_user) | (newss.News.is_private != True))
    else:
        news = db_sess.query(newss.News).filter(newss.News.is_private != True)
    return render_template("index.html", news=news)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(users.User).get(user_id)

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
    
class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Начать тренироваться вместе!')
    
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(users.User).filter(users.User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = users.User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(users.User).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = newss.NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(newss.News).filter(newss.News.id == id,
                                          newss.News.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.duration.data = news.duration
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(newss.News).filter(newss.News.id == id,
                                          newss.News.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.duration = form.duration.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование тренировки',
                           form=form)

@app.route('/news',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = newss.NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = newss.News(title=form.title.data, duration=form.duration.data, content=form.content.data, 
            user=current_user, is_private=form.is_private.data)
        db_sess.merge(news)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление тренировки', 
                           form=form)

@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(newss.News).filter(newss.News.id == id,
                                      newss.News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')

if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.run(port='8080', host='127.0.0.1')