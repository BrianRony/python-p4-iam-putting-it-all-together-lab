#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if not username or not password:
            return {'error': '422 Unprocessable Entity', 'message': 'Username and password are required.'}, 422

        try:
            user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            user.password_hash = password
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return user.to_dict(), 201
        
        except IntegrityError:
            db.session.rollback()
            return {'error': '422 Unprocessable Entity', 'message': 'Username already exists.'}, 422

        except Exception as e:
            db.session.rollback()
            return {'error': '500 Internal Server Error', 'details': str(e)}, 500


class CheckSession(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get('user_id')).first()
        if user:
            return user.to_dict(), 200
        else:
            return {'error': '401 Unauthorized'}, 401

class Login(Resource):
    def post(self):
        username = request.get_json()['username']
        password = request.get_json()['password']

        user = User.query.filter(User.username == username).first()
        if user:
            if user.authenticate(password):
                session['user_id'] = user.id
                return user.to_dict(), 200
        else:
            return {'error': '401 Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            user = User.query.filter(User.id == session['user_id']).first()
            session['user_id'] = None
            return {}, 204
        else:
            return {'error': '401 Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        if session.get('user_id'):
                recipes = Recipe.query.all()
                recipes_dict = [recipe.to_dict() for recipe in recipes]
                return recipes_dict, 200
        else:
            return {'error': '401 Unauthorized'}, 401
        
    def post(self):
        if session.get('user_id'):
            user = User.query.filter(User.id == session['user_id']).first()

            if not user:
                return {'error': 'User not found'}, 401
            
            data = request.get_json()
            title = data.get('title')
            instructions = data.get('instructions')
            minutes_to_complete = data.get('minutes_to_complete')

            # Validate input data
            if not title or not instructions or not minutes_to_complete:
                return {'error': 'Missing required fields'}, 422
            

            try:
                new_recipe = Recipe(
                    title=title,
                    instructions=instructions,
                    minutes_to_complete=minutes_to_complete,
                    user=user
                )

                db.session.add(new_recipe)
                db.session.commit()

                return new_recipe.to_dict(), 201
            
            except Exception as e:
                db.session.rollback()
                return {'error': 'An error occurred', 'details': str(e)}, 422
        else:
            return {'error': '401 Unauthorized'}, 401




api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)