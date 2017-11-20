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
        var buyer_name=$('[name="buyername"]').val();
        var buyer_addr=$('#buyer_info').find('[name="address"]').val();
        var buy_cell=$('#buyer_info').find('[name="cellphone"]').val();
        items['buyer']={'name':buyer_name,'addr':buyer_addr,'cellphone':buy_cell};
        items = JSON.stringify(items);
        $.ajax({
            type : "POST",
            url : "/_sort_product",
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