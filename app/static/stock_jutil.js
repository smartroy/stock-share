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

    $('#search_source').bind('click', function() {
        $.getJSON('/_search_source', {
            'source': $('#source').find('option:selected').val()

        }, function(data) {
            var i;
            var table_text = '<table class="table" id="result_table">'+
            '<thead>'+
            '<tr>'+
            '<th>Brand</th>'+
            '<th>Name/Nick name</th>'+
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
                        "<td><input type='text' name='qty' size=4 value=0></td>"+
                        "<td><input type='text' name='price' size=4 value=0.0></td>"+
                        "</tr>");

                }
                table_text +="</tbody></table>";
                $("div#sources_result").html(table_text);
                // $("div#sources_result").append(table_text);
            }
            });
        return false;
    });
});