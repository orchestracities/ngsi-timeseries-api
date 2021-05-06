from redis import Redis
from rq import Queue

q = Queue(connection=Redis())
ids = q.finished_job_registry.get_job_ids()
js = [q.fetch_job(i) for i in ids]

# curl -v localhost:8668/v2/notify \
#      -H 'Content-Type: application/json' \
#      -H 'fiware-service: x' -H 'fiware-servicepath: /' \
#      -d @notify-load-test.json

# curl -v localhost:8668/wq/notifications \
#      -H 'fiware-service: x' -H 'fiware-servicepath: /'

# curl -v localhost:8668/wq/notifications/summary \
#      -H 'fiware-service: x' -H 'fiware-servicepath: /'

# curl -v localhost:8668/wq/notifications?taskStatus=succeeded \
#      -H 'fiware-service: x' -H 'fiware-servicepath: /'

# curl -v localhost:8668/wq/notifications/count \
#      -H 'fiware-service: x' -H 'fiware-servicepath: /'

# curl -v localhost:8668/wq/notifications/count?taskStatus=failed \
#      -H 'fiware-service: x' -H 'fiware-servicepath: /'

# curl -v -X DELETE localhost:8668/wq/notifications \
#      -H 'fiware-service: x' -H 'fiware-servicepath: /'


# from redis import Redis

r = Redis()

ks = r.keys()
ts = [r.type(k) for k in ks]
# ks
# [b'rq:queue:default', b'rq:job:a9a9cef1-cfad-4939-be50-79093ab4f63a', b'rq:job:4d5690dc-fb5a-48f8-9121-1f10cca98ed6', b'rq:queues']
# ts
# [b'list', b'hash', b'hash', b'set']
#

j = r.hgetall('rq:job:a9a9cef1-cfad-4939-be50-79093ab4f63a')
job_ks = r.keys('rq:job:*')
# job_ks
# [b'rq:job:a9a9cef1-cfad-4939-be50-79093ab4f63a', b'rq:job:4d5690dc-fb5a-48f8-9121-1f10cca98ed6']
#

r.lrange('rq:queue:default', 0, -1)
# [b'4d5690dc-fb5a-48f8-9121-1f10cca98ed6', b'a9a9cef1-cfad-4939-be50-79093ab4f63a']
#

r.smembers('rq:queues')
# {b'rq:queue:default'}

r.zrange('rq:finished:default', 0, -1)
# [b'eA==:Lw==:"":NWU0MDhjZDNkZDllNDQ1ZDhhYTZkNTVkODg2MTcyYWM=', b'eA==:Lw==:"":ZDNhODBhOWE5NGM5NDZmZWJhMmE0MmM4YjBkNDFkYjc=', b'eA==:Lw==:"":YzI3MGEzZjVhOGRiNDI0OWI5ZjAwZGUwMTNmYWUwMWQ=', b'eA==:Lw==:"":MWNjMWYwM2I1ZmIwNGVhYzhhOThkYmY0ODdiN2VlMDg=']
r.zscan('rq:finished:default', cursor=0, match='eA==:Lw==*')
# (0, [(b'eA==:Lw==:"":NWU0MDhjZDNkZDllNDQ1ZDhhYTZkNTVkODg2MTcyYWM=', 1619795739.0), (b'eA==:Lw==:"":ZDNhODBhOWE5NGM5NDZmZWJhMmE0MmM4YjBkNDFkYjc=', 1619795739.0), (b'eA==:Lw==:"":YzI3MGEzZjVhOGRiNDI0OWI5ZjAwZGUwMTNmYWUwMWQ=', 1619795740.0), (b'eA==:Lw==:"":MWNjMWYwM2I1ZmIwNGVhYzhhOThkYmY0ODdiN2VlMDg=', 1619795741.0)])
r.zscan('rq:finished:default', cursor=0, match='eA==:Lw==1*')
# (0, [])
