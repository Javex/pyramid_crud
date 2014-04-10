$(document).ready(function(){
    List.init();
});

var List = {

    init: function() {
        this.drawCheckAllBox();
    },

    drawCheckAllBox: function() {
        checkbox = $('<input type="checkbox" id="check-all" />')
        $('table thead th:first').html(checkbox)
        $(checkbox).click(this.onCheckAllClick)
    },

    onCheckAllClick: function() {
        checked = $(this).prop('checked')
        $('[name="items"]').each(function() {
            $(this).prop('checked', checked)
        });
    },
}
