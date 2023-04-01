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
// function myfunction(){

//     inputfield = document.querySelectorAll("input");
//     input1 = inputfield[0].value;
//     input2 = inputfield[1].value;
//     input3 = inputfield[2].value;
 
//     fetch('http://127.0.0.1:5000/chronicpost', { 
//     method: 'POST',
//     headers: {
//      'Content-type': 'application/json',
//      'Access-Control-Allow-Origin': '*'
//    },
//     body: JSON.stringify({
//      symptom1 : input1,
//      symptom2 : input2,
//      symptom3 : input3
//    })
//  })
//    .then((response) => { return response.json()})
//    .then((data) => {
//                  prediction = data.prediction;
//                  predictionstring = prediction;
//                  yogarecommendationarray = data.yoga_recommendation;
//                  document.getElementById("disease_prediction").innerHTML="";
//                  var tag = document.createElement("h1");
//                  var text = document.createTextNode("Prediction : "+prediction);
//                  tag.appendChild(text);
//                  var element = document.getElementById("disease_prediction");
//                  element.appendChild(tag);
//                  console.log(data[0].prediction)})
//                  const buttonName = document.querySelector(".showrecommendation")
//                  buttonName.id="showrec"
//                  element.appendChild(buttonName)
//    .catch((error) => console.log('ERROR'))
//  }
 

 function yogaRecommendation(){

  let list = document.getElementById("yoga_recommendation_list");
  list.innerHTML="Yoga Recommendation: -\n";
  for (i = 0; i < yogarecommendationarray.length; ++i) {
    var li = document.createElement('li');
    li.innerText = yogarecommendationarray[i];
    list.appendChild(li);
 }
 }


//  const submitbutton = document.querySelector("button");
//  submitbutton.addEventListener("click",myfunction);
 const recommendationbutton=document.querySelector(".showrecommendation")
 recommendationbutton.addEventListener("click",yogaRecommendation)
  

 $('.subofchr').click(function(e){
  var $form = $('#symptoms-form')
  console.log("1")
  var data = $form.serialize();
  console.log("2")
  console.log(data)
  $.ajax({
      url:"/chronicpost",
      type:"POST",
      data: data,
      dataType: "json",
      success: function(response){
         prediction = response.prediction;
         predictionstring = prediction;

        const modal = document.getElementById("myModal");
        const backdrop = document.getElementById("myBackdrop");
        console.log(response.prediction);
        yogarecommendationarray = response.yoga_recommendation;
        $("#yogarecommendation_modal").find(".recyoga").html(response.prediction)
        $('#yogarecommendation_modal ul').empty()
        for(i=0; i<yogarecommendationarray.length; i++)
        {
         element = "<li>"+yogarecommendationarray[i]+"</li>"
         $("#yogarecommendation_modal ul").append(element)
        }
        setTimeout(function() {
            modal.classList.add("show");
            backdrop.style.display = "block";
        }, 1000); 




        // prediction = response.prediction;
        // predictionstring = prediction;
        // yogarecommendationarray = response.yoga_recommendation;
        // document.getElementById("disease_prediction").innerHTML="";
        // var tag = document.createElement("h1");
        // var text = document.createTextNode("Prediction : "+prediction);
        // tag.appendChild(text);
        // var element = document.getElementById("disease_prediction");
        // element.appendChild(tag);
        // console.log(response[0].prediction)    
          // prediction=response.prediction
          // // const modal = document.getElementById("myModal");
          // // const backdrop = document.getElementById("myBackdrop");
          // yogarecommendationarray = response.yoga_recommendation;

          // console.log(response.prediction);
          // $("#disease_prediction").html('<h2>'+response.prediction+'</h2>')
          // setTimeout(function() {
          //     modal.classList.add("show");
          //     backdrop.style.display = "block";
          // }, 1000);
      },
      error: function(response){
          console.log(response);
      }
  })
  e.preventDefault()
})