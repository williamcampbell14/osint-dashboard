from flask import Flask, Response, render_template, request as flask_request, session, jsonify
import json
import time
from web_tools import *
from logging.config import dictConfig
import concurrent.futures


dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console"]},
    }
)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

load_dotenv()
secret_key = os.getenv('SECRET_KEY')
app.secret_key = secret_key


def generate(interval, functions):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks to the ThreadPoolExecutor
        future_to_key = {executor.submit(func, *args): key for func, args, key in functions}
        
        for future in concurrent.futures.as_completed(future_to_key):
            key = future_to_key[future]
            try:
                result = future.result()
            except Exception as e:
                result = str(e)  # Handle exceptions if any
            data = {key: result}
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(interval)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/events')
def events():
    user_url = session.get('user_url')
    if user_url and not user_url.startswith('https://'):
        user_url = 'https://' + user_url
    domain, ip_str, title, favicon = website_information(user_url)

    functions_to_call = [
        (get_redirects, (user_url,), "Redirects"),
        (get_cookies, (user_url,), "Cookies"),
        (get_headers, (user_url,), "Headers"),
        (get_ip_info, (ip_str,), "IP Info"),
        (get_records, (domain,), "Domain"),
        (get_ssl, (domain,), "SSL"),
        (site_maps, (user_url,), "Site Maps"),
        (check_ports, (domain,), "Open Ports"),
        (whois_info, (domain,), "Whois Info"),
        # (get_screenshot, (user_url,), "Screenshot"),
        (get_internal_external_links, (user_url,), 'Internal Links'),
        (get_emails, (user_url,), "Linked Emails"),
        (get_phone_numbers, (user_url,), "Linked Phone Numbers")
    ]
    
    return Response(generate(1, functions_to_call), mimetype='text/event-stream')

@app.route('/web_tool', methods=["Get","POST"])

@app.route('/web_tool', methods=["GET", "POST"])
def web_tool():
    if flask_request.method == "POST":
        user_url = flask_request.form.get('web_input1')
        session['user_url'] = user_url  # Store user_url in session
        if user_url and not user_url.startswith('https://'):
            user_url = 'https://' + user_url
        
        domain, ip_str, title, favicon = website_information(user_url)

        result = {
            "domain": domain,
            "ip_str": ip_str,
            "title": title,
            "favicon": favicon
        }

        # Return data as JSON for API requests
        return jsonify(result)

    # Handle GET requests by rendering the template
    user_url = flask_request.args.get('web_input1', '')
    if user_url:
        session['user_url'] = user_url  # Store user_url in session
        if user_url and not user_url.startswith('https://'):
            user_url = 'https://' + user_url
        domain, ip_str, title, favicon = website_information(user_url)
        return render_template('web_tools.html', domain=domain, ip_str=ip_str, title=title, favicon=favicon)

    return render_template('web_tools.html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)