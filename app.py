import os

from flask import Flask, Response, request, render_template
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/signup')
def signup():
   return render_template('signup.html')

@app.route('/<file_name>.txt')
def method_name(file_name):
    return app.send_static_file(file_name + '.txt')

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
