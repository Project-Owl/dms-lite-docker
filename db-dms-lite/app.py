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
def getPayload(topic,data):
    payload = []
    label = []
    try:
        conn = mariadb.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        host= os.getenv('MYSQL_HOST'),
        database=os.getenv('MYSQL_DATABASE'),
        port=3306
        )
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT payload, timestamp 
            FROM clusterData
            WHERE topic = ? 
            ORDER BY timestamp DESC
            LIMIT ?
            ''', (topic,data))
        rows = cursor.fetchall()
        # grabs the row obj and jsonify datetime
        for info in rows:
            payload.append(int(info[0]))
            label.append(info[1])
        conn.commit()
        conn.close()
        print('got info')
        labeldate = []
        payload,label = payload[::-1],label[::-1]
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
            topiclst.append(info[0])
        conn.commit()
        conn.close()
        return topiclst
    except Exception as e:
        print(e)

# #For updates and warnings: 
# @app.route('/checkOutlier/<string:topic>/<int:maxval>/<int:minval>', methods=['GET'])

# If the sensor data changes by defined amount -> send an alert.
# pseudo: set the settings to monitor topic specific,
def outlierWarning(topic, maxval, minval):
    payloadout, labelout, duckout, = [], [], []
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
        '''SELECT payload, timestamp, duck_id
            FROM clusterData 
            WHERE topic = ? AND ((payload > ?) OR (payload < ?)) 
            LIMIT 1
            ''',(topic,maxval,minval))
        rows = cursor.fetchall()
        for info in rows:
            payloadout.append((info[0]))
            labelout.append(info[1])
            duckout.append(info[2])

        conn.commit()
        conn.close()
        print('got info')
        labeldate = []
        for date in labelout:
            rjson = json.dumps(date, default=str)
            labeldate.append(rjson)
        #add it to a dictionary and return
        result = {"payload" : payloadout, "label" :labeldate, "duckid":duckout}
        return result
    except Exception as e:
        print(e)
    
# I would like the API to return:  Last Time/Date of data and Data that was summited.
def duckInfo(duckid):
    payload, time, topic = [], [], []
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
        '''SELECT topic, payload, timestamp
            FROM clusterData 
            WHERE duck_id = ?
            LIMIT 1
            ''', (duckid,))
        rows = cursor.fetchall()

        for info in rows: 
            topic.append(info[0])
            payload.append(info[1])
            time.append(info[2])
        conn.commit()
        conn.close()
        timedate = []
        for t in time: 
            timedate.append(json.dumps(t, default=str))
        return {"topic":topic, "payload":payload, "timestamp":timedate}
    except Exception as e:
        print(e)

def getDucks():        
    ducklst=[]
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
        '''SELECT DISTINCT duck_id FROM clusterData''', )
        rows = cursor.fetchall()
        for info in rows:
            ducklst.append(info[0])
        conn.commit()
        conn.close()
        return ducklst
    except Exception as e:
        print(e)
        
        
class show_Payload(Resource):
    def get(self, topic, data):
        return getPayload(topic, data), 200
class get_Topics(Resource):
    def get(self):
        return getTopics(), 200
class checkAlert(Resource):
    def get(self, topic, maxval, minval):
        return outlierWarning(topic, maxval, minval), 200
class showData(Resource):
    def get(self, duckid): 
        return duckInfo(duckid), 200
class get_Ducks(Resource): 
    def get(self): 
        return getDucks(), 200

api.add_resource(show_Payload, "/showPayload/<string:topic>/<int:data>")
api.add_resource(get_Topics, "/getTopics")
api.add_resource(checkAlert, "/checkAlert/<string:topic>/<int:maxval>/<int:minval>")
api.add_resource(showData,"/showData/<string:duckid>")
api.add_resource(get_Ducks,"/getDucks")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
