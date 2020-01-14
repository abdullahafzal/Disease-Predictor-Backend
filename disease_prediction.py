#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import flask
from flask import request, jsonify
import time
import sqlite3
import random 
# import the necessary packages
from keras.preprocessing.image import img_to_array
from keras.models import load_model
from keras import backend
from imutils import build_montages
import cv2
import numpy as np
from flask_cors import CORS
import io


app = flask.Flask(__name__)
CORS(app)

conn = sqlite3.connect('database.db')
print("Opened database successfully")
conn.execute('CREATE TABLE IF NOT EXISTS Patients (id INTEGER PRIMARY KEY,firstName TEXT, lastName TEXT, ins_ID TEXT, city TEXT, dob TEXT)') 
conn.execute('CREATE TABLE IF NOT EXISTS Spiral (id INTEGER PRIMARY KEY,positive INTEGER, negative INTEGER)') 
conn.execute('CREATE TABLE IF NOT EXISTS Wave (id INTEGER PRIMARY KEY,positive INTEGER, negative INTEGER)')
conn.execute('CREATE TABLE IF NOT EXISTS Malaria (id INTEGER PRIMARY KEY,positive INTEGER, negative INTEGER)') 
conn.execute('CREATE TABLE IF NOT EXISTS Breast (id INTEGER PRIMARY KEY,positive INTEGER, negative INTEGER)') 


@app.route('/prediction', methods=['POST'])
def api_image():
    # Database
    print('API CALL')
    firstName = request.args['fname']
    lastName = request.args['lname']
    ins_ID = request.args['ins_ID']
    city = request.args['city']
    dob = request.args['dob']


        
    model_name = request.args["model"]
    photo = request.files['photo']
    in_memory_file = io.BytesIO()
    photo.save(in_memory_file)
    data = np.fromstring(in_memory_file.getvalue(), dtype=np.uint8)
    color_image_flag = 1
    orig = cv2.imdecode(data, color_image_flag)
    model_path = ""

    # load the pre-trained network
    print("[INFO] loading pre-trained network...")

    if model_name in "malaria":
        print("Maalaria model loaded")
        model_path = "malaria_model.model" # Please enter the path for Malaria model

    elif model_name in "spiral":
        print("Spiral model loaded")
        model_path = "spiral_model.model" # Please enter the path for Spiral model

    elif model_name in "wave":
        print("Wave model loaded")
        model_path = r"wave_model.model" # Please enter the path for wave model
        
    elif model_name in "breast":
        print("Wave model loaded")
        model_path = r"breast_cancer_model.model" # Please enter the path for wave model

    model = load_model(model_path)
    # initialize our list of results
    results = []

    # pre-process our image by converting it from BGR to RGB channel
    # ordering (since our Keras mdoel was trained on RGB ordering),
    # resize it to 64x64 pixels, and then scale the pixel intensities
    # to the range [0, 1]
    image = cv2.cvtColor(orig, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (48, 48))
    image = image.astype("float") / 255.0

    # order channel dimensions (channels-first or channels-last)
    # depending on our Keras backend, then add a batch dimension to
    # the image
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)

    # make predictions on the input image
    pred = model.predict(image)

    print("pred: ", pred)
    pred = pred.argmax(axis=1)[0]

    # an index of zero is the 'parasitized' label while an index of
    # one is the 'uninfected' label
    label = "UnInfected" if pred == 0 else "Infected"
    color = (0, 0, 255) if pred == 0 else (0, 255, 0)

    # resize our original input (so we can better visualize it) and
    # then draw the label on the image
    orig = cv2.resize(orig, (128, 128))
    cv2.putText(orig, label, (3, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                color, 2)

    # add the output image to our list of results
    results.append(orig)



    # Use the jsonify function from Flask to convert our list of
    # Python dictionaries to the JSON format.
    res = {}
    
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        cur.execute('INSERT INTO Patients VALUES(?,?,?,?,?,?)',(None,firstName, lastName, ins_ID, city, dob))
        res=cur.execute('SELECT * FROM Patients')

        if model_name in "malaria":
            if pred == 1:
                cur.execute('INSERT INTO Malaria VALUES(?,?,?)',(None,1,0))

            else:
                cur.execute('INSERT INTO Malaria VALUES(?,?,?)',(None,0,1))
            con.commit()

            positive = cur.execute('SELECT SUM(positive) FROM Malaria')
            positive = positive.fetchall()

            negative = cur.execute('SELECT SUM(negative) FROM Malaria')
            negative = negative.fetchall()

        elif model_name in "spiral":
            if pred == 1:
                cur.execute('INSERT INTO Spiral VALUES(?,?,?)',(None,1,0))
            else:
                cur.execute('INSERT INTO Spiral VALUES(?,?,?)',(None,0,1))
            con.commit()

            positive = cur.execute('SELECT SUM(positive) FROM Spiral')
            positive = positive.fetchall()
            negative = cur.execute('SELECT SUM(negative) FROM Spiral')
            negative = negative.fetchall()


        elif model_name in "wave":
            if pred == 1:
                cur.execute('INSERT INTO Wave VALUES(?,?,?)',(None,1,0))
            else:
                cur.execute('INSERT INTO Wave VALUES(?,?,?)',(None,0,1))
            con.commit()
            positive = cur.execute('SELECT SUM(positive) FROM Wave')
            positive = positive.fetchall()
            negative = cur.execute('SELECT SUM(negative) FROM Wave') 
            negative = negative.fetchall()
        
        elif model_name in "breast":
            if pred == 1:
                cur.execute('INSERT INTO Breast VALUES(?,?,?)',(None,1,0))
            else:
                cur.execute('INSERT INTO Breast VALUES(?,?,?)',(None,0,1))
            con.commit()
            positive = cur.execute('SELECT SUM(positive) FROM Breast')
            positive = positive.fetchall()
            negative = cur.execute('SELECT SUM(negative) FROM Breast') 
            negative = negative.fetchall()        
        
    if pred == 1:
        res = {"Prediction":"1", "positive":positive, "negative":negative}
        print(res)
    else:
        res = {"Prediction":"0", "positive":positive, "negative":negative}
        print(res)

    backend.clear_session()

    return jsonify(res)


@app.route('/data', methods=['GET'])
def data_db():
    # Database
    print('API GET')

    with sqlite3.connect("database.db") as con:
        cur = con.cursor()

        patients = cur.execute('SELECT COUNT(id) FROM Patients').fetchall()
        positive = cur.execute('SELECT SUM(positive) FROM Malaria').fetchall()
        negative =cur.execute('SELECT SUM(negative) FROM Malaria').fetchall()
        con.commit()

        positive += cur.execute('SELECT SUM(positive) FROM Spiral').fetchall()
        negative += cur.execute('SELECT SUM(negative) FROM Spiral').fetchall()
        con.commit()

        positive += cur.execute('SELECT SUM(positive) FROM Wave').fetchall()
        negative += cur.execute('SELECT SUM(negative) FROM Wave').fetchall()
        con.commit()
        
        positive += cur.execute('SELECT SUM(positive) FROM Breast').fetchall()
        negative += cur.execute('SELECT SUM(negative) FROM Breast').fetchall()
        con.commit()
        
        
        pos_list = list()
        for i in positive:
            pos_list.append(int(i[0]))
        neg_list = list()
        for i in negative:
            neg_list.append(int(i[0]))            
        res = {"patients": patients[0][0], "positive": sum(pos_list), "negative": sum(neg_list)}
        print(res)

    backend.clear_session()
    return jsonify(res)

@app.route('/patients', methods=['GET'])
def patients_db():
    print('API patient')

    with sqlite3.connect("database.db") as con:
        cur = con.cursor()

        results = cur.execute('SELECT * FROM Patients').fetchall()
        con.commit()
        patients_data = list()
        keys = ['id', 'firstName', 'lastName', 'ins_id', 'city', 'dob']
        for result in results:
            patients_data.append(dict(zip(keys, result)))

    backend.clear_session()
    return jsonify(patients_data)


app.run()



