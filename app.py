from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file named 'site.db'
db = SQLAlchemy(app)

# Define the data models
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Task', backref='worker', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50), nullable=False)
    tasks_done = db.Column(db.Integer, nullable=False)

# Wrap the creation of tables within the application context
with app.app_context():
    # Create the database tables
    db.create_all()

# Sample data for categories, subcategories, and prices
categories = ["Tshirts", "Shirts", "Saree", "Jeans"]
subcategories = {
    "Tshirts": ["Front", "Back", "Sleeves"],
    "Shirts": ["Front", "Back", "Sleeves"],
    "Saree": ["Pallu", "Pleats"],
    "Jeans": ["Front", "Back", "Pockets"]
}
prices = {
    "Tshirts": {"Front": 5, "Back": 4, "Sleeves": 3},
    "Shirts": {"Front": 6, "Back": 5, "Sleeves": 4},
    "Saree": {"Pallu": 8, "Pleats": 7},
    "Jeans": {"Front": 7, "Back": 6, "Pockets": 5}
}

@app.route('/')
def home():
    workers = Worker.query.all()
    return render_template('index.html', workers=workers)

@app.route('/salary_calculator', methods=['GET', 'POST'])
def salary_calculator():
    if request.method == 'POST':
        worker_name = request.form['worker_name']

        # Create a new worker or get the existing one
        worker = Worker.query.filter_by(name=worker_name).first()
        if worker is None:
            worker = Worker(name=worker_name)
            db.session.add(worker)
            db.session.commit()

        # Loop through categories and subcategories to get task-wise data
        for category in categories:
            for subcategory in subcategories[category]:
                task_key = f"{category}_{subcategory}"
                tasks_done = int(request.form.get(f'{task_key}_tasks_done', 0))

                # Save tasks to the database
                task = Task(worker_id=worker.id, category=category, subcategory=subcategory, tasks_done=tasks_done)
                db.session.add(task)
                db.session.commit()

        return redirect(url_for('result', worker_id=worker.id))

    return render_template('salary_calculator.html', categories=categories, subcategories=subcategories, prices=prices)

@app.route('/result/<int:worker_id>')
def result(worker_id):
    worker = Worker.query.get(worker_id)
    tasks_data = Task.query.filter_by(worker_id=worker.id).all()
    total_salary = calculate_total_salary(tasks_data)
    return render_template('result.html', worker=worker, tasks_data=tasks_data, total_salary=total_salary)

def calculate_total_salary(tasks_data):
    total_salary = 0
    for task in tasks_data:
        price = prices[task.category][task.subcategory]
        total_salary += task.tasks_done * price
    return total_salary


# Delete Worker route
@app.route('/delete_worker/<int:worker_id>', methods=['GET', 'POST'])
def delete_worker(worker_id):
    try:
        worker = Worker.query.get(worker_id)

        if request.method == "POST":
            # Delete associated tasks
            Task.query.filter_by(worker_id=worker.id).delete()

            # Delete worker
            db.session.delete(worker)
            db.session.commit()

            return redirect(url_for('home'))

        return render_template('delete_worker.html', worker=worker)

    except NoResultFound:
        # Handle the case where the worker with the given ID is not found
        return render_template('error.html', message="Worker not found")


if __name__ == '__main__':
    app.run(debug=True)

