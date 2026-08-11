# -*-coding:utf-8-*-
import os
import random
import shutil
import time

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django_apscheduler.jobstores import DjangoJobStore, register_job, register_events

from word.models import Word
from website.models import Website


class HinghwaBackgroundScheduler(BackgroundScheduler):
    def _process_jobs(self):
        while True:
            try:
                return super()._process_jobs()
            except Exception as e:
                print(f"Error processing jobs: {e}")
                time.sleep(5)


def random_word_of_the_day():
    all = Word.objects.all()
    item = Website.objects.get(id=1)
    item.word_of_the_day = random.choice(all).id
    item.save()
    print("update word of the day at 0:00")


def clear_audio_buffer():
    shutil.rmtree(os.path.join(settings.MEDIA_ROOT, "audio", "public"))
    print("remove the audio buffer in public files")


def register(fun, id, replace_existing):
    scheduler = HinghwaBackgroundScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(DjangoJobStore(), "default")
    register_job(scheduler, "cron", id=id, hour=0, replace_existing=replace_existing)(
        fun
    )
    scheduler.start()


try:
    try:
        register(random_word_of_the_day, "random_word_of_the_day", False)
        register(clear_audio_buffer, "clear_audio_buffer", False)
    except Exception:
        register(random_word_of_the_day, "random_word_of_the_day", True)
        register(clear_audio_buffer, "clear_audio_buffer", True)
except Exception as e:
    print(str(e))
