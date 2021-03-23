from flask import Flask, render_template, url_for 

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD']=True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/adminLogin')
def adminLogin():
    return render_template('adminLogin.html')

@app.route('/customerSignup')
def customerSignup():
    return render_template('customerSignup.html')

@app.route('/restaurantSignup')
def restaurantSignup():
    return render_template('restaurantSignup.html')

@app.route('/deliveryAgentSignup')
def deliveryAgentSignup():
    return render_template('deliveryAgentSignup.html')

if __name__ == "__main__":
    # cache.init_app(app)
    app.run(debug=True)