import datetime
import logging

log = logging.getLogger('lgc')

def session_cache_add(session, key, val, expires=None):
    if expires:
        ts = datetime.datetime.now() + datetime.timedelta(minutes=expires)
        ts = ts.strftime('%Y-%m-%d %H:%M')
    else:
        ts = None
    entry = {
        'ts': ts, 'val': val,
    }
    session[key] = entry
    log.debug('setting `%s` in cache', key)

def session_cache_del(session, key):
    try:
        del session[key]
    except:
        pass

def session_cache_get(session, key):
    entry = session.get(key)
    if entry == None:
        return None

    if entry['ts']:
        ts = datetime.datetime.strptime(entry['ts'], '%Y-%m-%d %H:%M')
        if datetime.datetime.now() > ts:
            log.debug('entry `%s` expired', key)
            session_cache_del(session, key)
            return None

    log.debug('found entry in cache for `%s`', key)
    return entry['val']
