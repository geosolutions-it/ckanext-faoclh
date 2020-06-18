import logging

from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, types

from ckan.model import Session, meta
from ckan.model.domain_object import DomainObject

log = logging.getLogger(__name__)

__all__ = ['TagImageUrl', 'tag_image_url']

tag_image_url = Table('tag_image_url', meta.metadata,
                      Column('id', types.Integer, primary_key=True),
                      Column('tag_id', types.UnicodeText, ForeignKey("tag.id", ondelete="CASCADE"), nullable=False,
                             unique=True),
                      Column('vocabulary', types.UnicodeText,
                             nullable=False, index=True),
                      Column('tag_name', types.UnicodeText,
                             nullable=False, index=True),
                      Column('image_url', types.UnicodeText,
                             nullable=True, index=True),
                      UniqueConstraint('vocabulary', 'tag_name',
                                       name='vocab_tag_name')
                      )


def setup():
    log.debug('Setting up FAO-CLH tag_image_url table')

    if not tag_image_url.exists():
        try:
            tag_image_url.create()
        except Exception, e:
            # Make sure the table does not remain incorrectly created
            if tag_image_url.exists():
                Session.execute('DROP TABLE tag_image_url')
                Session.commit()

            raise e

        log.info('tag_image_url table created')
    else:
        log.info('tag_image_url already exist')


class TagImageUrl(DomainObject):
    def __init__(self, tag_id=None, image_url=None, vocabulary=None, tag_name=None):
        self.tag_id = tag_id
        self.image_url = image_url
        self.vocabulary = vocabulary
        self.tag_name = tag_name

    @classmethod
    def get(cls, vocabulary, tag_name):
        session = meta.Session
        image_url = session.query(TagImageUrl.image_url).filter(
            TagImageUrl.vocabulary == vocabulary, TagImageUrl.tag_name == tag_name).first()
        if image_url:
            return image_url[0]

    @classmethod
    def get_tag_image_url(cls, tag_id):
        session = meta.Session
        image_url = session.query(TagImageUrl.image_url).filter(
            TagImageUrl.tag_id == tag_id).first()
        if image_url:
            return image_url[0]

    @classmethod
    def update(cls, tag_id, vocabulary, tag_name, image_url):
        session = meta.Session
        obj = session.query(TagImageUrl).filter(
            TagImageUrl.tag_id == tag_id).first()
        obj.image_url = image_url
        obj.vocabulary = vocabulary
        obj.tag_name = tag_name
        session.commit()

    @classmethod
    def persist(cls, tag_id, vocabulary, tag_name, image_url):
        session = meta.Session
        try:
            session.add_all([
                TagImageUrl(tag_id=tag_id, image_url=image_url,
                            vocabulary=vocabulary, tag_name=tag_name),
            ])

            session.commit()
        except Exception, e:
            # on rollback, the same closure of state
            # as that of commit proceeds.
            session.rollback()

            log.error('Exception occurred while persisting DB objects: %s', e)
            raise


meta.mapper(TagImageUrl, tag_image_url)
