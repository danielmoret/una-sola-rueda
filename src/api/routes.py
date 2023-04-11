"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, User, Talonario, User_ticket, Payment, Ticket
from api.utils import generate_sitemap, APIException
from werkzeug.security import generate_password_hash, check_password_hash
from base64 import b64encode
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import cloudinary.uploader as uploader
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

api = Blueprint('api', __name__)

def set_password(password, salt):
    return generate_password_hash(f"{password}{salt}")

def check_password(hash_password, password, salt):
    return check_password_hash(hash_password, f"{password}{salt}")

#endpoints user
@api.route('/user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        body = request.json
        email = body.get("email", None)
        password= body.get("password",None)
        role= body.get("role","raffler")
       
        if email is None or password is None:
            return "you need an email and a password",400
        else:
            salt = b64encode(os.urandom(32)).decode('utf-8')
            password = set_password(password, salt)
            try:
                user = User.create(email = email, password = password, salt=salt, role=role)
                return jsonify({"message": "User created"}),201
                
            except Exception as error: 
                print(error.args)
                db.session.rollback()
                return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]
            
@api.route('/user', methods=['GET'])
@jwt_required()
def gell_all_user():
    if request.method == 'GET':
        all_users = User.query.all()
        user_id = User.query.get(get_jwt_identity())
        
        if(user_id.role.value == "admin" or user_id.role.value == "super_admin"):
            return jsonify(list(map(lambda user: user.serialize(), all_users))),200          
        else:
            return jsonify([]),200
        
@api.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id=None):
    if request.method == "DELETE":
        if user_id is None:
            return jsonify({"message": "Bad request"})
        if user_id is not None:
            user = User.query.get(user_id)

            if user is None:
                return jsonify({"message": "user not found"}),404
            else:
                try:
                    user_delete = User.delete_user(user)
                    return jsonify(user_delete),204
        
                except Exception as error:
                    return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]
                    
       

@api.route('/user/login', methods=['POST'])
def handle_login():
     if request.method == 'POST':
         body = request.json 
         email = body.get('email', None)
         password = body.get('password', None)

        
         if email is None or password is None:
             return "you need an email and a password", 400
         else:
            login = User.query.filter_by(email=email).one_or_none()
            if login is None:
                return jsonify({"message":"bad credentials"}), 400
            else:
                 if check_password(login.password, password, login.salt):
                     token = create_access_token(identity=login.id)
                     return jsonify({"token": token, "role": login.role.value}),200
                 else:
                     return jsonify({"message":"bad credentials"}), 400

#endpoints talonario
@api.route('/talonario', methods=['GET'])
@jwt_required()
def get_talonarios():
    if request.method == 'GET':
        user_id = get_jwt_identity()
        talonarios = Talonario.query.filter_by(user_id = user_id)

        return (list(map(lambda talonario: talonario.serialize(),talonarios ))),200


@api.route('/talonario', methods=['POST'])
@jwt_required()
def  create_talonario():
    if request.method == 'POST':
        body = request.json
        user_id = get_jwt_identity()

        name = body.get('name', None)
        prize = body.get('prize', None)
        numbers= body.get('numbers',None)
        price = body.get('price', None)
        img_url_prize = body.get('img_url_prize', False)
        img_cloud_id = body.get('img_cloud_id', None)
        talonario_id = b64encode(os.urandom(32)).decode('utf-8')
        status = "activa"

        if name is None or prize is None or numbers is None or price is None or img_url_prize is None or img_cloud_id is None:
            return jsonify({"message": "incomplete data"}),400
        else:
            try:
                new_talonario = Talonario.create(**body, talonario_id = talonario_id, user_id = user_id, status = status)
                return jsonify(new_talonario.serialize()),201
            except Exception as error: 
                db.session.rollback()
                return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]

@api.route('/talonario/<int:talonario_id>', methods=['PUT'])
def  update_talonario(talonario_id):      
     if request.method == 'PUT': 
         talonario = Talonario.query.filter_by(id = talonario_id).first()

         if talonario is None:
             return jsonify({"message": "Talonario no encontrado"}),404
         else:
             talonario.status = "finalizada"
             try:
                db.session.commit()
                return jsonify({"message":"Talonario updated"}),200
             except Exception as error: 
                return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]

@api.route('/talonario/<int:talonario_id>', methods=['DELETE'])
def  delete_talonario(talonario_id):      
     if request.method == 'DELETE': 
         talonario = Talonario.query.get(talonario_id)

         if talonario is None:
             return jsonify({"message": "Talonario no encontrado"}),404
         else:
             try:
                cloudinary_delete_response = uploader.destroy(talonario.img_cloud_id)

                if cloudinary_delete_response["result"] != "ok":
                    return jsonify({"message":"Cloudinary delete error"})
                
                talonario_to_delete = Talonario.delete_talonario(talonario)
                return jsonify(talonario_to_delete),204
             except Exception as error: 
                db.session.rollback()
                return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]

#endpoints user_ticket
@api.route('/user-ticket', methods=['POST'])
def add_user_ticket():
    if request.method == 'POST':

        body = request.json
        name=body.get("name", None)
        phone= body.get("phone",None)
        email = body.get("email", None)

       
        if name is None or phone is None or email is None:
            return "you need an name and a phone and a email",400
        else:
            try:
                User_ticket.create(name = name, phone = phone, email=email)
                return jsonify({"message": "User created"}),201
                
            except Exception as error: 
                db.session.rollback()
                return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]
            
@api.route('/user-ticket', methods=['GET'])
def gell_all_user_ticket():
    if request.method == 'GET':
        all_users = User_ticket.query.all()
        
        return jsonify(list(map(lambda user: user.serialize(), all_users))),200          

       
        
@api.route('/user-ticket/<int:user_id>', methods=['DELETE'])
def delete_user_ticket(user_id=None):
    if request.method == "DELETE":
        if user_id is not None:
            user = User_ticket.query.get(user_id)

            if user is None:
                return jsonify({"message": "user not found"}),404
            else:
                try:
                    user_delete = User_ticket.delete_user(user)
                    return jsonify(user_delete),204
        
                except Exception as error:
                    return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]
                    
      

#enpoinst ticket     
@api.route('/ticket', methods=['POST'])
def create_ticket():

    if request.method == "POST":
        body = request.json
        number=body.get("number", None)
        status= body.get("status",None)
        talonario_id = body.get("talonario_id", None)
        user_ticket_id = body.get("user_ticket_id", None)

        if number is None or status is None or talonario_id is None or user_ticket_id is None:
            return jsonify({"message": "missing data"}),400

        try:
            new_ticket = Ticket.create(**body)
            return jsonify(new_ticket.serialize()), 201
        
        except Exception as error:
            return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]
 
@api.route('/ticket', methods=['GET'])
def get_all_ticket():
    if request.method == "GET":
        tickets = Ticket.query.all()
        tickets_dictionaries = []
        for ticket in tickets :
            tickets_dictionaries.append(ticket.serialize())
        
        return jsonify(tickets_dictionaries)

@api.route('/ticket/<int:talonario_id>', methods=['GET'])
def get_ticket(talonario_id):
    if request.method == "GET":
        tickets = Ticket.query.filter_by(talonario_id = talonario_id)
        tickets_dictionaries = []
        for ticket in tickets :
            tickets_dictionaries.append(ticket.serialize())
        
        return jsonify(tickets_dictionaries)

@api.route('/ticket/<int:number>/<int:talonario_id>', methods=['GET'])
def get_one_ticket(number, talonario_id):
    if request.method == "GET":
        ticket = Ticket.query.filter_by(talonario_id = talonario_id, number = number).one_or_none()
        
        if ticket is None:
            return jsonify({"message": "the ticket not found"}),400
        else:
            return jsonify(ticket.serialize())

@api.route('/ticket/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id=None):
    if request.method == "DELETE":
        if ticket_id is not None:
            ticket = Ticket.query.get(ticket_id)
            

            if ticket is None:
                return jsonify({"message": "ticket not found"}),404
            else:
                try:
                    ticket_delete = Ticket.delete(ticket)
                    return jsonify(ticket_delete),204
        
                except Exception as error:
                    return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]
                
#endpoints payments
@api.route('/payment', methods=['POST'])
def create_payment():

    if request.method == "POST":
        body = request.json
        payment_method=body.get("payment_method", None)
        number_of_tickets= body.get("number_of_tickets",None)
        total = body.get("total", None)
        date = body.get("date", None)
        talonario_id = body.get("talonario_id", None)
        user_ticket_id = body.get("user_ticket_id", None)

        if payment_method is None or number_of_tickets is None or total is None or date is None or talonario_id is None or user_ticket_id is None:
            return jsonify({"message": "missing data"}),400

        try:
            new_payment = Payment.create(**body)
            return jsonify(new_payment.serialize()), 201
        
        except Exception as error:
            return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]

@api.route('/payment/<int:talonario_id>', methods=['GET'])
def get_all_payments(talonario_id):
    if request.method == "GET":
        payments = Payment.query.filter_by(talonario_id = talonario_id)
        payments_dictionaries = []
        for payment in payments :
            payments_dictionaries.append(payment.serialize())

        return jsonify(payments_dictionaries)
    
@api.route('/payment/<int:payment_id>', methods=['PUT'])
def update_payment(payment_id):
    if request.method == "PUT":
        payment = Payment.query.filter_by(id = payment_id).first()

        if payment is None:
             return jsonify({"message": "payment not found"}),404
        else:
            payment.status = "aprobado"
            try:
                db.session.commit()
                return jsonify({"message":"Payment updated"}),200
            except Exception as error:
                return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]
            


@api.route('/payment/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id=None):
    if request.method == "DELETE":
        if payment_id is not None:
            payment = Payment.query.get(payment_id)
            

            if payment is None:
                return jsonify({"message": "payment not found"}),404
            else:
                try:
                    payment_delete = Ticket.delete(payment)
                    return jsonify(payment_delete),204
        
                except Exception as error:
                    return jsonify({"message": f"Error: {error.args[0]}"}),error.args[1]

#endpoint emails
@api.route('/verify-pay', methods = ['POST'])
def verify_pay():
    if request.method == "POST":
        data = request.json

        sender = "dmlord17@gmail.com"
        receptor = "dmlord17@gmail.com"

        

        message = MIMEMultipart('alternatives')
        message['Subject'] = "Unasolarueda.com - Orden 155878"
        message['From'] = sender
        message['To'] = receptor

        text = ""
        html = """<html>
                    <head></head>
                    <body>
                     <div style="text-align: center">
      <img
        style="width: 200px"
        src="https://res.cloudinary.com/drcuplwe7/image/upload/v1680654977/STICKERS_CRUZANGELO_k8nf24.png"
      />
    </div>
    <h1>Pedido Recibido</h1>
    <h2>Gracias por tu compra, tu pedido ha sido recibido</h2>
    <div style="text-align: center">
      <table border="1" style="margin: 0 auto; width: 100%">
        <tr>
          <th># Pedido</th>
          <th>Fecha</th>
          <th>Total</th>
          <th>Método de Pago</th>
        </tr>
        <tr>
          <td>1511818</td>
          <td>04/04/23</td>
          <td>$10</td>
          <td>Pago Movil</td>
        </tr>
      </table>
    </div>
                    </body>
                </html>"""
        
        message.attach(MIMEText(text,'plain'))
        message.attach(MIMEText(html,'html'))

        try:
            server = smtplib.SMTP("smtp.gmail.com",587)
            server.starttls()
            server.login("dmlord17@gmail.com","ihdclnptddsmyqfs")
            server.sendmail("dmlord17@gmail.com","dmlord17@gmail.com",message.as_string())
            server.quit()
            print("Email send")
            return jsonify({"message": "Email send succesfull"}),200
        except Exception as error:
            print(error)
            print("Email not sending, error")
            return jsonify({"message":"Error, try again, later"}),500

@api.route('/verified-payment/<int:user_ticket_id>', methods = ['POST'])
def verified_payment(user_ticket_id):
    if request.method == "POST":
        body = request.json

        numbers=body.get("numbers", None)

        data_user = User_ticket.query.get(user_ticket_id)
        data_payment = Payment.query.filter_by(user_ticket_id = user_ticket_id).first()

        numbers_div = ""

        for number in numbers:
            numbers_div = numbers_div + f"<span  style='border: 1px solid black;border-radius: 50%;background-color: black;color: white;padding: 10px;'>{number}</span>"

        sender = "dmlord17@gmail.com"
        receptor = "dmlord17@gmail.com"

        

        message = MIMEMultipart('alternatives')
        message['Subject'] = "Unasolarueda.com - Orden 155878"
        message['From'] = sender
        message['To'] = receptor

        text = ""
        html = f"""<html>
                    <head></head>
                    <body style="height: 100vh">
                     <div style="text-align: center">
      <img
        style="width: 200px"
        src="https://www.shutterstock.com/image-vector/auto-motorbikes-logo-design-vector-260nw-1133340668.jpg"
      />
    </div>
    <h1>Pago verificado</h1>
    <h2>Gracias por tu compra, {data_user.name}</h2>
    <div style="text-align: center">
      <table border="1" style="margin: 0 auto; width: 100%">
        <tr>
          <th># Pedido</th>
          <th>Fecha</th>
          <th>Total</th>
          <th>Método de Pago</th>
        </tr>
        <tr>
          <td>{data_payment.id}</td>
          <td>{data_payment.date}</td>
          <td>{data_payment.total}</td>
          <td>{data_payment.payment_method}</td>
        </tr>
      </table></div>
      <h3>Tus números son</h3>
      
         {numbers_div}
        
     
    
                    </body>
                </html>"""
        
        message.attach(MIMEText(text,'plain'))
        message.attach(MIMEText(html,'html'))

        try:
            server = smtplib.SMTP("smtp.gmail.com",587)
            server.starttls()
            server.login("dmlord17@gmail.com","ihdclnptddsmyqfs")
            server.sendmail("dmlord17@gmail.com","dmlord17@gmail.com",message.as_string())
            server.quit()
            print("Email send")
            return jsonify({"message": "Email send succesfull"}),200
        except Exception as error:
            print(error)
            print("Email not sending, error")
            return jsonify({"message":"Error, try again, later"}),500
        