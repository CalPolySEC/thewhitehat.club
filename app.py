######## IMPORTS ########

import os
import json
import requests
import re
from datetime import date
from flask import Flask, Response, request, render_template, jsonify, abort, after_this_request
from flask_scss import Scss
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from website_utils.timecard import MemoizedFile, get_date_or_none
from website_utils.config_loader import read_config

######## Initial Flask Application Setup/Configuration ########

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
read_config(app)

# Auth for status API
auth = HTTPBasicAuth()
users = {os.environ.get('API_USER'): generate_password_hash(os.environ.get('API_PASS'))}

# Start SCSS Compilation
app_dir = os.path.dirname(os.path.abspath(__file__))
asset_dir = os.path.join(app_dir, "assets")
static_dir = os.path.join(app_dir, "static")
scss_compiler = Scss(app, static_dir='static', asset_dir='assets', load_paths=None)
scss_compiler.update_scss()

######## Environment-related ########

# Memoized 
log_file = MemoizedFile(os.environ.get('BADGE_LOG_PATH', 'seclab.log'))

u = {'GET': 'None', 'POST': 'None'}
try:
    e = json.load(open(os.environ.get('e')))
except:
    e = None
if e is not None:
    u['GET'] = e.get('s', [{}])[0].get('GET')
    u['POST'] = e.get('s', [{}])[0].get('POST')


######## Site Pages ########

@app.route('/')
def index():
    url = request.host_url + apiurl[1:] + '/' + 'index'
    try:
        req = requests.get(url, timeout=1)
    except requests.exceptions.Timeout:
        # if the API is overloaded, then return an error page to notify the user
        return render_template('timeout.html')

    page_data = req.json().get("data")
    return render_template('index.html', page_data=page_data)


@app.route('/<page_name>')
def view_page(page_name: str):
    with open('data/pages.json', 'r') as f:
        pages = json.load(f)

        if page_name in pages.get('pages', []):
            if page_name == 'videos':
                video_writer()

            url = request.host_url + apiurl[1:] + '/' + page_name
            try:
                req = requests.get(url, timeout=1)
            except requests.exceptions.Timeout:
                # if the API is overloaded, then return an error page to notify the user
                return render_template('timeout.html')

            page_data = req.json().get("data")

            return render_template(page_name + '.html', page_data=page_data)
        else:
            abort(404)

@app.route('/status.svg')
def status_image():
    @after_this_request
    def add_header(response):
        if 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'no-store,max-age=0'
        return response
    return app.send_static_file('images/status.svg')

@app.route('/status.json')
def status_json():
    jsn = json.loads(open('data/status.json').read())
    return jsonify(jsn)

@app.route('/<file_name>.txt')
def textfile(file_name: str):
    return app.send_static_file(file_name + '.txt')


@app.route('/<file_name>.jpg')
def jpg(file_name: str):
    if file_name.split('-')[0] == 'officers':
        return app.send_static_file('images/officers/' + file_name.split('-')[1] + '.jpg')
    else:
        return app.send_static_file('images/' + file_name + '.jpg')


@app.route('/<file_name>.png')
def png(file_name: str):
    return app.send_static_file('images/' + file_name + '.png')


@app.route('/<file_name>.ico')
def ico(file_name: str):
    return app.send_static_file('images/' + file_name + '.ico')


@app.route('/<file_name>.css')
def css(file_name: str):
    return app.send_static_file('css/' + file_name + '.css')


@app.route('/<file_name>.otf')
def fonts(file_name: str):
    return app.send_static_file('fonts/' + file_name + '.otf')


@app.route('/<file_name>.js')
def js(file_name: str):
    if file_name == "sw":
        return app.send_static_file('sw' + '.js')
    return app.send_static_file('js/' + file_name + '.js')


@app.route('/<file_name>.pdf')
def pdf(file_name: str):
    return app.send_static_file('resources/' + file_name + '.pdf')


@app.route('/timecard.svg')
def timecard_image():
    range_start = get_date_or_none(request.args, 'start')
    range_stop = get_date_or_none(request.args, 'end')
    data, radii = log_file.get_timecard(range_start, range_stop)
    contents = render_template('timecard.svg', data=data, radii=radii)
    return Response(contents, mimetype='image/svg+xml')


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


@app.route('/' + u['GET'], methods=['GET'])
def sGET() -> Response:
    if u['GET'] == 'None':
        return abort(404)

    s = e.get("s", [{}, {}])
    return jsonify({"error": s[1].get("error"), "status": 404, "": s[0].get("POST")})


@app.route('/' + u['POST'], methods=['POST'])
def sPUT() -> Response:
    if u['POST'] == 'None':
        return abort(404)

    s = e.get("s", [{}])

    if len(re.compile(s[0].get("r"), re.IGNORECASE).findall(str(request.headers))) == 0:
        return jsonify({"error": "Could not connect to server using '" + ''.join(
            re.compile('(' + s[0].get("r", '')[0:14] + ')(\S*)', re.IGNORECASE).findall(str(request.headers))[
                0]) + '' + "'!"})
    try:
        r = request.json
    except Exception as m:
        return jsonify({"prompt": s[1]["d"], "response": "", "error": str(m)})
    if not r or not request:
        return jsonify(s[0][""][0])
    s = s[1]
    try:
        if type(r) is str:
            return jsonify({"prompt": s[r], "response": r})
        else:
            return jsonify({"prompt": s[r["response"]], "response": r["response"]})
    except Exception as msg:
        try:
            return jsonify({"prompt": s["d"], "response": r["response"], "type": "bad response"})
        except:
            return jsonify({"prompt": s["d"], "response": "", "type": "bad response"})


######## API Endpoints ########

# Change the version number when major API version rewrites occur!
# (Although support for older versions is recommended to be kept live until services have been fully migrated)
version = 1

apiurl = '/api/' + 'v' + str(version)


@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False


@app.route(apiurl + '/status', methods=['POST'])
@auth.login_required
def change_status() -> Response:
    status_name = request.json.get("StatusName")
    status_color = request.json.get("StatusColor")
    if updateStatus(status_name, status_color):
        return jsonify({"message": f"Status changed to {status_name}.", "status": 200})
    return jsonify({"message": "Error updating status.", "status": 500})


@app.route(apiurl, methods=['GET'])
@app.route(apiurl + '/', methods=['GET'])
def api_root() -> Response:
    message = "Welcome to CPSEC's API!"
    data = None
    return jsonify({"message": message, "data": data, "status": 200})


@app.route(apiurl + '/<endpoint>', methods=['GET'])
def api(endpoint: str):
    filename = "data/api.json"
    try:
        with open(filename, "r") as f:
            data = json.load(f)

            if data.get(endpoint) is None:
                message = message = "UNAVAILABLE! The endpoint '" + apiurl + "/" + endpoint + "' does not exist!"
                data = None
                return jsonify(
                    {"endpoint": endpoint, "error": "invalid endpoint", "message": message, "data": data}), 404

            result = {}

            endpoint_message = data[endpoint]["message"]
            if endpoint_message:
                result['message'] = endpoint_message
            else:
                return jsonify({"endpoint": endpoint, "error": "missing message"}), 404

            endpoint_data = data[endpoint].get("data")
            endpoint_file = data[endpoint].get("file")
            endpoint_function = data[endpoint].get("function")

            if endpoint_data:
                result['data'] = endpoint_data
            else:
                result['data'] = {}

            if endpoint_file and endpoint_function is None:
                with open(endpoint_file, "r") as ep_f:
                    datares = json.load(ep_f)
                    result.update({"data": datares})

            if endpoint_function:
                if endpoint_file is not None:
                    endpoint_function = endpoint_function[:-2] + '(\'' + str(endpoint_file) + '\')'
                try:
                    datares = eval(endpoint_function)
                except Exception as msg:
                    return jsonify(
                        {"msg": str(msg), "endpoint": endpoint, "error": endpoint_function + " function error"}), 500

                result.update({"data": datares})

            return jsonify(result)

    except FileNotFoundError:
        return jsonify({"endpoint": endpoint, "error": "'" + filename + "': open failure"}), 404
    except json.JSONDecodeError:
        return jsonify({"endpoint": endpoint, "error": "'" + filename + "': invalid json"}), 404
    except:
        return jsonify({"endpoint": endpoint, "error": "internal error"}), 500


### API Endpoint-related Functions ###

def updateStatus(status_name, status_color):
    url = f"https://img.shields.io/badge/lab-{status_name}-{status_color}"
    try:
        r = requests.get(url)
        open("static/images/status.svg", "wb").write(r.content)
        open("data/status.json", "w").write(f'{{"status": "{status_name}"}}')
    except:
        return False
    return True


def getEndpoints():
    endpoints = []
    filename = "data/api.json"

    try:
        with open(filename, "r") as f:
            data = json.load(f)
            for i in data:
                endpoints.append(i)

        endpoints.sort()

        return {"endpoints": endpoints}

    except FileNotFoundError:
        return {"error": "'" + filename + "': open failure"}
    except json.JSONDecodeError:
        return {"error": "'" + filename + "': invalid json"}
    except Exception as msg:
        return {"error": str(msg)}


def getUpcomingEvents():
    return {"status": "todo"}


def getToday():
    today = check_calendar()

    if today == ("None", "None", "None", "None"):
        data = None
    else:
        data = {}
        data['event'] = today[0]
        data['location'] = today[1]
        data['time'] = today[2]
        data['url'] = today[3]

    return data


def getVideos(filename: str):
    video_writer()
    videolist = []
    channel = {"name": "White Hat Cal Poly", "id": "UCn-I4GvWA5BiGxRJJBsKWBQ"}

    try:
        with open(filename, "r") as f:
            videos = json.load(f)

            for v in videos.get('items', []):
                video = {}
                splits = re.split(r'( [\-\-] )|( \-\- )', v.get('snippet', {}).get('title'))
                video['title'] = splits[0]
                video['speaker'] = splits[-1]
                video['description'] = v.get('snippet', {}).get('description')
                video['id'] = v.get('contentDetails', {}).get('videoId')
                video['url'] = 'https://youtu.be/' + v.get('contentDetails', {}).get('videoId')
                video['uploaded'] = v.get('snippet', {}).get('publishedAt')
                video['img'] = v.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url')

                videolist.append(video)
        return {"videos": videolist, "count": len(videolist), "channel": channel}

    except FileNotFoundError:
        unavailable = {'title': 'Unavailable', 'speaker': 'Unavailable', 'url': '', 'img': '/lab1.jpg'}
        videolist = [unavailable]
        return {"error": "'" + filename + "': open failure", "videos": videolist, "count": 1, "channel": channel}
    except json.JSONDecodeError:
        unavailable = {'title': 'Unavailable', 'speaker': 'Unavailable', 'url': '', 'img': '/lab1.jpg'}
        videolist = [unavailable]
        return {"error": "'" + filename + "': invalid json", "videos": videolist, "count": 1, "channel": channel}
    except Exception as msg:
        unavailable = {'title': 'Unavailable', 'speaker': 'Unavailable', 'url': '', 'img': '/lab1.jpg'}
        videolist = [unavailable]
        return {"error": str(msg), "videos": videolist, "count": 1, "channel": channel}


def getOfficers(filename: str):
    data = {}
    try:
        with open(filename, "r") as f:
            data['officers'] = json.load(f)
            data['positions'] = list(i for i in data.get('officers', []))
            data['count'] = len(data['officers'])
            return data

    except FileNotFoundError:
        return {"error": "'" + filename + "': open failure"}
    except json.JSONDecodeError:
        return {"error": "'" + filename + "': invalid json"}
    except Exception as msg:
        return {"error": str(msg)}


def getTimecard(filename: str):
    data = {}
    try:
        with open(filename, "r") as f:
            data['dates'] = json.load(f)
            data['count'] = len(data['dates'])
            return data

    except FileNotFoundError:
        return {"error": "'" + filename + "': open failure"}
    except json.JSONDecodeError:
        return {"error": "'" + filename + "': invalid json"}
    except Exception as msg:
        return {"error": str(msg)}


def getStatus():
    res = open("data/status.json").read()
    return json.loads(res)


######## Error Routing ########

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


######## Utility Functions ########

def tokenreauth():
    url = 'https://www.googleapis.com/oauth2/v4/token'

    try:
        headers = {'grant_type': 'refresh_token', 'refresh_token': os.environ.get('CALENDAR_REFRESH_TOKEN'),
                   'client_id': os.environ.get('CALENDAR_ID'), 'client_secret': os.environ.get('CALENDAR_SECRET')}
        final_url = url + "?refresh_token=" + headers['refresh_token'] + "&client_id=" + headers[
            'client_id'] + "&client_secret=" + headers['client_secret'] + "&grant_type=" + headers['grant_type']
    except:
        return None  # local development

    req = requests.post(final_url)
    res = req.json()

    os.environ['CALENDAR_AUTH_TOKEN'] = res['access_token']
    return os.environ.get('CALENDAR_AUTH_TOKEN')


def check_calendar():
    try:
        AUTH_TOKEN = os.environ.get('CALENDAR_AUTH_TOKEN')
        if AUTH_TOKEN is None:
            raise Exception()
    except:
        AUTH_TOKEN = tokenreauth()

    if AUTH_TOKEN is None:
        return ("None", "None", "None", "None")  # running in local development

    headers = {'Authorization': 'Bearer {}'.format(AUTH_TOKEN)}

    try:
        if requests.get('https://accounts.google.com/o/oauth2/v2/auth', headers=headers).status_code == 400:
            AUTH_TOKEN = tokenreauth()
            headers = {'Authorization': 'Bearer {}'.format(AUTH_TOKEN)}
    except:
        return ("None", "None", "None", "None")  # running webserver in offline mode

    recent = 'CkkKO182Z3FqaWNwZzhwMTM2YjluNnNxa2NiOWs4Z3BqZWI5cDZnczQ2YjloOHAwajZoMW03NG8zZ2c5bDZvGAEggICAxO__mfQVGg0IABIAGPjZmtWL6N0C'
    url = 'https://www.googleapis.com/calendar/v3/calendars/whitehatcalpoly@gmail.com/events?pageToken={}'.format(
        recent)

    res = requests.get(url, headers=headers).json()
    prev = ''

    try:
        while res.get('nextPageToken') is not None:
            prev = res
            res = requests.get(url + "?pageToken={}".format(res.get('nextPageToken'))).json()
    except:
        recent = res
        result = {'summary': None, 'location': None, 'start': {'dateTime': None}}

        for i in recent.get('items', []):
            try:
                if i.get('start', {}).get('dateTime', '').split('T')[0] == str(date.today()):
                    result = i
            except:
                if i.get('start', {}).get('date') == str(date.today()):
                    result = i

        if result.get('start', {}).get('dateTime') is None:
            return ("None", "None", "None", "None")  # no event could be found for the current date
        time = result.get('start', {}).get('dateTime', '').split('T')[1][:-6]
        print(result.get('start', {}).get('dateTime', '').split('T')[1][:-6].split(':'))
        time = time.split(':')
        time.remove(time[-1])
        print(time)
        hr = int(time[0])

        if hr >= 12 and hr != 24:
            time.append('PM')
        else:
            time.append('AM')

        hr = str(hr % 12)
        if hr == "0":
            hr = "12"
        time[0] = hr

        time = ":".join(time[:-1]) + " " + time[-1]
        print(time)
        try:
            return (result.get('summary'), result.get('location'), time, result.get('htmlLink'))
        except:
            return (result.get('summary'), "197-204", time, result.get('htmlLink'))


def video_writer():
    API_KEY = os.environ.get('VIDEOS_API')
    if API_KEY is None:
        return None

    maxResults = str(1)
    url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet%2CcontentDetails%2Cstatus&playlistId=UUn-I4GvWA5BiGxRJJBsKWBQ&maxResults='
    try:
        if requests.get(url + maxResults + '&key=' + API_KEY).json().get('items', [{}])[0].get('snippet', {})[
            'title'] == json.load(open('data/videos.json', 'r')).get('items', [{}])[0].get('snippet', {}).get('title'):
            print('SAME AS FILE')
            return ''
        else:
            print("NOPE")
            # this is the same code as for exceptions, need to make better/cleaner...
            maxResults = str(50)

            # TODO
            # make run in a separate file on a cronjob that also checks every n time interval
            # change to automatically getting requests and accessing the next page token until no page token exists:
            # OR, ideally just add newest video to the .json dictionary listing at index 0 of 'items' (ENSURE THAT EVERYTHING ELSE IS MOVED BACK IN INDEX)
            #   then would only need to get 1 result in request if different
            request1 = requests.get(url + maxResults + '&key=' + API_KEY).json()

            request2 = requests.get(
                url + maxResults + '&key=' + API_KEY + '&pageToken=' + request1.get('nextPageToken')).json()
            request = dict(request1)
            for i in request2.get('items', []):
                request['items'].append(i)

            with open('data/videos.json', 'w') as outfile:
                json.dump(request, outfile)
            return ''
    except:
        maxResults = str(50)

        # TODO
        # make run in a separate file on a cronjob that also checks every n time interval
        # change to automatically getting requests and accessing the next page token until no page token exists:
        # OR, ideally just add newest video to the .json dictionary listing at index 0 of 'items' (ENSURE THAT EVERYTHING ELSE IS MOVED BACK IN INDEX)
        #   then would only need to get 1 result in request if different
        request1 = requests.get(url + maxResults + '&key=' + API_KEY).json()

        request2 = requests.get(
            url + maxResults + '&key=' + API_KEY + '&pageToken=' + request1.get('nextPageToken')).json()
        request = dict(request1)
        for i in request2.get('items', []):
            request['items'].append(i)

        with open('data/videos.json', 'w') as outfile:
            json.dump(request, outfile)
        return ''


@app.context_processor
def utility_processor():
    return dict(check_calendar=check_calendar)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
