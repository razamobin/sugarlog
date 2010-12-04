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
 });
