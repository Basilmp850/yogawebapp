$('#clickBtn').click(function(e){
    var $form = $('#benefits-form')

    var data = $form.serialize();
    console.log(data)
    $.ajax({
        url:"/benefitspost",
        type:"POST",
        data: data,
        dataType: "json",
        success: function(response){
            const modal = document.getElementById("myModal");
            const backdrop = document.getElementById("myBackdrop");
            console.log(response.yoga_recommendation);
            $("#yogarecommendation_modal").find(".recyoga").html(response.yoga_recommendation)
            setTimeout(function() {
                modal.classList.add("show");
                backdrop.style.display = "block";
            }, 1000);
        },
        error: function(response){
            console.log(response);
        }
    })
    e.preventDefault()
})