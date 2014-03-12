<%inherit file="base.mako" />
<h1>${'New' if is_new else 'Edit'} ${view.title}</h1>
<form method="POST" class="crud-edit">
    % for title, fieldset_info in form.fieldsets:
        <%include file="fieldset.mako" args="title=title, fieldset_info=fieldset_info" />
    % endfor
    % for inline, items in form.inline_fieldsets.values():
        <%include file="edit_inline/tabular.mako" args="inline=inline, items=items" />
    % endfor
    ${form.csrf_token}
    <div class="pull-right">
    <input type="submit" class="btn btn-primary" name="save_close" value="Save" />
    <input type="submit" class="btn btn-default" name="save" value="Save & Continue Editing" />
    <input type="submit" class="btn btn-default" name="save_new" value="Save & New" />
    <a href="${request.route_url(view.route_name('list'))}" class="btn btn-danger">Cancel</a>
    </div>
</form>
