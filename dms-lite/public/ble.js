$(document).ready(function() {
    $(".show-more-button").on('click', function() {
        // If text is shown less, then show complete
        if ($(this).attr('data-more') == 0) {
            $(this).attr('data-more', 1);
            $(this).text('Show less');
            $(this).prev().css('display', 'inline'); //none
        }
        // If text is shown complete, then show less
        else if (this.getAttribute('data-more') == 1) {
            $(this).attr('data-more', 0);
            $(this).text('Show more');
            $(this).prev().css('display', 'none');
        }
    });
});
