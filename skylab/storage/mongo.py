from skylab.app.config import Config
from pymongo import MongoClient


class MongoService:
    _instance = None

    def __init__(self):
        self._uri = Config.mongo_uri()
        self._db = Config.mongo_database()
        self.client = MongoClient(self._uri)
        self.db = self.client[self._db]

    @classmethod
    def obtain(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def store_configuration(self, current_term: int, voted_for, commit_index: int, last_applied: int,
                            current_leader: int, next_index: list, match_index: list) -> bool:
        c = self.db['configuration']
        r = c.update_one(
            filter={'_id': 1},
            update={
                '$set': {'_id': 1, 'current_term': current_term, 'voted_for': voted_for, 'commit_index': commit_index,
                         'last_applied': last_applied, 'current_leader': current_leader, 'next_index': next_index,
                         'match_index': match_index}},
            upsert=True
        )
        return r.acknowledged

    # logs should be list of dicts
    def store_logs(self, logs: list) -> bool:
        _c = self.db['configuration']
        last_stored_log_index = _c.find_one({
            '_id': 2
        })
        if not last_stored_log_index:
            last_stored_log_index = {}
        last_stored_log_index = last_stored_log_index.get('last_index', 0)

        logs = [{'_id': last_stored_log_index + log_index + 1,
                 'term': log['term'],
                 'command': log['command']}
                for log_index, log in enumerate(logs)]

        if not logs[last_stored_log_index:]:
            return True

        c = self.db['logs']
        r = c.insert_many(logs[last_stored_log_index:])
        if not r.acknowledged:
            return False

        r = _c.update_one(
            filter={'_id': 2},
            update={
                '$set': {'_id': 2,
                         'last_index': last_stored_log_index + \
                                       len(logs[last_stored_log_index:])}},
            upsert=True
        )
        if not r.acknowledged:
            return False

        return True

    def load(self) -> (bool, dict, dict):
        c = self.db['configuration']
        configuration = c.find_one(
            filter={'_id': 1}
        )

        if not configuration:
            return False, {}, {}

        c = self.db['logs']
        logs = c.find({})

        return True, configuration, logs
