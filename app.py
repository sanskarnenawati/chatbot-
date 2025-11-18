import os
from flask import Flask, request, jsonify
from TM1py import TM1Service

app = Flask(__name__)

CONNECTION = {
    "base_url": "https://ap-southeast-2.planninganalytics.saas.ibm.com/api/3T7V4LYQCE61/v0/tm1/Headcount Planning/",
    "user": "apikey",
    "password": os.environ.get('TM1_API_KEY'),
    "ssl": True,
    "verify": False  # Render doesn't need Zscaler cert
}

cube_name = "PythonCube"

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    intent = req['queryResult']['intent']['displayName']
    params = req['queryResult']['parameters']

    version = params.get('version')
    month = params.get('month')
    measure = params.get('measure', 'Headcount')
    value = params.get('value')

    try:
        with TM1Service(**CONNECTION) as tm1:
            if intent in ["Create Data", "Update Data"]:
                tm1.cubes.cells.write(cube_name, {(version, month, measure): value})
                response_text = f"✅ Updated {month} in {version} to {value}"
            elif intent == "Read Data":
                cell_value = tm1.cubes.cells.get_value(cube_name, (version, month, measure))
                response_text = f"📊 {measure} for {month} in {version} is {cell_value}"
            elif intent == "Delete Data":
                tm1.cubes.cells.write(cube_name, {(version, month, measure): None})
                response_text = f"🗑 Deleted {measure} for {month} in {version}"
            else:
                response_text = "❌ Intent not recognized."
    except Exception as e:
        response_text = f"⚠️ Error: {str(e)}"

    return jsonify({"fulfillmentText": response_text})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)