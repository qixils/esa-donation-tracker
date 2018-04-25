// Make sure jQuery (django admin) is available, use admin jQuery instance
let $;

if (typeof $ === 'undefined') {
    $ = django.jQuery;
}

let EVENT_URL = "https://horaro.org/-/api/v1/events/";

$(function () {
    $("#id_horaro_id").change(function () {
        let val = $(this).val();
        let e = $("#horaro_cols");
        if (val) {
            $.ajax({
                dataType: "json",
                url: "/horaro_schedule_cols/" + val,
                method: "GET",
                success: function (data) {
                    e.text(data.join(", "));
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    e.text("Schedule not found");
                }
            });
        } else {
            e.text("Enter event ID or slug to check columns");
        }
    }).change();
});
