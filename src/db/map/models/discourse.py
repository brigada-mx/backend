from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from db.config import BaseModel


class DiscourseUser(BaseModel):
    discourse_user_id = models.IntegerField(unique=True)
    email = models.EmailField(unique=True, help_text='Same as Discourse `external_id`')
    body = JSONField()

    @classmethod
    def save_from_webhook(cls, body):
        user = body['user']
        instance = cls.objects.filter(discourse_user_id=user['id']).first()
        if instance is None:
            instance = cls()
        instance.discourse_user_id = user['id']
        instance.email = user.get('email') or user.get('external_id')
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
    discourse_user_id = models.IntegerField(db_index=True)
    event = models.TextField(blank=True, db_index=True, help_text='X-Discourse-Event request header')
    body = JSONField()

    @classmethod
    def save_from_webhook(cls, body, event=''):
        topic = body['topic']
        instance = cls()
        instance.discourse_user_id = topic['user_id']
        instance.body = body
        instance.event = event
        instance.save()
