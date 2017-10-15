import logging
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, Text
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import date, datetime
import sys

import logging

logger = logging.getLogger(__name__)


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def input_int(msg):
    while True:
        i = input(msg)
        if is_int(i) and int(i) >= 0:
            return i
        elif i == 'q':
            return None
        else:
            print('Invalid input, please try again')


class Series(Base):
    __tablename__ = 'series'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)

    def __repr__(self):
        return 'Series[Id={}, Name={}]'.format(self.id, self.name)


class CandidateEpisode(Base):
    __tablename__ = 'candidate_episode'

    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    description = Column(Text)
    air_date = Column(Date)
    season = Column(Integer)
    episode_num = Column(Integer)
    series_id = Column(Integer, ForeignKey('series.id'))
    series = relationship('Series')

    wtv_file_id = Column(Integer, ForeignKey('wtv_file.filename'))
    wtv_file = relationship('WtvFile', back_populates='candidate_episodes')

    def get_details(self):
        padded_season = str(self.season) if self.season >= 10 else '0' + str(self.season)
        padded_episode_num = str(self.episode_num) if self.episode_num >= 10 else '0' + str(self.episode_num)
        return '{} - s{}e{} - {}'.format(self.series.name, padded_season, padded_episode_num, self.name)

    def __repr__(self):
        return 'Episode[id={}, series={}, name={}, air_date={}, season={}, num={}]'.format(self.id, self.series.name,
                                                                                           self.name, self.air_date,
                                                                                           self.season,
                                                                                           self.episode_num)


class WtvFile(Base):
    __tablename__ = 'wtv_file'

    filename = Column(String(256), primary_key=True)
    description = Column(Text)
    series_id = Column(Integer, ForeignKey('series.id'))
    series = relationship('Series')
    candidate_episodes = relationship('CandidateEpisode', cascade='all, delete-orphan')
    selected_episode = relationship('SelectedEpisode', back_populates='wtv_file', uselist=False,
                                    cascade='all, delete-orphan')


class SelectedEpisode(Base):
    __tablename__ = 'selected_episode'

    # id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey('candidate_episode.id'), nullable=False)
    episode = relationship('CandidateEpisode', uselist=False)
    wtv_file_id = Column(String(256), ForeignKey('wtv_file.filename'), nullable=False, primary_key=True)
    wtv_file = relationship('WtvFile', uselist=False, back_populates='selected_episode')


class WtvDb():
    def __init__(self, db_file):
        if ':memory:' == db_file:
            self._engine = create_engine('sqlite:///:memory:', echo=False)
        else:
            path = os.path.abspath(db_file)
            self._engine = create_engine('sqlite:///' + path, echo=False)
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)
        self._session = None

    def begin(self):
        if self._session:
            self._session.close()
        self._session = self._Session()

    def end(self):
        self._session.close()
        self._session = None

    def _check_session(self):
        if self._session is None:
            raise Exception('Session is None. Call begin()')

    def store_candidates(self, tvdb, wtv_filename, meta, episodes):
        self._check_session()
        series_name = meta.tags.get('Title', None)
        series_id = tvdb.get_series_id(series_name)
        if series_id:
            series = self.get_or_create_series(series_id, series_name)
            candidates = [self.from_tvdb(series, e) for e in episodes]
            wtv_file = WtvFile(filename=wtv_filename, description=meta.tags.get('WM/SubTitleDescription', None),
                               series=series)
            wtv_file = self._session.merge(wtv_file)
            wtv_file.candidate_episodes = candidates
            self._session.commit()
        else:
            logger.warning('No series: {}'.format(series_name))

    def from_tvdb(self, series, e):
        self._check_session()
        return self._session.merge(CandidateEpisode(id=int(e['id']),
                                                    name=e['episodeName'],
                                                    description=e['overview'],
                                                    air_date=datetime.strptime(e['firstAired'], '%Y-%m-%d').date(),
                                                    season=int(e['airedSeason']),
                                                    episode_num=int(e['airedEpisodeNumber']),
                                                    series=series))

    def get_or_create_series(self, series_id, series_name) -> Series:
        self._check_session()
        series = self._session.query(Series).get(series_id)
        if not series:
            series = Series(id=series_id, name=series_name)
            self.save(series)
        return series

    def save(self, obj):
        self._check_session()
        self._session.add(obj)
        self._session.commit()

    def find_series(self, series_name) -> Series:
        self._check_session()
        query = self._session.query(Series).filter(Series.name == series_name)
        return query.one_or_none()

    def get_selected_episode(self, wtv_filename) -> CandidateEpisode:
        self._check_session()
        query = self._session.query(WtvFile).filter(WtvFile.filename == wtv_filename)
        wtv = query.one_or_none()
        if wtv and wtv.selected_episode:
            return wtv.selected_episode.episode
        else:
            return None

    def get_wtv(self, filename) -> WtvFile:
        self._check_session()
        return self._session.query(WtvFile).get(filename)

    def delete_wtv(self, filename):
        self._check_session()
        wtv_file = self.get_wtv(filename)
        if wtv_file:
            self._session.delete(wtv_file)
            self._session.commit()
        else:
            raise Exception('File not found: {}'.format(filename))

    def resolve_all(self, skip_no_options):
        query = self._session.query(WtvFile).order_by(WtvFile.filename).all()
        for wtv_file in query:
            if not skip_no_options or len(wtv_file.candidate_episodes) > 0:
                print()
                if self.resolve(wtv_file):
                    return

    def custom_season_episode(self, wtv_file):
        season = input_int('Enter Season: ')
        if season is None:
            return None
        episode = input_int('Enter Episode Number: ')
        if episode is None:
            return None
        candidate_episode = CandidateEpisode(episode_num=episode, season=season, name='Episode #{}'.format(episode),
                                             series=wtv_file.series, wtv_file=wtv_file)
        self.save(candidate_episode)
        self.save(SelectedEpisode(episode=candidate_episode, wtv_file=wtv_file))

    def resolve(self, wtv_file):
        while True:
            print('----------------------------------------')
            print(wtv_file.filename)
            print(wtv_file.description)
            print()
            print('Options:')
            count = 1
            for ep in wtv_file.candidate_episodes:
                selected = ''
                if wtv_file.selected_episode and wtv_file.selected_episode.episode == ep:
                    selected = '*'
                print('  {}{}) '.format(selected, count), end='')
                print(ep.get_details())
                print('     Air Date: {}'.format(ep.air_date))
                print('     {}'.format(ep.description))
                count += 1
            print('  {}{}) Custom Season/Episode'.format('', count))
            selection = input('Selection: ')
            if selection == 'q':
                return True
            elif selection == '':
                return False
            elif is_int(selection):
                s = int(selection)
                if 0 < s < count:
                    if wtv_file.selected_episode:
                        wtv_file.selected_episode.episode = wtv_file.candidate_episodes[s - 1]
                        self.save(wtv_file)
                    else:
                        self.save(SelectedEpisode(episode=wtv_file.candidate_episodes[s - 1], wtv_file=wtv_file))
                elif s == count:
                    self.custom_season_episode(wtv_file)
                else:
                    print('Invalid input')
            else:
                print('Invalid input')
