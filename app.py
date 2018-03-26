from flask import Flask, request, render_template, redirect
import pandas as pd
import numpy as np
import requests
import datetime
import simplejson as json
from bokeh.resources import INLINE
from bokeh.io import output_notebook, curdoc
from bokeh.layouts import row,column
from bokeh.models import ColumnDataSource, DataRange1d, Select, TextInput, CDSView
from bokeh.models.scales import LinearScale
from bokeh.plotting import figure, show,save, output_file
from bokeh.embed import components

def get_data(company):
    #Determine date one day in advance
    startdate=datetime.datetime.now()-datetime.timedelta(days=28)
    while datetime.datetime.now().day!=startdate.day+1:
        startdate=startdate-datetime.timedelta(1)
    
    #download the data from the api
    parameters={'date.gt':startdate.strftime('%Y-%m-%d'), 'ticker':company, 'api_key':'7chPxU-NeqD3a-cyxyyH'}
    webdata=requests.get('https://www.quandl.com/api/v3/datatables/WIKI/PRICES',params=parameters)
    
    #transform the downloaded data into a dataframe
    ##convert the json into a dictionary and isolate the datatable parameter
    data_dict=json.loads(webdata.text)
    dict_datatable=data_dict['datatable']
    ##get the column name parameters and convert form UTF8 into a string
    column_names=[str(column['name']) for column in dict_datatable['columns']]
    ##convert list of lists datatable into pandas data frame
    ticker_pd=pd.DataFrame(columns=column_names,data=dict_datatable['data'])
    ##convert date from string to datetime.datetime
    ticker_pd['date']=pd.to_datetime(ticker_pd['date'])
    ##rename ex-dividend to ex_dividend in case it needs to be stored in a database for cacheing
    ticker_pd.rename(columns={u'ex-dividend':u'ex_dividend'},inplace=True)
    ticker_pd['range']=ticker_pd['high']-ticker_pd['low']
    ticker_pd['adj_range']=ticker_pd['adj_high']-ticker_pd['adj_low']
    ticker_pd.to_csv('ticker_pd.csv')	
    return ColumnDataSource(data=ticker_pd)

def make_plot():
    column_tuple=tuple([app.vars['adjusted'],app.vars['value']])
    plot_column=col_dict[column_tuple]
    ds=get_data(app.vars['company'])
    plot=figure(x_axis_type='datetime',plot_width=800, toolbar_location='right')
    startdate=datetime.datetime.now()-datetime.timedelta(days=28)
    while datetime.datetime.now().day!=startdate.day+1:
        startdate=startdate-datetime.timedelta(1)
    sd_str=datetime.datetime.strftime(startdate,'%m/%d/%Y')
    ed_str=datetime.datetime.strftime(datetime.datetime.now(),'%m/%d/%Y')    
    plot.title.text='Stock Ticker '+sd_str+'-'+ed_str
    plot.line('date',plot_column,source=ds, line_width=3, line_alpha=.6)  
    plot.xaxis.axis_label='Date'
    if app.vars['adjusted']==True:
        plot.yaxis.axis_label=app.vars['value'] + '(Adjusted)'
    else:
        plot.yaxis.axis_label=app.vars['value']
    return plot   
	

app = Flask(__name__)
app.vars={}

col_dict={tuple([False,'open']):'open',tuple([False,'high']):'high',tuple([False,'low']):'low',
          tuple([False,'close']):'close',tuple([False,'volume']):'volume', tuple([False,'ex_dividend']):'ex_dividend',
          tuple([True,'ex_dividend']):'ex_dividend',tuple([False, 'split_ratio']):'split_ratio',
          tuple([True,'open']):'adj_open',tuple([True,'close']):'adj_close', tuple([True, 'high']):'adj_high', 
          tuple([True,'low']):'adj_low', tuple([True,'volume']):'adj_volume', tuple([True,'range']):'range',
          tuple([False,'range']):'adj_range'}



@app.route('/info', methods=['GET','POST'])
def input_form():
	if request.method=='GET':
		f=open('Get_worked.txt','w')
		f.write('Get Worked')
		f.close() 
		return render_template('input_form.html')		 

@app.route('/submitted', methods=['POST'])
def submitted():
	f=open('test.txt','w')
	f.write('post_worked')
	app.vars['company']=str(request.form['ticker'])
	app.vars['value']=str(request.form['value'])
	if 'adjusted' not in request.form:
		app.vars['adjusted']=False
	else:
		app.vars['adjusted']=True
	f.write('%s,%s,%s\n'%(app.vars['company'],app.vars['value'],app.vars['adjusted']))
	f.close()
	return redirect('/plot_page')


@app.route('/plot_page',methods=['POST','GET'])
def plot():
	output_file('templates/plot_page.html')
	plot=make_plot()
        plot.x_scale=LinearScale()
	plot.y_scale=LinearScale()
        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()
        save(plot)
  	return render_template('plot_page.html')

if __name__ == '__main__':
  app.run(debug=True, port=5000, host='0.0.0.0')
