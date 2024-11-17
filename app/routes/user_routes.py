from flask import Blueprint, request, jsonify
from app.models import User, db

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/create', methods=['POST'])
def create_user():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    
    new_user = User(first_name=first_name, last_name=last_name, email=email)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User created successfully!"}), 201
