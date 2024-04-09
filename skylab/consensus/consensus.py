import logging

from skylab.app.config import Config
from skylab.broker import MessageBroker
from skylab.storage.mongo import MongoService
from skylab.consensus.log import decode_log
from queue import Queue


class Consensus:
    TIMEOUT = -1
    HEARTBEAT = -1
    Q = Queue()

    def __init__(self, current_term=0, voted_for=None, log=[],
                 commit_index=-1, last_applied=-1,
                 next_index=[], match_index=[]):
        from skylab.consensus.state import FollowerState

        self.id = Config.node_id()
        self.current_term = current_term
        self.voted_for = voted_for
        self.log = log
        self.commit_index = commit_index
        self.last_applied = last_applied

        # Initialized to leader
        self.next_index = next_index
        self.match_index = match_index

        self.state = FollowerState(consensus_service=self)

    def store(self):
        mongo_service = MongoService.obtain()
        mongo_service.store_configuration(current_term=self.current_term, voted_for=self.voted_for,
                                          commit_index=self.commit_index, last_applied=self.last_applied,
                                          next_index=self.next_index, match_index=self.match_index)
        mongo_service.store_logs(logs=[log.encode() for log in self.log])

    def load(self):
        mongo_service = MongoService.obtain()
        success, configuration, logs = mongo_service.load()
        if not success:
            return

        self.current_term = configuration['current_term']
        self.voted_for = configuration['voted_for']
        self.commit_index = configuration['commit_index']
        self.last_applied = configuration['last_applied']
        self.next_index = configuration['next_index']
        self.match_index = configuration['match_index']
        self.log = [decode_log(log) for log in logs]

    def set_timer(self):
        self.state.set_timer()

    def alarm_handler(self, signum, frame):
        self.state.alarm_handler(signum, frame)

    def reset_timer(self):
        self.state.reset_timer()

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        return self.state.reply_append_entries(term=term, leader_id=leader_id, prev_log_index=prev_log_index,
                                               prev_log_term=prev_log_term, entries=entries,
                                               leader_commit=leader_commit)

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        return self.state.reply_vote_request(term=term, candidate_id=candidate_id, last_log_index=last_log_index,
                                             last_log_term=last_log_term)

    def request(self, log):
        return self.state.handle_request(log=log)

    def run(self):
        self.store()
        logging.info(self.__str__())

        return self.state.run()

    def start(self):
        self.load()
        self.run()

        from skylab.consensus.state import FollowerState, CandidateState, LeaderState
        while True:
            item = Consensus.Q.get()
            data_type = item['_data_type']
            if data_type == 'append_entries':
                term, success = self.reply_append_entries(
                    term=item['term'],
                    leader_id=item['leader_id'],
                    prev_log_index=item['prev_log_index'],
                    prev_log_term=item['prev_log_term'],
                    entries=item['entries'],
                    leader_commit=item['leader_commit']
                )
                message_broker = MessageBroker(channel_name=MessageBroker.Channels.CONSENSUS_TO_RPC)
                success = message_broker.produce(data_type=data_type, data={'_id': item['_id'], 'term': term,
                                                                            'success': success})
                if not success:
                    logging.error('[Exception|start]: Failed to produce by consensus')
                    continue

                if isinstance(self.state, CandidateState):
                    self.state = FollowerState(consensus_service=self)

            elif data_type == 'request_vote':
                term, granted = self.reply_vote_request(
                    term=item['term'],
                    candidate_id=item['candidate_id'],
                    last_log_index=item['last_log_index'],
                    last_log_term=item['last_log_term']
                )
                message_broker = MessageBroker(channel_name=MessageBroker.Channels.CONSENSUS_TO_RPC)
                success = message_broker.produce(data_type=data_type, data={'_id': item['_id'], 'term': term,
                                                                            'granted': granted})
                if not success:
                    logging.error('[Exception|start]: Failed to produce by consensus')
                    continue

            elif data_type == "add_log_request":
                success = self.request(log=item['log'])
                if not success:
                    logging.error('[Exception|start]: Failed to run the log command')
                    continue
                message_broker = MessageBroker(channel_name=MessageBroker.Channels.CONSENSUS_TO_REQUEST)
                produced_successfully = message_broker.produce(data_type=data_type, data={'_id': item['_id'],
                                                                                          'success': success})
                if not produced_successfully:
                    logging.error('[Exception|produce_by_consensus_to_request_rpc]: Failed to produce to request rpc')
                    continue

    def __str__(self):
        return f"{self.current_term} - {str(self.state)}\n[VOTED_FOR:{self.voted_for}, LAST_APPLIED:{self.last_applied}, " \
               f"COMMIT_INDEX:{self.commit_index}, NEXT_INDEX:{self.next_index}, " \
               f"MATCH_INDEX: {self.match_index}, LOG: {self.log}]"
