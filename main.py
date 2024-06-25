from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_required, LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Database creation
def create_db():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS login (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS telefoonboek (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        phone_number TEXT,
        FOREIGN KEY (user_id) REFERENCES login(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS films (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        film TEXT,
        jaar TEXT,
        bekeken INTEGER,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES login(id)
    )''')
    conn.commit()
    conn.close()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM login WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect("./database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM login WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            login_user(User(user[0], user[1], user[2]))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = sqlite3.connect("./database.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO login (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash('You have successfully registered! Please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists')
        conn.close()
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/telefoonboek', methods=['GET', 'POST'])
@login_required
def telefoonboek():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        phone_number = request.form['phone_number']
        c.execute("INSERT INTO telefoonboek (user_id, name, phone_number) VALUES (?, ?, ?)",
                  (current_user.id, name, phone_number))
        conn.commit()
        flash('Contact added successfully')
    c.execute("SELECT id, name, phone_number FROM telefoonboek WHERE user_id = ?", (current_user.id,))
    contacts = c.fetchall()
    conn.close()
    contact_data = {
        "telid": [contact[0] for contact in contacts],
        "naam": [contact[1] for contact in contacts],
        "telefoonnummers": [contact[2] for contact in contacts]
    }
    return render_template('telefoonboek.html', current_user=current_user, **contact_data)

@app.route('/addtelefoon', methods=['POST'])
@login_required
def addtelefoon():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    name = request.form['naam']
    phone_number = request.form['nummer']
    c.execute("INSERT INTO telefoonboek (user_id, name, phone_number) VALUES (?, ?, ?)",
              (current_user.id, name, phone_number))
    conn.commit()
    flash('Contact added successfully')
    conn.close()
    return redirect(url_for('telefoonboek'))

@app.route('/editnummer', methods=['POST'])
@login_required
def editnummer():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    telid = request.form['telid']
    nieuwnummer = request.form['nieuwnummer']
    c.execute("UPDATE telefoonboek SET phone_number = ? WHERE id = ? AND user_id = ?",
              (nieuwnummer, telid, current_user.id))
    conn.commit()
    flash('Nummer updated successfully')
    conn.close()
    return redirect(url_for('telefoonboek'))

@app.route('/editnaam', methods=['POST'])
@login_required
def editnaam():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    telid = request.form['telid']
    nieuwenaam = request.form['nieuwenaam']
    c.execute("UPDATE telefoonboek SET name = ? WHERE id = ? AND user_id = ?",
              (nieuwenaam, telid, current_user.id))
    conn.commit()
    flash('Naam updated successfully')
    conn.close()
    return redirect(url_for('telefoonboek'))

@app.route('/removetelefoon', methods=['POST'])
@login_required
def removetelefoon():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    telid = request.form['telid']
    c.execute("DELETE FROM telefoonboek WHERE id = ? AND user_id = ?", (telid, current_user.id))
    conn.commit()
    flash('Contact deleted successfully')
    conn.close()
    return redirect(url_for('telefoonboek'))

@app.route('/films', methods=['GET', 'POST'])
@login_required
def films():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    if request.method == 'POST':
        film = request.form['film']
        jaar = request.form['jaar']
        bekeken = request.form['bekeken']
        timestamp = request.form['timestamp']
        c.execute("INSERT INTO films (user_id, film, jaar, bekeken, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (current_user.id, film, jaar, bekeken, timestamp))
        conn.commit()
        flash('Film added successfully')
    c.execute("SELECT id, film, jaar, bekeken, timestamp FROM films WHERE user_id = ?", (current_user.id,))
    films = c.fetchall()
    conn.close()
    film_data = {
        "id": [film[0] for film in films],
        "film": [film[1] for film in films],
        "jaar": [film[2] for film in films],
        "bekeken": [film[3] for film in films],
        "timestamp": [film[4] for film in films]
    }
    return render_template('films.html', current_user=current_user, **film_data)

@app.route('/addfilm', methods=['POST'])
@login_required
def addfilm():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    film = request.form['film']
    jaar = request.form['jaar']
    bekeken = request.form['bekeken']
    timestamp = request.form['timestamp']
    c.execute("INSERT INTO films (user_id, film, jaar, bekeken, timestamp) VALUES (?, ?, ?, ?, ?)",
              (current_user.id, film, jaar, bekeken, timestamp))
    conn.commit()
    flash('Film added successfully')
    conn.close()
    return redirect(url_for('films'))

@app.route('/editfilm', methods=['POST'])
@login_required
def editfilm():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    idfilm = request.form['idfilm']
    nieuwenaam = request.form['nieuwenaam']
    nieuwjaar = request.form['nieuwjaar']
    bekeken = request.form['edit_bekeken']
    timestamp = request.form['timestamp']
    c.execute("UPDATE films SET film = ?, jaar = ?, bekeken = ?, timestamp = ? WHERE id = ? AND user_id = ?",
              (nieuwenaam, nieuwjaar, bekeken, timestamp, idfilm, current_user.id))
    conn.commit()
    flash('Film updated successfully')
    conn.close()
    return redirect(url_for('films'))

@app.route('/removefilm', methods=['POST'])
@login_required
def removefilm():
    conn = sqlite3.connect("./database.db")
    c = conn.cursor()
    idfilm = request.form['idfilm']
    c.execute("DELETE FROM films WHERE id = ? AND user_id = ?", (idfilm, current_user.id))
    conn.commit()
    flash('Film deleted successfully')
    conn.close()
    return redirect(url_for('films'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return '''Hij doet het niet
            <p>
            <a href="/">
            <button>Home</button>
            </a></p>'''

create_db()

if __name__ == '__main__':
    app.run(debug=True)
