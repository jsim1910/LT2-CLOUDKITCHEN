from flask import Flask, redirect
from flask import render_template
from flask import request
from flask import session
from bson.json_util import loads, dumps
from flask import make_response
import database as db
import authentication
import logging
import ordermanagement as om

app = Flask(__name__)

# Set the secret key to some random bytes. 
# Keep this really secret!
app.secret_key = b's@g@d@c0ff33!'

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.INFO)

navbar = """
         <a href='/'>Home</a> 
         <a href='/stalls'>Branches</a>
         <p/>
         """

@app.route('/')
def index():
    return render_template('index.html', page="Index")

@app.route('/stalls')
def branches():
    return render_template('stalls.html', page="Stalls")

@app.route('/kusina')
def kusina():
    return render_template('kusina.html')    

@app.route('/products')
def products():
    product_list = db.get_products()
    return render_template('kusina.html', page="Products", product_list=product_list)

@app.route('/productdetails')
def productdetails():
    code = request.args.get('code', '')
    product = db.get_product(int(code))

    return render_template('productdetails.html', code=code, product=product)

@app.route('/chicos')
def chicos():
    return render_template('chicos.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/auth', methods = ['GET', 'POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')

    is_successful, user = authentication.login(username, password)
    app.logger.info('%s', is_successful)
    if(is_successful):
        session["user"] = user
        return redirect('/')
    else:
        return redirect('/login')

@app.route('/loginerror')
def loginerror():
    return render_template('loginerror.html', page="Login Error")

@app.route('/logout')
def logout():
    session.pop("user",None)
    session.pop("cart",None)
    return redirect('/')

@app.route('/addtocart')
def addtocart():
    code = request.args.get('code')
    product = db.get_product(int(code))
    item=dict()
    # A click to add a product translates to a 
    # quantity of 1 for now

    item["qty"] = 1
    item["name"] = product["name"]
    item["subtotal"] = product["price"]*item["qty"]
    item["code"] = code

    if(session.get("cart") is None):
        session["cart"]={}

    cart = session["cart"]
    cart[code]=item
    session["cart"]=cart

    return redirect('/foodtray')


@app.route('/foodtray')
def cart():
    return render_template('foodtray.html')

@app.route('/checkout')
def checkout():
    # clear cart in session memory upon checkout
    om.create_order_from_cart()
    session.pop("cart",None)
    return redirect('/ordercomplete')

@app.route('/ordercomplete')
def ordercomplete():
    return render_template('ordercomplete.html')

@app.route('/api/products',methods=['GET'])
def api_get_products():
    resp = make_response( dumps(db.get_products()) )
    resp.mimetype = 'application/json'
    return resp

@app.route('/api/products/<int:code>',methods=['GET'])
def api_get_product(code):
    resp = make_response(dumps(db.get_product(code)))
    resp.mimetype = 'application/json'
    return resp

@app.route('/updatecart', methods = ['POST'])
def updatecart():

    request_type = request.form.get('submit')
    code = request.form.get('code')
    product = db.get_product(int(code))
    cart = session["cart"]

    # Update quantity of item in cart
    if request_type == "Update":
        quantity = int(request.form.get("quantity"))
        cart[code]["qty"] = quantity
        cart[code]["subtotal"] = quantity * product["price"]

    # Remove item from cart
    elif request_type == 'Remove':
        del cart[code]

    session["cart"] = cart

    return redirect('/foodtray')