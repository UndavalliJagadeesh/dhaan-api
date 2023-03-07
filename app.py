from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
import os
from flask_marshmallow import Marshmallow  # for serializing & deserializing ( database obj to text and vise-versa)
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, decode_token, get_jwt_identity
from flask_mail import Mail, Message

# import query


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'dhaan.db')
app.config['JWT_SECRET_KEY'] = '7by4GFmWmEWhbsy3i1VpMw'  # took random guid for temporary basis
# app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
# app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
# app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
# app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
# app.config['MAIL_USE_TLS'] = os.environ['MAIL_USE_TLS']
# app.config['MAIL_USE_SSL'] = os.environ['MAIL_USE_SSL']
app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'd5433d1b718bbb'
app.config['MAIL_PASSWORD'] = '42ac98144795db'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('create_db')
# @app.before_first_request
def create_db():
    db.create_all()
    print('Database created')


@app.cli.command('drop_db')
def drop_db():
    db.drop_all()
    print('Database dropped')


@app.route('/')
def home():
    return render_template('register.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    default_value = None
    fname = request.form.get('fname', default_value)
    lname = request.form.get('lname', default_value)
    email = request.form.get('mail', default_value)
    pswd = request.form.get('pswd', default_value)
    grp = request.form.get('grp', default_value)
    if User.query.filter_by(email=email).first():
        return jsonify(message='Entered email already exists'), 409
    person = User(first_name=fname, last_name=lname, email=email, password=pswd, group=grp)
    db.session.add(person)
    db.session.commit()
    return jsonify(message='User registered successfully'), 201


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('mail', None)
    pswd = request.form.get('pswd', None)

    test = User.query.filter_by(email=email, password=pswd).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="login successful", access_token=access_token), 200
    else:
        return jsonify(message="Invalid credentials"), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    test = User.query.filter_by(email=email).first()
    if test:
        msg = Message("Your password is \"" + test.password + "\" If you haven't requested for password, please "
                                                              "ignore this mail",
                      sender="admin@dhaan-api.com",
                      recipients=[email])
        # msg.subject("API Password")
        mail.send(msg)
        return jsonify(message="Password sent successful"), 200
    else:
        return jsonify(message="Email doesn't exists")


@app.route('/update_password', methods=['POST'])
@jwt_required()
def update_password():
    # jwt_token = request.headers.get('authorization', None)
    # decoded = jwt._decode_jwt_from_config(jwt_token, 'utf-8', False)
    # decoded = decode_token(jwt_token)
    email = get_jwt_identity()
    test = User.query.filter_by(email=email).first()
    if test:
        pswd = request.form.get('pswd', None)
        if test.password == pswd:
            new_pswd = request.form.get('newPswd', None)
            confirm_pswd = request.form.get('confirm_pswd', None)
            if new_pswd == confirm_pswd and new_pswd is not None:
                test.password = new_pswd
                db.session.commit()
                return jsonify(message="Password updated Successfully"), 202
            else:
                return jsonify(message="Passwords doesn't match"), 401
        else:
            return jsonify(message="Incorrect Password"), 401
    else:
        return jsonify(message="User doesn't exist"), 404


@app.route('/api', methods=['GET'])
@jwt_required()
def send_api():
    users = User.query.all()
    result = usersSchema.dump(users)
    return jsonify(result)


# database models
class User(db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    group = Column(String)


class Transact(db.Model):
    __tablename__ = 'transact'
    user_id = Column(Integer, db.ForeignKey('user.id'), primary_key=True)
    type = Column(String)
    # amount = Column(Integer)
    loc = Column(String)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password', 'group')


class TransactSchema(ma.Schema):
    class Meta:
        fields = ('user_id', 'type', 'loc')


userSchema = UserSchema()  # for retrival of single field
usersSchema = UserSchema(many=True)  # for retrival of multiple fields

transactSchema = TransactSchema()
transactsSchema = TransactSchema(many=True)

if __name__ == '__main__':
    app.run()
