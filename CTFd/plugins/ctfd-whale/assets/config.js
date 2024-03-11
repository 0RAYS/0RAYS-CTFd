const $ = CTFd.lib.$;


function getFormJson(form) {
    var o = {};
    var a = $(form).serializeArray();
    $.each(a, function () {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
}

$(".config-section > form:not(.form-upload)").submit(async function (event) {
    event.preventDefault();
    const obj = getFormJson($(this))
    const params = {};
    for (let x in obj) {
        if (obj[x] === "true") {
            params[x] = true;
        } else if (obj[x] === "false") {
            params[x] = false;
        } else {
            params[x] = obj[x];
        }
    }
    params['whale:refresh'] = btoa(+new Date).slice(-7, -2);

    await CTFd.api.patch_config_list({}, params);
    location.reload();
});
$(".config-section > form:not(.form-upload) > div > div > div > #router-type").change(async function () {
    await CTFd.api.patch_config_list({}, {
        'whale:router_type': $(this).val(),
        'whale:refresh': btoa(+new Date).slice(-7, -2),
    });
    location.reload();
});
