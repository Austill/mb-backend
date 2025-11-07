from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager

bcrypt = Bcrypt()
cors = CORS()
jwt = JWTManager()

# MongoDB client will be initialized in __init__.py
mongo = None
