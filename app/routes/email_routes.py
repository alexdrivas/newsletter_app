from flask import Blueprint, jsonify
from app.services.email_service import send_email
from app.models import User

email_bp = Blueprint('email_bp', __name__)

@email_bp.route('/send', methods=['POST'])
def send_email_to_user():
    user = User.query.first()
    if user:
        success, message = send_email(user.email, "Subject", "Email Body")
        if success:
            return jsonify({"message": "Email sent successfully!"}), 200
        else:
            return jsonify({"error": message}), 500
    return jsonify({"error": "No users found"}), 404
