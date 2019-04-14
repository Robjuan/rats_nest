
$.fn.update_ext_details = function () {
    var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection

    var model = $(this).data('modeltype');

    if (model == 'Player'){
        var index = $(this).attr('id').split('-')[1];
    } else if (model == 'Team'){
        var index = 0;
    } else {
        console.log('modeltype unsupported: '+model)
        return this;
    };

    var selected_pk = $(this).val();

    var extra_details_div = '#primary_form_extra_details-'+index;

    // don't display these fields
    // primary keys and names are shown in select2 box because of model __str__
    var exclude = ['player_ID', 'team_ID', 'proper_name', 'team_name']

    $.ajax({
            type: 'POST',
            url: 'ajax/set_extra_details',
            headers:{ "X-CSRFToken": csrftoken },
            data: {'modeltype': model,
                   'selected_pk': selected_pk},

            success: function(response){
                if (response['success']){

                    var det_json = JSON.parse(response['infojson']);

                    var disp_string = ''
                    $.each(det_json, function(key, value){
                        if (value && value != 'None'){
                            if (jQuery.inArray(key, exclude) == -1) {  // inArray returns -1 if not found
                                disp_string = disp_string+'<b>'+key+':</b> '+value+' <br> ';
                            };
                        };
                    });

                    $(extra_details_div).html(disp_string);

                } else {
                    console.log('update_ext_details failed');
                };

            },
            error: function (request, status, error) {
             console.log(request.responseText);
            }
    });

    return this;
};



$(document).ready(function(){
    console.log('analysis_jquery loaded');

    // updates the 'extra_details' div to show the full info about a selected match
    $(".django-select2-heavy").on('select2:select', function(event){
        $(this).update_ext_details();
    });

});