<%inherit file="base.mako" />
<%block name="head">
    <script src="${request.static_url('pyramid_crud:static/list.js')}"></script>
</%block>
<%block name="heading">
    <h1>${view.Form.title_plural}</h1>
</%block>
<a href="${request.route_url(view.routes['new'])}" class="btn btn-primary pull-right">New</a>
<form method="POST" class="form-inline">
    <div class="form-group">
        ${action_form.action(class_='form-control')}
        ${action_form.submit(class_='form-control')}
    </div>
    <table class="table table-striped">
        <thead>
            <tr>
                <th></th>
                % for col_info in view.iter_head_cols():
                    <th class="${col_info["css_class"]}">
                        ${col_info["label"]}
                    </th>
                % endfor
            </tr>
        </thead>
        <tbody>
                % for item, checkbox in zip(items, action_form.items):
                    <tr>
                        <td>
                            ${checkbox()}
                        </td>
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
                    </tr>
                % endfor
        </tbody>
    </table>
    ${action_form.csrf_token}
</form>
