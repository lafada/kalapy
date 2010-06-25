from difflib import unified_diff

from werkzeug.urls import url_quote_plus

from kalapy import db
from kalapy import web
from kalapy.web import request

from models import Page, Revision, Pagination


@web.route('/', defaults={'page': 'Main_Page'})
def home(page):
    return web.redirect(web.url_for('show', name=page))

@web.route('/<name>')
def show(name):
    revision = request.args.get('rev')
    if revision:
        revision = Page.by_revision(revision)
        revision_requested = True
    else:
        revision = Page.by_name(name)
        revision_requested = False
    if revision is None:
        return (web.render_template('missing.html',
                revision_requested=revision_requested,
                page_name=name,
                protected=False), 404)
    return web.render_template('show.html', revision=revision)

@web.route('/<name>/edit')
def edit(name):
    note = error = ''
    revision = Page.by_name(name)

    return web.render_template('edit.html',
        new=revision is None,
        revision=revision,
        page_name=name,
        note=note,
        error=error)

@web.route('/<name>', methods=('POST',))
def save(name):

    revision = Page.by_name(name)
    text = request.form.get('text')

    if request.form.get('cancel') or \
        revision and revision.text == text:
        return web.redirect(web.url_for('show', name=name))
    elif not text:
        error = 'You cannot save empty revisions.'
    else:
        note = request.form.get('note', '')
        page = revision.page if revision else Page(name=name)
        revision = Revision(text=text, page=page)
        revision.save()
        db.commit()

    return web.redirect(web.url_for('show', name=name))

@web.route('/<name>/log')
def log(name):
    """Show the list of recent changes."""
    revision = Page.by_name(name)
    if revision is None:
        return show(name)
    revisions = revision.page.revisions.all().order('-timestamp').fetch(-1)
    return web.render_template('log.html', revision=revision, revisions=revisions)

@web.route('/<name>/diff')
def diff(name):

    old = request.args.get('old')
    new = request.args.get('new')

    try:
        old = int(old)
        new = int(new)
    except:
        pass

    error = ''
    diff = page = old_rev = new_rev = None

    if not (old and new):
        error = 'No revisions specified.'
    else:
        revision = Page.by_name(name)
        revisions = dict([(rev.key, rev) for rev in revision.page.revisions \
            .all().filter('key in', [old, new]).fetch(-1)])

        if len(revisions) != 2:
            error = 'At least one of the revisions requested ' \
                    'does not exist.'
        else:
            new_rev = revisions[new]
            old_rev = revisions[old]
            page = old_rev.page
            diff = unified_diff(
                (old_rev.text + '\n').splitlines(True),
                (new_rev.text + '\n').splitlines(True),
                page.name, page.name,
                old_rev.time,
                new_rev.time,
                3
            )
    return web.render_template('diff.html',
        error=error,
        old_revision=old_rev,
        new_revision=new_rev,
        page=page,
        revision=page,
        diff=diff
    )

@web.route('/<name>/revert', methods=('GET', 'POST',))
def revert(name):
    """Revert an old revision."""
    rev_id = request.args.get('rev')
    try:
        rev_id = int(rev_id)
    except:
        pass

    old_revision = page = None
    error = 'No such revision'

    if request.method == 'POST' and request.form.get('cancel'):
        return web.redirect(web.url_for('show', name=page_name))

    if rev_id:
        old_revision = Page.by_revision(rev_id)
        if old_revision:
            new_revision = Page.by_name(name)
            if old_revision == new_revision:
                error = 'You tried to revert the current active ' \
                        'revision.'
            elif old_revision.text == new_revision.text:
                error = 'There are no changes between the current ' \
                        'revision and the revision you want to ' \
                        'restore.'
            else:
                error = ''
                page = old_revision.page
                if request.method == 'POST':
                    note = request.form.get('note', '')
                    note = 'revert' + (note and ': ' + note or '')
                    revision = Revision(page=page, text=old_revision.text,
                                         note=note)
                    revision.save()
                    db.commit()
                    return web.redirect(web.url_for('show', name=name))

    return web.render_template('revert.html',
        error=error,
        old_revision=old_revision,
        revision=page
    )

@web.route('/' + url_quote_plus('Spacial:Index'))
def index():
    letters = {}
    for page in Page.all().order('-name').fetch(-1):
        letters.setdefault(page.name.capitalize()[0], []).append(page)
    return web.render_template('index.html', letters=sorted(letters.items()))

@web.route('/' + url_quote_plus('Spacial:Recent_Changes'))
def changes():
    page = max(1, request.args.get('page', type=int))
    query = Revision.all().order('-timestamp')
    return web.render_template('changes.html',
        pagination=Pagination(query, 20, page, 'changes'))

