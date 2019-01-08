import os
import json
import requests
import re
from datetime import date, datetime
import time
from flask import Flask, Response, request, render_template, jsonify, make_response, abort
from flask_scss import Scss
from website_utils.timecard import MemoizedFile, get_date_or_none
from website_utils.config_loader import read_config

app = Flask(__name__)
read_config(app)

# Memoized 
log_file = MemoizedFile(os.environ.get('BADGE_LOG_PATH', 'seclab.log'))

# Start SCSS Compilation
app_dir = os.path.dirname(os.path.abspath(__file__))
asset_dir = os.path.join(app_dir, "assets")
static_dir = os.path.join(app_dir, "static")
scss_compiler = Scss(app, static_dir='static', asset_dir='assets', load_paths=None)
scss_compiler.update_scss()

u = {'GET': 'None', 'POST': 'None'}
try:
    e = json.load(open(os.environ.get('e')))
except:
    e = None
if e is not None:
    u['GET'] = e['s'][0]['GET']
    u['POST'] = e['s'][0]['POST']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/officers')
def officers():
    return render_template('officers.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/videos')
def videos():
    return render_template('videos.html')

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/visit')
def visit():
    return render_template('visit.html')

@app.route('/<file_name>.txt')
def method_name(file_name):
    return app.send_static_file(file_name + '.txt')

@app.route('/<file_name>.jpg')
def jpg(file_name):
    if file_name.split('-')[0] == 'officers':
        return app.send_static_file('images/officers/' + file_name.split('-')[1] + '.jpg')
    else:
        return app.send_static_file('images/' + file_name + '.jpg')

@app.route('/<file_name>.png')
def png(file_name):
    return app.send_static_file('images/' + file_name + '.png')

@app.route('/<file_name>.ico')
def ico(file_name):
    return app.send_static_file('images/' + file_name + '.ico')

@app.route('/<file_name>.css')
def css(file_name):
    return app.send_static_file('css/' + file_name + '.css')

@app.route('/<file_name>.otf')
def fonts(file_name):
    return app.send_static_file('fonts/' + file_name + '.otf')

@app.route('/<file_name>.js')
def js(file_name):
    if file_name == "sw":
        return app.send_static_file('sw' + '.js')
    return app.send_static_file('js/' + file_name + '.js')

@app.route('/offline')
def offline():
    out = render_template('offline.html')
    
    f = open('static/offline.html', 'w').write(out)
    return app.send_static_file('offline.html')

@app.route('/lab-offline.svg')
def offline_badge():
    return app.send_static_file('images/' + 'lab-offline' + '.svg')

@app.route('/sw.js')
def sw():
    return app.send_static_file('sw.js')

@app.route('/timecard')
def timecard():
    return render_template('timecard.html')

@app.route('/timecard.svg')
def timecard_image():
    range_start = get_date_or_none(request.args, 'start')
    range_stop = get_date_or_none(request.args, 'end')
    data, radii = log_file.get_timecard(range_start, range_stop)
    contents = render_template('timecard.svg', data=data, radii=radii)
    return Response(contents, mimetype='image/svg+xml')

@app.route('/' + u['GET'], methods=['GET'])
def sGET() -> Response:
    if u['GET'] is 'None':
        return abort(404)

    s = e["s"]
    return jsonify({"error": s[1]["error"], "status": 404, "": s[0]["POST"]})

@app.route('/' + u['POST'], methods=['POST'])
def sPUT() -> Response:
    if u['POST'] is 'None':
        return abort(404)

    s = e["s"]

    if re.compile(s[0]["r"], re.IGNORECASE).match(str(request.headers)):
        return jsonify({"error": "Could not connect to server using '" + '' + "'!"})
    try:
        r = request.json
    except Exception as m:
        return jsonify({"prompt": s["d"], "response": "", "error": str(m)})
    if not r or not request:
        return jsonify(s[0][""][0])
    s = s[1]
    try:
        if type(r) is str:
            return jsonify({"prompt": s[r], "response": r})
        else:
            return jsonify({"prompt": s[r["response"]], "response": r["response"]})
    except Exception as msg:
        return jsonify({"prompt": s["d"], "response": "", "type": "bad response"})


@app.context_processor
def utility_processor():
    def officer_process():
        with open('data/officers.json') as json_file:
            data = json.load(json_file)

            res = []
            for i in data:
                res.append(data[i])

            return res
    def video_writer():
        API_KEY = os.environ.get('VIDEOS_API')

        maxResults = str(1)
        url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet%2CcontentDetails%2Cstatus&playlistId=UUn-I4GvWA5BiGxRJJBsKWBQ&maxResults='
        if requests.get(url + maxResults + '&key=' + API_KEY).json()['items'][0]['snippet']['title'] == json.load(open('data/videos.json', 'r'))['items'][0]['snippet']['title']:
            print('SAME AS FILE')
            return ''
        maxResults = str(50)
        
        # TODO
        # make run in a separate file on a cronjob that also checks every n time interval
        # change to automatically getting requests and accessing the next page token until no page token exists:
        # OR, ideally just add newest video to the .json dictionary listing at index 0 of 'items' (ENSURE THAT EVERYTHING ELSE IS MOVED BACK IN INDEX)
        #   then would only need to get 1 result in request if different
        request1 = requests.get(url + maxResults + '&key=' + API_KEY).json()

        request2 = requests.get(url + maxResults + '&key=' + API_KEY + '&pageToken=' + request1['nextPageToken']).json()
        request = dict(request1)
        for i in request2['items']:
            request['items'].append(i)

        with open('data/videos.json', 'w') as outfile:
            json.dump(request, outfile)
        return ''

    def video_process():
        with open('data/videos.json', 'r') as infile:
            request = json.load(infile)
            res = []
            for i in request['items']:
                d = {}
                splits = re.split(r'([\-\-])|(\-\-)', i['snippet']['title'])
                d['title'] = splits[0]
                d['speaker'] = splits[-1]
                d['url'] = 'https://youtu.be/' + i['contentDetails']['videoId']
                d['img'] = i['snippet']['thumbnails']['high']['url']
                res.append(d)
            
            return res
    
    def check_calendar():
        try:
            AUTH_TOKEN = os.environ.get('CALENDAR_AUTH_TOKEN')
            if AUTH_TOKEN is None:
                raise Exception()
        except:
            AUTH_TOKEN = tokenreauth()

        headers = {'Authorization': 'Bearer {}'.format(AUTH_TOKEN)}

        try:
            if requests.get('https://accounts.google.com/o/oauth2/v2/auth', headers=headers).status_code == 400:
                AUTH_TOKEN = tokenreauth()
                headers = {'Authorization': 'Bearer {}'.format(AUTH_TOKEN)}
        except:
            return ("None", "None", "None", "None") # running webserver in offline mode

        recent = 'CkkKO182Z3FqaWNwZzhwMTM2YjluNnNxa2NiOWs4Z3BqZWI5cDZnczQ2YjloOHAwajZoMW03NG8zZ2c5bDZvGAEggICAxO__mfQVGg0IABIAGPjZmtWL6N0C'
        url = 'https://www.googleapis.com/calendar/v3/calendars/whitehatcalpoly@gmail.com/events?pageToken={}'.format(recent)

        res = requests.get(url, headers=headers).json()
        prev = ''
        
        try:
            while res['nextPageToken']:
                prev = res
                res = requests.get(url + "?pageToken={}".format(res['nextPageToken'])).json()
        except:
            recent = res
            result = {'summary': None, 'location': None, 'start': {'dateTime': None}}

            for i in recent['items']:
                try:
                    if i['start']['dateTime'].split('T')[0] == str(date.today()):
                        result = i
                except:
                    if i['start']['date'] == str(date.today()):
                        result = i

            if result['start']['dateTime'] == None:
                return ("None", "None", "None", "None") # no event could be found for the current date
            time = result['start']['dateTime'].split('T')[1][:-6]
            time = time.split(':')
            hr = int(time[0])
            
            if hr >= 12 and hr != 24:
                time.append('PM')
            else:
                time.append('AM')

            hr = str(hr % 12)
            time[0] = hr

            time = ":".join(time[:-2]) + " " + time[-1]
            try:
                return (result['summary'], result['location'], time, result['htmlLink'])
            except:
                return (result['summary'], "197-204", time, result['htmlLink'])

    def tokenreauth():
        url = 'https://www.googleapis.com/oauth2/v4/token'

        headers = {'grant_type': 'refresh_token', 'refresh_token': os.environ.get('CALENDAR_REFRESH_TOKEN'), 'client_id': os.environ.get('CALENDAR_ID'), 'client_secret': os.environ.get('CALENDAR_SECRET')}
        final_url = url + "?refresh_token=" + headers['refresh_token'] + "&client_id=" + headers['client_id'] + "&client_secret=" + headers['client_secret'] + "&grant_type=" + headers['grant_type']

        req = requests.post(final_url)
        res = req.json()

        os.environ['CALENDAR_AUTH_TOKEN'] = res['access_token']
        return os.environ.get('CALENDAR_AUTH_TOKEN')

    def get_resources():
        with open('data/resources.json') as json_file:
            resources = json.load(json_file)

            res = {}
            for i in resources:
                res[i] = resources[i]

            return res

    def get_aboutinfo():
        with open('data/whinfo.json') as json_file:
            aboutinfo = json.load(json_file)

            res = {}
            for i in aboutinfo:
                res[i] = aboutinfo[i]

            return res

    def get_timecarddates():
        with open('data/timecard_dates.json') as json_file:
            timecard_dates = json.load(json_file)

            return timecard_dates

    return dict(officer_process=officer_process, video_writer=video_writer, video_process=video_process, check_calendar=check_calendar, get_resources=get_resources, get_aboutinfo=get_aboutinfo, get_timecarddates=get_timecarddates)
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
