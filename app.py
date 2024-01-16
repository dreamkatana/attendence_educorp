from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db = SQLAlchemy(app)

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    secret_code = db.Column(db.String(20), nullable=True)
    course_code = db.Column(db.Integer, nullable=True)
    course_class = db.Column(db.String(20), nullable=True)

@app.route('/admin')
def admin():
    classes = Class.query.all()
    return render_template('admin.html', classes=classes)

@app.route('/add_class', methods=['GET', 'POST'])
def add_class():
    if request.method == 'POST':
        class_name = request.form['name']
        secret_code = request.form['secret']
        new_class = Class(name=class_name, secret_code=secret_code)
        db.session.add(new_class)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('add_class.html')

#if __name__ == '__main__':
with app.app_context():
    db.create_all()
    app.run(debug=True)
