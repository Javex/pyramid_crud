<%page args="inline, items" />
<input type="hidden" name="${inline.name}_count" value="${len(items)}" />
<fieldset>
    <legend>${inline.title_plural}</legend>
    <table class="table">
        <thead>
            <tr>
            % for field in inline():
                <th>${field.label.text}</th>
            % endfor
                <th>Delete?</th>
            </tr>
        </thead>
        <tbody>
            % for form, is_extra in items:
            <tr>
                <td style="display:none">
				% if form.obj:
					% for name, value in form.primary_keys:
						<input type="hidden" name="${inline.name}_${loop.index}_${name}" value="${value or ''}" />
					% endfor
				% endif
                </td>
                % for field in form:
                <td>
                    ${field()}
                </td>
                % endfor
                <td>
                    <input type="submit"
                        name="delete_${inline.name}_${loop.index}"
                        value="Delete"
                        class="btn btn-default"
                        formnovalidate />
                </td>
            </tr>
        % endfor
            <tr>
                <td colspan="${len(list(inline())) + 1}">
                    <input type="submit" 
                        name="add_${inline.name}" 
                        value="Add another ${inline.title}" 
                        class="btn btn-default"
                        formnovalidate />
                </td>
            </tr>
        </tbody>
    </table>
</fieldset>
