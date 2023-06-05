from datetime import datetime
from flask import Flask , render_template , request , flash , redirect , url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
from sqlalchemy.orm import relationship

app = Flask(__name__)

app.secret_key="RafikYoucef"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clients.sqlite3'
app.config['SQLACHEMY_TRACK_MODIFICATIONS'] = False 
db = SQLAlchemy(app)



#clients datadabe

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    checkin_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    checkout_date = db.Column(db.DateTime, nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room._id'))  # Foreign key to reference the assigned room
    assigned_room = db.relationship('Room', backref='clients')  # Relationship to access the assigned room

    def __init__(self, name, email, checkin_date, checkout_date):
        self.name = name
        self.email = email
        self.checkin_date = checkin_date
        self.checkout_date = checkout_date

#room database

class Room(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), nullable=False)
    room_type = db.Column(db.Enum('OneBedroom', 'FamilyRoom', 'Suite'), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, default=True)


    def __init__(self, number, room_type, price):
        self.number = number
        self.room_type = room_type
        self.price = price
        self.is_available = True

with app.app_context():  
     db.create_all()


def calculate_total_price(checkin_date, checkout_date, room):
    # Calculate the number of days
    num_days = (checkout_date - checkin_date).days

    # Get the room price
    room_price = room.price

    # Calculate the total price
    total_price = room_price * num_days

    return total_price

@app.route("/")

def home():
    return render_template("index.html")

        
@app.route('/admin', methods=['GET', 'POST'])

def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username and password are correct
        if username == 'Rafik' and password == '2003':
            # If the username and password are correct, redirect to the rooms page
            return redirect(url_for('gestion'))
        else:
            # If the username and password are incorrect, flash an error message
            flash('Your Username/Password are incorrect!', 'error')
            return redirect(url_for('admin'))
    else:
        # If it's a GET request, render the admin template
        return render_template('admin.html')


@app.route('/rooms')

def rooms():
    # Render the rooms template
    roo = Room.query.all()
    return render_template('rooms.html' , rooms=roo)


@app.route('/clients')

def clients():    
    client = Client.query.all()
    
    return render_template('clients.html' , clients=client)


@app.route('/gestion')

def gestion():

    return render_template('gestion.html')




@app.route('/add_room', methods=['GET','POST'])

def add_room():

    if request.method == 'POST':
        number = request.form['number']
        room_type = request.form['room_type']
        price = request.form['price']

        # Create a new Room object
        new_room = Room(number=number, room_type=room_type, price=price)

        # Add the new room to the database
        db.session.add(new_room)
        db.session.commit()

        # Redirect to rooms route
        return redirect(url_for('rooms'))

    else:   
        # Render the add_room.html template for GET requests
        return render_template('add_room.html')


@app.route('/delete_room', methods=['GET','POST'])

def delete_room():
    if request.method == 'POST':
        room_id = request.form['room_id']

    # Retrieve the room from the database based on the ID
        room = Room.query.get(room_id)

        if room:
            # Delete the room from the database
            db.session.delete(room)
            db.session.commit()
            flash('Room deleted successfully', 'success')
        else:
            flash('Room not found', 'error')

        # Redirect back to the rooms page
        return redirect(url_for('rooms')) 
    else:
        return render_template('delete_room.html')       


@app.route('/booking', methods=['GET', 'POST'])

def booking():

    if request.method == 'POST':
        # Get the form data
        name = request.form['name']
        email = request.form['email']
        checkin_date = datetime.strptime(request.form['checkin'], '%Y-%m-%d')
        checkout_date = datetime.strptime(request.form['checkout'], '%Y-%m-%d')
        room_type = request.form['room_type']

        existing_client = Client.query.filter_by(email=email).first()
        if existing_client:
            flash('Email already exists', 'error')
            return render_template('Form_booking.html')
        # Find an available room of the specified type and assign it to the client
        room = Room.query.filter_by(room_type=room_type, is_available=True).first()
        if not room:
            flash('Sorry, no rooms of this type are available', 'error')
            return render_template('Form_booking.html')

        # Create a new client entry in the database
        client = Client(name=name, email=email, checkin_date=checkin_date, checkout_date=checkout_date)
        db.session.add(client)
        db.session.commit()

        # Assign the room to the client
        client.assigned_room = room
        room.is_available = False

        # Calculate the total price
        total_price = calculate_total_price(checkin_date, checkout_date, room)

        
        return render_template('booking_details.html', client=client, total_price=total_price)

    else:
        return render_template('Form_booking.html')

if __name__ == "__main__":
    app.run(debug=True)
