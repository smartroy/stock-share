function add_item(){
    console.log("add item");
    var items=document.getElementById("itemtable").getElementsByClassName("item");
    var next = 0
    if (items[0]!=null){
        var last_id = items[items.length -1].id;
        next = Number(last_id.replace('item','')) + 1;
    }
    else{
        next =1;
    }
    console.log(next);
    entry = document.getElementById("item1").innerHTML;

    $("#itemtable").append(
        '<tr id="item' + next + '" class="item">'+entry+'<td><button type="button" id="remove' + next + '" onclick="remove_item(this.id)">-</button></tr>'
        );
    //document.getElementById("itemtable").innerHTML += '<tr id="item' + next + '" class="item"><td><input type="text" name="upc"></td><td><input type="text" name="brand"></td><td><input type="text" name="name"></td><td><input type="text" name="price"></td><td><input type="text" name="qty"></td><td><button type="button" id="remove' + next + '" onclick="remove_item(this.id)">-</button></tr>';

}

function remove_item(id){
    var index = Number(id.replace('remove',''));
    var parent=document.getElementById("itemtable");
    var child = document.getElementById('item'+index);
    parent.removeChild(child);
}




$(document).ready(function(){
    $SCRIPT_ROOT = {{request.script_root|tojson|safe}};
    $(function() {
        $('#search_source').bind('click', function() {
            $.getJSON($SCRIPT_ROOT + '/_search_source', {
            'source': $('#source').find('option:selected').val()

        }, function(data) {
            var i;
            var table_text = '<table class="table table-fixed">'+
            '<thead>'+
            '<tr>'+
            '<th></th>'+
            '<th></th>'+
            '<th>Brand</th>'+
            '<th>Name/Nick name</th>'+
            '<th>New Qty.</th>'+
            '<th>Price</th>'
            '</tr>'+
            '</thead>'+
            '<tbody>';
            if (data.length==0){
                $("div#sources_result").append("<h2>UPC not found</h2>");
            }else{
                for (i=0;i<data.length;i++){
                    table_text += ("<tr>"+
                        "<td><input type='checkbox' name='check' value= '1'><td>"+
                        "<td>"+data[i]["brand"]+"</td>"+
                        "<td>"+data[i]["nick_name"]+"</td>"+
                        "<td><input type='text' name='qty' size=4 value=0></td>"+
                        "<td><input type='text' name='price' size=4 value=0.0></td>"+
                        "</tr>");

                }
                table_text +="</table>";
                $("div#sources_result").replaceWith(table_text);}
            });
          return false;
      });
        $(document).on('click','a#add_stock',function(){
            $.getJSON($SCRIPT_ROOT+'/_add_stock',{
                'qty':$('input[name="qty"]').val(),
                'price':$('input[name="price"]').val(),
                'product_id':$('a#add_stock').attr('name')
            }, function (data) {
                console.log(data)
                window.location.href = data;
            });
            return false;
        });
        
    });
});