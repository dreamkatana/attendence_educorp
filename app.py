import uuid
import csv
from flask import Flask, render_template, redirect, url_for, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from io import StringIO

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
    unique_link = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(50))
    course_class = db.Column(db.String(50))
    emp = db.Column(db.Integer)
    matricula = db.Column(db.Integer)
    email = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

@app.route('/admin')
def admin():
    classes = Class.query.all()
    class_attendance_counts = db.session.query(
        Class.course_code,
        Class.course_class,
        db.func.count(Attendance.matricula)
    ).outerjoin(
        Attendance,
        db.and_(Class.course_code == Attendance.course_code, Class.course_class == Attendance.course_class)
    ).group_by(Class.course_code, Class.course_class).all()

    # Convert class_attendance_counts to a dictionary for easy access in the template
    attendance_dict = {(course_code, course_class): count for course_code, course_class, count in class_attendance_counts}

    return render_template('admin.html', classes=classes, attendance_dict=attendance_dict)


@app.route('/add_class', methods=['GET', 'POST'])
def add_class():
    if request.method == 'POST':
        class_name = request.form['name']
        secret_code = request.form['secret']
        course_code = request.form['course_code']
        course_class = request.form['course_class']
        new_class = Class(name=class_name, secret_code=secret_code, course_code=course_code, course_class=course_class)
        db.session.add(new_class)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('add_class.html')

@app.route('/attend/<unique_link>', methods=['GET', 'POST'])
def attend(unique_link):
    course = Class.query.filter_by(unique_link=unique_link).first_or_404()
    if request.method == 'POST':
        matricula = request.form['matricula']
        email = request.form['email']  # Assuming you want to capture the email
        secret = request.form['secret']
        if secret == course.secret_code:
            attendance = Attendance(course_code=course.course_code, course_class=course.course_class, emp=1, matricula=matricula, email=email)
            db.session.add(attendance)
            db.session.commit()
            # Format the response as needed
            return jsonify({"message": "Attendance registered successfully"})
        else:
            return jsonify({"error": "Invalid secret code"}), 400
    return render_template('attendance_form.html', course=course)

@app.route('/attendance_data/<course_code>/<course_class>')
def filtered_attendance_data(course_code, course_class):
    attendances = Attendance.query.filter_by(course_code=course_code, course_class=course_class).all()
    return render_template('attendance_data.html', attendances=attendances, course_code=course_code, course_class=course_class)

@app.route('/export_attendance_csv/<course_code>/<course_class>')
def export_attendance_csv(course_code, course_class):
    # Filter attendance records by course_code and course_class
    attendances = Attendance.query.filter_by(course_code=course_code, course_class=course_class).all()

    def generate():
        data = StringIO()
        csv_writer = csv.writer(data)

        # Write the header
        csv_writer.writerow(["01", "CURSO", "TURMA", "EMP", "MATRICULA", "DATA"])

        # Write the data rows
        for attendance in attendances:
            csv_writer.writerow([
                "02",
                attendance.course_code,
                attendance.course_class,
                "1",  # EMP is always 1
                attendance.matricula,
                attendance.date.strftime('%d/%m/%Y')  # Format the date
            ])
            data.seek(0)
            yield data.read()
            data.seek(0)
            data.truncate(0)

    # Generate the CSV file
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": f"attachment;filename=attendance_data_{course_code}_{course_class}.csv"})


#if __name__ == '__main__':
with app.app_context():
    db.create_all()
    app.run(debug=True)
