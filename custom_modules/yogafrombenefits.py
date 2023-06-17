from flask import request, jsonify, Blueprint, session, send_file, render_template
from scipy.stats import mode
import pickle
import numpy as np
import pdfkit
import os
# from app import app


yoga_from_benefits = Blueprint('yoga_from_benefits', __name__)

benefits=pickle.load(open('./pickled_files/benefits.pkl', 'rb'))  
encoder = pickle.load(open('./pickled_files/yogafrombenefits_encoder.pkl', 'rb'))
final_svm_model=pickle.load(open('./pickled_files/yogafrombenefits_final_svm_model.pkl', 'rb'))
final_nb_model=pickle.load(open('./pickled_files/yogafrombenefits_final_nb_model.pkl', 'rb'))   
final_rf_model=pickle.load(open('./pickled_files/yogafrombenefits_final_rf_model.pkl', 'rb'))   

benefit_index = {}
for index, value in enumerate(benefits):
	benefit = " ".join([i.capitalize() for i in value.split("_")])
	benefit_index[benefit] = index

data_dict = {
	"benefit_index":benefit_index,
	"predictions_classes":encoder.classes_
}

def predictYoga(benefits):
	benefits = benefits.split(",")
	
	# creating input data for the models
	input_data = [0] * len(data_dict["benefit_index"])
	for benefit in benefits:
		index = data_dict["benefit_index"][benefit]
		input_data[index] = 1
		
	# reshaping the input data and converting it
	# into suitable format for model predictions
	input_data = np.array(input_data).reshape(1,-1)
	
	# generating individual outputs
	rf_prediction = data_dict["predictions_classes"][final_rf_model.predict(input_data)[0]]
	nb_prediction = data_dict["predictions_classes"][final_nb_model.predict(input_data)[0]]
	svm_prediction = data_dict["predictions_classes"][final_svm_model.predict(input_data)[0]]
	
	# making final prediction by taking mode of all predictions
	final_prediction = mode([rf_prediction, nb_prediction, svm_prediction])[0][0]
	predictions = {
		"rf_model_prediction": rf_prediction,
		"naive_bayes_prediction": nb_prediction,
		"svm_model_prediction": nb_prediction,
		"final_prediction":final_prediction
	}
	return predictions

# print(predictYoga("Spine Flexibility,Calmness,Digestion")["final_prediction"]);

@yoga_from_benefits.route('/benefitspost',methods=['POST'])
def benefitspost():
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
     prediction = predictYoga(prediction_attributes)["final_prediction"]
     symptoms = {    
          "symptom1": request.form.get("1"),
          "symptom2": request.form.get("2"),
          "symptom3": request.form.get("3"),
          "symptom4": request.form.get("4"),
          "symptom5": request.form.get("5"),
          "yoga_recommendation" : prediction
     }
     session['symptoms'] = symptoms
     return jsonify(symptoms)
    

   

@yoga_from_benefits.route('/pdf1')
def yoga_rec_pdffunction():
 # Set up options
 options = {
 'page-size': 'A4',
 'margin-top': '0mm',
 'margin-right': '0mm',
 'margin-bottom': '0mm',
 'margin-left': '0mm',
 }
 config = pdfkit.configuration(wkhtmltopdf='wkhtmltopdf.exe')
 # Directory path

 directory = os.path.join('templates','Basic_layouts')
 # HTML file name
 html_file = 'pdfhtmlfile_yogarec.html'

 #rendering the template based on the symptoms and predicted output
 symptoms = session['symptoms']
 count = 0
 for i in range(1,6,1):
     if len(symptoms['symptom'+str(i)]):
         count = count + 1

 print(count)
 base_path = os.path.join(session['user_header'],'rendered_files')
 # Path to output PDF file

 output_pdf = os.path.join(base_path,'output.pdf')
#  rendered_html_path = os.path.join(session['user_header'],'rendered_html')
 rendered_html_path = os.path.join(base_path,'rendered_pdfhtml.html')
#  rendered_html_path = os.path.join(directory,'rendered_pdfhtml.html')
 # Get the full file path
 html_path = os.path.join(directory, html_file)
 rendered_html_file = render_template('Basic_layouts/pdfhtmlfile_yogarec.html', symptoms=symptoms, count = count+1)
 with open(rendered_html_path, 'w') as f:
        f.write(rendered_html_file)
 # Generate PDF from HTML file
 pdfkit.from_file(rendered_html_path, output_pdf, options=options, configuration = config)
 if os.path.exists(output_pdf):
 # Send the PDF file as a response
#     response = make_response(send_file(output_pdf))
#     response.headers['Content-Disposition'] = f'attachment; filename={output_pdf}'

#     return response

    return send_file(output_pdf, as_attachment=False)
#   return send_file(output_pdf, attachment_filename=output_pdf, as_attachment=True)
 return 'pdf not rendered'


