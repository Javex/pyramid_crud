<%inherit file="base.mako" />
<%!
    import sqlalchemy as sa
%>
<h1>${view.Form.title_plural}</h1>
<a href="${request.route_url(view.routes['new'])}" class="btn btn-primary pull-right">New</a>
<table class="table">
    <thead>
        <tr>
            % for col_info in view.iter_head_cols():
                <th class="${col_info["css_class"]}">
                    ${col_info["label"]}
                </th>
            % endfor
            <th>Delete</th>
        </tr>
    </thead>
    <tbody>
            % for item in items:
                <tr>
                    % for title, col in view.iter_list_cols(item):
                        % if col is True or col is False:
                            <td class="text-${'success' if col else 'danger'} text-center">
                        % else:
                            <td>
                        % endif
                            % if title in getattr(view, 'list_display_links', []) or not hasattr(view, 'list_display_links') and loop.first:
                                <a href="${view._edit_route(item)}">
                                    % if col is True:
                                        Yes
                                    % elif col is False:
                                        No
                                    % else:
                                        ${col}
                                    % endif
                                </a>
                            % else:
                                % if col is True:
                                    Yes
                                % elif col is False:
                                    No
                                % else:
                                    ${col}
                                % endif
                            % endif
                        </td>
                    % endfor
                    <td>
                        <form method="POST" action="${view._delete_route(item)}">
                            ${view.delete_form().button()}
                            ${view.delete_form().csrf_token}
                        </form>
                    </td>
                </tr>
            % endfor
    </tbody>
</table>
