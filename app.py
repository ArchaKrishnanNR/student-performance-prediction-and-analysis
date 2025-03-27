import os
from flask import Flask, render_template, jsonify, request, redirect, session, flash, url_for
import mysql.connector
import hashlib
import datetime
import joblib
import numpy as np
import json  # Import json for proper handling of lists in URLs

app = Flask(__name__)
app.secret_key = "lbs2025"  # Secret key for session and flash messages

# Load ML Model and Thresholds
model = joblib.load('student_model.pkl')
thresholds = joblib.load('thresholds.pkl')

# Database Connection Function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Athira2004@",  # Change this to your MySQL password
        database="student_performance_prediction_and_analysis"
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['loginUsername']
        password = hashlib.sha256(request.form['loginPassword'].encode()).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username  # Store user session
            login_time = datetime.datetime.now()
            cursor.execute("INSERT INTO userlogin (username, login_time) VALUES (%s, %s)", (username, login_time))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        else:
            conn.close()
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['registerUsername']
    email = request.form['registerEmail']
    password = hashlib.sha256(request.form['registerPassword'].encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        conn.commit()
        conn.close()
        flash("Registration Successful! You can now log in.", "success")
        return redirect(url_for('login'))
    except mysql.connector.IntegrityError:
        conn.close()
        flash("Username or Email already exists. Try a different one.", "error")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))
@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'GET':
        # Render the prediction form if accessed via GET
        return render_template('prediction.html')

    if 'username' not in session:
        flash("Please log in to make predictions.", "error")
        return redirect(url_for('login'))

    username = session['username']
    student_id = request.form.get('studentid')

    # Validate Student ID
    if not student_id:
        flash("Student ID is required.", "error")
        return redirect(url_for('home'))

    # Print form data for debugging
    print("Form data received:")
    for key, value in request.form.items():
        print(f"{key}: {value}")

    conn = None
    try:
        # Preprocess categorical values
        gender = 1 if request.form.get('gender', '').lower() == 'male' else 0
        age = int(request.form.get('age', 0))
        address = 1 if request.form.get('address', '').lower() == 'urban' else 0
        parent_education = int(request.form.get('parentEducation', 0))
        travel_time = int(request.form.get('travelTime', 0))
        study_time = int(request.form.get('studyTime', 0))
        failures = int(request.form.get('failures', 0))
        extra_classes = 1 if request.form.get('extraClasses', '').lower() == 'yes' else 0
        extra_curricular = 1 if request.form.get('extraCurricular', '').lower() == 'yes' else 0
        internet_access = 1 if request.form.get('internetAccess', '').lower() == 'yes' else 0
        health = int(request.form.get('health', 0))
        absences = int(request.form.get('absences', 0))
        sub1_mark = int(request.form.get('subject1Mark', 0))
        sub2_mark = int(request.form.get('subject2Mark', 0))
        sub3_mark = int(request.form.get('subject3Mark', 0))

        # Print processed data for debugging
        print(f"Processed data for student {student_id}:")
        print(f"gender: {gender}, age: {age}, address: {address}, parent_education: {parent_education}")
        print(f"travel_time: {travel_time}, study_time: {study_time}, failures: {failures}")
        print(f"extra_classes: {extra_classes}, extra_curricular: {extra_curricular}")
        print(f"internet_access: {internet_access}, health: {health}, absences: {absences}")
        print(f"sub1_mark: {sub1_mark}, sub2_mark: {sub2_mark}, sub3_mark: {sub3_mark}")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Store student data with better error handling
        try:
            print("Attempting to insert/update student data...")
            query = """
                INSERT INTO student (student_id, username, gender, age, address, parent_education, travel_time,
                                    study_time, failures, extra_classes, extra_curricular, internet_access,
                                    health, absences, sub1_mark, sub2_mark, sub3_mark)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    gender = VALUES(gender),
                    age = VALUES(age),
                    address = VALUES(address),
                    parent_education = VALUES(parent_education),
                    travel_time = VALUES(travel_time),
                    study_time = VALUES(study_time),
                    failures = VALUES(failures),
                    extra_classes = VALUES(extra_classes),
                    extra_curricular = VALUES(extra_curricular),
                    internet_access = VALUES(internet_access),
                    health = VALUES(health),
                    absences = VALUES(absences),
                    sub1_mark = VALUES(sub1_mark),
                    sub2_mark = VALUES(sub2_mark),
                    sub3_mark = VALUES(sub3_mark)
            """

            params = (student_id, username, gender, age, address, parent_education, travel_time,
                      study_time, failures, extra_classes, extra_curricular, internet_access,
                      health, absences, sub1_mark, sub2_mark, sub3_mark)

            cursor.execute(query, params)

            # Check if rows were affected
            rows_affected = cursor.rowcount
            print(f"Student table update - rows affected: {rows_affected}")

            conn.commit()
            print("Student data successfully committed")
        except mysql.connector.Error as db_err:
            print(f"Database error during student update: {db_err}")
            if conn:
                conn.rollback()
            flash(f"Database error: {str(db_err)}", "error")
            return redirect(url_for('home'))

        # Verify the data was stored by fetching it back
        print("Verifying stored student data...")
        try:
            cursor.execute("""
                SELECT gender, age, address, parent_education, travel_time, study_time, failures,
                       extra_classes, extra_curricular, internet_access, health, absences,
                       sub1_mark, sub2_mark, sub3_mark
                FROM student
                WHERE student_id = %s
            """, (student_id,))

            student_data = cursor.fetchone()

            if not student_data:
                print(f"ERROR: No data found for student_id {student_id} after insert/update")
                flash("Failed to store student data.", "error")
                return redirect(url_for('home'))

            print(f"Retrieved student data: {student_data}")

            student_data = np.array(student_data, dtype=np.float64).reshape(1, -1)

            # Predict marks
            predicted_marks = model.predict(student_data)[0]
            print(f"Predicted marks: {predicted_marks}")

            weak_subjects = []
            if predicted_marks[0] < thresholds['Sub1']:
                weak_subjects.append("Subject 1")
            if predicted_marks[1] < thresholds['Sub2']:
                weak_subjects.append("Subject 2")
            if predicted_marks[2] < thresholds['Sub3']:
                weak_subjects.append("Subject 3")

            weak_subjects_str = ", ".join(weak_subjects) if weak_subjects else "None"
            print(f"Weak subjects: {weak_subjects_str}")

            # Store prediction results in session for result page
            session['prediction_results'] = {
                'sub1': int(predicted_marks[0]),
                'sub2': int(predicted_marks[1]),
                'sub3': int(predicted_marks[2]),
                'weak_subjects': weak_subjects_str
            }

            # Store prediction results in database
            try:
                print("Storing prediction results...")
                cursor.execute("""
                    INSERT INTO prediction (username, studentid, predicted_sub1, predicted_sub2, predicted_sub3, weak_subject)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        predicted_sub1 = VALUES(predicted_sub1),
                        predicted_sub2 = VALUES(predicted_sub2),
                        predicted_sub3 = VALUES(predicted_sub3),
                        weak_subject = VALUES(weak_subject)
                """, (username, student_id, int(predicted_marks[0]), int(predicted_marks[1]), int(predicted_marks[2]), weak_subjects_str))

                rows_affected = cursor.rowcount
                print(f"Prediction table update - rows affected: {rows_affected}")

                conn.commit()
                print("Prediction data successfully committed")
            except mysql.connector.Error as db_err:
                print(f"Database error during prediction storage: {db_err}")
                conn.rollback()
                flash(f"Error storing prediction results: {str(db_err)}", "error")
                return redirect(url_for('home'))

            # Return JSON response only after all database operations are complete
            return jsonify({
                "success": True,
                "predicted_marks": {
                    "sub1": int(predicted_marks[0]),
                    "sub2": int(predicted_marks[1]),
                    "sub3": int(predicted_marks[2])
                }
            })

        except mysql.connector.Error as db_err:
            print(f"Database error during student data retrieval: {db_err}")
            flash(f"Error retrieving student data: {str(db_err)}", "error")
            return redirect(url_for('home'))

    except ValueError as ve:
        print(f"Value error: {ve}")
        flash(f"Invalid input data: {str(ve)}", "error")
        return redirect(url_for('home'))
    except mysql.connector.Error as db_err:
        print(f"Database connection error: {db_err}")
        flash(f"Database connection error: {str(db_err)}", "error")
        return redirect(url_for('home'))
    except Exception as e:
        print(f"Unexpected error: {e}")
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return redirect(url_for('home'))
    finally:
        # Make sure the connection is always closed
        if conn:
            try:
                conn.close()
                print("Database connection closed")
            except:
                pass

@app.route('/result')
def result():
    # Check if prediction results exist in session
    if 'prediction_results' not in session:
        flash("No prediction results available.", "error")
        return redirect(url_for('predict'))

    # Get prediction results from session
    prediction_results = session.pop('prediction_results', None)

    return render_template('result.html', results=prediction_results)
# Add these routes to your existing app.py file

@app.route('/charts')
def charts():
    if 'username' not in session:
        flash("Please log in to view charts.", "error")
        return redirect(url_for('login'))

    # Get the most recent predicted student ID for this user
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the most recent student prediction - using predictionid (the primary key)
    cursor.execute("""
        SELECT studentid FROM prediction
        WHERE username = %s
        ORDER BY predictionid DESC LIMIT 1
    """, (username,))
    result = cursor.fetchone()

    if not result:
        flash("No prediction data available. Make a prediction first.", "error")
        return redirect(url_for('predict'))

    student_id = result['studentid']

    # Get the current student's data
    cursor.execute("""
        SELECT studentid, predicted_sub1, predicted_sub2, predicted_sub3
        FROM prediction
        WHERE studentid = %s
    """, (student_id,))
    current_student = cursor.fetchone()

    # Get previously predicted students data (limit to 10)
    cursor.execute("""
        SELECT studentid, predicted_sub1, predicted_sub2, predicted_sub3
        FROM prediction
        WHERE username = %s AND studentid != %s
        ORDER BY predictionid DESC
        LIMIT 10
    """, (username, student_id))
    previous_students = cursor.fetchall()

    # Get average subject marks for all students
    cursor.execute("""
        SELECT
            AVG(predicted_sub1) as avg_sub1,
            AVG(predicted_sub2) as avg_sub2,
            AVG(predicted_sub3) as avg_sub3
        FROM prediction
        WHERE username = %s
    """, (username,))
    averages = cursor.fetchone()

    # Get factor data for the current student
    cursor.execute("""
        SELECT student_id, gender, age, address, parent_education, travel_time,
               study_time, failures, extra_classes, extra_curricular,
               internet_access, health, absences, sub1_mark, sub2_mark, sub3_mark
        FROM student
        WHERE student_id = %s
    """, (student_id,))
    student_factors = cursor.fetchone()

    # Get weak subjects distribution
    cursor.execute("""
        SELECT
            COUNT(CASE WHEN weak_subject LIKE '%Subject 1%' THEN 1 END) as weak_sub1,
            COUNT(CASE WHEN weak_subject LIKE '%Subject 2%' THEN 1 END) as weak_sub2,
            COUNT(CASE WHEN weak_subject LIKE '%Subject 3%' THEN 1 END) as weak_sub3,
            COUNT(CASE WHEN weak_subject = 'None' THEN 1 END) as no_weak
        FROM prediction
        WHERE username = %s
    """, (username,))
    weak_subjects = cursor.fetchone()

    conn.close()

    chart_data = {
        'current_student': current_student,
        'previous_students': previous_students,
        'averages': averages,
        'student_factors': student_factors,
        'weak_subjects': weak_subjects
    }

    return render_template('chart.html', chart_data=chart_data)

if __name__ == '__main__':
     app.run(debug=True)