from django.db import models
from django.utils import simplejson

eventType = ["Censor", "Throttling", "Offline"]
targetType = ["Website", "Service"]

class EventType:
    Censor, Throttling, Offline = range(3)

    @staticmethod
    def getEventType(id):
        if id==EventType.Censor:
            return "Censor"
        elif id==EventType.Throttling:
            return "Throttling"
        elif id==EventType.Offline:
            return "Offline"
        else:
            return "Unknown"

class TargetType:
    Website, Service = range(2)

    @staticmethod
    def getTargetType(id):
        if id==TargetType.Website:
            return "Website"
        elif id==TargetType.Service:
            return "Service"
        else:
            return "Unknown"
    

class Event(models.Model):
    targetType        = models.PositiveSmallIntegerField()
    eventType         = models.PositiveSmallIntegerField()
    firstDetectionUTC = models.DateTimeField()
    lastDetectionUTC  = models.DateTimeField()
    target            = models.TextField()
    active            = models.BooleanField()    # indicate if the event is still happening

    @staticmethod
    def getActiveEvents(limit=0):
        #return self.activated==True
        # TODO: order by firstDetection or lastDetection ?
        query = Event.objects.filter(active=True)#.order_by(lastDetectionUTC)
        if limit>0:
            query = query[:limit]
        return query

    # TODO: more search methods:
    #   search by location (should be the name of place or coordinates ?
    #   search by isp ?
    #   search events for specific website
    #   search events for specific services
    #   search old events too, limited by dates

    # get all the active events, in a location, and for a specific website/service
    #@staticmethod
    #def getActiveEvents(location, target):
    #    pass


    #def __unicode__(self):
    #    return u'%s %s %s' % (self.targetType, self.eventType, self.firstDetectionUTC)

    #def __str__(self):
    #    return '%s %s %s' % (self.targetType, self.eventType, self.firstDetectionUTC)

    def getDict(self):

        locations = []
        for location in self.eventlocation_set.all():
            locations.append({'city': location.city, 'country': location.country, 'lat': location.latitude, 'lng': location.longitude})

        event = {
          'url': "/events/" + str(self.id),
          'targetType': TargetType.getTargetType(self.targetType),
          'target': self.target,
          'type': EventType.getEventType(self.eventType),
          'firstdetection': self.firstDetectionUTC.ctime(),
          'lastdetection': self.lastDetectionUTC.ctime(),
          'active': self.active,
          'locations': locations
        }
        return event


class EventLocation(models.Model):
    event    = models.ForeignKey('Event')
    city     = models.CharField(max_length=100)
    country  = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude= models.FloatField()


class EventISP(models.Model):
    event = models.ForeignKey('Event')
    isp   = models.CharField(max_length=100)


class EventWebsiteReport(models.Model):
    event  = models.ForeignKey('Event')
    report = models.ForeignKey('reports.WebsiteReport')


class EventServiceReport(models.Model):
    event  = models.ForeignKey('Event')
    report = models.ForeignKey('reports.WebsiteReport')