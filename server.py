from flask import Flask, jsonify, request
import mysql.connector
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  
db_config = {
    'user': 'root',    
    'password': 'Maybe@123', 
    'host': 'localhost',        
    'database': 'mind_engage'  
}
def connect_db():
    return mysql.connector.connect(**db_config)


@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    admin_id = data.get('admin_id')
    password = data.get('password')

    try:
        connection = connect_db()
        cursor = connection.cursor()

        query = "SELECT * FROM admin WHERE admin_id = %s AND password = %s"
        cursor.execute(query, (admin_id, password))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    


    
#To Add Course
@app.route('/add-course', methods=['POST'])
def add_course():
    db = None
    try:
        data = request.json
        course_name = data.get('courseName')
        course_code = data.get('courseCode')
        course_cc = data.get('courseCC')
        if not course_name or not course_code or not course_cc:
            return jsonify({"error": "All fields are required"}), 400
        db = connect_db()
        cursor = db.cursor()
        query = "INSERT INTO course (course_name, course_code, course_cc) VALUES (%s, %s, %s)"
        cursor.execute(query, (course_name, course_code, course_cc))
        db.commit()
        return jsonify({"message": "Course added successfully!"}), 200
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()

@app.route('/course', methods=['GET'])
def get_courses():
    try:
        # Connect to the database
        connection = connect_db()
        cursor = connection.cursor()

        # Execute query to get the desired columns
        cursor.execute("SELECT course_id, course_name, course_cc FROM course")

        # Fetch all results
        courses = cursor.fetchall()

        # Close cursor and connection
        cursor.close()
        connection.close()

        # Format the results into a list of dictionaries
        courses_list = [{'courseID': row[0], 'courseName': row[1], 'courseCC': row[2]} for row in courses]

        # Return the data as JSON
        return jsonify(courses_list)
    except Exception as e:
        # Return error message if any
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/create-course-table', methods=['POST'])
def create_course_table():
    try:
        data = request.get_json()
        course_name = data.get('courseName')

        # Validate course name
        if not course_name or not course_name.strip():
            return jsonify({'error': 'courseName is required and cannot be empty'}), 400

        # Sanitize course name and limit length
        course_name_sanitized = ''.join(e for e in course_name if e.isalnum())
        MAX_COURSE_NAME_LENGTH = 50  # Set your desired length
        if len(course_name_sanitized) > MAX_COURSE_NAME_LENGTH:
            return jsonify({'error': f'courseName must be less than {MAX_COURSE_NAME_LENGTH} characters'}), 400

        connection = connect_db()
        cursor = connection.cursor()

        # Creating the SQL query to create a table
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{course_name_sanitized}` (
            `s_no` INT NOT NULL AUTO_INCREMENT,
            `lesson` VARCHAR(255) NOT NULL,
            `description` TEXT NOT NULL,
            `content` LONGTEXT,
            PRIMARY KEY (`s_no`)
        )"""

        cursor.execute(create_table_query)
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': f'Table `{course_name_sanitized}` created successfully!'}), 200

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500



# Endpoint to get lessons for a specific course table
@app.route('/get-lessons/<course_name>', methods=['GET'])
def get_lessons(course_name):
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)

        # Sanitizing course name to avoid SQL injection attacks
        course_name_sanitized = ''.join(e for e in course_name if e.isalnum())

        query = f"SELECT * FROM `{course_name_sanitized}`"
        cursor.execute(query)
        lessons = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify(lessons), 200

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


# Endpoint to add quiz questions for a specific lesson
@app.route('/add-quiz-question/<lesson_name>', methods=['POST'])
def add_quiz_question(lesson_name):
    try:
        data = request.get_json()
        question = data.get('question')
        optionA = data.get('optionA')
        optionB = data.get('optionB')
        optionC = data.get('optionC')
        optionD = data.get('optionD')
        correctOption = data.get('correctOption')
        reason = data.get('reason')

        if not question or not optionA or not optionB or not optionC or not optionD or not correctOption or not reason:
            return jsonify({"error": "All fields are required"}), 400

        connection = connect_db()
        cursor = connection.cursor()

        # Sanitizing lesson name to avoid SQL injection attacks
        lesson_name_sanitized = ''.join(e for e in lesson_name if e.isalnum())

        # Dynamically create a table for the quiz corresponding to the lesson if it doesn't exist
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{lesson_name_sanitized}_quiz` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT,
            optionA VARCHAR(255),
            optionB VARCHAR(255),
            optionC VARCHAR(255),
            optionD VARCHAR(255),
            correctOption CHAR(1),
            reason TEXT
        );
        """
        cursor.execute(create_table_query)

        # Insert the quiz question into the lesson's quiz table
        insert_query = f"""
        INSERT INTO `{lesson_name_sanitized}_quiz` 
        (question, optionA, optionB, optionC, optionD, correctOption, reason) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (question, optionA, optionB, optionC, optionD, correctOption, reason))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Quiz question added successfully!'}), 200

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    
@app.route('/create-lesson-table', methods=['POST'])
def create_lesson_table():
    try:
        data = request.get_json()
        lesson_name = data.get('lessonName')

        if not lesson_name:
            return jsonify({"error": "Lesson name is required"}), 400

        connection = connect_db()
        cursor = connection.cursor()

        # Sanitize the lesson name to avoid SQL injection
        lesson_name_sanitized = ''.join(e for e in lesson_name if e.isalnum())

        # SQL query to create the lesson quiz table dynamically
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{lesson_name_sanitized}_quiz` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT,
            optionA TEXT,
            optionB TEXT,
            optionC TEXT,
            optionD TEXT,
            correctOption CHAR(255),
            reason TEXT
        );
        """
        cursor.execute(create_table_query)
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': f'Table for lesson {lesson_name_sanitized}_quiz created successfully!'}), 200

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/get-quizzes/<lesson_name>', methods=['GET'])
def get_quizzes(lesson_name):
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)

        # Sanitizing lesson name to avoid SQL injection attacks
        lesson_name_sanitized = ''.join(e for e in lesson_name if e.isalnum())

        query = f"SELECT * FROM `{lesson_name_sanitized}_quiz`"  # Assuming the quizzes are stored in a table named after the lesson
        cursor.execute(query)
        quizzes = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify(quizzes), 200

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


# Endpoint to add a lesson to a specific course table
@app.route('/add-lesson/<course_name>', methods=['POST'])
def add_lesson(course_name):
    try:
        data = request.get_json()
        lesson = data.get('lesson')
        description = data.get('description')
        content = data.get('content')

        if not lesson or not description:
            return jsonify({"error": "lesson ,description and content are required"}), 400

        connection = connect_db()
        cursor = connection.cursor()

        # Sanitizing course name to avoid SQL injection attacks
        course_name_sanitized = ''.join(e for e in course_name if e.isalnum())

        query = f"INSERT INTO `{course_name_sanitized}` (lesson, description,content) VALUES (%s, %s, %s)"
        cursor.execute(query, (lesson, description, content))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Lesson added successfully!'}), 200

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


# Endpoint to get the description of a specific lesson
@app.route('/get-lesson-description/<course_name>/<lesson>', methods=['GET'])
def get_lesson_description(course_name, lesson):
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)

        # Sanitizing course name to avoid SQL injection attacks
        course_name_sanitized = ''.join(e for e in course_name if e.isalnum())

        query = f"SELECT description , content FROM `{course_name_sanitized}` WHERE lesson = %s"
        cursor.execute(query, (lesson,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Lesson not found'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500



@app.route('/delete-course', methods=['POST'])
def delete_course():
    data = request.get_json()
    course_name = data.get('courseName')

    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Use parameterized queries to avoid SQL injection
        cursor.execute("DELETE FROM course WHERE course_name = %s", (course_name,))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Course deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    




@app.route('/edit-course', methods=['POST'])
def edit_course():
    data = request.get_json()
    course_name = data['courseName']
    new_course_name = data['newCourseName']
    course_code = data['courseCode']
    course_cc = data['courseCC']

    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("UPDATE course SET course_name = %s, course_code = %s, course_cc = %s WHERE course_name = %s", (new_course_name, course_code, course_cc, course_name))
        connection.commit()

        cursor.close()
        connection.close()
        return jsonify({'message': 'Course edited successfully'})
    except Exception as e:

        return jsonify({'error': str(e)}), 400



@app.route('/edit-lesson/<course_name>', methods=['POST'])
def edit_lesson(course_name):
    data = request.get_json()
    old_lesson_name = data.get('oldLessonName')
    new_lesson_name = data.get('newLessonName')
    new_description = data.get('newDescription')
    new_content = data.get('newContent')

    # Sanitize course_name to prevent SQL injection
    course_name_sanitized = course_name.replace("`", "``")  # Escape backticks if any

    try:
        connection = connect_db()  # Function to connect to the MySQL database
        cursor = connection.cursor()

        # SQL query to update the lesson's name and description in the course-specific table
        query = f"""
            UPDATE `{course_name_sanitized}` 
            SET lesson = %s, description = %s , content = %s
            WHERE lesson = %s
        """
        cursor.execute(query, (new_lesson_name, new_description, new_content, old_lesson_name))

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'Lesson updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/delete-lesson/<course_name>', methods=['POST'])
def delete_lesson(course_name):
    data = request.get_json()
    lesson_name = data.get('lesson')
    course_name_sanitized = course_name.replace("`", "``")  
    try:
        connection = connect_db() 
        cursor = connection.cursor()
        query = f"""
            DELETE FROM `{course_name_sanitized}` 
            WHERE lesson = %s
        """
        cursor.execute(query, (lesson_name,))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'message': 'Lesson deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/user_register', methods=['POST'])
def user_register():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        password = data.get('password')
        name = data.get('name')
        connection = connect_db()
        cursor = connection.cursor()
        query = "INSERT INTO user_registrations (user_id, name, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (user_id, name, password))
        connection.commit()
        cursor.close()

        return jsonify({'success': True, 'message': 'User registered successfully', 'user_id': user_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

# User login route
@app.route('/user_login', methods=['POST'])
def user_login():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        password = data.get('password')
        connection = connect_db()

        cursor = connection.cursor()
        query = "SELECT * FROM user_registrations WHERE user_id = %s AND password = %s"
        cursor.execute(query, (user_id, password))
        user_data = cursor.fetchone()
        connection.commit()
        cursor.close()

        if user_data:
            return jsonify({'success': True, 'message': 'User login successful', 'user_id': user_id}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid user credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/get-quiz/<string:lesson>', methods=['GET'])
def get_quiz(lesson):
    connection = connect_db()  # Ensure this function is properly defined to connect to your DB
    cursor = connection.cursor(dictionary=True)  # Fetch data as dictionaries

    # Format the table name based on the lesson
    table_name = f"{lesson}_quiz"  # Assumes lesson names do not have special characters or spaces

    try:
        # Dynamic query to select from the lesson-specific quiz table
        query = f'SELECT * FROM {table_name}'
        cursor.execute(query)
        quiz_questions = cursor.fetchall()  # This will now return a list of dictionaries
        
        return jsonify(quiz_questions)  # Return JSON response
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Return an error response if query fails
    finally:
        cursor.close()
        connection.close()



if __name__ == '__main__':
    app.run(host="10.32.1.143", port=5000, debug=True)