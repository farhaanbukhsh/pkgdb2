# -*- coding: utf-8 -*-
#
# Copyright © 2013  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

'''
pkgdb tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

from datetime import date
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from pkgdb.lib import model

DB_PATH = 'sqlite:///:memory:'


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        self.session = model.create_tables(DB_PATH)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)

        self.session.rollback()

        ## Empty the database if it's not a sqlite
        if self.session.bind.driver != 'pysqlite':
            self.session.execute('DROP TABLE "GroupPackageListingAcl" CASCADE;')
            self.session.execute('DROP TABLE "GroupPackageListing" CASCADE;')
            self.session.execute('DROP TABLE "PersonPackageListingAcl" CASCADE;')
            self.session.execute('DROP TABLE "PersonPackageListing" CASCADE;')
            self.session.execute('DROP TABLE "PackageListing" CASCADE;')
            self.session.execute('DROP TABLE "Collection" CASCADE;')
            self.session.execute('DROP TABLE "Package" CASCADE;')
            self.session.execute('DROP TABLE "Log" CASCADE;')
            self.session.commit()


def create_collection(session):
    """ Create some basic collection for testing. """
    collection = model.Collection(
                                  name = 'Fedora',
                                  version = '18',
                                  status = 'Active',
                                  owner = 10,
                                  publishurltemplate=None,
                                  pendingurltemplate=None,
                                  summary='Fedora 18 release',
                                  description=None,
                                  branchname='F18',
                                  distTag='.fc18',
                                  git_branch_name='f18',
                                  )
    session.add(collection)

    collection = model.Collection(
                                  name = 'Fedora',
                                  version = 'devel',
                                  status = 'Under Development',
                                  owner = 11,
                                  publishurltemplate=None,
                                  pendingurltemplate=None,
                                  summary='Fedora rawhide',
                                  description=None,
                                  branchname='devel',
                                  distTag='.fc19',
                                  git_branch_name='master',
                                  )
    session.add(collection)
    session.commit()


def create_package(session):
    """ Create some basic package for testing. """
    package = model.Package(name = 'Guake',
                            summary = 'Top down terminal for GNOME',
                            status = 'Approved',
                            review_url='https://bugzilla.redhat.com/450189',
                            shouldopen=None,
                            upstream_url='http://guake.org'
                            )
    session.add(package)

    package = model.Package(name = 'fedocal',
                            summary = 'A web-based calendar for Fedora',
                            status = 'Approved',
                            review_url='https://bugzilla.redhat.com/915074',
                            shouldopen=None,
                            upstream_url='http://fedorahosted.org/fedocal'
                            )
    session.add(package)

    package = model.Package(name = 'geany',
                            summary = 'A fast and lightweight IDE using GTK2',
                            status = 'Approved',
                            review_url=None,
                            shouldopen=None,
                            upstream_url=None
                            )
    session.add(package)

    session.commit()


def create_package_listing(session):
    """ Add some package to a some collection. """
    create_collection(session)
    create_package(session)

    guake_pkg = model.Package.by_name(session, 'Guake')
    fedocal_pkg = model.Package.by_name(session, 'fedocal')
    f18_collec = model.Collection.by_simple_name(session, 'F18')
    devel_collec = model.Collection.by_simple_name(session, 'devel')

    # Pkg: Guake - Collection: F18 - Approved
    pkgltg = model.PackageListing(owner=10,
                                  status='Approved',
                                  packageid=guake_pkg.id,
                                  collectionid=f18_collec.id,
                                  qacontact=None,
                                  )
    session.add(pkgltg)
    # Pkg: Guake - Collection: devel - Approved
    pkgltg = model.PackageListing(owner=10,
                                  status='Approved',
                                  packageid=guake_pkg.id,
                                  collectionid=devel_collec.id,
                                  qacontact=None,
                                  )
    session.add(pkgltg)
    # Pkg: fedocal - Collection: F18 - Orphaned
    pkgltg = model.PackageListing(owner=10,
                                  status='Orphaned',
                                  packageid=fedocal_pkg.id,
                                  collectionid=f18_collec.id,
                                  qacontact=None,
                                  )
    session.add(pkgltg)
    # Pkg: fedocal - Collection: devel - Deprecated
    pkgltg = model.PackageListing(owner=10,
                                  status='Deprecated',
                                  packageid=fedocal_pkg.id,
                                  collectionid=devel_collec.id,
                                  qacontact=None,
                                  )
    session.add(pkgltg)
    session.commit()


def create_person_package(session):
    """ Add packagers to packages. """
    create_package_listing(session)

    guake_pkg = model.Package.by_name(session, 'Guake')
    fedocal_pkg = model.Package.by_name(session, 'fedocal')
    f18_collec = model.Collection.by_simple_name(session, 'F18')
    devel_collec = model.Collection.by_simple_name(session, 'devel')
    pklist_guake_f18 = model.PackageListing.by_pkgid_collectionid(
        session, guake_pkg.id, f18_collec.id)
    pklist_guake_devel = model.PackageListing.by_pkgid_collectionid(
        session, guake_pkg.id, devel_collec.id)

    packager = model.PersonPackageListing(user_id = 10,
                                          packagelisting_id=pklist_guake_f18.id
                                          )
    session.add(packager)
    packager = model.PersonPackageListing(user_id = 20,
                                          packagelisting_id=pklist_guake_devel.id
                                          )
    session.add(packager)
    session.commit()


def create_person_package_acl(session):
    """ Add ACLs of a packagr on a package. """
    create_person_package(session)

    guake_pkg = model.Package.by_name(session, 'Guake')

    pkglist = model.PersonPackageListing.by_userid_pkglistid(session, 10,
    guake_pkg.id)

    packager = model.PersonPackageListingAcl(acl='commit',
                                             status='Approved',
                                             personpackagelistingid=pkglist.id
                                             )

    session.add(packager)
    session.commit()


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)