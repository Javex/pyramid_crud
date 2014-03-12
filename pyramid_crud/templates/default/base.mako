<!DOCTYPE html>
<html lang="en">
    <head>
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">
        <link rel="stylesheet" href="/static/style.css">
        <script src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>${view.title_plural} | CRUD</title>
    </head>
    <body style="margin:0 20px">
    % for msg in request.session.pop_flash('error'):
        <div class="alert alert-danger">${msg}</div>
    % endfor
    % for msg in request.session.pop_flash('warning'):
        <div class="alert alert-warning">${msg}</div>
    % endfor
    % for msg in request.session.pop_flash('info'):
        <div class="alert alert-info">${msg}</div>
    % endfor
    % for msg in request.session.pop_flash():
        <div class="alert alert-success">${msg}</div>
    % endfor
        ${self.body()}
    </body>
</html>
