import time

from django.template import Context, loader
from django.http import HttpResponse

def index(request, view_id):
    t = loader.get_template(view_id)
    c = Context({'cs': time.strftime("%Y/%m/%d-%H:%M:%S", time.localtime(time.time()-60*60)),
                 'ce': time.strftime("%Y/%m/%d-%H:%M:%S", time.localtime()),
                 'metric': 'cpu_user',
                 'hostid': 'cloud1'})
    return HttpResponse(t.render(c))