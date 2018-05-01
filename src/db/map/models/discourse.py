from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from db.config import BaseModel


class DiscourseUser(BaseModel):
    discourse_user_id = models.IntegerField(unique=True)
    discourse_external_id = models.TextField(db_index=True)
    email = models.EmailField(db_index=True)
    body = JSONField()

    @classmethod
    def save_from_webhook(cls, body):
        user = body['user']
        instance = cls.objects.filter(discourse_user_id=user['id']).first()
        if instance is None:
            instance = cls()
        instance.discourse_user_id = user['id']
        instance.discourse_external_id = user['external_id']
        instance.email = user['email']
        instance.body = body
        instance.save()


class DiscoursePostEvent(BaseModel):
    discourse_user_id = models.IntegerField(db_index=True)
    event = models.TextField(blank=True, db_index=True, help_text='X-Discourse-Event request header')
    body = JSONField()

    @classmethod
    def save_from_webhook(cls, body, event=''):
        post = body['post']
        instance = cls()
        instance.discourse_user_id = post['user_id']
        instance.body = body
        instance.event = event
        instance.save()


class DiscourseTopicEvent(BaseModel):
    event = models.TextField(blank=True, db_index=True, help_text='X-Discourse-Event request header')
    body = JSONField()

    @classmethod
    def save_from_webhook(cls, body, event=''):
        instance = cls()
        instance.body = body
        instance.event = event
        instance.save()
