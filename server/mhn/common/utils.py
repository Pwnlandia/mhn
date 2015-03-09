from math import ceil

from flask import jsonify, g, current_app

from mhn.constants import PAGE_SIZE, ALLOWED_ADDON_EXTENSIONS

from ConfigParser import SafeConfigParser

import os

import mhn.api.errors as apierrors


def get_addons():
    addons_basedir = os.path.join(os.getcwd(), "mhn/addons/")
    addons_dirs = next(os.walk(addons_basedir))[1]
    add_ons = []
    parser = SafeConfigParser()
    for dirname in addons_dirs:
        if dirname not in current_app.config['DISABLED_ADDONS']:
            parser.read(os.path.join(addons_basedir, dirname, 'addon.cfg'))
            add_ons.append((dirname, parser.get('config', 'menu').replace('\'', '')))
    return add_ons


def allowed_addon_filename(filename):
    """
    Function to check if the nam of the file to upload is valid
    :return:
    return a tuple (Boolean, Error_Text, Error_Status)
    True: If the filename follows a pattern [name_of_the_file_without_spaces].allowed_extension, Error is empty
    False: Pattern is no correct, Error send
    """
    extensions = filename.split(".")
    if len(extensions) > 2:
        extension = extensions[1]
        for subext in extensions[2:]:
            extension = extension + "." + subext
    else:
        extension = extensions[1]

    if (len(extensions) != 3) or (len(extensions[0].split(" ")) !=1):
        return (False, apierrors.API_ADDON_NAME_INVALID.format(filename), 400)
    elif extension not in ALLOWED_ADDON_EXTENSIONS:
        return (False, apierrors.API_ADDON_EXTENSION_INVALID, 400)

    return (True, '', '')


def error_response(message, status_code=400):
    resp = jsonify({'error': message})
    resp.status_code = status_code
    return resp


def alchemy_pages(query, **kwargs):
    page = kwargs.get('page', g.page)
    page_size = kwargs.get('limit', PAGE_SIZE)
    items = query.\
            offset((page - 1) * page_size).\
            limit(page_size)
    return Pagination(page, page_size, query.count(), items)


def mongo_pages(result, total, **kwargs):
    page_size = kwargs.get('limit', PAGE_SIZE)
    return Pagination(g.page, page_size, total, result)


def paginate_options(**kwargs):
    page = kwargs.get('page', g.page)
    page_size = kwargs.get('limit', PAGE_SIZE)
    return dict(skip=(page - 1) * page_size, limit=page_size)


class Pagination(object):
    """
    This Pagination class will work with both SQLAlchemy
    objects and Clio objects.
    Taken and stripped from Flask-SQLAlchemy"""

    def __init__(self, page, per_page, total, items):
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    @property
    def prev_num(self):
        """Number of the previous page."""
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
