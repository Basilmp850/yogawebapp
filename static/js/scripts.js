$('#signupform').submit(function(e) {
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();
    console.log(data)
    $.ajax({
        url:"/user/signup",
        type:"POST",
        data: data,
        dataType: "json",
        success: function(resp){
            console.log("0")
            console.log("success: ",resp.email);
            console.log("1")
            console.log("2")
            window.location.href='/user/verify/'+resp._id
        },
        error: function(resp){
            console.log(resp);
            $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
    });
    e.preventDefault();


});

$('#loginform').submit(function(e) {
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();
    console.log(data)
    var $alertmsg = $('#expirationWarning')
    $error.text("Processing")
    $.ajax({
        url:"/user/login",
        type:"POST",
        data: data,
        dataType: "json",
        success: function(resp){
            console.log("success: ",resp);
            window.location.href='/home'
        },
        error: function(resp){
            console.log(resp);
            $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
    });
    e.preventDefault();


});