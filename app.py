'''
API ENDPOINTS
'''
import os
import re
import ast
import cv2
import uuid 
import time
import signal
import string
import random
import requests
import itertools
import subprocess
import simplejson as json
from bson import json_util
from datetime import datetime
from operator import itemgetter
import dateutil.parser as parser
from bson.json_util import dumps
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_cors import CORS, cross_origin
from collections import defaultdict, Iterable
from flask import Flask, flash, request, redirect, render_template ,jsonify

app=Flask(__name__)

cors = CORS(app, resources={

    r"/*": {
        "origins": "*"

    }
})

app.secret_key = "secret key"

# Get current path
path = os.getcwd()
# file Upload
UPLOAD_FOLDER = os.path.join(path, '/var/www/html/quotas')
UPLOAD_FOLDER_IMAGE = '/var/www/html/cbi'

# Make directory if quotas is not exists
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_IMAGE'] = UPLOAD_FOLDER_IMAGE

# Allowed extension you can set your own
ALLOWED_EXTENSIONS = set(['jpg','png','jpeg', 'gif', 'webp', 'svg', 'ico', 'cur','tif','tiff','avif'])

import sys
import os.path
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir)))

app.config['MONGO_DBNAME'] = 'photo_bomb'
app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/photo_bomb?unicode_decode_error_handler=ignore'

mongo = PyMongo(app)

now = datetime.now()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_form():
    return render_template('upload.html')

#BROADCAST UPON STARTING SINGLE CAMERA
@app.route('/controls/start' , methods=['POST'])
def channels():
    #query db to check if camera 
    #RUNNING   or  NOT ..
    request_data = request.get_json()
    if request_data['status'] == True:
        cameras = mongo.db.live_cams
        camera = cameras.find_one({'_id' : ObjectId(str(request_data['camera_id']))})
        _status = ''
        status_report = {}
        if camera:
            if  camera['cam_status']=="ON":
                _status = camera['displayname'] + ' ' + 'CAMERA ALREADY RUNNING. STOP TO UPDATE ANY FURTHER CHANGES'
                status_report= {'status':True,'message':_status,'camera_id':request_data['camera_id']}

            if camera['cam_status']=="OFF":
                _status = camera['displayname'] + ' ' + 'CAMERA START PROCESS IN PROGRESS'
                url = "http://127.0.0.1:5008"
                payload ={'id':str(request_data['camera_id'])}
                headers = {'Content-type': 'application/json'}
                requests.post(url, data=json.dumps(payload), headers=headers,timeout=10)
                status_report= {'status':True,'message':_status,'camera_id':request_data['camera_id']}
        return status_report

    #STOP SINGLE CAMERA
    if request_data['status'] == False:
        status = []
        pid_list = []
        pid_t = mongo.db.live_cams
        res = pid_t.find_one({'_id' : ObjectId(str(request_data['camera_id']))})
        if res:
            pid_t1=res['live_cam_pid']
            pid_list.append(pid_t1)
            pid_t2=res['notification_pid']
            pid_list.append(pid_t2)
            pid_t3=res['media_player_pid']
            pid_list.append(pid_t3)
            pid_t4=res['facial_detection_pid']
            pid_list.append(pid_t4)
            pid_t5=res['facial_recognition_pid']
            pid_list.append(pid_t5)
            pid_t7=res['person_of_interest_pid']
            pid_list.append(pid_t7)
            pid_t8=res['alerts_cam_pid']
            pid_list.append(pid_t8)

            #SWITCH CAM STATUS IF SUCCESSFUL
            pid_t.update_one({"_id": ObjectId(str(request_data['camera_id']))},{"$set": {"cam_status": "OFF","camera_player":"/camera/is/oflline/stream.m3u8"}})

            for pid in pid_list:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    _err='PROCESS '+ pid +' STOPPED SUCESSFULLY FOR '+res['displayname']+' CAMERA'
                    status.append(_err)
                except:
                    err='PROCESS '+ pid +' NOT FOUND FOR '+res['displayname']+' CAMERA'
                    status.append(err)
                    print(err)

        return {'status':False,'message':status,'camera_id':request_data['camera_id']}

#START ALL CAMERAS
@app.route('/controls/cams' , methods=['POST'])
def cams():
    ids = []
    status = []
    status_report = {}
    request_data = request.get_json()
    if request_data['status'] == True:
        cameras = mongo.db.live_cams
        for camera in cameras.find():
            if camera.get('cam_status')=="ON":
                _status = camera.get('displayname') + ' ' + 'CAMERA ALREADY RUNNING. STOP TO UPDATE ANY FURTHER CHANGES'
                status_report= {'status':True,'message':_status}
                status.append(status_report)
        for _camera in cameras.find():
            if _camera.get('cam_status')=="OFF":
                _status = _camera.get('displayname') + ' ' + 'CAMERA START PROCESS IN PROGRESS'
                url = "http://127.0.0.1:5008"
                camera_id = json.loads(json_util.dumps(_camera['_id']))
                payload ={'id':camera_id['$oid']}
                headers = {'Content-type': 'application/json'}
                requests.post(url, data=json.dumps(payload), headers=headers,timeout=10)
                status_report= {'status':True,'message':_status,'camera_id':camera_id['$oid']}
                status.append(status_report)
                print(_camera['_id'])
                print(_status)
                print(payload)
            

        
    if request_data['status'] == False:
        ids = []
        status = []
        pid_list = []
        pid_t = mongo.db.live_cams
        for id in pid_t.find():
            ids.append(str(id['_id']))
        for _id in ids:
            res = pid_t.find_one({'_id' : ObjectId(_id)})
            if res:
                if  res['cam_status']=="ON":
                    pid_t1=res['live_cam_pid']
                    pid_list.append(pid_t1)
                    pid_t2=res['notification_pid']
                    pid_list.append(pid_t2)
                    pid_t3=res['media_player_pid']
                    pid_list.append(pid_t3)
                    pid_t4=res['facial_detection_pid']
                    pid_list.append(pid_t4)
                    pid_t5=res['facial_recognition_pid']
                    pid_list.append(pid_t5)
                    pid_t7=res['person_of_interest_pid']
                    pid_list.append(pid_t7)
                    pid_t8=res['alerts_cam_pid']
                    pid_list.append(pid_t8)

                    #SWITCH CAM STATUS IF SUCCESSFUL
                    pid_t.update_one({"_id": '_id'},{"$set": {"cam_status": "OFF","camera_player":"/camera/is/oflline/stream.m3u8"}})

                    for pid in pid_list:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            _err='PROCESS '+ pid +' STOPPED SUCESSFULLY FOR '+res['displayname']+' CAMERA'
                            status.append(_err)
                        except:
                            err='PROCESS '+ pid +' NOT FOUND FOR '+res['displayname']+' CAMERA'
                            status.append(err)
                            print(err)
                if  res['cam_status']=="OFF":
                    status_report= {'status':True,'message':'CAMERA ALREADY STOOPED','camera_id':_id}
                    status.append(status_report)
    print(status)
    return jsonify({'status': status})

#REGISTER NEW LOCATION AND  CAMERA
@app.route('/api/location/', methods=['POST'])
def register_locations():
    result = []
    request_data = request.get_json()  # getting data from client
    locationname =request_data["locationname"]
    #locationname = request_data['locationname']
    _type= request_data['type']
    address = request_data['address']
    active = request_data['active']
    no_of_cams = request_data['no_of_cams']
    cameraList = request_data['camDetails']
    cam_location = mongo.db.live_cams_locations
    #validate camera locat
    _locationname = cam_location.find_one({'locationname' : locationname})
    # if location exist save camera
    if _locationname:
        location_id =str(_locationname['_id'])
        for index in range(len(cameraList)):
            for camera in cameraList: 
                # single_camera_dict = json.loads(single_camera_string)
                single_camera_dict = {}
                single_camera_dict['id']=location_id
                single_camera_dict['active']=str(camera['active'])
                single_camera_dict['camera_gps']=str(camera['camera_gps'])
                single_camera_dict['camera_ip']=str(camera['camera_ip'])
                single_camera_dict['camera_type']=str(camera['camera_type'])
                single_camera_dict['cameraname']=str(camera['cameraname'])
                single_camera_dict['displayname']=str(camera['displayname'])
                single_camera_dict['createdAt']=str(now.strftime("%m/%d/%Y"))
                single_camera_dict['camera_player']='/camera/is/oflline/stream.m3u8'

                #gather additional camera metrics
                cap = cv2.VideoCapture(camera['camera_ip'])
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH )
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

                single_camera_dict['frame_rate']="15"
                single_camera_dict['poi_threshold']=str(30)
                single_camera_dict['frame_width']=str(width)
                single_camera_dict['max_frame_rate']=str(25)
                single_camera_dict['frame_height']=str(height)

                #camera status
                single_camera_dict['cam_status']="OFF"
                single_camera_dict['live_cam_pid']=""
                single_camera_dict['alerts_cam_pid']=""
                single_camera_dict['notification_pid']=""
                single_camera_dict['media_player_pid']=""
                single_camera_dict['facial_detection_pid']=""
                single_camera_dict['person_of_interest_pid']=""
                single_camera_dict['facial_recognition_pid']=""

                #check if camera exists in
                _cameraList =  mongo.db.live_cams.find_one({'camera_ip' : str(camera['camera_ip'])})
                if _cameraList:
                    print(" camera with  id " + str(_cameraList['_id']) + " exists")
                else:
                    single_camera_dict.update({'channel_name':str(_locationname['channel_name'])})            
                    #insert camera
                    camera = mongo.db.live_cams.insert(single_camera_dict)
                    if camera :
                        result.append(" camera id " + location_id)
                    else :
                        result.append(" camera not created")       
                cap.release()
            return jsonify(dumps({}))
    else:
          #generate channel key 
        letters = string.ascii_lowercase
        #registe queue channel
        channel_name =''.join(random.choice(letters) for i in range(11))
        #register location and camera first time
        camera_location=mongo.db.live_cams_locations.insert({'id' :str(uuid.uuid4()) ,'locationname':locationname,'type' : _type,'address' : address,'active' : active,'no_of_cams': no_of_cams,'channel_name':channel_name})
        print('camera_location ===')

        _locationname = cam_location.find_one({'locationname' : locationname})
    
        # if location exist save camera
        if _locationname:
            print(str(_locationname['_id']))
            location_id =str(_locationname['_id'])
            for camera in cameraList:  
                # single_camera_dict = json.loads(single_camera_string)
                single_camera_dict = {}
                single_camera_dict['id']=location_id
                single_camera_dict['active']=str(camera['active'])
                single_camera_dict['camera_gps']=str(camera['camera_gps'])
                single_camera_dict['camera_ip']=str(camera['camera_ip'])
                single_camera_dict['camera_type']=str(camera['camera_type'])
                single_camera_dict['cameraname']=str(camera['cameraname'])
                single_camera_dict['displayname']=str(camera['displayname'])
                single_camera_dict['createdAt']=str(now.strftime("%m/%d/%Y"))
                single_camera_dict['camera_player']='/camera/is/oflline/stream.m3u8'

                #gather additional camera metrics
                cap = cv2.VideoCapture(camera['camera_ip'])
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH )
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

                single_camera_dict['frame_rate']="15"
                single_camera_dict['poi_threshold']=str(30)
                single_camera_dict['frame_width']=str(width)
                single_camera_dict['max_frame_rate']=str(25)
                single_camera_dict['frame_height']=str(height)
                #camera status
                single_camera_dict['cam_status']="OFF"
                single_camera_dict['live_cam_pid']=""
                single_camera_dict['alerts_cam_pid']=""
                single_camera_dict['notification_pid']=""
                single_camera_dict['media_player_pid']=""
                single_camera_dict['facial_detection_pid']=""
                single_camera_dict['person_of_interest_pid']=""
                single_camera_dict['facial_recognition_pid']=""

                single_camera_dict.update({'channel_name':str(_locationname['channel_name'])})
                #insert camera
                camera = mongo.db.live_cams.insert(single_camera_dict)
                if camera :
                    result.append(" camera id " + location_id)
                else :
                    result.append(" camera not created") 
                cap.release()      
                return jsonify(dumps(camera))

#REGISTER LOCATION
@app.route('/api/locations/', methods=['POST','PUT'])
def register_camera_and_locations():
    result = []
    locationname = request.form['locationname']
    _type= request.form['type']
    address = request.form['address']
    active = request.form['active']
    no_of_cams = request.form['no_of_cams']
    cameraList = request.form['camDetails']
    cam_location = mongo.db.live_cams_locations
    #validate camera locat
    _locationname = cam_location.find_one({'locationname' : locationname})
    if _locationname:
        #select camera from list
        camera_list = ''.join(camera for camera in cameraList)
        if len(camera_list) > 2 :
            single_camera=json.dumps(camera_list[1:-1])
            single_camera_string = single_camera.replace("\"","").replace("'", "\"")
            number_of_string_dictionaries=single_camera_string.count('}')
            if number_of_string_dictionaries == 1:
                single_camera_dict = json.loads(single_camera_string)
                single_camera_dict['id']=location_id
                single_camera_dict.update({'channel_name':str(_locationname['channel_name'])})
                #insert camera
                camera = mongo.db.live_cams.insert(single_camera_dict)
                if camera :
                    result.append(" camera id " + location_id)
                else :
                    result.append(" camera not created")

            if number_of_string_dictionaries > 1:
                cameras=re.findall(r'\{.*?\}', single_camera_string)
                for _camera in cameras:
                    single_camera_dict = json.loads(_camera)
                    single_camera_dict['id']=location_id
                    single_camera_dict.update({'channel_name':str(_locationname['channel_name'])})
                    #insert camera
                    camera = mongo.db.live_cams.insert(single_camera_dict)
                    if camera :
                        result.append(" camera id " + location_id)
                    else :
                        result.append(" camera not created")
        else:
            result.append("add 1 or more camera")
    else:
        #generate channel key 
        letters = string.ascii_lowercase
        #registe queue channel
        channel_name =''.join(random.choice(letters) for i in range(11))
        #register location and camera first time
        camera_location=mongo.db.live_cams_locations.insert({'id' :str(uuid.uuid4()) ,'locationname':locationname,'type' : _type,'address' : address,'active' : active,'no_of_cams': no_of_cams,'channel_name':channel_name})
        if camera_location:
            #select camera from list
            camera_list = ''.join(camera for camera in cameraList)
            if len(camera_list) > 2:
                single_camera=json.dumps(camera_list[1:-1])
                single_camera_string = single_camera.replace("\"","").replace("'", "\"")
                number_of_string_dictionaries=single_camera_string.count('}')
                if number_of_string_dictionaries == 1:
                    single_camera_dict = json.loads(single_camera_string)
                    single_camera_dict['id']=str(camera_location)
                    single_camera_dict.update({'channel_name':channel_name})
                    print(single_camera_dict)
                    #insert camera
                    camera = mongo.db.live_cams.insert(single_camera_dict)
                    if camera :
                        channel_name = ''
                        result.append(" camera id " + str(camera_location))
                    else :
                        result.append(" camera not created")

                if number_of_string_dictionaries > 1:
                    cameras=re.findall(r'\{.*?\}', single_camera_string)
                    for _camera in cameras:
                        single_camera_dict = json.loads(_camera)
                        single_camera_dict['id']=str(camera_location)
                        single_camera_dict.update({'channel_name':channel_name})
                        #insert camera
                        camera = mongo.db.live_cams.insert(single_camera_dict)
                        if camera :
                            channel_name = ''
                            result.append(" camera id " + str(camera_location))
                        else :
                            result.append(" camera not created")
            else:
                result.append("add 1 or more camera") 
    return jsonify({'result' : result})

#UPDATE SINGLE CAMERA
@app.route('/api/locations/camera/update', methods=['POST'])
def update_one_camera():
    output = ''
    status_report= ''
    camera = mongo.db.live_cams
    request_data = request.get_json()
    _camera = camera.update_one({"_id": ObjectId(str(request_data['id']))},{"$set": {"camera_ip": request_data['camera_ip'],"camera_type": request_data['camera_type'],"cameraname": request_data['cameraname'],"displayname": request_data['displayname'],"frame_rate": request_data['frame_rate'],"poi_threshold": request_data['poi_threshold']}})
    if _camera:
        output = request_data['cameraname'] + " UPDATED SUCESSFULLY"
        status_report= {'message':output,'camera_id':request_data['id']}
    else:
        output = request_data['cameraname'] + " NOT UPDATED"
        status_report= {'message':output,'camera_id':request_data['id']}
    return status_report

#DELETE SINGLE CAMERA
@app.route('/api/locations/camera/delete/<id>', methods=['POST'])
def delete_one_camera(id):
    camera = mongo.db.live_cams
    _camera = camera.delete_one({'_id' : ObjectId(str(id))})
    if _camera:
        output = "TARGET CAMERA REMOVED"
    else:
        output = "TARGET CAMERA NOT REMOVED"
    return jsonify({'result' : output})

#DELETE SINGLE LOCATION
@app.route('/api/locations/delete/<id>', methods=['POST'])
def delete_one_location(id):
    location = mongo.db.live_cams_locations
    _location = location.delete_one({'_id' : ObjectId(str(id))})
    if _location:
        output = "TARGET LOCATIONS REMOVED"
    else:
        output = "TARGET LOCATION NOT REMOVED"
    return jsonify({'result' : output})

#GET ALL LOCATIONS WITH ALL CAMERAS
@app.route('/api/locations/all/', methods=['GET'])
def get_all_camera_locations():
  locations = mongo.db.live_cams_locations
  output = []
  _output = []
  _camera_location = {}
  _camDetails = []
  cameras = mongo.db.live_cams
  for location in locations.find():
      if location:
          _camera_location = {'id': str(location['_id']),'locationname' : location['locationname'], 'type' : location['type'], 'address' : location['address'], 'no_of_cams' : location['no_of_cams'],'channel_name' : location['channel_name']}
          for camera in cameras.find({'id' :str(location['_id'])}):
              if camera:
                  _camDetails.append({'frame_rate' : camera['frame_rate'],'min_frame_rate' : str(5),'max_frame_rate' : camera['max_frame_rate'],'poi_threshold' : camera['poi_threshold'],'max_poi_threshold' : str(92),'id': str(camera['_id']),'cam_status' : camera['cam_status'],'location_id': str(camera['id']),'cameraname' : camera['cameraname'], 'camera_ip' : camera['camera_ip'], 'camera_gps' : camera['camera_gps'], 'camera_type' : camera['camera_type'], 'active' : camera['active'], 'createdAt' : camera['createdAt'],'channel_name' : camera['channel_name'], 'displayname' : camera['displayname'],'camera_player' : camera['camera_player']})
              else:
                   _camDetails = []
          _output = [i for n, i in enumerate(_camDetails) if i not in _camDetails[n + 1:]]
          res = [i for i in _output if not (i['channel_name'] != location['channel_name'])]
          _camera_location.update({'camDetails':res})
      output.append(_camera_location)
  return jsonify({'result' : output})

#SELECT SINGLE CAMERA
@app.route('/api/locations/<id>', methods=['GET'])
def get_one_camera_location(id):
    location = mongo.db.live_cams_locations
    _location = location.find_one({'_id' : ObjectId(str(id))})
    output = []
    _camera_location = {}
    _camDetails = []
    cameras = mongo.db.live_cams
    if _location:
         _camera_location ={'id': str(_location['_id']),'locationname' : _location['locationname'], 'type' : _location['type'], 'address' : _location['address'], 'no_of_cams' : _location['no_of_cams'],'channel_name' : _location['channel_name']}
         for camera in cameras.find({'id' :str(id)}):
            if camera:
                _camDetails.append({'id': str(camera['_id']),'location_id': str(camera['id']),'cameraname' : camera['cameraname'], 'camera_ip' : camera['camera_ip'], 'camera_gps' : camera['camera_gps'], 'camera_type' : camera['camera_type'], 'active' : camera['active'], 'createdAt' : camera['createdAt'],'channel_name' : camera['channel_name'] , 'displayname' : camera['displayname'],'camera_player' : camera['camera_player']})
            else:
                _camDetails = []
         _camera_location.update({'camDetails':_camDetails})
         output.append(_camera_location)
    else:
        output = "No such location"
    return jsonify({'result' : output})

#GET ALL CAMERAS
@app.route('/api/locations/camera/all', methods=['GET'])
def get_all_cameras():
  cameras = mongo.db.live_cams
  output = []
  for camera in cameras.find():
    output.append({'frame_rate' : camera['frame_rate'],'min_frame_rate' : str(5),'max_frame_rate' : camera['max_frame_rate'],'poi_threshold' : camera['poi_threshold'],'max_poi_threshold' : str(92),'id': str(camera['_id']),'location_id': str(camera['id']),'cam_status' : camera['cam_status'],'cameraname' : camera['cameraname'], 'camera_ip' : camera['camera_ip'], 'camera_gps' : camera['camera_gps'], 'camera_type' : camera['camera_type'], 'active' : camera['active'], 'createdAt' : camera['createdAt'],'channel_name' : camera['channel_name'] , 'displayname' : camera['displayname'],'camera_player' : camera['camera_player']})
  return jsonify({'result' : output})

@app.route('/api/camera/<id>', methods=['GET'])
def get_one_camera(id):
    cameras = mongo.db.live_cams
    camera = cameras.find_one({'_id' : ObjectId(str(id))})
    output = []
    if camera:
         output.append({'id': str(camera['_id']),'location_id': str(camera['id']),'cameraname' : camera['cameraname'], 'camera_ip' : camera['camera_ip'], 'camera_gps' : camera['camera_gps'], 'camera_type' : camera['camera_type'], 'active' : camera['active'], 'createdAt' : camera['createdAt'],'channel_name' : camera['channel_name'],'camera_player' : camera['camera_player']})
    else:
        output = "No such camera"
    return jsonify({'result' : output})

#RECORDINGS
@app.route('/api/locations/recordings/all/<id>', methods=['GET'])
def get_top5_camera_recording(id):
    output,topk = [] , []
    default_dict = defaultdict(list)
    recordings = mongo.db.recordings
    for recording in recordings.find({'camera_id' :str(id)}):
        if recording:
            output.append({'camera_id': str(recording['camera_id']),'recording_id': str(recording['recording_id']),'recording_time' : recording['recording_time'], 'time_day' : recording['time_day'], 'time_month' : recording['time_month'], 'time_date' : recording['time_date'], 'time_year' : recording['time_year'], 'time_score' : recording['time_score'], 'recording_url' : recording['recording_url']})
        else:
            output = "No such camera"
    results= sorted(output, key=itemgetter('time_score'),reverse=True) 
    if len(results) >= 5 :
        topk = list(itertools.islice(results, 5))
    else:
        topk =results
    return jsonify({'result' : topk})

@app.route('/api/locations/recordings/playlist', methods=['GET'])
def get_all_camera_recording():
    output = []
    jdump,query = {},{}
    sort = ['time_score', -1]
    DateFormat="%Y-%m-%dT%H:%M:%S.%fZ"
    end_date=str(request.args.get('end_date', None))
    start_date=str(request.args.get('start_date', None))
    if start_date =='undefined' and end_date =='undefined':
        query = {'camera_id' :str(request.args.get('id', None))}
    if end_date !='undefined' and start_date =='undefined':
        query = {'camera_id' :str(request.args.get('id', None)),'utc_time': {'$lt': datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ"), '$gte': datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ")}}
        
    if start_date !='undefined' and end_date =='undefined':
        query = {'camera_id' :str(request.args.get('id', None)),'utc_time': {'$lt': datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ"), '$gte': datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ")}}
    
    if start_date !='undefined' and end_date !='undefined':
        query = {'camera_id' :str(request.args.get('id', None)),'utc_time': {'$gte':  datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ") , '$lt':  datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ")}}

    count = mongo.db.recordings.count_documents(query)
    page_num = int(request.args.get('offset', None))
    page_size = int(request.args.get('limit', None))
    skips = page_size * (page_num - 1)

    results= dumps(mongo.db.recordings.find(query).skip(skips).limit(page_size).sort([sort]))
    for res in ast.literal_eval(results):
        res.pop("_id", None)
        output.append(res)
    jdump['count']=count
    jdump['result']=output
    jdump['page_size']=len(output)
    jdump['index']=request.args.get('offset', None)
    return jsonify(jdump)

#SCREENS
res = ""
@app.route('/api/screens/start' , methods=['POST'])
def cctv():
    if request.method == 'POST':
        
        dict=request.json
        n =int(dict.get('screens'))
        status = ""
        status_list = []
        camera_details = {}
        camera_details_list = []
        cameras = mongo.db.live_cams
        if dict.get('status') == True:
            for  camera in cameras.find():
                camera_details_list.append( str(camera['_id']))
            if n > len(camera_details_list):
                status = "Only "+str(len(camera_details_list))+ " screens available"
                res={"status":status}
            else:
                batches = [camera_details_list[i * n:(i + 1) * n] for i in range((len(camera_details_list) + n - 1) // n )]
                #START SUBSCRIBER
                for batch in batches:
                    for idx,_batch in enumerate(batch):
                        #VIDEO DISPLAY
                        if len(batch)==1 and idx==0:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),0,0,0,0)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==2 and idx==0:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),106,315,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==2 and idx==1:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),960,315,854,450)
                            #sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),Xpos,Ypos,Width,Height)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==3 and idx==0:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),106,90,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==3 and idx==1:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),960,90,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==3 and idx==2:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),533,540,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==4 and idx==0:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),106,90,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==4 and idx==1:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),960,90,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==4 and idx==2:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),106,540,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==4 and idx==3:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),960,540,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==5 and idx==0:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),0,75,640,480)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==5 and idx==1:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),640,75,640,480)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==5 and idx==2:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),1280,75,640,480)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==5 and idx==3:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),106,555,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==5 and idx==4:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),960,555,854,450)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==6 and idx==0:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),0,75,640,480)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==6 and idx==1:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),640,75,640,480)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==6 and idx==2:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),1280,75,640,480)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==6 and idx==3:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),0,555,640,480)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==6 and idx==4:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),640,555,640,480)
                            subprocess.run(["./POD",sub_metrics])

                        if len(batch)==6 and idx==5:
                            sub_metrics = ""
                            sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),1280,555,640,480)
                            #sub_metrics ="{},{},{},{},{},{},{},{},".format(batch[0],_batch,idx,len(batch),Xpos,Ypos,Width,Height)
                            subprocess.run(["./POD",sub_metrics])
                    res={"status":batch}
                    
                #START PUBLISHER
                for batch in batches:
                    pub_metrics =""
                    pub_metrics ="{},".format(batch[0])
                    subprocess.run(["./ENGINE",pub_metrics])
                    res={"status":"media started sucessfully"}
                    
        if dict.get('status') == False:
            res={"status":"media stopped sucessfully"}
    return res

@app.route('/api/screens/all', methods=['GET'])
def get_all_screens():
  screens = mongo.db.screens
  output = []
  jdump,query = {},{}
  count = mongo.db.screens.count_documents(query)
  print(count)
  print(mongo.db.screens.find(query))
  page_num = int(request.args.get('offset', None))
  page_size = int(request.args.get('limit', None))
  skips = page_size * (page_num - 1)
  results= dumps(mongo.db.screens.find(query).skip(skips).limit(page_size))
  print(results)
  for res in ast.literal_eval(results):
      res.pop("_id", None)
      output.append(res)
  jdump['count']=count
  jdump['result']=output
  jdump['page_size']=len(output)
  jdump['index']=request.args.get('offset', None)
  return jsonify(jdump)

#POIs
@app.route('/api/poi/all', methods=['GET'])
def get_all_persons_of_interest():
  persons = mongo.db.person_of_interest
  output = []
  for person in persons.find({}, projection={'facial_unstructured': False,'facial_luminannce': False}):
    output.append({'url':['http://192.168.8.205'],'photo' : 'http://192.168.8.205' + person['photo'], 'name' : person['name'], 'residence' : person['residence'], 'age' : person['age'], 'gender' : person['gender'], 'social_media_profile' : person['social_media_profile'], 'place_of_birth' : person['place_of_birth'], 'id' : str(person['_id']), 'nationality' : person['nationality'], 'education' : person['education'], 'arrest_details' : person['arrest_details']})
  #return jsonify({'result' : output})
  return json.dumps({'result' : output})

dd = defaultdict(list)
@app.route('/api/poi/<id>', methods=['GET'])
def get_one_person_of_interest(id):
    person = mongo.db.person_of_interest
    _person = person.find_one({'id' : id})
    if _person:
        output={'id' : _person['id'],'url':['http://192.168.8.205'],'photo' : 'http://192.168.8.205' + _person['photo'], 'name' : _person['name'], 'residence' : _person['residence'], 'age' : _person['age'], 'gender' : _person['gender'], 'social_media_profile' : _person['social_media_profile'], 'place_of_birth' : _person['place_of_birth'], 'id' : _person['id'], 'nationality' : _person['nationality'], 'education' : _person['education'], 'arrest_details' : _person['arrest_details']}
    else:
        output = "NO SUCH PERSON"
    return jsonify({'result' : output})

@app.route('/api/target/delete/<id>', methods=['POST'])
def delete_one_person_of_interest(id):
    person = mongo.db.person_of_interest
    _person = person.delete_one({'_id' : ObjectId(str(id))})
    if _person:
        output = "TARGET USER REMOVED"
    else:
        output = "TARGET USER NOT REMOVED"
    return jsonify({'result' : output})

@app.route('/profiles/display', methods=['POST'])
def webhook():
    gId = request.form['sId']
    dType = request.form['dType']
    social_media_profile =request.form['social_media_profile']
    name =request.form['name']
    residence =request.form['residence']
    #age = request.form['age']
    age ='18'
    gender =request.form['gender']
    education =request.form['education']
    arrest_details =request.form['arrest_details']
    nationality =request.form['nationality']
    place_of_birth =request.form['place_of_birth']
    image= request.files['photo']
    QueryPost_list = []
    files = request.files.to_dict() 
    for file in files:
        if file and allowed_file(files[file].filename):
            _filename=re.sub(r"\.", "", str(time.time()))+'.png'
            files[file].save(os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], _filename))
            _id =  mongo.db.person_of_interest.insert({'id':str(gId),'residence':str(residence),'age':str(age),'gender':str(gender),'social_media_profile':str(social_media_profile),'place_of_birth':str(place_of_birth),'nationality':str(nationality),'education':str(education),'arrest_details':str(arrest_details),'name':str(name),'snapshot':'/var/www/html/cbi/'+str(_filename),'photo':'/cbi/'+str(_filename)})
            if _id:
                id = str(_id)
                photo_path = mongo.db.person_of_interest.find_one({'_id' : ObjectId(str(_id))})
                QueryCpp = {str(id+':'+ photo_path['snapshot'])}
                QueryPost_list.append(QueryCpp)
    print(QueryPost_list)
    print(gId)
    proc = subprocess.Popen(["/home/smokeiedcamlive/IED/POLICE/POI/build/POI",str(QueryPost_list)])
    #return jsonify({'result' :QueryPost_list})
    return '200'

@app.route('/images/profiles/all', methods=['GET'])
def get_all_profiles():
  profiles = mongo.db.profiles
  output = []
  jdump,query = {},{}
  count = mongo.db.profiles.count_documents(query)
  print(mongo.db.profiles.find(query))
  page_num = int(request.args.get('offset', None))
  page_size = int(request.args.get('limit', None))
  skips = page_size * (page_num - 1)
  results= dumps(mongo.db.profiles.find(query).skip(skips).limit(page_size))
  for res in ast.literal_eval(results):
      #res.pop("_id", None)
      output.append(res)
  jdump['count']=count
  jdump['result']=output
  jdump['page_size']=len(output)
  jdump['index']=request.args.get('offset', None)
  return jsonify(jdump)

@app.route('/images/profiles/<id>', methods=['GET'])
def get_one_photo(id):
    cameras = mongo.db.profiles
    camera = cameras.find_one({'_id' : ObjectId(str(id))})
    results= dumps(camera)
    print(results)
    output = []
    if camera:
        camera.pop("_id", None)
        output.append(camera)
    else:
        output = "No such photo"
    return jsonify({'result' : output})

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5007,use_reloader=False)
