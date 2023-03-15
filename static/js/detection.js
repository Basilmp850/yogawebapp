$('#file-upload-form').submit(function(e) {
    var form = $('#file-upload-form')[0]
    console.log("0")
    var fd = new FormData(form)
    for (var p of fd) {
        let name = p[0];
        let value = p[1];
    
        console.log(name, value)
    }
    console.log("1")
    
    $.ajax({
        url : "/detection/",
        type : 'POST',
        data: fd,
        dataType:'json',
        cache: false,
        processData: false,  // tell jQuery not to process the data
        contentType: false,   // tell jQuery not to set contentType
        success: function(resp){
            console.log("success: ",resp[0].full_filename);
            console.log("2")
            $('#uploadvideocontainer').empty()
            // const videocontainer = document.getElementById('videocontainer')
            // videocontainer.innerHTML=""
            // const video = document.createElement('video');
            // video.src = "../static/processed_videos/processed_video.mp4"

           setTimeout($("#uploadedvideocontainer").append('<video controls> <source src="../static/processed_videos/processed_video.mp4" type="video/mp4">  Your browser does not support the html video tag.  </video>'),10000)
            // video.controls = true;
            // video.muted = false;

            // videocontainer.appendChild(video)
            // window.location.href=="/detection/"
            console.log("3")
        },
        error: function(resp){
            console.log("4")
            console.log(resp);
            // $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
      })
      e.preventDefault();

});


