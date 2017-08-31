from flask import Flask, render_template, request, redirect, jsonify
import requests
import os
import pandas as pd
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Category10, Category20
from bokeh.layouts import gridplot
import datetime

app = Flask(__name__)
API_KEY = os.environ.get('Quandl_API_KEY')


class QuandleRequest(object):
    def __init__(self, ticker_):
        """Object to handle Quandle Interface"""
        self._params = {}
        self.ticker(ticker_)
        self._params['api_key'] = str(API_KEY)
        self.start_date('2017-01-01')

    def get_tick(self):
        return self._params['ticker']

    def ticker(self, ticker):
        self._params['ticker'] = ticker.replace(' ', '')

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


def _plot_one(df, rel_vars, tick):
    p = figure(x_axis_type='datetime',
               tools="pan,wheel_zoom,box_zoom,reset,save")
    if len(rel_vars) > 2:
        colors = Category10[len(rel_vars)]
    else:
        colors = ['red', 'blue']
    for i, var in enumerate(rel_vars):
        p.line(df['date'].values,
               df[var].values,
               line_width=2,
               line_color=colors[i],
               legend="{}: {}".format(tick, var))
    p.xaxis.axis_label = 'Date'
    script, div = components(p)
    return jsonify(script=script, plot_div=div)


def _plot_two(df, rel_vars, tick):
    """create a figure for each relevent variable"""
    figures = []
    ticks = list(sorted(df['ticker'].unique()))
    if len(ticks) > 2:
        colors = Category20[len(ticks)]
    else:
        colors = ['red', 'blue']
    for i, var in enumerate(rel_vars):
        p = figure(x_axis_type='datetime',
                   tools="pan,wheel_zoom,box_zoom,reset,save")
        # now loop through each tick
        for j, tick in enumerate(ticks):
            _df = df[df['ticker'] == tick]
            p.line(_df['date'].values,
                   _df[var].values,
                   line_width=2,
                   line_color=colors[j],
                   legend="{}".format(tick))
        figures.append(p)

    script, div = components(gridplot(*tuple(figures), ncols=3))
    return jsonify(script=script, plot_div=div)


@app.route('/_stock_data', methods=['GET'])
def stock_input():
    tick = request.args['stock-ticker']
    if tick == '':
        return jsonify({})
    qr = QuandleRequest(request.args['stock-ticker'])
    df = qr.get()
    num_ticks = len(df['ticker'].unique())
    rel_vars = [i for i in request.args.keys() if i in list(df.columns)]
    tick = qr.get_tick()
    if num_ticks == 1:
        return _plot_one(df, rel_vars, tick)
    elif num_ticks > 1:
        return _plot_two(df, rel_vars, tick)
    else:
        return jsonify({})


@app.route('/')
def index():
    check_items = [
        {"id": 'close', 'name': "Closing price"},
        {"id": 'adj_close', 'name': "Adjusted closing price"},
        {"id": 'open', 'name': 'Opening price'},
        {"id": 'adj_open', 'name': 'Ajusted opening price'}]

    year_list = list(range(2014, datetime.datetime.now().year + 1))
    return render_template('index.html',
                           check_items=check_items,
                           year_list=year_list)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
