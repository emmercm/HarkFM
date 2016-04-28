$(document).ready(function() {
    var progress_bar = $('.bar-time .progress .progress-bar:visible');
    if(progress_bar.length) {
        setInterval(function() {
            progress_bar.first().html(py.elapsed());
            progress_bar.first().css('width', py.percent()+'%');
            progress_bar.last().html(py.remaining());
        }, 100);
    }

    $('input:visible').first().focus();
});

$(document).keyup(function(e) {
    $('*[keyup='+e.which+']:visible').click();
});

function love(reference) {
    $(reference).attr({'onclick':'', 'class':'fa fa-spinner fa-pulse'});
    py.love();
}
function unlove(reference) {
    $(reference).attr({'onclick':'', 'class':'fa fa-spinner fa-pulse'});
    py.unlove();
}

function save_settings(reference) {
    var values = new Object();
    $(reference).closest('.modal-dialog').find('input').each(function() {
        var $input = $(this);
        var value = $input.val();
        switch($input.attr('type')) {
            case 'checkbox':
                value = $input.is(':checked');
                break;
        }
        values[$input.attr('name')] = value;
    });
    py.save_settings(JSON.stringify(values));
    $(reference).closest('.modal').modal('hide');
}