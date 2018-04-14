$(function() {
    
    $('#source').on('change',function(){
         
        var source = $(this).find(':selected').val();
        $.getJSON('/_sort_products',{
            'source':source
        }, function(data){
            var table = "";
            for (i=0;i<data.length;i++){
                table += "<tr>"+
                    "<td title='"+data[i]["brand"]+"'>"+data[i]["brand"]+"</td>" +
                    "<td title='"+data[i]["name"]+"'>"+data[i]["name"]+"</td>" +
                    "<td title='"+data[i]["nick_name"]+"'>"+data[i]["nick_name"]+"</td>" +
                    "<td title='"+data[i]["color"]+"'>"+data[i]["color"]+"</td>" +
                    "<td title='"+data[i]["upc"]+"'>"+data[i]["upc"]+"</td>" +
                    "<td title='"+data[i]["source"]+"'>"+data[i]["source"]+"</td>" +
                    "<td><a href='/product/product_details/'"+data[i]["_id"]+">Edit</a></td>" +
                    "<td><a href='/product/product_delete/'"+data[i]["_id"]+">Delete</a></td>" +
                "</tr>";
            }

            $('#products_body').html(table);
        });
        return false;
    });
    
    $('input[type=file]').on('change',function(){
        $("#file_count").html("");
        readURL(this);
            
    });
        
    
    
});

function readURL(input) {
    if(input.files){

        for(i=0;i<input.files.length;i++){
            var reader = new FileReader();
            
            reader.onload = function(e) {
              $($.parseHTML('<img>')).attr('src',e.target.result).appendTo($("#file_count"));
            }
            
            reader.readAsDataURL(input.files[i]);
        }
    }
    
  
}