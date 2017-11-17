$(function() {
    // $('#submit_order').bind('click','#sources_result',function(){

    //     var items ={};
    //     // console.log($('#sources_result').html());
    //     $('#itemtable tr').each(function(){
    //         // console.log("in loop");
    //         // console.log($(this).html());
    //         var item_qty=$(this).find('[name="qty"]').val();
    //         if(parseInt(item_qty)>0){
    //             // add_table +=$(this).html();
    //             var item_id =$(this).attr('id');
                
    //             var item_price=$(this).find('[name="price"]').val();
    //             items[item_id]={'qty':item_qty,'price':item_price};


    //         }
    //     });
    //     var buyer_name=$('[name="buyername"]').val();
    //     var buyer_addr=$('#buyer_info').find('[name="address"]').val();
    //     var buy_cell=$('#buyer_info').find('[name="cellphone"]').val();
    //     items['buyer']={'name':buyer_name,'addr':buyer_addr,'cellphone':buy_cell};
    //     items = JSON.stringify(items);
    //     $.ajax({
    //         type : "POST",
    //         url : "/_add_order",
    //         data: items,
    //         contentType: 'application/json;charset=UTF-8',
    //         success: function(result) {
    //             console.log(result);
    //             window.location.href = result;
    //         }
    //     });
    //     //  $.getJSON('/_add_order',items, function (data) {
    //     //     console.log(data)
    //     //     window.location.href = data;
    //     // });
    //     return false;
    //     // console.log(items);
        
    // });

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
            '<th>Required Qty.</th>'+
            '<th>New Qty.</th>'+
            '<th>Price</th>' +
            '</tr>'+
            '</thead>'+
            '<tbody>';
            if (data.length==0){
                $("div#sources_result").append("<h2>UPC not found</h2>");
            }else{
                for (i=0;i<data.length;i++){
                    table_text += ("<tr id='"+data[i]["_id"]+"''>"+

                        "<td name='brand'>"+data[i]["brand"]+"</td>"+
                        "<td name='nick_name'>"+data[i]["name"]+"/"+data[i]["nick_name"]+"</td>"+
                        "<td name='count'>"+data[i]["count"]+"</td>"+
                        "<td><input type='text' name='qty' size=4 value=0></td>"+
                        "<td><input type='text' name='price' size=4 value=0.0></td>"+
                        "</tr>");

                }
                table_text +="</tbody></table>";
                table_text +="<button class='actionBtn' type='button' id='add_search' >Add to Stock</button>";
                $("div#sources_result").html(table_text);
                $('#add_search').bind('click','#sources_result',function(){
        
                    var items ={};
                    // console.log($('#sources_result').html());
                    $('#result_table tr').each(function(){
                        var item_qty=$(this).find('[name="qty"]').val();
                        if(parseInt(item_qty)>0){
                            // add_table +=$(this).html();
                            var item_id =$(this).attr('id');
                            
                            var item_price=$(this).find('[name="price"]').val();
                            items[item_id]={'qty':item_qty,'price':item_price};


                        } 
                    });
                    items = JSON.stringify(items);
                    $.ajax({
                        type : "POST",
                        url : "/_add_stock",
                        data: items,
                        contentType: 'application/json;charset=UTF-8',
                        success: function(result) {
                            console.log(result);
                            window.location.href = result;
                        }
                    });
        
    });
                // $("div#sources_result").append(table_text);
            }
            });
        return false;
    });

    $('#add_scan').bind('click','#scan_result',function(){
        submit_scan();  
        $('#upc_input').val('');  
    });
    
    $(document).keypress(function(e){
        if(e.which == 13){
            submit_scan();
            $('#upc_input').val('');
        }
    });

});

function add_purchase(bt){
        
        var items ={};
        // console.log($('#sources_result').html());
        var row=$(bt).parents('tr');
        // alert(row.attr('id'));
        item_qty=row.find('[name="new_qty"]').val();
        if(parseInt(item_qty)>0){
            item_price=row.find('[name="get_price"]').val();
            item_id=row.attr('id');
            items[item_id]={'qty':item_qty,'price':item_price};
        }
        items = JSON.stringify(items);
        $.ajax({
            type : "POST",
            url : "/_add_stock",
            data: items,
            contentType: 'application/json;charset=UTF-8',
            success: function(result) {
                console.log(result);
                window.location.href = result;
            }
        });
        
};

function submit_scan(){
    var upc=$('#upc_scan').find('[name="upc"]').val();
        var product_qty = $('#scan_table').find('[name='+upc+']').find('[name="new_qty"]').val();
        if (!product_qty){
            $.getJSON('/_search_upc', {

                'upc': upc

            }, function(data) {
                //for (var i=0;i<data.length;i++){
                if(data.length<1){
                    alert('product with UPC'+upc+' not found in inventory');
                }    
                else{
                    table_add = "<tr id='"+data[0]["_id"]+"' name='"+upc+"'>"+

                        "<td name='brand'>"+data[0]["brand"]+"</td>"+
                        "<td name='nick_name'>"+data[0]["name"]+"/"+data[0]["nick_name"]+"</td>"+
                        "<td>"+'<input name="new_qty" size=4 value=1>'+"</td>"+
                        
                        "<td><input type='text' name='get_price' size=4 value=0.0></td>"+
                        '<td><button class="actionBtn" type="button" name="add_purchase" onclick="add_purchase(this)" >Add</button></td>'+
                        "</tr>";
                    $('#scan_table').append(table_add);
                }
            });

        }
        else{
            $('#scan_table').find('[name='+upc+']').find('[name="new_qty"]').val(parseInt(product_qty)+1)
        }

}