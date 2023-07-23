from flask import Flask, render_template
from flask_apscheduler import APScheduler
from refresh_html import refresh_web

# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True
    TEMPLATES_AUTO_RELOAD = True

# create app
app = Flask(__name__)
app.config.from_object(Config())

# initialize scheduler
scheduler = APScheduler()

# interval example
@scheduler.task('interval', id='do_refresh_template', seconds=300, misfire_grace_time=900)
def refresh_template():
    refresh_web()
    print('HTML with new weather information refreshed. This job executes every 5 minutes')

scheduler.start()

@app.route('/')
def render_the_map():
    return render_template('weather_test_now.html')

if __name__ == '__main__':
    app.run()