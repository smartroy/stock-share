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
    $("#itemtable").append(
                        '<tr id="item' + next + '" class="item"><td><input type="text" name="upc"></td><td><input type="text" size="10" name="brand"></td><td><input type="text" size="10" name="name"></td><td><input type="text" size="10" name="size"><td><input type="text" size="10" name="color"></td><td><input type="text" size="10" name="source"></td<td><button type="button" id="remove' + next + '" onclick="remove_item(this.id)">-</button></tr>'
        );
    //document.getElementById("itemtable").innerHTML += '<tr id="item' + next + '" class="item"><td><input type="text" name="upc"></td><td><input type="text" name="brand"></td><td><input type="text" name="name"></td><td><input type="text" name="price"></td><td><input type="text" name="qty"></td><td><button type="button" id="remove' + next + '" onclick="remove_item(this.id)">-</button></tr>';

}

function remove_item(id){
    var index = Number(id.replace('remove',''));
    var parent=document.getElementById("itemtable");
    var child = document.getElementById('item'+index);
    parent.removeChild(child);
}