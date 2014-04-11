<%inherit file="${context.get('view').get_template_for('base')}" />
<h1>${'New' if is_new else 'Edit'} ${view.Form.title}</h1>
<form method="POST" class="crud-edit">
    % for fieldset in form.get_fieldsets():
        <%include file="${context.get('view').get_template_for('fieldsets/%s' % fieldset['template'])}" args="fieldset=fieldset" />
    % endfor
    % for inline, items in form.inline_fieldsets.values():
        <%include file="${context.get('view').get_template_for('edit_inline/tabular')}" args="inline=inline, items=items" />
    % endfor
    ${form.csrf_token}
    <div class="pull-right">
    <input type="submit" class="btn btn-primary" name="save_close" value="Save" />
    <input type="submit" class="btn btn-default" name="save" value="Save & Continue Editing" />
    <input type="submit" class="btn btn-default" name="save_new" value="Save & New" />
    <a href="${request.route_url(view.routes['list'])}" class="btn btn-danger">Cancel</a>
    </div>
</form>
