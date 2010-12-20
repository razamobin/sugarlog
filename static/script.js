 $(document).ready(function() {

    // hide all reply forms
    $('.reply-form').hide();

    // show all reply js links
    $('.reply-link').show();

    // handle reply link click
    $('a.reply-link', this).click(function() {
        $('#reply-' + this.id.replace('reply-link-', '')).toggle();
        if (this.text === 'reply') {
            $(this).text('close');
        } else {
            $(this).text('reply');
        }
        return false;
    });

    var d = new Date();
    var t = d.getTime();
    //t = t - 3 * 60 * 60 * 1000;
    t = Math.floor(t / 1000 / 60 / 60) * 60 * 60 * 1000;
    d.setTime(t);

    // add time picker on new page
    $("#timestart").timePicker({
        startTime: '00:00',//d,
        show24Hours: false,
        separator: '.',
        step: 30});
});
