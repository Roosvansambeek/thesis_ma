from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from database import load_courses_from_db, load_favorite_courses_from_db, add_interests_to_db , add_login_to_db, update_interests, add_views_to_db,  search_courses_from_db, add_click_to_db, load_last_viewed_courses_from_db
from flask import request, redirect, url_for, flash
from datetime import datetime
import httpagentparser



#TFIDF
#fav
from TFIDF_algorithmfav import get_recommendations_fav_TFIDF

#int
from TFIDF_algorithminterests import get_course_recommendations_int_TFIDF

#edu
from TFIDF_education import recs_on_education_TFIDF

#course
from TFIDF_algorithmcourse import get_recommendations_course_TFIDF



app = Flask(__name__)


app.secret_key = 'session_key'

@app.route("/")
def landing():
    user_agent = request.headers.get('User-Agent')
    device = httpagentparser.detect(user_agent)
    print(f"User agent: {user_agent}")
    print(f"Device: {device}")
    if 'mobile' in user_agent.lower():
        return render_template('mobile_error.html')
    return render_template('signin.html')


@app.route("/participate", methods =["GET", "POST"])
def participate():
  return render_template('participate.html')

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == 'POST':
        student_number = request.form['student_number']
        session['student_number'] = student_number
        education = request.form['education']

        add_login_to_db(student_number, education)

        return redirect('/state_interests.html')

    return render_template('signin.html')

@app.route("/state_interests.html")
def state_interests():
    return render_template('state_interests.html')

@app.route("/state_interests/stated.html", methods=['POST'])
def stated_interests():
    data = request.form
    student_number = session.get('student_number')  
    
  
    if student_number:
        update_interests(student_number, data)

    previous_page = request.referrer
    return redirect(f'/home/{student_number}')



@app.route("/home/<student_number>", methods=['GET', 'POST'])
def home(student_number):
   
    student_number = student_number or session.get('student_number', default_value)
    
    education_recommendations = recs_on_education_TFIDF(student_number)
    num_education_recommendations=len(education_recommendations)
    fav_recommendations = get_recommendations_fav_TFIDF(student_number)
    interests_recommendations = get_course_recommendations_int_TFIDF(student_number)
    viewed_courses=load_last_viewed_courses_from_db(student_number)

    favorite_courses=load_favorite_courses_from_db(student_number)
    
    data = request.form  

    if request.method == 'POST':
        rating = request.form.get('rating')
        course_code = request.form.get('course_code')

        favorite_courses=load_favorite_courses_from_db(student_number)

        fav_recommendations = get_recommendations_fav_TFIDF(student_number)

        #interests_recommendations = get_course_recommendations_int_TFIDF(student_number)
        viewed_courses=load_ratings_and_details_for_viewed_courses(student_number)



    return render_template('home.html', student_number=student_number, fav_recommendations=fav_recommendations, interests_recommendations=interests_recommendations, viewed_courses=viewed_courses, education_recommendations=education_recommendations, favorite_courses=favorite_courses)


@app.route("/course/<course_code>/<student_number>/rating", methods=['POST'])
def rating_course(course_code, student_number):
  data = request.form
  student_number = session.get('student_number')
  add_click_to_db(student_number, course_code, data)
  previous_page = request.referrer
  return redirect(previous_page)

@app.route("/course/<course_code>/<student_number>/remove_rating", methods=['POST'])
def remove_rating(course_code, student_number):
    data = request.form
    student_number = session.get('student_number')
    add_click_to_db(student_number, course_code, data)
    previous_page = request.referrer
    return redirect(previous_page)

@app.route("/course/<course_code>/<student_number>/clicked", methods=['POST'])
def clicked_course(course_code, student_number):
    data = request.form
    student_number = session.get('student_number')
    add_click_to_db(student_number, course_code, data)
    return redirect(url_for('show_course', course_code=course_code, student_number=student_number))


@app.route('/favourites/<student_number>')
def favorite_courses(student_number):
    student_number = session.get('student_number')
    favorite_courses = load_favorite_courses_from_db(student_number)
    
    return render_template('favourites.html', favorite_courses=favorite_courses, student_number=student_number)

      
@app.route("/courses/<student_number>")
def hello_world(student_number):
    courses = load_courses_from_db()
    return render_template('courses.html', courses=courses, filters=filters, student_number=student_number)



@app.route("/course/<course_code>/<student_number>", methods=['GET', 'POST'])
def show_course(student_number, course_code):
    # Load the course data
    courses = load_courses_from_db()
    student_number = session.get('student_number')
    favorite_courses = load_favorite_courses_from_db(student_number)
    
    viewed_courses=load_last_viewed_courses_from_db(student_number)
    course_code = request.view_args['course_code']
    recommendations_courses = get_recommendations_course_TFIDF(course_code)
    course = [course for course in courses if course.get('course_code') == course_code]

    

    if not course:
        return "Not Found", 404

    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    add_views_to_db(student_number, course_code, timestamp, id)

    return render_template('coursepage.html', course=course[0], student_number=student_number, course_code=course_code, recommendations_courses=recommendations_courses, favorite_courses=favorite_courses)


@app.route("/search", methods=['GET'])
def search():
    query = request.args.get('query')
    student_number = session.get('student_number') # Replace this with the actual 
    results = search_courses_from_db(query)
    return render_template('search_results.html', query=query, results=results, student_number=student_number)

if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)