#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
## Author: Adriano Monteiro Marques <adriano@umitproject.org>
## Author: Diogo Pinheiro <diogormpinheiro@gmail.com>
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

from django.shortcuts import render_to_response
from django.utils import simplejson as json
from django.http import HttpResponse, Http404
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404

from google.appengine.api import channel

import datetime, logging
from gui.forms import SuggestServiceForm, SuggestWebsiteForm, WebsiteEventForm, ServiceEventForm
from gui.decorators import cant_repeat_form
from geoip.models import Location
from suggestions.models import WebsiteSuggestion, ServiceSuggestion
from events.models import Event, TargetType, EventType
from reports.models import WebsiteReport
from notificationsystem.system import NotificationSystem
from filetransfers.api import serve_file


# Our current limit is 25. Let's play around with this and we'll figure if it is enough
SHOW_EVENT_LIMIT = 25

# View cache is set to 10 minutes now. We'll slowly decrease this with time to test
VIEW_CACHE_TIME = 60 * 10


def home(request):
    return map(request)


def map(request):
    token = channel.create_channel('map')
    
    # Our current limit 
    events = Event.get_active_events(SHOW_EVENT_LIMIT)
    events_dict = []
    for event in events:
        events_dict.append(event.get_dict())
    initialEvents = json.dumps(events_dict, use_decimal=True)
    return render_to_response('notificationsystem/map.html', {'token': token, 'initial_events': initialEvents})


def realtimebox(request):
    token = channel.create_channel('realtimebox')
    events = Event.get_active_events(SHOW_EVENT_LIMIT)
    events_dict = []
    for event in events:
        events_dict.append(event.get_dict())
    initialEvents = json.dumps(events_dict, use_decimal=True)
    return render_to_response('notificationsystem/realtimebox.html', {'token': token, 'initial_events': initialEvents})


def event(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        raise Http404
    eventDict = event.get_full_dict()
    locations = json.dumps(eventDict['locations'])
    blockingNodes = json.dumps(eventDict['blockingNodes'])

    return render_to_response('events/event.html', {'eventInfo': eventDict, 'locations': locations, 'blockingNodes': blockingNodes})



def about(request):
    user = request.user
    return render_to_response('gui/about.html', locals())


@cant_repeat_form(SuggestServiceForm, ['service_name', 'host_name', 'port', 'location'])
def suggest_service(request, form, valid, *args, **kwargs):
    if (form is not None) and valid:
        service_name = form.cleaned_data['service_name']
        host_name = form.cleaned_data['host_name']
        port = form.cleaned_data['port']
        location = Location.retrieve_location(form.cleaned_data['location'].split(', ')[0])
        
        suggestion = ServiceSuggestion()
        suggestion.service_name = service_name
        suggestion.host_name = host_name
        suggestion.port = port
        suggestion.location = location
        suggestion.user = request.user
        suggestion.save()
        
        return HttpResponse(json.dumps(dict(status='OK',
                   msg='Website suggestion added successfully! Make sure you \
subscribe to receive the site status once it is tested.',
                   errors=None)))
    elif (form is not None) and (not valid):
        return HttpResponse(json.dumps(dict(status='FAILED',
                   msg='Failed to add your suggestion. Please, make sure you \
provided all terms.',
                   errors=form.errors)))
    
    form = SuggestServiceForm()
    return render_to_response('gui/suggest_service.html', locals())


@cant_repeat_form(SuggestWebsiteForm, ['website', 'location'])
def suggest_website(request, form, valid, *args, **kwargs):
    if (form is not None) and valid:
        website = form.cleaned_data['website']
        location = Location.retrieve_location(form.cleaned_data['location'].split(', ')[0])
        
        suggestion = WebsiteSuggestion()
        suggestion.website_url = website
        suggestion.location = location
        #suggestion.user = request.user
        suggestion.save()
        
        return HttpResponse(json.dumps(dict(status='OK',
                   msg='Website suggestion added successfully! Make sure you \
subscribe to receive the site status once it is tested.',
                   errors=None)))
    elif (form is not None) and (not valid):
        return HttpResponse(json.dumps(dict(status='FAILED',
                msg='Failed to add your suggestion. Please, make sure you \
provided at least a valid website.',
                errors=form.errors)))
    
    form = SuggestWebsiteForm()
    return render_to_response('gui/suggest_website.html', locals())


def create_website_event(request):
    if request.method == 'POST':
        form = WebsiteEventForm(request.POST)
        if form.is_valid():
            website = form.cleaned_data['website']
            first_detection = form.cleaned_data['first_detection']
            event_type = form.cleaned_data['event_type']
            location = Location.retrieve_location(form.cleaned_data['location'].split(', ')[0])

            logging.info(location)

            event = Event()
            event.active = True
            if first_detection:
                event.first_detection_utc = first_detection
            else:
                event.first_detection_utc = datetime.datetime.now()
            event.last_detection_utc  = datetime.datetime.now()
            event.target = website
            event.target_type = TargetType.Website
            if event_type:
                # 'censor', 'throttling', 'offline'
                if event_type == 'censor':
                    event.event_type = EventType.Censor
                elif event_type == 'throttling':
                    event.event_type = EventType.Throttling
                else:
                    event.event_type = EventType.Offline
            else:
                event.event_type = EventType.Offline

            logging.info(location)

            if location!=None:
                event.location_ids.append(location.id)
                event.location_names.append(location.name)
                event.location_country_names.append(location.country_name)
                event.location_country_codes.append(location.country_code)
                event.lats.append(location.lat)
                event.lons.append(location.lon)
                event.isps.append('')

            event.save()
            NotificationSystem.publishEvent(event)

            return HttpResponse(json.dumps(dict(status='OK',
                       msg='Website event added successfully!',
                       errors=None)))
        else:
            return HttpResponse(json.dumps(dict(status='FAILED',
                    msg='Failed to add event.',
                    errors=form.errors)))
    
    form = WebsiteEventForm()
    return render_to_response('gui/create_website_event.html', locals())


def create_service_event(request):
    if request.method == 'POST':
        form = ServiceEventForm(request.POST)
        if form.is_valid():
            service = form.cleaned_data['service']
            first_detection = form.cleaned_data['first_detection']
            event_type = form.cleaned_data['event_type']
            location = Location.retrieve_location(form.cleaned_data['location'].split(', ')[0])

            event = Event()
            event.active = True
            if first_detection:
                event.first_detection_utc = first_detection
            else:
                event.first_detection_utc = datetime.datetime.now()
            event.last_detection_utc  = datetime.datetime.now()
            event.target = service
            event.target_type = TargetType.Service
            if event_type:
                # 'censor', 'throttling', 'offline'
                if event_type == 'censor':
                    event.event_type = EventType.Censor
                elif event_type == 'throttling':
                    event.event_type = EventType.Throttling
                else:
                    event.event_type = EventType.Offline
            else:
                event.event_type = EventType.Offline

            if location!=None:
                event.location_ids.append(location.id)
                event.location_names.append(location.name)
                event.location_country_names.append(location.country_name)
                event.location_country_codes.append(location.country_code)
                event.lats.append(location.lat)
                event.lons.append(location.lon)
                event.isps.append('')

            event.save()
            NotificationSystem.publishEvent(event)

            return HttpResponse(json.dumps(dict(status='OK',
                       msg='Website event added successfully!',
                       errors=None)))
        else:
            return HttpResponse(json.dumps(dict(status='FAILED',
                    msg='Failed to add event.',
                    errors=form.errors)))

    form = ServiceEventForm()
    return render_to_response('gui/create_service_event.html', locals())


def serve_media(request, id):
    upload = get_object_or_404(WebsiteReport, pk=id)
    return serve_file(request, upload.file)
