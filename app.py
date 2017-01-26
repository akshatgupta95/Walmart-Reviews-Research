from flask import Flask, request, render_template, g
import os
import json
import urllib2

app = Flask(__name__)

sec_k = os.urandom(24)
app.secret_key = sec_k


@app.route('/')
def index():
	return render_template('search.html', items_dict={}, search_query_dict={})

@app.route('/search')
def search():
	return render_template('search.html')

def make_api_call(search_query):
	search_query = search_query.replace(' ', '%20')
	url = "http://api.walmartlabs.com/v1/search?apiKey=vydf8ym75f468rbgwy5k5xwp&query=" + search_query
	data = json.load(urllib2.urlopen(url))
	return_dict = {}

	for item in data['items']:
		item_name = item['name']
		item_url = item['productUrl']
		item_id = item['itemId']
		review_url = "http://api.walmartlabs.com/v1/reviews/%s?apiKey=vydf8ym75f468rbgwy5k5xwp&format=json" % str(item_id)
		review_data = json.load(urllib2.urlopen(review_url))
		reviews = []
		for review in review_data['reviews']:
			reviews.append(review['reviewText'])

		return_dict[item_id] = {
			'item_name' : item_name,
			'item_url' : item_url,
			'reviews' : reviews
		}

	return return_dict

@app.route('/request_handler', methods=['GET', 'POST'])
def request_handler():
	search_query = request.form['search_query']
	items_dict = make_api_call(search_query)
	search_query_dict={'search_query' : search_query}
	return render_template('search.html', items_dict=items_dict, search_query_dict=search_query_dict)

if __name__ == '__main__':
	app.run(debug=True)