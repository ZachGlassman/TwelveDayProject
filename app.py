from flask import Flask, render_template, request, redirect
from wtforms import Form, StringField
import requests
import os


app = Flask(__name__)
API_KEY = os.environ.get('Quandl_API_KEY')

class StockForm(Form):
  stock_id = StringField('Stock Ticker')

@app.route('/', methods=['POST'])
def stock_input():
  payload = {'ticker':request.form['stock-ticker'],
           'date.gte':'2017-05-18',
           'date.lte':'2017-05-20',
           'api_key':str(API_KEY)}
  r = requests.get(
            'https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json',
            params=payload
            )
  return r.json()

@app.route('/')
def index():
  form = StockForm()
  return render_template('index.html', form=form)

if __name__ == '__main__':
  port = int(os.environ.get("PORT", 5000))
  app.run(host='0.0.0.0', port=port)
