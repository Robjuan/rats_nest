$.fn.initalise_datatable = function(data_reference){

    var colnames = [];
    $(this).find('thead > tr > th').each(function(index){
        colnames.push($(this).data('colname'));
    });

    columns = colnames.map(function(d) {
        return {'data':d}
    })

    //var csrftoken = Cookies.get('csrftoken');
    var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection

    var target_constructor = $(this).data('target')

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

        // this maps straight on to the jquery ajax
        ajax: {
            type : 'POST',
            url : 'ajax/get_datatables_json',
            headers : { "X-CSRFToken": csrftoken },
            data : { 'target_constructor': target_constructor,
                     'col_list': JSON.stringify(colnames),
                     'data_reference': JSON.stringify(data_reference) }
        },



    });


};


$(document).ready(function(){
    console.log('dataframe_display_jquery loaded');

    var game_ids = [];
    $('.game_table').each(function(index){
        game_ids.push($(this).data('gameid'))
    });

    $('#team_table').initalise_datatable(game_ids);

    $('.game_table').each(function(index){
        $(this).initalise_datatable($(this).data('gameid'));
    });

});