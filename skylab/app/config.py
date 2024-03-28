from dotenv import dotenv_values


class Config:
    _loaded = {}

    @classmethod
    def load(cls, file: str = ".env"):
        cls._loaded = dotenv_values(file)

    @classmethod
    def grpc_server_host(cls) -> str:
        return cls._loaded.get("GRPC_SERVER_HOST", "localhost")

    @classmethod
    def grpc_server_port(cls) -> int:
        return int(cls._loaded.get("GRPC_SERVER_PORT", "50051"))

    @classmethod
    def proto_files(cls) -> list:
        return list(cls._loaded.get("PROTO_FILES").split(","))

    @classmethod
    def timeout(cls) -> int:
        return int(cls._loaded.get("TIMEOUT"))

    @classmethod
    def timeout_delta(cls) -> int:
        return int(cls._loaded.get("TIMEOUT_DELTA"))

    @classmethod
    def node_id(cls) -> int:
        return int(cls._loaded.get("NODE_ID"))

    @classmethod
    def trusted_nodes(cls) -> list:
        return list(cls._loaded.get("TRUSTED_NODES").split(","))

    @classmethod
    def heartbeat(cls) -> int:
        return int(cls._loaded.get("HEARTBEAT"))

    @classmethod
    def heartbeat_delta(cls) -> int:
        return int(cls._loaded.get("HEARTBEAT_DELTA"))

    @classmethod
    def append_entries_timeout(cls) -> int:
        return int(cls._loaded.get("APPEND_ENTRIES_TIMEOUT"))

    @classmethod
    def request_vote_timeout(cls) -> int:
        return int(cls._loaded.get("REQUEST_VOTE_TIMEOUT"))

    @classmethod
    def redis_host(cls) -> str:
        return cls._loaded.get("REDIS_HOST")

    @classmethod
    def redis_port(cls) -> str:
        return cls._loaded.get("REDIS_PORT")

    @classmethod
    def redis_append_entries_queue(cls) -> str:
        return cls._loaded.get("REDIS_APPEND_ENTRIES_QUEUE")

    @classmethod
    def redis_request_vote_queue(cls) -> str:
        return cls._loaded.get("REDIS_REQUEST_VOTE_QUEUE")
