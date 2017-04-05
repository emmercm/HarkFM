if(typeof(QWebChannel) != 'undefined') {
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.py = channel.objects.py;

        // Handle socket I/O for track time
        var progress_bar = $('.bar-time .progress .progress-bar:visible');
        if(progress_bar.length) {
            setInterval(py.update, 100);
        }
        py.updated.connect(function(elapsed, percent, remaining) {
            progress_bar.first().html(elapsed);
            progress_bar.first().css('width', percent+'%');
            progress_bar.last().html(remaining);
        });
    });
} else {
    alert('QWebChannel is not supported!');
}

$(document).ready(function() {
    // .modal-body max-height:calc()
    function onresize_modal() {
        var $modal = $('body > .modal:visible');
        if($modal.length) {
            var height = $(window).height() - 10;
            height -= parseInt($modal.find('.modal-dialog').css('margin-top'));
            height -= $modal.find('.modal-header').outerHeight();
            height -= $modal.find('.modal-footer').outerHeight();
            $modal.find('.modal-body').css('max-height', height+'px');
        }
    }
    $('.modal').on('shown.bs.modal', onresize_modal);
    $(window).resize(onresize_modal);

    function onresize_imgbox() {
        $('.img-box').each(function() {
            var $box = $(this);
            $box.height($box.width());
        });
    }
    $(window).resize(onresize_imgbox);
    onresize_imgbox();

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