from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "hotel_booking_secret_key" # Required for flashing messages

# --- UPDATE THESE WITH YOUR MYSQL CREDENTIALS ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Mysql@123', # Update if you have a password
    'database': 'hotel_db'
}
# ------------------------------------------------

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rooms')
def rooms():
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message="Could not connect to the database. Did you run setup_db.py?")
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Rooms")
    rooms = cursor.fetchall()
    conn.close()
    
    return render_template('rooms.html', rooms=rooms)

@app.route('/book', methods=['GET', 'POST'])
def book():
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message="Could not connect to the database. Did you run setup_db.py?")
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        room_id = request.form.get('room_id')
        check_in_date = request.form.get('check_in_date')
        check_in_time = request.form.get('check_in_time')
        check_out_date = request.form.get('check_out_date')
        
        if customer_name and room_id and check_in_date and check_out_date:
            cursor.execute("""
                INSERT INTO Bookings (customer_name, room_id, check_in_date, check_in_time, check_out_date) 
                VALUES (%s, %s, %s, %s, %s)
            """, (customer_name, room_id, check_in_date, check_in_time, check_out_date))
            conn.commit()
            booking_id = cursor.lastrowid
            conn.close()
            return redirect(url_for('confirmation', booking_id=booking_id))
        else:
            flash("Please fill in all fields", "error")
            
    cursor.execute("SELECT * FROM Rooms")
    rooms = cursor.fetchall()
    conn.close()
    
    # Pre-select room if passed in URL
    selected_room = request.args.get('room_id')
    
    return render_template('book.html', rooms=rooms, selected_room=selected_room)

@app.route('/confirmation/<int:booking_id>')
def confirmation(booking_id):
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message="Could not connect to the database.")
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.booking_id, b.customer_name, r.room_type, r.price, b.check_in_date, b.check_in_time, b.check_out_date
        FROM Bookings b 
        JOIN Rooms r ON b.room_id = r.room_id 
        WHERE b.booking_id = %s
    """, (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    
    if booking:
        # Calculate total price
        from datetime import datetime
        try:
            # check_in_date and check_out_date are date objects from mysql-connector
            d1 = booking['check_in_date']
            d2 = booking['check_out_date']
            nights = (d2 - d1).days
            if nights <= 0: nights = 1 # Minimum 1 night
            booking['nights'] = nights
            booking['total_price'] = nights * booking['price']
        except Exception as e:
            print(f"Calculation Error: {e}")
            booking['nights'] = 1
            booking['total_price'] = booking['price']
            
    if not booking:
        return render_template('error.html', message="Booking not found.")
        
    return render_template('confirmation.html', booking=booking)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message="Could not connect to the database.")
        
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        room_type = request.form.get('room_type')
        price = request.form.get('price')
        description = request.form.get('description')
        
        if room_type and price:
            cursor.execute("INSERT INTO Rooms (room_type, price, description) VALUES (%s, %s, %s)", (room_type, price, description))
            conn.commit()
            flash("Room added successfully!", "success")
            return redirect(url_for('admin'))
        else:
            flash("Please provide room type and price.", "error")
            
    cursor.execute("SELECT * FROM Rooms")
    rooms = cursor.fetchall()
    
    cursor.execute("""
        SELECT b.booking_id, b.customer_name, r.room_type, r.price, b.check_in_date, b.check_in_time, b.check_out_date
        FROM Bookings b 
        JOIN Rooms r ON b.room_id = r.room_id
        ORDER BY b.booking_id DESC
    """)
    bookings = cursor.fetchall()
    
    # Calculate totals for admin view
    from datetime import datetime
    for b in bookings:
        try:
            d1 = b['check_in_date']
            d2 = b['check_out_date']
            nights = (d2 - d1).days
            if nights <= 0: nights = 1
            b['total_price'] = nights * b.get('price', 0) # Note: Need to join price in query
        except:
            b['total_price'] = 0

    conn.close()
    
    return render_template('admin.html', rooms=rooms, bookings=bookings)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message="Could not connect to the database.")
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Bookings WHERE booking_id = %s", (booking_id,))
    conn.commit()
    conn.close()
    
    flash("Booking has been successfully cancelled.", "success")
    return redirect(url_for('admin'))

@app.route('/cancel', methods=['GET', 'POST'])
def cancel():
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        
        conn = get_db_connection()
        if not conn:
            return render_template('error.html', message="Could not connect to the database.")
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Bookings WHERE booking_id = %s", (booking_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            flash(f"Booking #{booking_id} has been successfully cancelled.", "success")
        else:
            flash(f"Booking #{booking_id} was not found.", "error")
            
        return redirect(url_for('index'))
        
    return render_template('cancel.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
