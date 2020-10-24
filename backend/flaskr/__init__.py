import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)  
 
  CORS(app)
  # CORS(app, resources={r"/api/*": {"origins": "*"}})

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


  @app.route('/categories')
  def get_categories():
    categories_list = Category.query.order_by(Category.type).all()

    if len(categories_list) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'categories': {category.id: category.type for category in categories_list}
    })
 

  @app.route('/questions')
  def get_questions():
      selection_list = Question.query.order_by(Question.id).all()
      current_list_questions = paginate_questions(request, selection_list)

      categories_list = Category.query.order_by(Category.type).all()

      if len(current_list_questions) == 0:
          abort(404)

      return jsonify({
          'success': True,         
          'categories': {category.id: category.type for category in categories_list},
          'current_category': None,
          'questions': current_list_questions,
          'total_questions': len(selection_list)
      })
 

  @app.route("/questions/<question_id>", methods=['DELETE'])
  def delete_question(question_id):      
      try:
          question_to_delete = Question.query.get(question_id)
          question_to_delete.delete()
          return jsonify({
              'success': True,
              'deleted': question_id
          })

      except:
          abort(422)
 

  @app.route("/questions", methods=['POST'])
  def add_question():
      body = request.get_json()

      if not ('category' in body and 'question' in body and 'difficulty' in body and 'answer' in body):
          abort(422)

      question_new = body.get('question')
      answer_new = body.get('answer')
      difficulty_new = body.get('difficulty')
      category_new = body.get('category')

      try:
          question = Question(category=category_new, question=question_new, difficulty=difficulty_new, answer=answer_new)
          question.insert()
          return jsonify({
              'success': True,
              'created': question.id,
          })
      except:
          abort(422)

 
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
      body = request.get_json()
      search_term = body.get('searchTerm', None)

      if search_term:
          results_list = Question.query.filter(
              Question.question.ilike(f'%{search_term}%')).all()

          return jsonify({
              'success': True,
              'questions': [question.format() for question in results_list],
              'total_questions': len(results_list),
              'current_category': None
          })
      abort(404)
 

  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions_category(category_id):
      try:
          questions_list = Question.query.filter(
              Question.category == str(category_id)).all()

          return jsonify({
              'success': True,
              'questions': [question.format() for question in questions_list],
              'total_questions': len(questions_list),
              'current_category': category_id
          })
      except:
          abort(404)

 
  @app.route('/quizzes', methods=['POST'])
  def start_game():
      try:
          body = request.get_json()

          if not ('quiz_category' in body and 'previous_questions' in body):
              abort(422)

          category = body.get('quiz_category')
          previous_questions_list = body.get('previous_questions')

          if category['type'] == 'click':
              available_questions_list = Question.query.filter(
              Question.id.notin_((previous_questions_list))).all()
          else:
              available_questions_list = Question.query.filter_by(
              category=category['id']).filter(Question.id.notin_((previous_questions_list))).all()

          question_new = available_questions_list[random.randrange(
              0, len(available_questions_list))].format() if len(available_questions_list) > 0 else None

          return jsonify({
              'success': True,
              'question': question_new
          })
      except:
          abort(422)
 
  #   Error Handling
  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
          "success": False,
          "error": 400,
          "message": "bad request"
      }), 400


  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
          "success": False,
          "error": 404,
          "message": "resource not found"
      }), 404


  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
          "success": False,
          "error": 422,
          "message": "unprocessable"
      }), 422 


  return app    