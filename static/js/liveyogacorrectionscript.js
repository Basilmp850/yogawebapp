// $('select').on('change', function() {
//     alert( this.value );
//   });

var fetchNow = function() {
    fetch(' http://127.0.0.1:5000/getvariables').then(response=>{
        dataval = response.json()
        return dataval
        console.log("Response :", dataval)
        console.log(dataval.previous_command)
    }).then(function (data) {
        console.log('GET response:');
        console.log(data.previous_command); 

        if(data.previous_command.slice(-9)=="correct!!")
         completed=true
        else {
          setTimeout(fetchNow(),1000);
       }
    });
}

var fetchVariables = function(){
    $.ajax({
        url:"/getvariables",
        type:"GET",
        dataType: "json",
        success: function(resp){
            console.log(resp.previous_command); 
            setTimeout(function(){
                fetchVariables()
            },1000);
        },
        error: function(resp){
            console.log(resp.error);
            setTimeout(function(){
                fetchVariables()
            },1000);
        }
    });
}

fetchVariables()

