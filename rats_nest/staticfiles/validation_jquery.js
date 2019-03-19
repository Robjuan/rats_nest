$(document).ready(function(){
    console.log('validation_jquery loaded');

    // auto-selects the match for each nameform
    $(".django-select2-heavy").each(function(index){
        var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection

        var form_id = this.id
        var current_form = $(this);

        $.ajax({
            type: 'POST',
            url: 'parse_validate_player/get_initial_match',
            headers:{ "X-CSRFToken": csrftoken },
            data: {'form_id': form_id },

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

                }
            },
            error: function (request, status, error) {
                 console.log(request.responseText);
            }
        });
    });


    // updates the corresponding details form when a player is selected in the name form
    $(".django-select2-heavy").on('select2:select', function(event){
        var csrftoken = $("[name=csrfmiddlewaretoken]").val(); // required for django csrf protection

        var selection_data = $(this).val()
        var form_id = this.id

        $.ajax({
            type: 'POST',
            url: 'parse_validate_player/update_details',
            headers:{ "X-CSRFToken": csrftoken },
            data: {'selection_data': selection_data, 'form_id': form_id },

            success: function(response) { // response is the JsonResponse generated by the function in views.py
                 if(response['success']) {
                     $.each(response['field_data'], function(name, value){
                        // details form fields are id'd as: id_details-*-[fieldname]
                        var details_form_id = "id_details-" + response['form_id'] + "-" + name
                        form_to_change = "#" + details_form_id
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
    });
});

/*
// this doesn't fully inject, it just opens the search and enters a term. needs click to confirm.
function select2_search ($el, term) {
  $el.select2('open');

  // Get the search box within the dropdown or the selection
  // Dropdown = single, Selection = multiple
  var $search = $el.data('select2').dropdown.$search || $el.data('select2').selection.$search;
  // This is undocumented and may change in the future

  $search.val(term);
  $search.trigger('input');
}
*/