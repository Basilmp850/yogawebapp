from flask import request, jsonify
from app import app

symptoms = {
        "symptom1" : "",
        "symptom2" : "",
        "symptom3" : "",
        "prediction": ""
    }


import pickle 
from scipy.stats import mode
import numpy as np
from sklearn.preprocessing import LabelEncoder
import pandas as pd
	

data = pickle.load(open('./pickled_files/diseasepredictiondataset.pkl', 'rb'))  
test_data = pickle.load(open('./pickled_files/diseasepredictiontestdataset.pkl', 'rb'))
final_svm_model = pickle.load(open('./pickled_files/svm_model.pkl', 'rb'))
final_rf_model =  pickle.load(open('./pickled_files/rf_model.pkl', 'rb'))
final_nb_model = pickle.load(open('./pickled_files/nb_model.pkl', 'rb'))
encoder = pickle.load(open('./pickled_files/encoder.pkl', 'rb')) 
yogarecommendation = pickle.load(open('./pickled_files/yogarecommendationdictionary.pkl','rb'))


#testing
# encoder = LabelEncoder()
# data["prognosis"] = encoder.fit_transform(data["prognosis"])
# encoder = LabelEncoder()
encoder.fit_transform(test_data["prognosis"])
X = data.iloc[:,:-1]
symptoms = X.columns.values
# print(symptoms)
# Creating a symptom index dictionary to encode the
# input symptoms into numerical form
symptom_index = {}
for index, value in enumerate(symptoms):
	symptom = " ".join([i.capitalize() for i in value.split("_")])
	symptom_index[symptom] = index

data_dict = {
	"symptom_index":symptom_index,
	"predictions_classes":encoder.classes_
}
# print(final_rf_model.predit())
# print(add())

def predictDisease(symptoms):
	symptoms = symptoms.split(",")
	
	# creating input data for the models
	print(len(data_dict["symptom_index"]))
	input_data = [0] * len(data_dict["symptom_index"])
	for symptom in symptoms:
		index = data_dict["symptom_index"][symptom]
		input_data[index] = 1
		
	# reshaping the input data and converting it
	# into suitable format for model predictions
	input_data = np.array(input_data).reshape(1,-1)
	
	# generating individual outputs
	print(final_rf_model.predict(input_data))
	rf_prediction = data_dict["predictions_classes"][final_rf_model.predict(input_data)[0]]
	nb_prediction = data_dict["predictions_classes"][final_nb_model.predict(input_data)[0]]
	svm_prediction = data_dict["predictions_classes"][final_svm_model.predict(input_data)[0]]
    
	# making final prediction by taking mode of all predictions
	final_prediction = mode([rf_prediction, nb_prediction, svm_prediction])[0][0]
    #In the future, the below line may replace the above line.
	# final_prediction = pd.DataFrame([(rf_prediction), (nb_prediction), (svm_prediction)],columns=('prediction')).mode()[0][0]
	predictions = {
		"rf_model_prediction": rf_prediction,
		"naive_bayes_prediction": nb_prediction,
		"svm_model_prediction": svm_prediction,
		"final_prediction":final_prediction
	}
	return predictions

@app.route('/chronicpost',methods=['POST'])
def chronicpost():
    print("1")
    prediction_attributes=""
    if request.method=="POST":
     print("2")
     first = 1
     requestdata = {
          "symptom1": request.form.get("1"),
          "symptom2": request.form.get("2"),
          "symptom3": request.form.get("3"),
          "symptom4": request.form.get("4"),
          "symptom5": request.form.get("5")
     }
     print("3")
    #  term1 = (requestdata['symptom1']) if len(requestdata['symptom1'])!=0 else ''
    #  prediction_attributes+=term1
     for i in range(1,6,1):
      term = requestdata['symptom'+str(i)]
      if not len(term)==0 and first:
        term = (requestdata['symptom'+str(i)])
        first=0
      elif len(term)==0:
           continue
      else:
           term=','+term
      prediction_attributes+=term          
    #   if term1=='' and i==2:
    #        term = (requestdata['symptom'+str(i)]) if len(requestdata['symptom'+str(i)])!=0 else ''
    #   else: 
    #    term = (','+requestdata['symptom'+str(i)]) if len(requestdata['symptom'+str(i)])!=0 else ''
     print(prediction_attributes)
     prediction = predictDisease(prediction_attributes)["final_prediction"]
     if prediction=="Dimorphic hemmorhoids(piles)":
          prediction="Dimorphic hemorrhoids (piles)"
     symptoms = {    
          "symptom1": request.form.get("1"),
          "symptom2": request.form.get("2"),
          "symptom3": request.form.get("3"),
          "symptom4": request.form.get("4"),
          "symptom5": request.form.get("5"),
          "prediction" : prediction if not prediction=="Peptic ulcer diseae" else "Peptic ulcer disease",
          "yoga_recommendation":  yogarecommendation[prediction] if not prediction=='Peptic ulcer diseae' else yogarecommendation["Peptic ulcer disease"]
     }

     return jsonify(symptoms)
    # prediction_attributes=""
    # if request.method=="POST":
    #  requestdata = request.get_json();
    #  term1 = (requestdata['symptom1']) if len(requestdata['symptom1'])!=0 else ''
    #  prediction_attributes+=term1
    #  for i in range(2,4,1):
    #   if term1=='' and i==2:
    #        term = (requestdata['symptom'+str(i)]) if len(requestdata['symptom'+str(i)])!=0 else ''
    #   else: 
    #    term = (','+requestdata['symptom'+str(i)]) if len(requestdata['symptom'+str(i)])!=0 else ''
    #   prediction_attributes+=term

    #  prediction = predictDisease(prediction_attributes)["final_prediction"]
    #  symptoms = {    
    #     "symptom1" : requestdata['symptom1'],
    #     "symptom2" : requestdata['symptom2'],
    #     "symptom3" : requestdata['symptom3'],
    #     "prediction" : prediction,
    #     "yoga_recommendation" : yogarecommendation[prediction]
    #  }

    #  return jsonify(symptoms)
    

