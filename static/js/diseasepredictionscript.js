// const API_URL = 'https://jsonplaceholder.typicode.com/users';
// async function fetchUsers() {
//   const response = await fetch(API_URL)
//   const users = await response.json();
//   return users;
// }
// fetchUsers().then(users => {
//   console.log(users); // fetched users
// });

// document.getElementById("browser")
var predictionstring;
function myfunction(){

    inputfield = document.querySelectorAll("input");
    input1 = inputfield[0].value;
    input2 = inputfield[1].value;
    input3 = inputfield[2].value;
    input4 = inputfield[3].value;
    input5 = inputfield[4].value;
 
    fetch('http://127.0.0.1:5000/chronicpost', { 
    method: 'POST',
    headers: {
     'Content-type': 'application/json',
     'Access-Control-Allow-Origin': '*'
   },
    body: JSON.stringify({
     symptom1 : input1,
     symptom2 : input2,
     symptom3 : input3,
     symptom4 : input4,
     symptom5 : input5
   })
 })
   .then((response) => { return response.json()})
   .then((data) => {
                 prediction = data.prediction;
                 predictionstring = prediction;
                 yogarecommendationarray = data.yoga_recommendation;
                 document.getElementById("disease_prediction").innerHTML="";
                 var tag = document.createElement("h1");
                 var text = document.createTextNode("Prediction : "+prediction);
                 tag.appendChild(text);
                 var element = document.getElementById("disease_prediction");
                 element.appendChild(tag);
                 console.log(data[0].prediction)})
                 const buttonName = document.querySelector(".showrecommendation")
                 buttonName.id="showrec"
                 element.appendChild(buttonName)
   .catch((error) => console.log('ERROR'))
 }
 

 function yogaRecommendation(){
  stringname = ""
  let list = document.getElementById("yoga_recommendation_list");
  // list.innerHTML="Yoga Recommendation: -\n";
  for (i = 0; i < yogarecommendationarray.length; ++i) {
    var li = document.createElement('li');
    li.innerText = yogarecommendationarray[i];
    // list.appendChild(li);
    stringname = stringname + yogarecommendationarray[i] + "\n";
    
 }
alert(stringname)
 }


 const submitbutton = document.querySelector("button");
 submitbutton.addEventListener("click",myfunction);
 const recommendationbutton=document.querySelector(".showrecommendation")
 recommendationbutton.addEventListener("click",yogaRecommendation)
  