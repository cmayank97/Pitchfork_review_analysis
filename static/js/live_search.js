function liveSearch(value){
    $("#results").show();
    value = value.trim();
    if(value != ""){
        $.ajax({
            url: "search",
            data: {searchText: value},
            dataType: "json",
            success: function(data){
                var res = "";
                for(i in data.results){
                    res += "<option onclick ='myfunction(this.text)'>"+data.results[i]+"</option>";
                }
                $("#results").html(res);
            }
        });
    }
    else{
        $("#results").html("");
    }
}