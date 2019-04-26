
$(document).ready(function(){
    console.log('dataframe_display_jquery loaded');

    var game_ids = [];
    $('.game_table').each(function(index){
        game_ids.push($(this).data('gameid'))
    });


    var with_title = false;
    var colnames = [];
    $('#team_table').find('thead > tr > th').each(function(index){
        colnames.push($(this).data('colname'));
    });

    columns = colnames.map(function(d) {
        return {'data':d}
    })

    //var csrftoken = Cookies.get('csrftoken');
    var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection

    $('#team_table').DataTable({
        //serverSide: true,
        processing: true,
        paging: false,
        searching: false,
        stateSave: true,
        autoWidth: true,

        columns: columns,

        // this maps straight on to the jquery ajax
        ajax: {
            type : 'POST',
            url : 'ajax/get_datatables_json',
            headers : { "X-CSRFToken": csrftoken },
            data : { 'target_constructor': 'Team',
                     'col_list': JSON.stringify(colnames),
                     'data_reference': JSON.stringify(game_ids) }
        },



    });

});