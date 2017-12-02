//$SCRIPT_ROOT = {{request.script_root|tojson|safe}};
//$(document).ready(function(){

$(function() {
    $('#search_source').bind('click', function() {
        $.getJSON('/_search_source', {
            'source': $('#source').find('option:selected').val()

        }, function(data) {
            var i;
            var table_text = '<table class="table table-fixed" id="result_table">'+
                                '<thead>'+
                                '<tr>'+
                                '<th>Brand</th>'+
                                '<th>Name/Nick name</th>'+
                                '<th>Color</th>'+
                                '<th>New Qty.</th>'+
                                '<th>Price</th>'+
                                '<th>Note</th>'+
                                '</tr>'+
                                '</thead>'+
                                '<tbody>';
            if (data.length==0){
                $("div#sources_result").append("<h2>UPC not found</h2>");
            }else{
                for (i=0;i<data.length;i++){
                    var link_addr = '{{url_for("main.product_details",product_id ='+data[i]["_id"]+')}}>';
                    table_text += ("<tr name='"+data[i]["_id"]+"''>"+

                        "<td name='brand'>"+data[i]["brand"]+"</td>"+
                        "<td name='nick_name'><a href=\"/product/product_details/"+data[i]["_id"]+"\" target=\"_blank\">"+data[i]["name"]+"/"+data[i]["nick_name"]+"</a></td>"+
                        "<td name='color'>"+data[i]["color"]+"</td>"+
                        "<td><input type='text' name='qty' size=4 value=0></td>"+
                        "<td><input type='text' name='price' size=4 value=0.0></td>"+
                        "<td><input type='text' name='note' size=4 style='width:100%;'></td>"+
                        "</tr>");

                }
                table_text +="</table>";
                table_text +="<button class='actionBtn' type='button' id='add_search' >Add to Order</button>";
                $("div#sources_result").html(table_text);
                $('#add_search').bind('click','#sources_result',function(){
        
                    var add_table ='';
                    // console.log($('#sources_result').html());
                    $('#result_table tr').each(function(){
                        // console.log("in loop");
                        // console.log($(this).html());
                        var item_qty=$(this).find('[name="qty"]').val();
                        if(parseInt(item_qty)>0){
                            // add_table +=$(this).html();
                            var item_id =$(this).attr('name');
                            var item_brand = $(this).find('[name="brand"]').text();
                            var item_name=$(this).find('[name="nick_name"]').text();
                            var item_color = $(this).find('[name="color"]').text();
                            var item_price=$(this).find('[name="price"]').val();
                            var item_note=$(this).find('[name="note"]').val();
                            add_table += ("<tr id='"+item_id+"''>"+

                                    "<td name='brand'>"+item_brand+"</td>"+
                                    "<td name='nick_name'>"+item_name+"</td>"+
                                    "<td name='color'>"+item_color+"</td>"+
                                    "<td><input type='text' name='qty' size=4 value="+item_qty+"></td>"+
                                    "<td><input type='text' name='price' size=4 value="+item_price+"></td>"+
                                    "<td><input type='text' name='note' size=4 style='width:100%;' value="+item_note+"></td>"+
                                    "</tr>");
                        }
                    });
                    $('#itemtable').append(add_table);
                });
            }
            });
        return false;
    });

    

    $('#submit_order').bind('click','#itemtable',function(){
        
        var items ={};
        // console.log($('#sources_result').html());
        $('#itemtable tr').each(function(){
            console.log("in loop");
            console.log($(this).html());
            var item_qty=$(this).find('[name="qty"]').val();
            if(parseInt(item_qty)>0){
                // add_table +=$(this).html();
                var item_id =$(this).attr('id');
                
                var item_price=$(this).find('[name="price"]').val();
                var item_note=$(this).find('[name="note"]').val();
                items[item_id]={'qty':item_qty,'price':item_price,"note":item_note};


            }
        });
        var ship_name=$('#ship_info').find('[name="ship_name"]').val();
        var ship_addr=$('#ship_info').find('[name="address"]').val();
        var ship_cell=$('#ship_info').find('[name="cellphone"]').val();

        var bill_name=$('#bill_info').find('[name="bill_name"]').val();
        var bill_addr=$('#bill_info').find('[name="address"]').val();
        var bill_cell=$('#bill_info').find('[name="cellphone"]').val();
        items['bill']={'name':bill_name,'addr':bill_addr,'cellphone':bill_cell};
        items['ship']={'name':ship_name,'addr':ship_addr,'cellphone':ship_cell};
        items = JSON.stringify(items);
        $.ajax({
            type : "POST",
            url : "/_add_order",
            data: items,
            contentType: 'application/json;charset=UTF-8',
            success: function(result) {
                console.log(result);
                window.location.href = result;
            }
        });
        //  $.getJSON('/_add_order',items, function (data) {
        //     console.log(data)
        //     window.location.href = data;
        // });
        return false;
        // console.log(items);
        
    });

    $('#submit_email').bind('click','#send_email',function(){
        var email_item={};
        email_item['email'] = $('#email').val();
        email_item['subject'] = $('#subject').val();
        if(email_item['email']){
            email_item=JSON.stringify(email_item);
            $.ajax({
            type : "POST",
            url : "/_send_email",
            data: email_item,
            contentType: 'application/json;charset=UTF-8',
            success: function(result) {
                console.log(result);
                window.location.href = result;
            }
        });
        }
        else{
            alter("Please fill in email address");
        }
    });

    
    // $(document).on('click','a#add_stock',function(){
    //     $.getJSON('/_add_stock',{
    //         'qty':$('input[name="qty"]').val(),
    //         'price':$('input[name="price"]').val(),
    //         'product_id':$('a#add_stock').attr('name')
    //     }, function (data) {
    //         console.log(data)
    //         window.location.href = data;
    //     });
    //     return false;
    // });
    
});
//});

function ship_item(bt){
        
        var items ={};
        // console.log($('#sources_result').html());
        var row=$(bt).parents('tr');
        // alert(row.attr('id'));
        item_qty=row.find('[name="ship_qty"]').val();
    
        if(parseInt(item_qty)>0){
            
            item_id=row.attr('id');
            items[item_id]={'qty':item_qty};
        
            items = JSON.stringify(items);
            $.ajax({
                type : "POST",
                url : "/order/_item_ship",
                data: items,
                contentType: 'application/json;charset=UTF-8',
                success: function(result) {
                    console.log(result);
                    window.location.href = result;
                }
            });
        }
        else{
            alert("Please the amount you want to ship")
        }
        
};