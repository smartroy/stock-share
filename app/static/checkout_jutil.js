//$SCRIPT_ROOT = {{request.script_root|tojson|safe}};
//$(document).ready(function(){

$(function() {
    

    
    $('.order_selector').bind('click',function(){
        p_div = $(this).closest("div");
        chekc_boxes = $(p_div).find('input[type="checkbox"]').prop('checked',this.checked);
        // console.log(p_div.attr('name'));
    });


    $('.pay_selected').bind('click',function(){
        var items={};
        var payment=false;
        var item_info=$(this).closest("div").find('[class="order_item_info"]').each(
                function(){
                    var confirm = $(this).find('[name="confirm"]').is(":checked");
                    if(confirm){
                        payment=true;
                        var key = $(this).attr("id").replace('order_item','');
                        var qty = $(this).find('[name="pay_qty"]').val();
                        var name=$(this).find('[name="product_name"]').html();
                        var price=$(this).find('[name="price"]').val();
                    
                        items[key]={'qty':qty,'confirm':confirm,'name':name,'total':qty*price};
                    }
                    // console.log(items[key]);
                    
                }
            );

        // console.log(info_id);
        // for (var i = 0; i < item_info.length; i++) {
        //     console.log(item_info[i].attr('id'));       
        // }
        var dialog_div = $(document.createElement('div'));
        dialog_div.id = "Confirm Payment";
        if(!payment){
            dialog_div.html("Please select items to pay");
            dialog_div.dialog({
                height: "auto",
                width: 700,
                modal: true,
                resizable: true,

                buttons:{
                    OK:function(){
                        $(this).dialog("close");
                    }
                    
                }
            });
        }
        else{
            var inner = "<p>The following items will be marked as Checked Out</p>"+
                        "<table class='table table-fixed'>";

            for(key in items){
                
                    inner+="<tr>"+
                            "<td>"+items[key]["name"]+"</td>"+
                            
                            "<td>Qty "+items[key]["qty"]+"</td>"+
                            "<td>Total "+items[key]["total"]+"</td>"+
                            "</tr>";
                
            }
            inner+="</table>";
            dialog_div.html(inner);

            dialog_div.dialog({
                height: "auto",
                width: 700,
                modal: true,
                resizable: true,

                buttons:[
                    {
                        id:"confirm-button",
                        text:"Confirm",
                        
                        click:function(){
                            $("#confirm-button").attr('disabled',true);
                            items = JSON.stringify(items);
                            $.ajax({
                                type : "POST",
                                url : "/order/checkout/_add_payment",
                                data: items,
                                contentType: 'application/json;charset=UTF-8',
                                success: function(result) {
                                    console.log(result);
                                    window.location.href = result;
                                }
                            });
                        },
                    },
                    {   
                        id:"cancle-button",
                        text:"Cancel",
                        click:function(){
                            $(this).dialog("close");
                        }
                    }
                ]






                // {
                //     Confirm:function(){
                //         items = JSON.stringify(items);
                //         $.ajax({
                //             type : "POST",
                //             url : "/order/checkout/_add_payment",
                //             data: items,
                //             contentType: 'application/json;charset=UTF-8',
                //             success: function(result) {
                //                 console.log(result);
                //                 window.location.href = result;
                //             }
                //         });
                //     },
                //     Cancel:function(){
                //         $(this).dialog("close");
                //     }
                // }
            });
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

