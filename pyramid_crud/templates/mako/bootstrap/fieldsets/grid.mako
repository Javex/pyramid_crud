<%page args="fieldset"/>
<fieldset>
    % if fieldset["title"]:
        <legend>${fieldset["title"]}</legend>
    % endif
    % for field in fieldset["fields"]:
        <div class="pull-left col-md-2 form-group">
            ${field()} ${field.label()}
        </div>
    % endfor
</fieldset>
