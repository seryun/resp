from flask import Flask,render_template,request
import sqlite3 as sql
import matplotlib.pyplot as plt
import numpy as np
from functools import wraps, update_wrapper
from datetime import datetime
from io import BytesIO
from flask import send_file, make_response

import requests

plt.style.use('ggplot')

app = Flask(__name__)

date = datetime.now()
today = date.strftime('%Y%m%d')
graphdate = today


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
        
    return update_wrapper(no_cache, view)


@app.route('/')
def home():
   date = datetime.now()
   today = date.strftime('%Y%m%d')
   con = sql.connect('test3.db')
   con.row_factory = sql.Row
   cur = con.cursor()
   cur.execute("select * from d"+today+" order by date_time desc limit 1")
   rows = cur.fetchall();
   
   con.commit()

   return render_template('home.html', rows=rows)


@app.route('/about')
def about():
    return render_template('about.html') 


@app.route('/lists',methods=['POST','GET'])
@nocache
def lists():
    global today
    con = sql.connect('test3.db')
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("select * from d"+today)
    rows = cur.fetchall()
    if request.method== 'POST':
        try:
            select = request.form['select']
            global graphdate
            graphdate=select
            with sql.connect("test3.db") as con:
                con.row_factory = sql.Row
                cur = con.cursor()
                cur.execute("select * from d"+select)
                rows = cur.fetchall()
                con.commit()
        except:
            con.rollback()
        
    return render_template("lists.html",rows=rows)


@app.route('/linechart/')
@nocache
def linechart():

    con = sql.connect('test3.db')
    c = con.cursor()
    c.execute('SELECT date_time, rpm FROM d'+graphdate)
    data = c.fetchall()

    date_times = []
    rpms = []
     
    for row in data:
        date_times.append(row[0][12:20])
        rpms.append(row[1])

    plt.plot_date(date_times,rpms,c="blue",ls="--",mec="blue",marker="s",ms=4)
    plt.xlabel('Date Time')
    plt.ylabel('RPM')
    plt.title('Data Graph')
    plt.yticks(np.arange(0, 50, 5))
   
    fig = plt.gcf()
    fig.set_size_inches(300, 7)
    fig.autofmt_xdate(rotation=20)
    
    plt.axhspan(0, 7, color='#FAED7D', alpha=0.4)
    plt.axhspan(7, 30, color='#74D36D', alpha=0.4)
    plt.axhspan(30, 50, color='#FAED7D', alpha=0.4)
    plt.tight_layout()
    plt.margins(x=0)
    
    img = BytesIO()
    img.truncate()
    fig.savefig(img)
    img.seek(0)
    
    return send_file(img, mimetype='image/gif')


@app.route('/graph')
@nocache
def graph():
    msg=graphdate
    return render_template('graph.html',msg=msg)


if __name__ == '__main__':
   app.run(debug=True,threaded=True)
   
