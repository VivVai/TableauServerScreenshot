from flask import Flask, render_template, request, send_file
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import os
import io

app = Flask(__name__)

ns = {'t': 'http://tableau.com/api'}

def fetch_tableau_image(server, site, token_name, token_secret, workbook_name, dashboard_name, filter_field, filter_value):
    token = None
    site_id = None
    headers = {}

    # Step 1: Authenticate
    try:
        auth_url = f"{server}/api/3.18/auth/signin"
        auth_payload = {
            "credentials": {
                "personalAccessTokenName": token_name,
                "personalAccessTokenSecret": token_secret,
                "site": {"contentUrl": site}
            }
        }
        response = requests.post(auth_url, json=auth_payload)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        credentials_elem = root.find('t:credentials', ns)
        token = credentials_elem.get('token')
        site_elem = credentials_elem.find('t:site', ns)
        site_id = site_elem.get('id')
        headers = {"X-Tableau-Auth": token}
    except:
        return None, "Authentication failed"

    # Step 2: Get Workbook ID
    try:
        response = requests.get(f"{server}/api/3.18/sites/{site_id}/workbooks", headers=headers)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        workbook_id = None
        for wb in root.findall('.//t:workbook', ns):
            if wb.get('name') == workbook_name:
                workbook_id = wb.get('id')
                break
        if not workbook_id:
            return None, "Workbook not found"
    except:
        return None, "Error getting workbook"

    # Step 3: Get View ID
    try:
        response = requests.get(f"{server}/api/3.18/sites/{site_id}/workbooks/{workbook_id}/views", headers=headers)
        root = ET.fromstring(response.text)
        view_id = None
        for v in root.findall('.//t:view', ns):
            if v.get('name') == dashboard_name:
                view_id = v.get('id')
                break
        if not view_id:
            return None, "Dashboard view not found"
    except:
        return None, "Error getting view"

    # Step 4: Get Image
    try:
        encoded_field = quote(filter_field)
        encoded_value = quote(filter_value)
        image_url = f"{server}/api/3.18/sites/{site_id}/views/{view_id}/image?vf_{encoded_field}={encoded_value}"
        img_response = requests.get(image_url, headers=headers, stream=True)
        img_response.raise_for_status()
        return img_response.content, None
    except:
        return None, "Error fetching image"

@app.route('/', methods=['GET', 'POST'])
def index():
    image_data = None
    error = None

    defaults = {
        'server': 'https://us-east-1.online.tableau.com',
        'site': 'casepracticeproduct',
        'token_name': 'Vivek',
        'token_secret': 'ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss',
        'workbook_name': 'Chart Types - Radial Chart ',
        'dashboard_name': 'Radial Charts for skill assessment',
        'filter_field': 'Name',
        'filter_value': 'Lionel Messi'
    }

    if request.method == 'POST':
        form = request.form
        image_data, error = fetch_tableau_image(
            server=form['server'],
            site=form['site'],
            token_name=form['token_name'],
            token_secret=form['token_secret'],
            workbook_name=form['workbook_name'],
            dashboard_name=form['dashboard_name'],
            filter_field=form['filter_field'],
            filter_value=form['filter_value']
        )
        if image_data:
            return send_file(
                io.BytesIO(image_data),
                mimetype='image/png',
                as_attachment=True,
                download_name='dashboard_image.png'
            )

    # Always pass defaults to the template
    return render_template('index.html', error=error, defaults=defaults)

if __name__ == '__main__':
    app.run(debug=True)
