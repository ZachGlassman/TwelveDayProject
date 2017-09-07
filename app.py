from flask import Flask, render_template, request, redirect, jsonify, url_for
import requests
import os
import pandas as pd
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Category10, Category20
from bokeh.layouts import gridplot
import datetime
from Transform import AccessTransform, DifferenceTransform

app = Flask(__name__)
# some global variables for applications
API_KEY = os.environ.get('Quandl_API_KEY')
if API_KEY is None:
    # we are local development, kluge for now
    with open(os.path.dirname(__file__) + '/../api_key.txt', 'r') as fp:
        API_KEY = fp.readlines()[0]


PLOT_OPTIONS = {
    'tools': "pan,wheel_zoom,box_zoom,reset,save",
    'height': 250,
    'width': 250
}

CHECK_ITEMS = [AccessTransform("Closing price", "close", "date", "close"),
               AccessTransform("Adjusted closing price",
                               "adj_close", "date", "adj_close"),
               AccessTransform("Opening price", "open", "date", "open"),
               AccessTransform("Ajusted opening price",
                               "adj_open", "date", "adj_open"),
               DifferenceTransform("Price Change", 'p_diff',
                                   'date', ['open', 'close'])
               ]
CHECK_ITEMS_DICT = {i.id: i for i in CHECK_ITEMS}

# TODO
# add metadata call and then only fetch relevent data


class QuandleRequest(object):
    def __init__(self, ticker_):
        """Object to handle Quandle Interface"""
        self._params = {}
        self.ticker(ticker_)
        self._params['api_key'] = str(API_KEY)

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


def _plot_one(df, rel_vars, tick, normalize):
    p = figure(x_axis_type='datetime',
               tools=PLOT_OPTIONS['tools'])
    if len(rel_vars) > 2:
        colors = Category10[len(rel_vars)]
    else:
        colors = ['red', 'blue']
    for i, var in enumerate(rel_vars):
        x, y = CHECK_ITEMS_DICT[var](df, normalize)
        p.line(x, y,
               line_width=2,
               line_color=colors[i],
               legend="{}: {}".format(tick, var))
    p.xaxis.axis_label = 'Date'
    script, div = components(p)
    return jsonify(script=script, plot_div=div)


def _plot_two(df, rel_vars, tick, normalize):
    """create a figure for each relevent variable"""
    figures = []
    ticks = list(sorted(df['ticker'].unique()))
    if len(ticks) > 2:
        colors = Category20[len(ticks)]
    else:
        colors = ['red', 'blue']
    for i, var in enumerate(rel_vars):
        if i > 0:
            p = figure(x_axis_type='datetime',
                       x_range=figures[0].x_range,
                       tools=PLOT_OPTIONS['tools'])
        else:
            p = figure(x_axis_type='datetime',
                       tools=PLOT_OPTIONS['tools'])
        # now loop through each tick
        for j, tick in enumerate(ticks):
            _df = df[df['ticker'] == tick]
            x, y = CHECK_ITEMS_DICT[var](_df, normalize)
            p.line(x, y,
                   line_width=2,
                   line_color=colors[j],
                   legend="{}".format(tick))
        figures.append(p)

    script, div = components(gridplot(*tuple(figures),
                                      ncols=3,
                                      plot_width=PLOT_OPTIONS['height'],
                                      plot_height=PLOT_OPTIONS['width']))
    return jsonify(script=script, plot_div=div)


def parse_ticker(request):
    """parse the return ticker stock-tick-num"""
    start_date = request.args.get('start-date', None)
    end_date = request.args.get('end-date', None)
    return request.args['ticker-select'], start_date, end_date


def format_date(date):
    month, day, year = date.split('/')
    return '{}{}{}'.format(year, month, day)


def get_query_keys_vars(keys):
    rel_vars = []
    for key in keys:
        if key in CHECK_ITEMS_DICT.keys():
            rel_vars += CHECK_ITEMS_DICT[key].variables
    return list(set(rel_vars))


@app.route('/_stock_data', methods=['GET'])
def stock_input():
    tick, start_date, end_date = parse_ticker(request)
    normalize = request.args.get('normalize', None)
    if normalize is not None:
        normalize = True
    else:
        normalize = False
    if tick == '':
        return jsonify({})
    qr = QuandleRequest(tick)
    if start_date != '':
        qr.start_date(format_date(start_date))
    if end_date != '':
        qr.end_date(format_date(end_date))
    df = qr.get()
    num_ticks = len(df['ticker'].unique())
    rel_vars = [i for i in request.args.keys() if i in CHECK_ITEMS_DICT.keys()]
    tick = qr.get_tick()
    if num_ticks == 1:
        return _plot_one(df, rel_vars, tick, normalize)
    elif num_ticks > 1:
        return _plot_two(df, rel_vars, tick, normalize)
    else:
        return jsonify({})


def get_tick_names():
    root = os.path.dirname(os.path.abspath(__file__))
    static = os.path.join(root, 'static')
    filename = os.path.join(static, 'tick_names.txt')
    with open(filename, 'r') as fp:
        names = fp.readlines()[0].split(',')
    return names


@app.route('/')
def index():
    year_list = list(range(2014, datetime.datetime.now().year + 1))
    tick_names = get_tick_names()
    return render_template('index.html',
                           check_items=CHECK_ITEMS,
                           year_list=year_list,
                           tick_names=tick_names)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
