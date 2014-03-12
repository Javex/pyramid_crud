<%inherit file="base.mako" />
<%!
    import sqlalchemy as sa
%>
<h1>${view.title_plural}</h1>
% if request.session.peek_flash():
    <ul>
        % for msg in request.session.pop_flash():
            <li>${msg}</li>
        % endfor
    </ul>
% endif
<a href="${request.route_url(view.route_name('new'))}" class="btn btn-primary pull-right">New</a>
<table class="table">
    <thead>
        <tr>
            % for col in [getattr(view.form.Meta.model, c) for c in view.list_display]:
                <th class="${'text-center' if isinstance(col.type, sa.types.Boolean) else ''}">
                    ${col.info["label"]}
                </th>
            % endfor
            <th>Delete</th>
        </tr>
    </thead>
    <tbody>
            % for item in items:
                <tr>
                    % for col in [getattr(item, c) for c in view.list_display]:
                        % if col is True or col is False:
                            <td class="text-${'success' if col else 'danger'} text-center">
                        % else:
                            <td>
                        % endif
                            % if loop.first:
                                <a href="${view._edit_route(item)}">
                                    ${col}
                                </a>
                            % else:
                                % if col is True or col is False:
                                    ${'Yes' if col else 'No'}
                                % else:
                                    ${col}
                                % endif
                            % endif
                        </td>
                    % endfor
                    <td>
                        <form method="POST" action="${view._delete_route(item)}">
                            ${view.delete_form.button()}
                            ${view.delete_form.csrf_token}
                        </form>
                    </td>
                </tr>
            % endfor
    </tbody>
</table>
