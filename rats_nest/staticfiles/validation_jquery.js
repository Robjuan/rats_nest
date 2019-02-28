$(document).ready(function(){
    // select2 boxes are id'd in format : id_names-*-proper_name
    console.log('validation_jquery loaded');


    $('.django-select2').select2();

    $("#id_names-1-proper_name").on('select2:selecting', function(event){
            //var data = event.params.data;
            console.log('we did it');
    });
});
