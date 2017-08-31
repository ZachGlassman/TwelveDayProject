from flask import Flask, render_template, request, redirect, jsonify
import requests
import os
import pandas as pd
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Category10

app = Flask(__name__)
API_KEY = os.environ.get('Quandl_API_KEY', '4YU33LfF8JAjDEzKThkY')


class QuandleRequest(object):
    def __init__(self, ticker):
        """Object to handle Quandle Interface"""
        self._params = {}
        self._params['ticker'] = ticker
        self._params['api_key'] = str(API_KEY)
        self.start_date('2017-01-01')

    def tick(self):
        return self._params['ticker']

    def start_date(self, date):
        self._params['date.gte'] = date

    def end_date(self, date):
        self._params['date.lte'] = date

    def _request(self):
        r = requests.get('https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json',
                         params=self._params)
        # handle errors
        self._response = r.json()

    def _response_to_df(self):
        j = self._response['datatable']
        _d = {col['name']: [k[i] for k in j['data']]
              for i, col in enumerate(j['columns'])}

        df = pd.DataFrame(_d)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def get(self):
        self._request()
        return self._response_to_df()


@app.route('/_stock_data', methods=['GET'])
def stock_input():
    qr = QuandleRequest(request.args['stock-ticker'])
    df = qr.get()
    pos_vars = list(df.columns)
    p = figure(x_axis_type='datetime',
               tools="pan,wheel_zoom,box_zoom,reset,save")
    rel_vars = [i for i in request.args.keys() if i in pos_vars]
    if len(rel_vars) > 2:
        colors = Category10[len(rel_vars)]
    else:
        colors = ['red', 'blue']
    tick = qr.tick()
    for i, var in enumerate(rel_vars):
        p.line(df['date'].values,
               df[var].values,
               line_width=2,
               line_color=colors[i],
               legend="{}: {}".format(tick, var))
    p.xaxis.axis_label = 'Date'
    script, div = components(p)
    return jsonify(script=script, plot_div=div)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
