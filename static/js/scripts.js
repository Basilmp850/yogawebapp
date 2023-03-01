$("form[name=signup_form").submit(function(e) {
    
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.seralize();

    $.ajax({
        url:"/user/signup",
        type:"POST",
        data: data,
        dataType: "json",
        success: function(resp){
            console.log("success: ",resp);
        },
        error: function(resp){
            console.log(resp);
        }
    });
    e.preventDefault();

})