
$.fn.select_initial_match = function() {
    //console.log('select_initial_match called');
    var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection

    var full_element_id = $(this).attr('id');
    var current_form = $(this);

    var form_class = $(this).data('modeltype');


    // this prepares the key here based on what class of primary validator is being used
    // in each view where this ajax will be loaded, the dictionary will be prepared based on that same class information
    // this validator setup does not support mixing team and player validators in the same view
    // this also assumes that any time you are validating teams you are selecting only one

    var id_array = $(this).attr('id').split('-');
    var match_key = id_array[1]; // for Team this will be field name, for Player this will be formset index

    if (form_class == 'Team'){
        var form_index = 0; // team validation assumes only one at a time
        var pri_prefix = '#id_primary_validator'; // this string from forms.py definition
        var checkbox_id = pri_prefix + '-selected';

    } else if (form_class == 'Player'){
        var form_index = match_key;
        var pri_prefix = '#'+id_array[0];
        var checkbox_id = pri_prefix +'-'+ form_index + '-selected'

    } else {
        alert('unknown form_class: ' +form_class);
    };

    $.ajax({
        type: 'POST',
        url: 'ajax/get_initial_match',
        headers:{ "X-CSRFToken": csrftoken },
        data: {'match_key': match_key },

        success: function(response){
            if(response['success']){
                var text = response['match_text'];
                var id = response['match_id'];

                if(id){
                    // has match, hide the detail form, make detail form not required
                    secondary_form_div = '#secondary_form_div-'+form_index;
                    $(secondary_form_div).toggle();
                    $(secondary_form_div).find('input, select').prop('required', false);
                    set_active_form(form_index, 1);

                    // Set the value, creating a new option if necessary
                    // should always be creating a new value because this is only called once on load
                    if (current_form.find("option[value='" + id + "']").length) {
                        current_form.val(id).trigger('change');
                    } else {
                        // Create a DOM Option and pre-select by default
                        var newOption = new Option(text, id, true, true);
                        // Append it to the select
                        current_form.append(newOption).trigger('change');
                        current_form.trigger('select2:select');

                    };

                } else { // id will be passed as None with success True if there is no initial match for that form
                    // no match, hide the select2 form
                    primary_form_div = '#primary_form_div-'+form_index;
                    $(primary_form_div).toggle();
                    $(primary_form_div).find('input, select').prop('required', false);
                    $(checkbox_id).prop('checked', true); // checkbox will start as unchecked bc forms.py
                    set_active_form(form_index, 2);

                };

            } else {
                console.log('select_initial_match ajax was ' + response['success']);
                console.log(response['warning']);
            };

        },

        error: function (request, status, error) {
             console.log(request.responseText);
        }
    });



    return this;
};

function set_active_form(form_index, prisec) {
    var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection
    var index = form_index;
    var ps = prisec;
    // form_index is the index in a formset (will be 0 for single form page)
    // 1 or 2 refers to primary or secondary form active
    var dict = {[index] : ps}; // square brackets for "computed" name not just var name as string
    //console.log(dict)

    var json_request_dict = JSON.stringify(dict);

    $.ajax({
        type: 'POST',
        url: 'ajax/set_active_form',
        headers: { "X-CSRFToken": csrftoken },
        data: {'json_request_dict': json_request_dict},
        success: function(response){
            //console.log('updated active_form_dict');
        },
        error: function (request, status, error) {
             console.log(request.responseText);
        }

    });

    return this;
};

$.fn.update_ext_details = function () {
    var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection

    var model = $(this).data('modeltype');
    if (model == 'Player'){
        var index = $(this).attr('id').split('-')[1];
    } else if (model == 'Team'){
        var index = 0;
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
};

$.fn.toggle_associated_form = function() {

    var model = $(this).data('modeltype');

    if (model == 'Player'){ // player are formsets
        var index = $(this).attr('id').split('-')[1];

    } else if (model == 'Team'){ // team are individual forms
        var index = 0;

    } else {
        console.log('malformed data-model-type: ' + model);
        console.log($(this).attr('name'));
        var index = -1;
    };

    var primary_form = '#primary_form_div-'+index;
    var secondary_form = '#secondary_form_div-'+index;

    $(secondary_form).toggle();
    $(primary_form).toggle();

    // here we must restore the form to it's regular state re: required
    // otherwise it will be possible to submit a form without required info and the model will complain

    if ($(secondary_form).is(':visible')){
        $(secondary_form).find('input, select').each(function(index){
            if ($(this).hasClass('initially_required')){
                $(this).prop('required', true);
            }
        });
        $(primary_form).find('input, select').prop('required', false);

        set_active_form(index, 2);


    } else if ($(primary_form).is(':visible')){
        $(primary_form).find('input, select').each(function(index){
            if ($(this).hasClass('initially_required')){
                $(this).prop('required', true);
            }
        });
        $(secondary_form).find('input, select').prop('required', false);

        set_active_form(index, 1);
    }

    return this;
};

$(document).ready(function(){
    console.log('validation_jquery loaded');

    // mark all required inputs as 'initially_required' so we can restore this on toggles
    $(document).find('input, select').each(function(index){
        if ($(this).prop('required')){
            $(this).addClass('initially_required');
        }
    });

    // updates the 'extra_details' div to show the full info about a selected match
    $(".django-select2-heavy").on('select2:select', function(event){
        $(this).update_ext_details();
    });

    // auto-selects the match for each nameform
    $(".django-select2-heavy").each(function(index){
        $(this).select_initial_match();
    });

    // toggles visibility of the divs
    // also informs the view of the active form by calling 'set_active_dict'
    $(':checkbox').change(function(){
        $(this).toggle_associated_form();
    });


});
