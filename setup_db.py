import mysql.connector

# --- UPDATE THESE WITH YOUR MYSQL CREDENTIALS ---
DB_USER = 'root'
DB_PASSWORD = 'Mysql@123' # Change this to your password! (e.g. 'root')
DB_HOST = 'localhost'
# ------------------------------------------------

def setup_database():
    try:
        print("Connecting to MySQL...")
        # Connect to MySQL server
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # Create Database
        cursor.execute("CREATE DATABASE IF NOT EXISTS hotel_db")
        print("Database 'hotel_db' created or already exists.")

        # Switch to the database
        cursor.execute("USE hotel_db")

        # Create Rooms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Rooms (
                room_id INT AUTO_INCREMENT PRIMARY KEY,
                room_type VARCHAR(255) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                description TEXT
            )
        """)
        print("Table 'Rooms' created or already exists.")

        # Create Bookings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Bookings (
                booking_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(255) NOT NULL,
                room_id INT,
                check_in_date DATE,
                check_in_time TIME,
                check_out_date DATE,
                FOREIGN KEY (room_id) REFERENCES Rooms(room_id) ON DELETE CASCADE
            )
        """)
        print("Table 'Bookings' created or already exists.")

        # Insert some dummy rooms if empty
        cursor.execute("SELECT COUNT(*) FROM Rooms")
        if cursor.fetchone()[0] == 0:
            rooms_data = [
                ('Standard Room', 1200.00, 'A cozy room with a queen-size bed, perfect for solo travelers or couples.'),
                ('Deluxe Room', 2200.00, 'Spacious room with a king-size bed, seating area, and beautiful city views.'),
                ('Luxury Suite', 4500.00, 'Premium living space with separate lounge, sophisticated decor, and high-end amenities.'),
                ('Presidential Suite', 8500.00, 'The ultimate luxury experience with panoramic views, private dining, and opulent furnishings.')
            ]
            cursor.executemany("INSERT INTO Rooms (room_type, price, description) VALUES (%s, %s, %s)", rooms_data)
            conn.commit()
            print("Inserted default rooms.")

        print("Database setup complete! You can now run app.py")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        print("\nPlease check your MySQL credentials (DB_USER, DB_PASSWORD) at the top of this file and ensure your MySQL server is running.")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_database()
