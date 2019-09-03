from enum import Enum

class LGCError:
    OK = 'OK'
    INVALID_DATA = 'INVDATA'
    SYSTEM_ERROR = 'SYS'
    DB_ERROR = 'DB'

    class Meta:
        abstract = True

class ReqAction:
    ADD = 'add'
    UPDATE = 'update'
    DELETE = 'delete'

    class Meta:
        abstract = True

class ReqType:
    CASE = 'EM'
    HR = 'HR'

    class Meta:
        abstract = True

class MsgType(Enum):
    NEW_EM = 1,
    NEW_HR = 2,
    DEL = 3,
    PW_RST = 4,
    MODERATION = 5,
    DEL_REQ = 6,
    HR_INIT_ACCOUNT = 7,
