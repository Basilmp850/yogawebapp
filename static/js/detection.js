$('#file-upload-form').submit(function(e) {
    // tag='<div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div>'
    // $("#uploadvideocontainer").append(tag)
    // var videocontainer = document.getElementById('uploadvideocontainer')

    // boostrap_div = document.createElement("div");
    // bootstrap_div.classList.add('spinner-border')
    // bootstrap_span = document.createElement("span")
    // bootstrap_span.classList.add("sr-only")
    // var txt = document.createTextNode("Loading...");
    // bootstrap_span.appendChild(txt);
    // bootstrap_div.append(bootstrap_span)
    // bootstrap_div.role="status"
    // videocontainer.append(boostrap_div)

    var form = $('#file-upload-form')[0]
    console.log("0")
    var fd = new FormData(form)
    for (var p of fd) {
        let name = p[0];
        let value = p[1];
    
        console.log(name, value)
    }
    console.log("1")

    // $('.spinner-border').tagsinput('refresh');
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
            user_header = resp[0].user_header
            console.log('[user_header]',user_header)
            console.log('[response]',resp)
           setTimeout(function() {
            $("#uploadedvideocontainer").append('<img src="../'+resp[0].full_filename + '" class = "imgcontainer" >')
            $("#pose_prediction").append('<h1>'+resp[0].pose_prediction+'</h1>')

            // document.getElementById("videotag").getElementsByTagName("source")[0].src = "../"+user_header+'/processed_videos/processed_video.mp4'
        }  
            ,5000)
           
            
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


