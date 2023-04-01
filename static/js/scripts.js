$('#signupform').submit(function(e) {
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();
    console.log(data)
    $error.text("Signing up!!")
    $.ajax({
        url:"/user/signup",
        type:"POST",
        data: data,
        dataType: "json",
        success: function(resp){
            console.log("0")
            console.log("success: ",resp);
            console.log("1")
            console.log("2")
            $('#modalform').find('input:submit').before('<input name="user-id" type="hidden" value="'+resp._id+'">')
            const modal = document.getElementById("signupModal");

            setTimeout(function() {
                modal.classList.add("show");
                backdrop.style.display = "block";
                }, 1000);

                // window.location.href='/'+resp._id
            // window.location.href='/user/verify/'+resp._id
        },
        error: function(resp){
            console.log(resp);
            $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
    });
    e.preventDefault();


});

$('#modalform').submit(function(e) {
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();
    console.log(data)
    $error.text("Verifying OTP!!")
    $.ajax({
        url:"/user/validate",
        type:"POST",
        data: data,
        dataType: "json",
        success: function(resp){
            console.log("success: ",resp);
            window.location.href='/home'

                // window.location.href='/'+resp._id
            // window.location.href='/user/verify/'+resp._id
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
    $error.text("Logging In...")
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
            // console.log(resp);
            $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
    });
    e.preventDefault();


});


const modal = document.getElementById("signupModal");
const backdrop = document.getElementById("signupbackdrop");
// clickBtn.addEventListener("click", function() {
// setTimeout(function() {
// modal.classList.add("show");
// backdrop.style.display = "block";
// }, 1000);
// });

backdrop.addEventListener("click", function() {
modal.classList.remove("show");
backdrop.style.display = "none";
});