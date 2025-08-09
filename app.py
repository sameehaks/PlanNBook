from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
import pymysql
from decimal import Decimal
import datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key'

try:
    db = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="plannbook_db"
    )
    cursor = db.cursor()
except Exception as e:
    print(f"Error connecting to database: {e}")


@app.route('/')
def home():
    """Renders the home page. This is the first page the user sees."""
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

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered! Try logging in.")
            return redirect(url_for('home'))

        # Insert new user into the database
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        db.commit()

        # Log in the new user automatically
        session['email'] = email
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        session['user_id'] = user[0]

        flash("Registration successful! You're now logged in.")
        return redirect(url_for('home'))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash("Please fill out all fields.")
            return redirect(url_for('home'))

        cursor.execute("SELECT id, name FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            session['email'] = email
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            flash("Login successful!")
            return redirect(url_for('home'))
        else:
            flash("Incorrect email or password. Please try again.")
            return redirect(url_for('home'))

    # If GET request, just show the homepage or login modal
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    """Logs the user out and clears the session."""
    session.pop('email', None)
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/themes')
def themes():
    """Displays available themes to the user."""
    if 'user_id' not in session:
        flash("Please login to view this page.")
        return redirect(url_for('home'))

    user_id = session['user_id']
    cursor.execute("SELECT id, name, description, image1, image2, image3 FROM themes")
    data = cursor.fetchall()
    themes = [
        {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'image1': row[3],
            'image2': row[4],
            'image3': row[5]
        } for row in data
    ]
    cursor.execute("SELECT theme_id FROM selected_theme WHERE user_id = %s", (user_id,))
    selected_ids = [row[0] for row in cursor.fetchall()]

    return render_template("themes.html", themes=themes, selected_theme_ids=selected_ids)

@app.route('/select_theme', methods=['POST'])
def select_theme():
    """Handles selecting or deselecting a theme."""
    if 'user_id' not in session:
        flash("Please login to continue.")
        return redirect(url_for('home'))

    user_id = session['user_id']
    theme_id = request.form.get('theme_id')
    action = request.form.get('action')

    if action == 'select':
        cursor.execute("DELETE FROM selected_theme WHERE user_id = %s", (user_id,))
        cursor.execute("INSERT INTO selected_theme (user_id, theme_id) VALUES (%s, %s)", (user_id, theme_id))
        flash("Theme selected successfully.")
    elif action == 'deselect':
        cursor.execute("DELETE FROM selected_theme WHERE user_id = %s AND theme_id = %s", (user_id, theme_id))
        flash("Theme deselected.")

    db.commit()
    return redirect(url_for('themes'))

@app.route('/decor')
def decor():
    """Displays available decor options."""
    if 'user_id' not in session:
        flash("Please login to view this page.")
        return redirect(url_for('home'))

    themes = ['Royal Wedding', 'Bollywood Night', 'Engagement Ceremony', 'Beach Resort',
              'Birthday Bash', 'Corporate Event', 'Haldi', 'Mehendi']

    cursor.execute("SELECT image FROM selected_decor WHERE user_id = %s", (session['user_id'],))
    selected_images = [row[0] for row in cursor.fetchall()]

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

@app.route('/select_decor', methods=['POST'])
def select_decor():
    """Handles selecting or deselecting decor items."""
    if 'user_id' not in session:
        flash("Please login to continue.")
        return redirect(url_for('home'))

    user_id = session['user_id']
    
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    user_exists = cursor.fetchone()
    if not user_exists:
        flash("Your session is invalid. Please log in again.")
        session.pop('user_id', None)
        session.pop('email', None)
        return redirect(url_for('home'))

    theme_name = request.form.get('theme')
    decor_type = request.form.get('decor_type')
    image = request.form.get('image')
    price = request.form.get('price')
    action = request.form.get('action')

    cursor.execute("SELECT id FROM decor WHERE image1 = %s OR image2 = %s OR image3 = %s OR image4 = %s", (image, image, image, image))
    result = cursor.fetchone()
    if not result:
        flash("Decor not found.")
        return redirect(url_for('decor'))

    decor_id = result[0]

    if action == 'select':
        cursor.execute("DELETE FROM selected_decor WHERE user_id=%s AND theme_name=%s", (user_id, theme_name))
        cursor.execute("""
            INSERT INTO selected_decor (user_id, decor_id, theme_name, decor_type, image, price)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, decor_id, theme_name, decor_type, image, price))
        flash(f"{decor_type} decor selected for {theme_name}.")
    elif action == 'deselect':
        cursor.execute("DELETE FROM selected_decor WHERE user_id=%s AND theme_name=%s AND image=%s",
                         (user_id, theme_name, image))
        flash(f"{decor_type} decor deselected for {theme_name}.")

    db.commit()
    return redirect(url_for('decor') + f"#{theme_name.replace(' ', '_')}")

@app.route('/foodmenu')
def foodmenu():
    """Displays the food menu based on the selected theme."""
    if 'user_id' not in session:
        flash("Please login to continue.")
        return redirect(url_for('home'))

    user_id = session['user_id']
    selected_theme = request.args.get('theme')

    cursor.execute("SELECT DISTINCT theme_name FROM food_items")
    available_themes = [row[0] for row in cursor.fetchall()]

    menu = {}
    selected_food_ids = []

    if selected_theme:
        # Fetch food items for the selected theme
        cursor.execute("""
            SELECT id, theme_name, category, name, description, price
            FROM food_items
            WHERE theme_name = %s
        """, (selected_theme,))
        food_items = cursor.fetchall()

        for row in food_items:
            price_str = str(row[5]).replace('₹', '').replace(',', '')
            try:
                price_decimal = Decimal(price_str)
            except:
                price_decimal = Decimal(0)

            item = {
                'id': row[0],
                'theme_name': row[1],
                'category': row[2],
                'name': row[3],
                'description': row[4],
                'price': price_decimal
            }
            menu.setdefault(item['category'], []).append(item)

        # Fetch the previously selected food items for the user and theme
        cursor.execute("""
            SELECT food_id
            FROM selected_food
            WHERE user_id = %s AND theme_name = %s
        """, (user_id, selected_theme))
        selected_food_ids = [row[0] for row in cursor.fetchall()]

    return render_template(
        "foodmenu.html",
        available_themes=available_themes,
        selected_theme=selected_theme,
        menu=menu,
        selected_food_ids=selected_food_ids  # Pass the list of selected IDs to the template
    )

@app.route('/select_food', methods=['POST'])
def select_food():
    """Saves the user's food item selections."""
    if 'user_id' not in session:
        flash("Please login to continue.")
        return redirect(url_for('home'))

    user_id = session['user_id']
    selected_food_ids = request.form.getlist('food_ids')
    theme_name = request.form.get('theme_name')

    cursor.execute("DELETE FROM selected_food WHERE user_id = %s AND theme_name = %s", (user_id, theme_name))

    for food_id in selected_food_ids:
        cursor.execute(
            "INSERT INTO selected_food (user_id, food_id, theme_name) VALUES (%s, %s, %s)",
            (user_id, food_id, theme_name)
        )

    db.commit()
    flash(f"Food items for {theme_name} saved successfully.")
    return redirect(url_for('foodmenu', theme=theme_name))

@app.route('/booking')
def booking():
    """Calculates and displays the total amount for the user's selections before booking."""
    if 'user_id' not in session:
        flash("Please login to continue.")
        return redirect(url_for('home'))

    user_id = session['user_id']
    total_amount = Decimal(0)

    cursor.execute("SELECT t.id, t.name FROM selected_theme st JOIN themes t ON st.theme_id = t.id WHERE st.user_id = %s", (user_id,))
    selected_theme_data = cursor.fetchone()
    selected_theme = (selected_theme_data[0], selected_theme_data[1]) if selected_theme_data else None

    cursor.execute("SELECT decor_id, price FROM selected_decor WHERE user_id = %s", (user_id,))
    selected_decor_with_price = cursor.fetchall()
    
    selected_decor = []
    if selected_decor_with_price:
        decor_ids = [item[0] for item in selected_decor_with_price]
        placeholders = ', '.join(['%s'] * len(decor_ids))
        query = f"SELECT id, decor_type FROM decor WHERE id IN ({placeholders})"
        cursor.execute(query, tuple(decor_ids))
        decor_details = {item[0]: item[1] for item in cursor.fetchall()}

        for decor_id, price in selected_decor_with_price:
            decor_type = decor_details.get(decor_id, 'N/A')
            selected_decor.append((decor_id, decor_type, price))
            try:
                price_decimal = Decimal(str(price).replace('₹', '').replace(',', ''))
                total_amount += price_decimal
            except Exception:
                print(f"Error converting decor price for decor_id {decor_id}: {price}")
    
    cursor.execute("SELECT food_id FROM selected_food WHERE user_id = %s", (user_id,))
    selected_food_ids = [row[0] for row in cursor.fetchall()]

    selected_food = []
    if selected_food_ids:
        placeholders = ', '.join(['%s'] * len(selected_food_ids))
        query = f"SELECT name, price FROM food_items WHERE id IN ({placeholders})"
        cursor.execute(query, tuple(selected_food_ids))
        selected_food = cursor.fetchall()

    for food_item in selected_food:
        try:
            price_decimal = Decimal(str(food_item[1]).replace('₹', '').replace(',', ''))
            total_amount += price_decimal
        except Exception:
            print(f"Error converting food price for food_item {food_item[0]}: {food_item[1]}")
            
    return render_template(
        "booking.html", 
        selected_theme=selected_theme, 
        selected_decor=selected_decor, 
        selected_food=selected_food, 
        total_amount=total_amount
    )

@app.route('/book_event', methods=['POST'])
def book_event():
    """
    Saves the user's booking details to the database and redirects to the payment page.
    """
    if 'user_id' not in session:
        flash("Please login to continue.")
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
    
    try:
        cursor.execute("SELECT theme_id FROM selected_theme WHERE user_id = %s", (user_id,))
        theme_id_tuple = cursor.fetchone()
        theme_id = theme_id_tuple[0] if theme_id_tuple else None
        
        if not theme_id:
            flash("Booking failed: No theme selected.")
            return redirect(url_for('booking'))

        cursor.execute("SELECT decor_id, price FROM selected_decor WHERE user_id = %s", (user_id,))
        selected_decor_raw = cursor.fetchall()
        decor_ids = [str(item[0]) for item in selected_decor_raw]
        decor_id_string = ','.join(decor_ids)

        for decor_id, price in selected_decor_raw:
            try:
                cleaned_price = str(price).replace('₹', '').replace(',', '').strip()
                if cleaned_price:
                    total_amount += Decimal(cleaned_price)
            except Exception as e:
                print(f"Error processing decor price for decor_id {decor_id}: {e}")
                
        cursor.execute("SELECT food_id FROM selected_food WHERE user_id = %s", (user_id,))
        selected_food_ids_temp = [row[0] for row in cursor.fetchall()]
        selected_food_raw = []
        if selected_food_ids_temp:
            placeholders = ', '.join(['%s'] * len(selected_food_ids_temp))
            query = f"SELECT id, price FROM food_items WHERE id IN ({placeholders})"
            cursor.execute(query, tuple(selected_food_ids_temp))
            selected_food_raw = cursor.fetchall()
        
        food_ids = [str(item[0]) for item in selected_food_raw]
        food_ids_string = ','.join(food_ids)
        for food_item in selected_food_raw:
            try:
                price_decimal = Decimal(str(food_item[1]).replace('₹', '').replace(',', ''))
                total_amount += price_decimal
            except Exception:
                print(f"Error processing food price for food_item {food_item[0]}: {food_item[1]}")

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
        db.commit()

        booking_id = cursor.lastrowid
        if not booking_id:
            db.rollback()
            flash("Booking failed: Could not create a booking ID.")
            return redirect(url_for('booking'))

        cursor.execute("DELETE FROM selected_theme WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM selected_decor WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM selected_food WHERE user_id = %s", (user_id,))
        db.commit()

        flash("Booking confirmed.")
        return redirect(url_for('payment', booking_id=booking_id))
    
    except Exception as e:
        db.rollback()
        flash(f"An error occurred during booking: {str(e)}")
        print(f"Booking failed with error: {e}")

    return redirect(url_for('booking'))

@app.route('/payment/<int:booking_id>')
def payment(booking_id):
    """
    Renders the payment page, showing the total amount, advance amount, and user details.
    """
    if 'user_id' not in session:
        flash("Please login to continue.")
        return redirect(url_for('home'))

    user_id = session['user_id']

    cursor.execute("""
        SELECT b.total_amount, u.name, u.email
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.id = %s AND b.user_id = %s
    """, (booking_id, user_id))
    booking_data = cursor.fetchone()

    if not booking_data:
        flash("Booking not found or you don't have permission to view it.")
        return redirect(url_for('home'))
    
    total_amount, name, email = booking_data
    advance_amount = total_amount * Decimal('0.10')
    
    return render_template("payment.html", booking_id=booking_id, total_amount=total_amount, advance_amount=advance_amount)

if __name__ == '__main__':
    app.run(debug=True)