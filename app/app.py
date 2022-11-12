import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Resource, Api, reqparse
from flask_wtf import csrf
from flask_jwt_extended import create_access_token
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.secret_key = 'my_secret_key'
api = Api(app)
# 
app.config["JWT_SECRET_KEY"] = "my_secret_key"
jwt = JWTManager(app)

# database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{}:{}@{}/{}'.format(    
    os.environ.get('DB_USER', 'your_user'),
    os.environ.get('DB_PASS', 'your_password'),
    os.environ.get('DB_HOST', 'db'),
    os.environ.get('DB_NAME', 'your_db')
)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

    def __repr__(self):
        return '<User %r>' % self.name

# end database

# api
parser = reqparse.RequestParser()
parser.add_argument('id', type=int)
parser.add_argument('name', type=str)
parser.add_argument('email', type=str)
parser.add_argument('password', type=str)

class UserLoginApi(Resource):
    response = {"status": 400, "message": "Bad request"}  
    def post(self):        
        csrf.generate_csrf()
        args = parser.parse_args()
        email = args['email'] 
        password = args['password'] 
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            access_token = create_access_token(identity=email)
            return jsonify(access_token=access_token)
        return {"error": "Invalid login credentials"}, 401  
        
class UserListApi(Resource):
    response = {"status": 400, "message": "Bad request"}
    def get(self):
        ret = []
        res = User.query.all()
        for user in res:
            ret.append(
                {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email
                }
            )
        return jsonify(ret) 

    def post(self):        
        csrf.generate_csrf()
        args = parser.parse_args()
        name = args['name']
        email = args['email'] 
        password = args['password'] 
        model = User(name=name, email=email, password=password)
        db.session.add(model)
        db.session.commit()
        self.response["status"] = 201
        self.response["message"] = "User created successfully"
        return self.response, 201

class UserApi(Resource):
    response = {"status": 400, "message": "Bad request"}
    def get(self, user_id):
        res = User.query.filter_by(id=user_id).first()
        if res:
            return {'id': res.id, "name":res.name, "email":res.email}
        return {"user":"None"}

    def put(self, user_id):
        user = User.query.filter_by(id=user_id).first()
        if user:
            csrf.generate_csrf()
            args = parser.parse_args()
            user.name = args['name']
            user.email = args['email']  
            user.password = args['password']             
            db.session.commit()
            self.response["status"] = 200
            self.response["message"] = "User updated successfully"
            return self.response, 200
        return {"user":"None"}

    def delete(self, user_id):
        res = User.query.filter_by(id=user_id).first()
        if res:
            db.session.delete(res)
            db.session.commit()
            self.response["status"] = 200
            self.response["message"] = "Deleted user successfully"
            return self.response, 200
        return {"user":"None"}

api.add_resource(UserLoginApi, '/login')
api.add_resource(UserListApi, '/user')
api.add_resource(UserApi, '/user/<int:user_id>')
# end api

@app.route('/')
def hello_world():
    return "Hello Flask framework" 

if __name__ == '__main__':
    app.run(debug=True)