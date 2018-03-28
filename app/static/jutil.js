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
                                '<th>Avg Price</th>'+
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
                        "<td name='avg_price'>"+data[i]["avg_price"].toFixed(1)+"</td>"+
                        "<td><input type='text' name='price' size=4 value="+data[i]["current_price"].toFixed(1)+"></td>"+
                        "<td><input type='text' name='note' size=4 style='width:100%;'></td>"+
                        "</tr>");

                }
                table_text +="</tbody></table>";
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
                    $("div#sources_result").html(table_text);
                });
            }
            });
        return false;
    });

    

    $('#submit_order').bind('click','#itemtable',function(){
        
        var items ={'empty':true};
        // console.log($(':#sources_result').html());
        $('#itemtable tr').each(function(){
            // console.log("in loop");
            console.log($(this).html());
            var item_qty=$(this).find('[name="qty"]').val();
            if(parseInt(item_qty)>0){
                // add_table +=$(this).html();

                var item_id =$(this).attr('id');
                
                var item_price=$(this).find('[name="price"]').val();
                var item_note=$(this).find('[name="note"]').val();
                items[item_id]={'qty':item_qty,'price':item_price,"note":item_note};
                item['empty']=false;

            }
        });
        if(items['empty']){
            alert("Nothing in the Order list\n");
        }
        // var ship_name=$('#ship_info').find('[name="ship_name"]').val();
        // vaTherer ship_addr=$('#ship_info').find('[name="address"]').val();
        // var ship_cell=$('#ship_info').find('[name="cellphone"]').val();
        else{
            var bill_name=$('#bill-info').find('[name="bill_name"]').val();
            var bill_addr=$('#bill-info').find('[name="address"]').val();
            var bill_cell=$('#bill-info').find('[name="cellphone"]').val();
            var pay=$('#bill-info').find('[name="pay"]').is(":checked");
            var ship_name=$('#ship-info').find('[name="bill_name"]').val();
            var ship_addr=$('#ship-info').find('[name="address"]').val();
            var ship_cell=$('#ship-info').find('[name="cellphone"]').val();
            var package=$('#ship-info').find('[name="package"]').is(":checked");
            items['bill']={'name':bill_name,'addr':bill_addr,'cellphone':bill_cell,'pay':pay};
            items['ship']={'name':ship_name,'addr':ship_addr,'cell':ship_cell,'package':package};
            items = JSON.stringify(items);
            // console.log(items)
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
        }
        return false;
        // //  $.getJSON('/_add_order',items, function (data) {
        // //     console.log(data)
        // //     window.location.href = data;
        // // });
        // return false;
        // console.log(items);
        
    });

    $('#submit_email').bind('click','#send_email',function(){
        var email_item={};
        email_item['email'] = $('#send_email').find('[name="email"]').val();
        email_item['subject'] = $('#send_email').find('[name="subject"]').val();
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
            alert("Please fill in email address");
        }
    });
    $('#add_service').bind('click','#new_service',function(){
        var service_item={};
        service_item['email'] = $('#new_service').find('[name="email"]').val();
        // email_item['subject'] = $('#send_email').find('[name="subject"]').val();
        if(service_item['email']){
            service_item=JSON.stringify(service_item);
            $.ajax({
            type : "POST",
            url : "/_add_service",
            data: service_item,
            contentType: 'application/json;charset=UTF-8',
            success: function(result) {
                console.log(result);
                window.location.href = result;
            }
        });
        }
        else{
            alert("Please fill in email address");
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
        var row=$(bt).closest('div');
        // alert(row.attr('id'));
        var item_qty=row.find('[name="ship_qty"]').val();
        var cell = row.find('[name="cell"]').val();
        var name = row.find('[name="name"]').val();
        var addr = row.find('[name="addr"]').val();
        console.log(row)
        console.log(cell)
        console.log(name)
        if(parseInt(item_qty)>0){
            
            item_id=row.attr('id');
            items[item_id]={'qty':item_qty,'name':name,'cell':cell,'addr':addr};
        
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

function ship_cancel(bt){
        
        var items ={};
        var row=$(bt).closest('tr');
        
        console.log(row)
        
            
        item_id=row.attr('id');
        items['id']=item_id;
        var json_data ={
            "action":"cancel",
            "items": items
        };
        json_data = JSON.stringify(json_data);
        $.ajax({
            type : "POST",
            url : "/order/_item_ship_update",
            data: json_data,
            contentType: 'application/json;charset=UTF-8',
            success: function(result) {
                console.log(result);
                window.location.href = result;
            }
        });
        // }
        // else{
        //     alert("Please the amount you want to ship")
        // }
        
};

function ship_release(bt){
        
        var items ={};
        var row=$(bt).closest('tr');
        
        console.log(row)
        
            
        item_id=row.attr('id');
        items['id']=item_id;
        var json_data ={
            "action":"release",
            "items": items
        };
        json_data = JSON.stringify(json_data);
        $.ajax({
            type : "POST",
            url : "/order/_item_ship_update",
            data: json_data,
            contentType: 'application/json;charset=UTF-8',
            success: function(result) {
                console.log(result);
                window.location.href = result;
            }
        });
        // }
        // else{
        //     alert("Please the amount you want to ship")
        // }
        
};

function ship_edit(bt){
        
        var items ={};
        var row=$(bt).closest('tr');
        
        console.log(row)
        
            
        item_id=row.attr('id');
        items['id']=item_id;
        var json_data ={
            "action":"release",
            "items": items
        };
        json_data = JSON.stringify(json_data);
        $.ajax({
            type : "POST",
            url : "/order/_item_ship_update",
            data: json_data,
            contentType: 'application/json;charset=UTF-8',
            success: function(result) {
                console.log(result);
                window.location.href = result;
            }
        });
        // }
        // else{
        //     alert("Please the amount you want to ship")
        // }
        
};

