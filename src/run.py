from flask import Flask, render_template
from flask_apscheduler import APScheduler

# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True

# create app
app = Flask(__name__)
app.config.from_object(Config())

# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
# scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()

@app.route('/')
def home():
    return render_template('index2.html')


if __name__ == '__main__':
    app.run()