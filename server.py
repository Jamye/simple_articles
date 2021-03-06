from flask import Flask, render_template, redirect, request, flash, url_for, session, logging
# from data import Articles     #initially used for dummy-data
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

app.secret_key = 'secret123'


# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'articlesApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  #configs so that we return dicttionaries from DB
# initialize MYSQL
mysql = MySQL(app)

# Articles = Articles()       #initially used for dummy-data

@app.route('/')
def index():
    return render_template('home.html')
#about page
@app.route('/about')
def about():
    return render_template('about.html')

#articles page
@app.route('/articles')
def articles():
    #create cursor
    cur = mysql.connection.cursor()

    #get articles/execute
    result = cur.execute("SELECT * FROM articles")

    #pulls the information from DB
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles = articles)
    else:
        msg = "No Articles Found"
        return render_template('articles.html', msg=msg)

        #close connection
        cur.close()


@app.route('/article/<string:id>/')
def article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #query for the article associated with ID
    result = cur.execute("SELECT * FROM articles WHERE id = %s", (id))

    article = cur.fetchone()

    return render_template('article.html', article = article)

#register form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match.')
    ])
    confirm = PasswordField('Confirm Password')

#user register
@app.route('/register', methods=['Get', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #create cursor
        cur = mysql.connection.cursor()

        #execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #commit to db
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('You are now registered', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form = form)

# User login
@app.route('/login', methods= ['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            password = data['password']

            # compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                app.logger.info('PASSWORD MATCHED')
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid Login'
                return render_template('login.html', error = error)
            cur.close()
        else:
            error = 'Username not found.'
            return render_template('login.html', error = error)

    return render_template('login.html')

#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please log in', 'danger')
            return redirect(url_for('login'))
    return wrap

#logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#dashboard and calls @is_logged_in to prevent gets to dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #create cursor
    cur = mysql.connection.cursor()

    #get articles/execute
    result = cur.execute("SELECT * FROM articles")

    #pulls the information from DB
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles = articles)
    else:
        msg = "No Articles Found"
        return render_template('dashboard.html', msg=msg)

        #close connection
        cur.close()

    return render_template('dashboard.html')


#Article form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=6, max=250)])
    body = TextAreaField('Body', [validators.Length(min=30)])

#Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create cursor
        cur = mysql.connection.cursor()

        #execute cursor
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        #commit to DB
        mysql.connection.commit()

        #close the connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)



if __name__ == '__main__':
    app.run(debug=True)
