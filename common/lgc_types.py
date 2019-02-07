class LGCError:
    OK = "OK"
    INVALID_DATA = "INVDATA"
    SYSTEM_ERROR = "SYS"
    DB_ERROR = "DB"

    class Meta:
        abstract = True

class ReqAction:
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"

    class Meta:
        abstract = True

class ReqType:
    CASE = "EM"
    HR = "HR"

    class Meta:
        abstract = True
