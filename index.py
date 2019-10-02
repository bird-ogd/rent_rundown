from flask import Flask, redirect, render_template, request, session
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import csv
import os
from flask_dropzone import Dropzone

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config.update(
    DROPZONE_MAX_FILE_SIZE=1,
    DROPZONE_REDIRECT_VIEW='result'
)
dropzone = Dropzone(app)

def csv_to_list(csv_file):
	f = open(csv_file)
	reader = csv.reader(f)
	data_list = list(csv.reader(f))
	data_list.pop(0)
	return data_list

def to_datetime(datestring, date_format):
	return datetime.strptime(datestring, date_format)

def return_result(filename):
	result = csv_to_list(filename)

	rent_due = []
	daily_balance = []
	balance = 0
	total_in = 0
	total_out = 0
	total_payment_dates = 0

	date_pos = 0
	in_pos = 2
	out_pos = 3
	date_format = "%d/%m/%y"

	startdate = to_datetime(result[0][0], date_format)
	enddate = to_datetime(result[-1][0], date_format) + relativedelta(months=1)
	tenancy_length = (enddate - startdate).days
	length = tenancy_length

	while tenancy_length > 0:
		for i in result:
			if startdate == to_datetime(i[date_pos], date_format):
				if(i[2]):
					balance += float(i[in_pos])
					total_in += float(i[in_pos])
				if(i[3]):
					balance -= float(i[out_pos])
					total_out += float(i[out_pos])
					total_payment_dates += 1
		rent_due.append(balance)
		startdate += relativedelta(days=1)
		tenancy_length -= 1

	for j in rent_due:
		if j > 0:
			daily_balance.append(0)
		else:
			daily_balance.append(j)

	rent = total_out / total_payment_dates
	final_arrears = total_out - total_in
	avg_arrears = abs(sum(daily_balance) / len(daily_balance))
	two_months = rent * 2
	arrears_prop = final_arrears / rent / 2.5

	if final_arrears > two_months:
		prop = 100
	else:
		prop = avg_arrears / rent + arrears_prop

	return [	prop, 
				length, 
				rent, 
				total_in,
				total_out,
				final_arrears,
				total_payment_dates,
				round(avg_arrears, 2)
			]

@app.route("/", methods=['GET', 'POST'])
def index():
	session.clear()
	if request.method == 'POST':
		f = request.files.get('file')
		result_set = return_result(f.filename)
		session['result'] = result_set
	return render_template("index.html")

@app.route("/result", methods=['GET', 'POST'])
def result():
	return render_template("result.html", 	prop=session['result'][0], 
											tenancy_length=session['result'][1],
											rent="{:12.2f}".format(session['result'][2]),
											total_in="{:12.2f}".format(session['result'][3]),
											total_out="{:12.2f}".format(session['result'][4]),
											final_arrears="{:12.2f}".format(session['result'][5]),
											total_payment_dates=session['result'][6],
											average_arrears="{:12.2f}".format(session['result'][7]),
											)