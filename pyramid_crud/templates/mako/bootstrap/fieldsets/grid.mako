<%page args="fieldset"/>
<fieldset>
    % if fieldset["title"]:
        <legend>${fieldset["title"]}</legend>
    % endif
    % if any([field.errors for field in fieldset["fields"]]):
        <div class="alert alert-danger">
            % for field, msg in [(field, msg) for field in fieldset["fields"] for msg in field.errors]:
                <b>${field.label.text}:</b> ${msg}
                % if not loop.last:
                    <br />
                % endif
            % endfor
        </div>
    % endif
    % for field in fieldset["fields"]:
        <div class="pull-left col-md-2 form-group ${'has-error' if field.errors else ''}">
            ${field()} ${field.label(class_='control-label')}
        </div>
    % endfor
</fieldset>
