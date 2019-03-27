
$.fn.select_initial_match = function() {
    //console.log('select_initial_match called');

    var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection

    var full_element_id = $(this).attr('id')
    var current_form = $(this);
    var current_classes = current_form.attr('class').split(/\s+/) // split by any whitespace

    var form_class = null;
    $.each(current_classes, function(index, item){
        if (item.includes('primaryform')) {
            form_class = item.split('_')[0]
            // 'Team' or 'Player'
        };
    });

    // this prepares the key here based on what class of primary validator is being used
    // in each view where this ajax will be loaded, the dictionary will be prepared based on that same information
    // this validator setup does not support mixing team and player validators in the same view
    // this also assumes that any time you are validating teams you are selecting only one

    if (form_class == 'Team'){
        match_key = $(this).attr('name') // id is just name with "id_" prepended

    } else if (form_class == 'Player'){
        id_array = full_element_id.split('-')
        match_key = id_array[1] // this will give the formset index from form id

    } else {
        alert(form_class);
    };

    $.ajax({
        type: 'POST',
        url: 'ajax/get_initial_match',
        headers:{ "X-CSRFToken": csrftoken },
        data: {'match_key': match_key },

        success: function(response){
            if(response['success']){
                var text = response['match_text']
                var id = response['match_id']

                // Set the value, creating a new option if necessary
                // should always be creating a new value because this is only called once on load
                if (current_form.find("option[value='" + id + "']").length) {
                    current_form.val(id).trigger('change');
                } else {
                    // Create a DOM Option and pre-select by default

                    var newOption = new Option(text, id, true, true);
                    // Append it to the select
                    current_form.append(newOption).trigger('change');
                    current_form.trigger('select2:select')
                }

            } else {
                console.log(response) // will be here if no request.session['match_dict'] exists
            };
        },
        error: function (request, status, error) {
             console.log(request.responseText);
        }
    });



  return this;
};


$.fn.update_secondary_validator = function() {
    //console.log('update_secondary_validator called');

    var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection

    var selection_data = $(this).val()

    var current_form = $(this);
    var current_classes = current_form.attr('class').split(/\s+/) // split by any whitespace


    // TODO (if req) genericise this even further to be Single/Formset instead of Team/Player

    var form_class = null;
    $.each(current_classes, function(index, item){
        if (item.includes('primaryform')){
            form_class = item.split('_')[0]
            // 'Team' or 'Player'
        };
    });

    // this function only has to deal with a single form at a time and is called individually per select event

    // find all fields that are in the corresponding detail form
    // Player: find all that have "id_details-*-" in them (player)
    // Team: find all that have "id" and also corresponding class


    var field_dict = {};
    var form_id = $(this).attr('id');
    var secondaryform_class = '.' + form_class + '_secondaryform'

    if (form_class == 'Team'){
        // this loops over every secondary form (ie, the only one) and builds field_dict entry
        $(secondaryform_class).each(function(index){
            field_dict[$(this).attr('id')] = $(this).attr('name'); // name equals model field name
        });

    } else if (form_class == 'Player'){
        // extract id information from select2 form
        var split_id = form_id.split('-');
        var form_prefix = split_id[0]; // has id_* prepended
        var form_index = split_id[1]; // form index in formset
        var form_field_name = split_id[2]; // matches the model field name

        // this loops over every secondary form, and if it is the appropriate index builds the field_dict entry
        $(secondaryform_class).each(function(index){
            var sec_form_name = $(this).attr('name');
            if (sec_form_name.includes(form_index)){ // ensure only the appropriate secondaryform
                // extract field name from secondary form field
                var sec_field_name = sec_form_name.split('-')[2]; // prefix-index-fieldname
                field_dict[$(this).attr('id')] = sec_field_name;
            };
        });

    } else {
        alert(form_class);
    };

    // have to use stringify to send more complex data types within json
    var json_field_dict = JSON.stringify(field_dict)
    var data = {'form_class': form_class,
                'selection_data': selection_data,
                'json_field_dict': json_field_dict}

    $.ajax({
        type: 'POST',
        url: 'ajax/update_details',
        headers:{ "X-CSRFToken": csrftoken },
        data: data,

        // send a dict that is id : field_name
        // where id is the object id (fully formed) that will be returned back to us
        // and field_name is the field name from the form (ie, the field name for the model)
        // also sending form_class

        success: function(response) { // response is the JsonResponse generated by the function in views.py

            // response should be a dict of id:val that can just be blindly changed here

             if(response['success']) {
                 $.each(response['field_data'], function(name, value){
                    var form_to_change = '#'+name+secondaryform_class
                    $(form_to_change).val(value);
                    $(form_to_change).trigger('change');
                 });
             }

        },
        error: function (request, status, error) {
             console.log(request.responseText);
             // do we need anything more than console logging on this error?
        }
   });

};


$(document).ready(function(){
    console.log('validation_jquery loaded');

    // updates the corresponding details form when a player is selected in the name form
    $(".django-select2-heavy").on('select2:select', function(event){
        $(this).update_secondary_validator();
    });


    // auto-selects the match for each nameform
    $(".django-select2-heavy").each(function(index){
        $(this).select_initial_match();
    });

});
