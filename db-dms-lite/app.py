import mariadb
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
import os
import json

app = Flask(__name__)
# app.config["DEBUG"] = True
CORS(app, origins=["http://localhost:3000"])
api = Api(app)

class ApiBeta(Resource):
     def get(self):
         return hello()
api.add_resource(ApiBeta, '/')

def hello():
    return ''' API SERVER RUNNING (BETA)  '''

# @app.route('/showPayload/<string:topic>', methods=['GET'])
def getPayload(topic):
    payload = []
    label = []
    try:
        conn = mariadb.connect(
        user= os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        host= os.getenv('MYSQL_HOST'),
        database=os.getenv('MYSQL_DATABASE'),
        port=3306
        )
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT payload, timestamp FROM clusterData
            WHERE topic = ?''', (topic,))
        rows = cursor.fetchall()
        # grabs the row obj and jsonify datetime
        for info in rows:
            payload.append(int(info[0]))
            label.append(info[1])
        conn.commit()
        conn.close()
        print('got info')
        labeldate = []
        for date in label:
            rjson = json.dumps(date, default=str)
            labeldate.append(rjson)
        #add it to a dictionary and return
        result = {"payload" : payload, "label" :labeldate}
        return result
    except Exception as e:
        print(e)

# #called when the page loads
# @app.route('/getTopics', methods=['GET'])
def getTopics():
    topiclst=[]
    try:
        conn = mariadb.connect(
        user= os.getenv('MYSQL_USER'),
        password= os.getenv('MYSQL_PASSWORD'),
        host=os.getenv('MYSQL_HOST'),
        database=os.getenv('MYSQL_DATABASE'),
        port=3306
        )
        cursor = conn.cursor()
        cursor.execute(
        '''SELECT DISTINCT topic FROM clusterData''', )
        rows = cursor.fetchall()
        for info in rows:
            topiclst.append(info[0]) #this is a list['','','']
        conn.commit()
        conn.close()
        topicdic = {"topics" : topiclst}
        return topicdic
    except Exception as e:
        print(e)

# #For updates and warnings: 
# @app.route('/checkOutlier/<string:topic>/<int:maxval>/<int:minval>', methods=['GET'])
def outlierWarning(topic, maxval, minval):
    payloadout = []
    labelout = []
    try:
        conn = mariadb.connect(
        user= os.getenv('MYSQL_USER'),
        password= os.getenv('MYSQL_PASSWORD'),
        host=os.getenv('MYSQL_HOST'),
        database=os.getenv('MYSQL_DATABASE'),
        port=3306
        )
        cursor = conn.cursor()
        cursor.execute(
        '''SELECT payload, timestamp FROM clusterData WHERE topic = ? AND ((payload > ?) OR (payload < ?)) 
            ORDER BY payload ASC''',(topic,maxval,minval))
        rows = cursor.fetchall()
        for info in rows:
            payloadout.append((info[0]))
            labelout.append(info[1])
        conn.commit()
        conn.close()
        print('got info')
        labeldate = []
        for date in labelout:
            rjson = json.dumps(date, default=str)
            labeldate.append(rjson)
        #add it to a dictionary and return
        result = {"payload" : payloadout, "label" :labeldate}
        return result
    except Exception as e:
        print(e)


class show_Payload(Resource):
    def get(self, topic):
        return getPayload(topic), 200
class get_Topics(Resource):
    def get(self):
        return getTopics(), 200
class checkOutlier(Resource):
    def get(self, topic, maxval, minval):
        return outlierWarning(topic, maxval, minval), 200

api.add_resource(show_Payload, "/showPayload/<string:topic>")
api.add_resource(get_Topics, "/getTopics")
api.add_resource(checkOutlier, "/checkOutlier/<string:topic>/<int:maxval>/<int:minval>")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

# app.run()