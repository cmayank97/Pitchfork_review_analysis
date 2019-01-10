$(document).ready(function() {
    $(".button").click(function(event) {
        $.ajax({
            type: "POST",
            url: "get_review",
            contentType: "application/json",
            dataType: "json",
            data: JSON.stringify({
                id: event.target.id
            }),
            success: function(response) {
                var modal = document.getElementById('myModal');
                var span = document.getElementsByClassName("close")[0];
                document.getElementById('reviewContent').innerHTML = response.data;
                modal.style.display = "block";
                span.onclick = function() {
                    modal.style.display = "none";
                }
                window.onclick = function(event) {
                    if (event.target == modal) {
                        modal.style.display = "none";
                    }
                }
            }
        });
    });
});