from datetime import date, datetime
from website import app
from flask import Blueprint, render_template, session, redirect, url_for, \
        request, abort
from flask_flatpages import FlatPages
from random import sample
import os

mod = Blueprint('pages', __name__)
pages = FlatPages(app)

def get_pages(pages, offset=None, limit=None, section=None, year=None, before=None, after=None):
  """ Retrieves pages that match specific criteria
  """
  things = list(pages)
  # Assign section if one is not set in the page
  for thing in things:
    if not thing.meta.get('section'):
      thing.meta['section'] = thing.path.split('/')[0]
  # filter unpublished
  if not app.debug:
    things = [p for p in things if p.meta.get('published') is True]
  # filter section
  if section:
    things = [p for p in things if p.meta.get('section') == section]
  # filter year
  if year:
    things = [p for p in things if p.meta.get('date').year == year]
  if before:
    things = [p for p in things if p.meta.get('date') < before]
  if after:
    things = [p for p in things if p.meta.get('date') > after]
  # sort what's left by date
  things = sorted(things, reverse=True, key=lambda p: p.meta.get('date', date.today()))
  # assign prev/next in series
  for i, thing in enumerate(things):
    if i != 0:
      if section and things[i - 1].meta.get('section') == section:
        thing.next = things[i - 1]
    if i != len(things) - 1:
      if section and things[i +1].meta.get('section') == section:
        thing.prev = things[i +1]
  # offset and limit
  if offset and limit:
    return things[offset:limit]
  elif limit:
    return things[:limit]
  elif offset:
    return things[offset:]
  else:
    return things
  
def get_years(pages):
  years = list(set([page.meta.get('date').year for page in pages]))
  years.reverse()
  return years

def section_exists(section):
  return not len(get_pages(pages, section=section)) == 0

@mod.route('/<path:path>/')
def page(path):
  section = path.split('/')[0]
  page = pages.get_or_404(path)
  # ensure an accurate "section" meta is available
  page.meta['section'] = page.meta.get('section', section)
  # show all pages in debug, but hide unpublished in production
  if not app.debug and not page.meta.get('published', False):
    abort(404)
  template = page.meta.get('template', '%s/page.html' % section)
  rtn_images = []
  if os.path.isdir(os.path.join(app.static_folder, 'images', path)):
    raw_images = os.listdir(os.path.join(app.static_folder, 'images', path))
    if len(raw_images) > 3:
      choices = sample(raw_images, 3)
    else:
      choices = raw_images
    for raw_image in choices:
      # Flask-Images already knows to look in the static folder, so only include the rest
      rtn_images.append(os.path.join('images', path, raw_image))
  return render_template(template, page=page, section=section, images=rtn_images)

@mod.route('/<string:section>/')
def section(section):
  if not section_exists(section):
    abort(404)
  template = '%s/index.html' % section
  things = get_pages(pages, limit=app.config['SECTION_MAX_LINKS'], section=section)
  years = get_years(get_pages(pages, section=section))
  return render_template(template, pages=things, section=section, years=years)

@mod.route('/<string:section>/upcoming/')
def section_upcoming(section):
  if not section_exists(section):
    abort(404)
  template = '%s/upcoming.html' % section
  things = get_pages(pages, section=section, after=date.today())
  years = get_years(get_pages(pages, section=section))
  return render_template(template, pages=things, section=section, years=years)

@mod.route('/<string:section>/past/')
def section_past(section):
  if not section_exists(section):
    abort(404)
  template = '%s/past.html' % section
  things = get_pages(pages, section=section, before=date.today())
  years = get_years(get_pages(pages, section=section))
  return render_template(template, pages=things, section=section, years=years)

@mod.route('/<string:section>/<int:year>/')
def section_archives_year(section, year):
  if not section_exists(section):
    abort(404)
  template = '%s/archives.html' % section
  years = get_years(get_pages(pages, section=section))
  things = get_pages(pages, section=section, year=year)
  return render_template(template, pages=things, section=section, years=years, year=year)

@mod.route('/')
def all_pages():
  template = 'general/index.html'
  things = get_pages(pages, limit=app.config['SECTION_MAX_LINKS'])
  years = get_years(get_pages(pages))
  return render_template(template, pages=things, years=years)
