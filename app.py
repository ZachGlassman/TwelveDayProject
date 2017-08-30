from flask import Flask, render_template, request, redirect
import requests
import os
import pandas as pd
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Category10

app = Flask(__name__)
API_KEY = os.environ.get('Quandl_API_KEY')


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


@app.route('/', methods=['POST'])
def stock_input():
    qr = QuandleRequest(request.form['stock-ticker'])
    df = qr.get()
    p = figure(x_axis_type='datetime',
               tools=['pan', 'save', 'undo'])
    rel_vars = ['adj_close', 'adj_high', 'adj_low', 'open',
                'adj_open', 'close']
    colors = Category10[len(rel_vars)]
    tick = qr.tick()
    for i, var in enumerate(rel_vars):
        p.line(df['date'].values,
               df[var].values,
               line_width=2,
               line_color=colors[i],
               legend="{}: {}".format(tick, var))
    script, div = components(p)
    return render_template('plots.html', script=script, plot_div=div)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
