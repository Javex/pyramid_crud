<%inherit file="base.mako" />
<%block name="heading">
    <h1>Delete ${view.Form.title_plural}</h1>
</%block>
Are you sure you want to delete the following items?
<ul>
    % for item in items:
        <li>${item}</li>
    % endfor
</ul>
<form method="POST">
    ${form.csrf_token}
    ${form.action}
    % for field in form.items:
        ${field}
    % endfor
    ${form.confirm_delete(class_='btn btn-primary')}
    <a href="${request.route_url(view.routes['list'])}" class="btn btn-danger">Cancel</a>
</form>
