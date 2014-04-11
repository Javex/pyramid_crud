<%page args="fieldset"/>
<fieldset>
	% if fieldset["title"]:
		<legend>${fieldset["title"]}</legend>
    % endif
    % for field in map(lambda f: getattr(form, f), fieldset['fields']):
        % if field.widget.input_type == 'hidden':
            ${field()}
        % else:
            ${field.label()}: ${field()}<br />
            % if field.errors:
                <ul>
                    % for msg in field.errors:
                        <li>${msg}</li>
                    % endfor
                </ul>
            % endif
        % endif
    % endfor
</fieldset>
