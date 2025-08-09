from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
import pymysql
from decimal import Decimal
import datetime
import os
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Use a strong, random secret key for session management
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

# Flask-Mail configuration - Use environment variables
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['shammishaikh29@gmail.com'] = os.environ.get('MAIL_USERNAME')
app.config['xjampcbhpihlwvgw'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

# Database Connection configuration - Use environment variables
db_config = {
    'host': os.environ.get('sameehaks.mysql.pythonanywhere-services.com'),
    'user': os.environ.get('sameehaks'),
    'password': os.environ.get('plannbooksaal'),
    'database': os.environ.get('sameehaks$plannbook_db'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Establishes a new database connection for a request."""
    return pymysql.connect(**db_config)

def get_reset_token(user_id):
    s = Serializer(app.secret_key)
    return s.dumps({'user_id': user_id}, salt='password-reset-salt')

def verify_reset_token(token):
    s = Serializer(app.secret_key, salt='password-reset-salt')
    conn = None
    cursor = None
    try:
        data = s.loads(token, max_age=1800)
        user_id = data['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, password FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return user_data
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Routes ---

@app.route('/')
def home():
    """Renders the home page."""
    return render_template("home.html")

@app.route('/aboutus')
def aboutus():
    """Renders the About Us page."""
    return render_template("aboutus.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # --- FIX: Hash the password before storing it ---
        hashed_password = generate_password_hash(password)

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Email already registered! Try logging in.", 'warning')
                return redirect(url_for('home'))

            # Insert new user into the database with the HASHED password
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
            conn.commit()

            # Log in the new user automatically
            session['email'] = email
            cursor.execute("SELECT id, name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            session['user_id'] = user['id']
            session['user_name'] = user['name']

            flash("Registration successful! You're now logged in.", 'success')
            return redirect(url_for('home'))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"An error occurred: {e}", 'danger')
            return redirect(url_for('register'))
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash("Please fill out all fields.", 'warning')
            return redirect(url_for('home'))

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # --- FIX: Fetch the HASHED password from the database ---
            cursor.execute("SELECT id, name, password FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            # --- FIX: Use check_password_hash to verify the password ---
            if user and check_password_hash(user['password'], password):
                session['email'] = email
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                flash("Login successful!", 'success')
                return redirect(url_for('home'))
            else:
                flash("Incorrect email or password. Please try again.", 'danger')
                return redirect(url_for('home'))
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
            return redirect(url_for('login'))
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    """Logs the user out and clears the session."""
    session.pop('email', None)
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/themes')
def themes():
    """Displays available themes to the user."""
    if 'user_id' not in session:
        flash("Please login to view this page.", 'warning')
        return redirect(url_for('home'))

    user_id = session['user_id']
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, image1, image2, image3 FROM themes")
        themes_data = cursor.fetchall()
        
        cursor.execute("SELECT theme_id FROM selected_theme WHERE user_id = %s", (user_id,))
        selected_ids = [row['theme_id'] for row in cursor.fetchall()]

        return render_template("themes.html", themes=themes_data, selected_theme_ids=selected_ids)
    except Exception as e:
        flash(f"An error occurred: {e}", 'danger')
        return redirect(url_for('home'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/select_theme', methods=['POST'])
def select_theme():
    """Handles selecting or deselecting a theme."""
    if 'user_id' not in session:
        flash("Please login to continue.", 'warning')
        return redirect(url_for('home'))

    user_id = session['user_id']
    theme_id = request.form.get('theme_id')
    action = request.form.get('action')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if action == 'select':
            cursor.execute("DELETE FROM selected_theme WHERE user_id = %s", (user_id,))
            cursor.execute("INSERT INTO selected_theme (user_id, theme_id) VALUES (%s, %s)", (user_id, theme_id))
            flash("Theme selected successfully.", 'success')
        elif action == 'deselect':
            cursor.execute("DELETE FROM selected_theme WHERE user_id = %s AND theme_id = %s", (user_id, theme_id))
            flash("Theme deselected.", 'info')

        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"An error occurred: {e}", 'danger')
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    
    return redirect(url_for('themes'))

@app.route('/decor')
def decor():
    """Displays available decor options."""
    if 'user_id' not in session:
        flash("Please login to view this page.", 'warning')
        return redirect(url_for('home'))

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        themes = ['Royal Wedding', 'Bollywood Night', 'Engagement Ceremony', 'Beach Resort',
                  'Birthday Bash', 'Corporate Event', 'Haldi', 'Mehendi']

        cursor.execute("SELECT image FROM selected_decor WHERE user_id = %s", (session['user_id'],))
        selected_images = [row['image'] for row in cursor.fetchall()]

        image_prices = {
            'royal_simple1.jpeg': '₹40,000', 'royal_simple2.jpeg': '₹42,000', 'royal_simple3.jpeg': '₹44,000', 'royal_simple4.jpeg': '₹46,000', 'royal_elegant1.jpeg': '₹72,000', 'royal_elegant2.jpeg': '₹80,000', 'royal_elegant3.jpeg': '₹75,000', 'royal_elegant4.jpeg': '₹82,000', 'royal_premium1.jpeg': '₹150,000', 'royal_premium2.jpeg': '₹120,000', 'royal_premium3.jpeg': '₹125,000', 'royal_premium4.jpeg': '₹130,000',
            'bolly_simple1.jpeg': '₹40,000', 'bolly_simple2.jpeg': '₹42,000', 'bolly_simple3.jpeg': '₹43,000', 'bolly_simple4.jpeg': '₹45,000', 'bolly_elegant1.jpeg': '₹72,000', 'bolly_elegant2.jpeg': '₹75,000', 'bolly_elegant3.jpeg': '₹77,000', 'bolly_elegant4.jpeg': '₹80,000', 'bolly_premium1.jpeg': '₹115,000', 'bolly_premium2.jpeg': '₹118,000', 'bolly_premium3.jpeg': '₹120,000', 'bolly_premium4.jpeg': '₹122,000',
            'birthday_simple1.jpeg': '₹42,000', 'birthday_simple2.jpeg': '₹45,000', 'birthday_simple3.jpeg': '₹40,000', 'birthday_simple4.jpeg': '₹43,000', 'birthday_elegant1.jpeg': '₹70,000', 'birthday_elegant2.jpeg': '₹72,000', 'birthday_elegant3.jpeg': '₹74,000', 'birthday_elegant4.jpeg': '₹76,000', 'birthday_premium1.jpeg': '₹93,000', 'birthday_premium2.jpeg': '₹95,000', 'birthday_premium3.jpeg': '₹97,000', 'birthday_premium4.jpeg': '₹100,000',
            'engage_simple1.jpeg': '₹30,000', 'engage_simple2.jpeg': '₹32,000', 'engage_simple3.jpeg': '₹33,000', 'engage_simple4.jpeg': '₹35,000', 'engage_elegant1.jpeg': '₹60,000', 'engage_elegant2.jpeg': '₹62,000', 'engage_elegant3.jpeg': '₹65,000', 'engage_elegant4.jpeg': '₹68,000', 'engage_premium1.jpeg': '₹90,000', 'engage_premium2.jpeg': '₹92,000', 'engage_premium3.jpeg': '₹94,000', 'engage_premium4.jpeg': '₹97,000',
            'beach_simple1.jpeg': '₹45,000', 'beach_simple2.jpeg': '₹47,000', 'beach_simple3.jpeg': '₹48,000', 'beach_simple4.jpeg': '₹49,000', 'beach_elegant1.jpeg': '₹78,000', 'beach_elegant2.jpeg': '₹80,000', 'beach_elegant3.jpeg': '₹82,000', 'beach_elegant4.jpeg': '₹85,000', 'beach_premium1.jpeg': '₹110,000', 'beach_premium2.jpeg': '₹112,000', 'beach_premium3.jpeg': '₹114,000', 'beach_premium4.jpeg': '₹118,000',
            'corporate_simple1.jpeg': '₹25,000', 'corporate_simple2.jpeg': '₹28,000', 'corporate_simple3.jpeg': '₹30,000', 'corporate_simple4.jpeg': '₹32,000', 'corporate_elegant1.jpeg': '₹55,000', 'corporate_elegant2.jpeg': '₹58,000', 'corporate_elegant3.jpeg': '₹60,000', 'corporate_elegant4.jpeg': '₹63,000', 'corporate_premium1.jpeg': '₹85,000', 'corporate_premium2.jpeg': '₹87,000', 'corporate_premium3.jpeg': '₹89,000', 'corporate_premium4.jpeg': '₹92,000',
            'haldi_simple1.jpeg': '₹20,000', 'haldi_simple2.jpeg': '₹22,000', 'haldi_simple3.jpeg': '₹24,000', 'haldi_simple4.jpeg': '₹25,000', 'haldi_elegant1.jpeg': '₹40,000', 'haldi_elegant2.jpeg': '₹42,000', 'haldi_elegant3.jpeg': '₹44,000', 'haldi_elegant4.jpeg': '₹45,000', 'haldi_premium1.jpeg': '₹65,000', 'haldi_premium2.jpeg': '₹68,000', 'haldi_premium3.jpeg': '₹70,000', 'haldi_premium4.jpeg': '₹72,000',
            'mehendi_simple1.jpeg': '₹22,000', 'mehendi_simple2.jpeg': '₹24,000', 'mehendi_simple3.jpeg': '₹26,000', 'mehendi_simple4.jpeg': '₹28,000', 'mehendi_elegant1.jpeg': '₹45,000', 'mehendi_elegant2.jpeg': '₹47,000', 'mehendi_elegant3.jpeg': '₹50,000', 'mehendi_elegant4.jpeg': '₹52,000', 'mehendi_premium1.jpeg': '₹75,000', 'mehendi_premium2.jpeg': '₹78,000', 'mehendi_premium3.jpeg': '₹80,000', 'mehendi_premium4.jpeg': '₹83,000'
        }
        return render_template("decor.html", themes=themes, selected_image_names=selected_images, image_prices=image_prices)
    except Exception as e:
        flash(f"An error occurred: {e}", 'danger')
        return redirect(url_for('home'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/select_decor', methods=['POST'])
def select_decor():
    """Handles selecting or deselecting decor items."""
    if 'user_id' not in session:
        flash("Please login to continue.", 'warning')
        return redirect(url_for('home'))

    user_id = session['user_id']
    theme_name = request.form.get('theme')
    decor_type = request.form.get('decor_type')
    image = request.form.get('image')
    price = request.form.get('price')
    action = request.form.get('action')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user_exists = cursor.fetchone()
        if not user_exists:
            flash("Your session is invalid. Please log in again.", 'danger')
            session.clear()
            return redirect(url_for('home'))

        cursor.execute("SELECT id FROM decor WHERE image1 = %s OR image2 = %s OR image3 = %s OR image4 = %s", (image, image, image, image))
        result = cursor.fetchone()
        if not result:
            flash("Decor not found.", 'danger')
            return redirect(url_for('decor'))

        decor_id = result['id']

        if action == 'select':
            cursor.execute("DELETE FROM selected_decor WHERE user_id=%s AND theme_name=%s", (user_id, theme_name))
            cursor.execute("""
                INSERT INTO selected_decor (user_id, decor_id, theme_name, decor_type, image, price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, decor_id, theme_name, decor_type, image, price))
            flash(f"{decor_type} decor selected for {theme_name}.", 'success')
        elif action == 'deselect':
            cursor.execute("DELETE FROM selected_decor WHERE user_id=%s AND theme_name=%s AND image=%s",
                            (user_id, theme_name, image))
            flash(f"{decor_type} decor deselected for {theme_name}.", 'info')

        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"An error occurred: {e}", 'danger')
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return redirect(url_for('decor') + f"#{theme_name.replace(' ', '_')}")

@app.route('/foodmenu')
def foodmenu():
    """Displays the food menu based on the selected theme."""
    if 'user_id' not in session:
        flash("Please login to continue.", 'warning')
        return redirect(url_for('home'))

    user_id = session['user_id']
    selected_theme = request.args.get('theme')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT theme_name FROM food_items")
        available_themes = [row['theme_name'] for row in cursor.fetchall()]

        menu = {}
        selected_food_ids = []

        if selected_theme:
            cursor.execute("""
                SELECT id, theme_name, category, name, description, price
                FROM food_items
                WHERE theme_name = %s
            """, (selected_theme,))
            food_items = cursor.fetchall()

            for item in food_items:
                menu.setdefault(item['category'], []).append(item)

            cursor.execute("""
                SELECT food_id
                FROM selected_food
                WHERE user_id = %s AND theme_name = %s
            """, (user_id, selected_theme))
            selected_food_ids = [row['food_id'] for row in cursor.fetchall()]

        return render_template(
            "foodmenu.html",
            available_themes=available_themes,
            selected_theme=selected_theme,
            menu=menu,
            selected_food_ids=selected_food_ids
        )
    except Exception as e:
        flash(f"An error occurred: {e}", 'danger')
        return redirect(url_for('home'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/select_food', methods=['POST'])
def select_food():
    """Saves the user's food item selections."""
    if 'user_id' not in session:
        flash("Please login to continue.", 'warning')
        return redirect(url_for('home'))

    user_id = session['user_id']
    selected_food_ids = request.form.getlist('food_ids')
    theme_name = request.form.get('theme_name')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM selected_food WHERE user_id = %s AND theme_name = %s", (user_id, theme_name))

        for food_id in selected_food_ids:
            cursor.execute(
                "INSERT INTO selected_food (user_id, food_id, theme_name) VALUES (%s, %s, %s)",
                (user_id, food_id, theme_name)
            )

        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"An error occurred: {e}", 'danger')
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    flash(f"Food items for {theme_name} saved successfully.", 'success')
    return redirect(url_for('foodmenu', theme=theme_name))

@app.route('/booking')
def booking():
    """Calculates and displays the total amount for the user's selections before booking."""
    if 'user_id' not in session:
        flash("Please login to continue.", 'warning')
        return redirect(url_for('home'))

    user_id = session['user_id']
    total_amount = Decimal(0)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch selected theme
        cursor.execute("SELECT t.id, t.name FROM selected_theme st JOIN themes t ON st.theme_id = t.id WHERE st.user_id = %s", (user_id,))
        selected_theme_data = cursor.fetchone()
        selected_theme = (selected_theme_data['id'], selected_theme_data['name']) if selected_theme_data else None

        # Fetch selected decor and calculate price
        cursor.execute("SELECT decor_type, price FROM selected_decor WHERE user_id = %s", (user_id,))
        selected_decor_with_price = cursor.fetchall()
        
        selected_decor = []
        for decor_item in selected_decor_with_price:
            try:
                price_str = str(decor_item['price']).replace('₹', '').replace(',', '').strip()
                price_decimal = Decimal(price_str)
                total_amount += price_decimal
                selected_decor.append((decor_item['decor_type'], decor_item['price']))
            except Exception as e:
                print(f"Error converting decor price: {e}")

        # Fetch selected food and calculate price
        cursor.execute("SELECT food_id FROM selected_food WHERE user_id = %s", (user_id,))
        selected_food_ids = [row['food_id'] for row in cursor.fetchall()]

        selected_food = []
        if selected_food_ids:
            placeholders = ', '.join(['%s'] * len(selected_food_ids))
            query = f"SELECT name, price FROM food_items WHERE id IN ({placeholders})"
            cursor.execute(query, tuple(selected_food_ids))
            selected_food = cursor.fetchall()

        for food_item in selected_food:
            try:
                price_str = str(food_item['price']).replace('₹', '').replace(',', '').strip()
                price_decimal = Decimal(price_str)
                total_amount += price_decimal
            except Exception as e:
                print(f"Error converting food price: {e}")

        return render_template(
            "booking.html",
            selected_theme=selected_theme,
            selected_decor=selected_decor,
            selected_food=selected_food,
            total_amount=total_amount
        )
    except Exception as e:
        flash(f"An error occurred: {e}", 'danger')
        return redirect(url_for('home'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/book_event', methods=['POST'])
def book_event():
    """Saves the user's booking details to the database."""
    if 'user_id' not in session:
        flash("Please login to continue.", 'warning')
        return redirect(url_for('home'))

    user_id = session['user_id']
    event_date = request.form.get('event_date')
    event_time = request.form.get('event_time')
    guests = request.form.get('guests')
    your_location = request.form.get('your_location')
    event_address = request.form.get('event_address')
    phone_number = request.form.get('phone_number')
    notes = request.form.get('notes')
    created_at = datetime.datetime.now()
    total_amount = Decimal(0)

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT theme_id FROM selected_theme WHERE user_id = %s", (user_id,))
        theme_id_tuple = cursor.fetchone()
        theme_id = theme_id_tuple['theme_id'] if theme_id_tuple else None

        if not theme_id:
            flash("Booking failed: No theme selected.", 'danger')
            return redirect(url_for('booking'))

        cursor.execute("SELECT decor_id, price FROM selected_decor WHERE user_id = %s", (user_id,))
        selected_decor_raw = cursor.fetchall()
        decor_ids = [str(item['decor_id']) for item in selected_decor_raw]
        decor_id_string = ','.join(decor_ids)

        for item in selected_decor_raw:
            try:
                cleaned_price = str(item['price']).replace('₹', '').replace(',', '').strip()
                if cleaned_price:
                    total_amount += Decimal(cleaned_price)
            except Exception as e:
                print(f"Error processing decor price: {e}")

        cursor.execute("SELECT food_id FROM selected_food WHERE user_id = %s", (user_id,))
        selected_food_ids_temp = [row['food_id'] for row in cursor.fetchall()]
        selected_food_raw = []
        if selected_food_ids_temp:
            placeholders = ', '.join(['%s'] * len(selected_food_ids_temp))
            query = f"SELECT id, price FROM food_items WHERE id IN ({placeholders})"
            cursor.execute(query, tuple(selected_food_ids_temp))
            selected_food_raw = cursor.fetchall()

        food_ids = [str(item['id']) for item in selected_food_raw]
        food_ids_string = ','.join(food_ids)

        for food_item in selected_food_raw:
            try:
                price_decimal = Decimal(str(food_item['price']).replace('₹', '').replace(',', ''))
                total_amount += price_decimal
            except Exception as e:
                print(f"Error processing food price: {e}")

        cursor.execute(
            """
            INSERT INTO bookings (
                user_id, theme_id, decor_ids, food_ids, event_date, event_time,
                guests, location, event_address, special_requests, created_at,
                phone_number, total_amount
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id, theme_id, decor_id_string, food_ids_string, event_date, event_time,
                guests, your_location, event_address, notes, created_at,
                phone_number, total_amount
            )
        )
        conn.commit()

        booking_id = cursor.lastrowid
        if not booking_id:
            if conn:
                conn.rollback()
            flash("Booking failed: Could not create a booking ID.", 'danger')
            return redirect(url_for('booking'))

        # Clear the user's selections after a successful booking
        cursor.execute("DELETE FROM selected_theme WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM selected_decor WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM selected_food WHERE user_id = %s", (user_id,))
        conn.commit()

        flash("Booking confirmed.", 'success')
        return redirect(url_for('payment', booking_id=booking_id))
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"An error occurred during booking: {str(e)}", 'danger')
        print(f"Booking failed with error: {e}")
        return redirect(url_for('booking'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/payment/<int:booking_id>')
def payment(booking_id):
    """Renders the payment page, showing the total amount, advance amount, and user details."""
    if 'user_id' not in session:
        flash("Please login to continue.", 'warning')
        return redirect(url_for('home'))

    user_id = session['user_id']
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.total_amount, u.name, u.email
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE b.id = %s AND b.user_id = %s
        """, (booking_id, user_id))
        booking_data = cursor.fetchone()

        if not booking_data:
            flash("Booking not found or you don't have permission to view it.", 'danger')
            return redirect(url_for('home'))

        total_amount = booking_data['total_amount']
        name = booking_data['name']
        email = booking_data['email']
        advance_amount = total_amount * Decimal('0.10')

        return render_template("payment.html", booking_id=booking_id, total_amount=total_amount, advance_amount=advance_amount, name=name, email=email)
    except Exception as e:
        flash(f"An error occurred: {e}", 'danger')
        return redirect(url_for('home'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Password Reset Routes ---
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_id_tuple = cursor.fetchone()

            if user_id_tuple:
                user_id = int(user_id_tuple['id'])
                token = get_reset_token(user_id)
                reset_url = url_for('reset_token', token=token, _external=True)

                msg = Message(
                    'Password Reset Request',
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[email]
                )
                msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, simply ignore this email.
'''
                mail.send(msg)
            
            flash('If your email is in our system, you will receive a password reset link shortly.', 'info')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred while sending the email: {e}", 'danger')
            return redirect(url_for('forgot_password'))
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    return render_template('forgot_password.html')

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    user = verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_token.html', token=token)

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # --- FIX: Hash the new password before updating it ---
            hashed_password = generate_password_hash(password)
            cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, user['id']))
            conn.commit()
            flash('Your password has been updated! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"An error occurred while updating the password: {e}", 'danger')
            return render_template('reset_token.html', token=token)
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    return render_template('reset_token.html', token=token)

if __name__ == '__main__':
    app.run(debug=True)