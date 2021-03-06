#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
## Author: Adriano Monteiro Marques <adriano@umitproject.org>
##
## Copyright (C) 2011 S2S Network Consultoria e Tecnologia da Informacao LTDA
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url('^$', 'gui.views.home', name='home'),
    url('^about/?$', 'gui.views.about', name='about'),
    url('^suggest_service/?$', 'gui.views.suggest_service', name='suggest_service'),
    url('^suggest_website/?$', 'gui.views.suggest_website', name='suggest_website'),
    url('^wsrdata/(?P<id>\d+)/?$', 'gui.views.serve_media', name='serve_media'),
    url('^create_website_event/?$', 'gui.views.create_website_event', name='create_website_event'),
    url('^create_service_event/?$', 'gui.views.create_service_event', name='create_service_event'),
)