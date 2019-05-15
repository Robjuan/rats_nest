$.fn.initalise_datatable = function(data_reference){

    var colnames = [];
    $(this).find('thead > tr > th').each(function(index){
        colnames.push($(this).data('colname'));
    });

    columns = colnames.map(function(d) {
        return {'data':d}
    });

    // required for django csrf protection
    var csrftoken = Cookies.get('csrftoken');
    if(!csrftoken){
        var csrftoken = $("[name=csrfmiddlewaretoken]").val();
    };

    var target_constructor = $(this).data('target');

    // todo: what if the player didn't play that game?

    if ($(this).data('playerid')){
        var playerid = $(this).data('playerid');
    } else {
        var playerid = -1;
    };

    $(this).DataTable({
        //serverSide: true,
        //processing: true,
        paging: false,
        searching: false,
        stateSave: true,
        autoWidth: true,
        bInfo: false,
        scrollX: true,

        columns: columns,

        // this maps straight on to the jquery ajax call
        ajax: {
            type : 'POST',
            url : 'ajax/get_datatables_json',
            headers : { "X-CSRFToken": csrftoken },
            data : { 'target_constructor': target_constructor,
                     'col_list': JSON.stringify(colnames),
                     'data_reference': JSON.stringify(data_reference),
                     'player_id':playerid }
        },



    });


};


$(document).ready(function(){
    console.log('dataframe_display_jquery loaded');

    var game_ids = [];
    $('.game_table').each(function(index){
        game_ids.push($(this).data('gameid'))
    });


    $('.game_table').each(function(index){
        $(this).initalise_datatable($(this).data('gameid'));
    });


    $('#compound_table').initalise_datatable(game_ids);

});